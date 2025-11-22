from os import getenv
import warnings
from datetime import datetime, timedelta
import json
import re
from typing import Optional, Dict, Any, List, TypedDict, cast
from pathlib import Path

import requests
from flask import Flask, Response, send_file, render_template, redirect, request, abort
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pymemcache.client import base
from werkzeug import Response as WerkzeugResponse

warnings.filterwarnings(
    "ignore",
    message=(
        "Using the in-memory storage for tracking rate limits as no storage was "
        "explicitly specified"
    ),
)

app = Flask(import_name=__name__)

memcached_host = getenv("MEMCACHED_HOST", "scarlettbytes-memcached")

limiter: Limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=f"memcached://{memcached_host}:11211",
    app=app,
    default_limits=["200 per day", "50 per hour"],
)

mc = base.Client((memcached_host, 11211))

_key_cache: Optional[str] = None
_key_cache_time: Optional[datetime] = None

CACHE_TIMEOUT: int = 300

GITHUB_API_BASE: str = "https://api.github.com"
GITHUB_USER_AGENT: str = "scarlettbytes-site/1.0"
GITHUB_TOKEN: Optional[str] = getenv("GITHUB_TOKEN")

_logged_token_state: bool = False

BLOG_DIR: Path = Path("blog")
BLOG_CACHE_TIMEOUT: int = 60


description: str = (
    "Scarlett Samantha Verheul is a Software Developer from Rotterdam, "
    "Netherlands. I specialize in Python, Flask, Docker, DevOps, Linux, "
    "and Open Source."
)

default_template_vars: Dict[str, Any] = {
    "title": "Scarlett Samantha Verheul - Software Developer",
    "author": "Scarlett Samantha Verheul",
    "keywords": ",".join(
        [
            "Scarlett Samantha Verheul",
            "Scarlett VerheulScarlettSamantha",
            "Scarlett",
            "Software Developer",
            "Python",
            "Flask",
            "Docker",
            "DevOps",
            "Linux",
            "Open Source",
            "Rotterdam",
            "Netherlands",
            "Vacancies",
            "Jobs",
            "Hiring",
            "PHP",
            "Laravel",
            "Symfony",
        ]
    ),
    "description": description,
    "og_title": "Scarlett Samantha Verheul - Software Developer",
    "og_description": description,
}


class CommitInfo(TypedDict):
    sha: str
    message: str
    url: str
    date: str
    repo: str


class BlogPost(TypedDict):
    slug: str
    title: str
    date: str
    summary: str
    content: str


_blog_cache: Optional[List[BlogPost]] = None
_blog_cache_time: Optional[datetime] = None


def _cache_get(key: str) -> Optional[Dict[str, Any]]:
    try:
        raw = mc.get(key)
    except Exception as exc:
        app.logger.error("Memcached get error for key %s: %s", key, exc)
        return None

    if raw is None:
        return None

    try:
        if isinstance(raw, bytes):
            raw_str: str = raw.decode("utf-8")
        else:
            raw_str = str(raw)
        return json.loads(raw_str)
    except Exception as exc:
        app.logger.error("Failed to decode cache entry for key %s: %s", key, exc)
        return None


def _cache_set(key: str, value: Any, ttl: int = CACHE_TIMEOUT) -> None:
    try:
        mc.set(key, json.dumps(value), expire=ttl)
    except Exception as exc:
        app.logger.error("Memcached set error for key %s: %s", key, exc)


def _github_headers() -> Dict[str, str]:
    global _logged_token_state

    headers: Dict[str, str] = {
        "Accept": "application/vnd.github+json",
        "User-Agent": GITHUB_USER_AGENT,
    }

    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
        headers["X-GitHub-Api-Version"] = "2022-11-28"
        if not _logged_token_state:
            app.logger.info(
                "GITHUB_TOKEN detected; using authenticated GitHub requests."
            )
            _logged_token_state = True
    else:
        if not _logged_token_state:
            app.logger.warning(
                "GITHUB_TOKEN not configured; using unauthenticated GitHub API "
                "(very low rate limits, likely to hit 403)."
            )
            _logged_token_state = True

    return headers


def _github_get(
    path: str,
    params: Optional[Dict[str, Any]] = None,
    timeout: float = 5.0,
) -> Optional[requests.Response]:
    headers: Dict[str, str] = _github_headers()

    try:
        response: requests.Response = requests.get(
            url=f"{GITHUB_API_BASE}{path}",
            headers=headers,
            params=params,
            timeout=timeout,
        )
    except requests.RequestException as exc:
        app.logger.error("GitHub request error for %s: %s", path, exc, exc_info=True)
        return None

    app.logger.info(
        "GitHub GET %s status=%s reason=%s auth_header=%s",
        path,
        response.status_code,
        response.reason,
        "yes" if "Authorization" in headers else "no",
    )

    if response.status_code != 200:
        body_repr: str
        try:
            body_json: Any = response.json()
            body_repr = json.dumps(body_json)
        except ValueError:
            body_repr = response.text

        if len(body_repr) > 500:
            body_repr = body_repr[:500] + "...(truncated)"

        app.logger.error(
            "GitHub non-200 for %s: status=%s reason=%s body=%s",
            path,
            response.status_code,
            response.reason,
            body_repr,
        )

        return None

    return response


def fetch_recent_commits(
    author: str,
    repo: str,
    limit: int = 5,
    bypass_cache: bool = False,
) -> List[CommitInfo]:
    cache_key: str = f"github:repo_commits:{author}/{repo}:{limit}"

    if not bypass_cache:
        cached: Optional[Dict[str, Any]] = _cache_get(cache_key)
        if isinstance(cached, Dict) and isinstance(cached.get("commits"), list):
            raw_commits: List[Dict[str, Any]] = cached["commits"]
            commits_from_cache: List[CommitInfo] = []
            for item in raw_commits:
                item: Dict[str, Any] = item
                commits_from_cache.append(
                    CommitInfo(
                        sha=str(item.get("sha", "")),
                        message=str(item.get("message", "")),
                        url=str(item.get("url", "")),
                        date=str(item.get("date", "")),
                        repo=str(item.get("repo", f"{author}/{repo}")),
                    )
                )
            if commits_from_cache:
                return commits_from_cache

    response: Optional[requests.Response] = _github_get(
        path=f"/repos/{author}/{repo}/commits",
        params={"per_page": limit},
    )

    if response is None:
        app.logger.warning(
            "fetch_recent_commits: GitHub response was None for %s/%s",
            author,
            repo,
        )
        return []

    commits: List[CommitInfo] = []
    repo_display: str = f"{author}/{repo}"

    for item in response.json():
        item: Dict[str, Any] = item

        commit_data: Dict[str, Any] = cast(Dict[str, Any], item.get("commit", {}))
        author_info: Dict[str, Any] = cast(
            Dict[str, Any],
            commit_data.get("author", {}),
        )

        raw_date: str = str(author_info.get("date", ""))
        display_date: str = raw_date

        if raw_date:
            try:
                parsed: datetime = datetime.fromisoformat(
                    raw_date.replace("Z", "+00:00")
                )
                display_date = parsed.strftime("%Y-%m-%d")
            except ValueError:
                display_date = raw_date

        message: str = str(commit_data.get("message", "")).split("\n", 1)[0]

        commits.append(
            CommitInfo(
                sha=str(item.get("sha", ""))[:7],
                message=message,
                url=str(item.get("html_url", "")),
                date=display_date,
                repo=repo_display,
            )
        )

    _cache_set(
        cache_key,
        {"commits": commits},
        ttl=CACHE_TIMEOUT,
    )

    return commits


def fetch_user_recent_commits(
    username: str,
    limit: int = 5,
    bypass_cache: bool = False,
) -> List[CommitInfo]:
    cache_key: str = f"github:user_commits:{username}:{limit}"

    if not bypass_cache:
        cached: Optional[Dict[str, Any]] = _cache_get(cache_key)
        if isinstance(cached, Dict) and isinstance(cached.get("commits"), list):
            raw_commits: List[Dict[str, Any]] = cached["commits"]
            commits_from_cache: List[CommitInfo] = []
            for item in raw_commits:
                commits_from_cache.append(
                    CommitInfo(
                        sha=str(item.get("sha", "")),
                        message=str(item.get("message", "")),
                        url=str(item.get("url", "")),
                        date=str(item.get("date", "")),
                        repo=str(item.get("repo", "")),
                    )
                )
            if commits_from_cache:
                return commits_from_cache

    repos_response: Optional[requests.Response] = _github_get(
        path=f"/users/{username}/repos",
        params={"per_page": 20, "sort": "pushed"},
    )

    if repos_response is None:
        app.logger.warning(
            "fetch_user_recent_commits: GitHub repos response was None for user %s",
            username,
        )
        return []

    commits: List[CommitInfo] = []

    for repo_data in repos_response.json():
        repo_data: Dict[str, Any] = repo_data

        owner_login: str = str(
            cast(Dict[str, Any], repo_data.get("owner", {})).get("login") or username
        )
        repo_name: str = str(repo_data.get("name", ""))

        if not repo_name:
            continue

        per_repo_limit: int = min(3, limit)
        repo_commits: List[CommitInfo] = fetch_recent_commits(
            author=owner_login,
            repo=repo_name,
            limit=per_repo_limit,
            bypass_cache=bypass_cache,
        )

        for commit in repo_commits:
            commits.append(commit)
            if len(commits) >= limit:
                break

        if len(commits) >= limit:
            break

    if commits:
        _cache_set(
            cache_key,
            {"commits": commits},
            ttl=CACHE_TIMEOUT,
        )

    return commits


def get_git_info(author: str, repo: str) -> Dict[str, str]:
    cache_key: str = f"github:git_info:{author}/{repo}"

    cached: Optional[Dict[str, Any]] = _cache_get(cache_key)
    if isinstance(cached, Dict):
        commit_hash_cached: str = str(cached.get("commit_hash", "unknown"))
        branch_name_cached: str = str(cached.get("branch_name", "unknown"))
        if commit_hash_cached != "unknown":
            return {
                "commit_hash": commit_hash_cached,
                "branch_name": branch_name_cached,
            }

    response: Optional[requests.Response] = _github_get(
        path=f"/repos/{author}/{repo}/commits",
        params={"per_page": 1},
    )

    if response is None:
        app.logger.warning(
            "get_git_info: GitHub response was None for %s/%s", author, repo
        )
        return {"commit_hash": "unknown", "branch_name": "unknown"}

    data: List[Any] = response.json()
    if not data:
        app.logger.warning("get_git_info: empty JSON list for %s/%s", author, repo)
        return {"commit_hash": "unknown", "branch_name": "unknown"}

    latest_commit: Dict[str, Any] = cast(Dict[str, Any], data[0])
    commit_hash: str = str(latest_commit.get("sha", ""))[:7]

    info: Dict[str, str] = {
        "commit_hash": commit_hash or "unknown",
        "branch_name": "main",
    }

    _cache_set(cache_key, info, ttl=CACHE_TIMEOUT)

    return info


def fetch_latest_package_zip(
    author: str,
    package: str,
    bypass_cache: bool = False,
) -> Optional[str]:
    cache_key: str = f"github:latest_zip:{author}/{package}"

    if not bypass_cache:
        cached: Optional[Dict[str, Any]] = _cache_get(cache_key)
        if isinstance(cached, Dict) and cached.get("zip_url"):
            return str(cached["zip_url"])

    response: Optional[requests.Response] = _github_get(
        path=f"/repos/{author}/{package}/releases/latest",
        params=None,
    )

    if response is None:
        app.logger.warning(
            "fetch_latest_package_zip: GitHub response was None for %s/%s",
            author,
            package,
        )
        return None

    latest_release: Any = response.json()
    zip_url: Any = latest_release.get("zipball_url")
    if zip_url is None:
        app.logger.warning(
            "fetch_latest_package_zip: no zipball_url in latest release for %s/%s",
            author,
            package,
        )
        return None

    payload: Dict[str, Any] = {
        "zip_url": zip_url,
    }
    _cache_set(cache_key, payload, ttl=CACHE_TIMEOUT)

    return str(zip_url)


def _parse_blog_file(path: Path) -> Optional[BlogPost]:
    try:
        raw: str = path.read_text(encoding="utf-8")
    except OSError as exc:
        app.logger.error("Failed to read blog file %s: %s", path, exc)
        return None

    lines: List[str] = raw.splitlines()
    meta: Dict[str, str] = {}
    body_lines: List[str] = []
    in_header: bool = True
    started_header: bool = False

    for line in lines:
        stripped: str = line.strip()
        if not started_header and stripped == "---":
            started_header = True
            continue
        if in_header:
            if not stripped:
                in_header = False
                continue
            if ":" in line:
                key, value = line.split(":", 1)
                meta[key.strip().lower()] = value.strip()
            else:
                in_header = False
                body_lines.append(line)
        else:
            body_lines.append(line)

    slug: str = meta.get("slug") or path.stem
    title: str = meta.get("title") or path.stem.replace("-", " ").title()

    file_mtime: float = path.stat().st_mtime
    date_str: str = meta.get("date") or datetime.fromtimestamp(file_mtime).strftime(
        "%Y-%m-%d"
    )

    body: str = "\n".join(body_lines).strip()
    summary: str = meta.get("summary", "")

    if not summary:
        first_line: str = body.split("\n", 1)[0]
        if len(first_line) > 160:
            summary = first_line[:157].rstrip() + "..."
        else:
            summary = first_line

    return BlogPost(
        slug=slug,
        title=title,
        date=date_str,
        summary=summary,
        content=body,
    )


def get_blog_posts() -> List[BlogPost]:
    global _blog_cache, _blog_cache_time

    if (
        _blog_cache is not None
        and _blog_cache_time is not None
        and (datetime.now() - _blog_cache_time) < timedelta(seconds=BLOG_CACHE_TIMEOUT)
    ):
        return _blog_cache

    posts: List[BlogPost] = []

    if BLOG_DIR.exists() and BLOG_DIR.is_dir():
        for path in sorted(
            BLOG_DIR.glob("*.md"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        ):
            parsed: Optional[BlogPost] = _parse_blog_file(path)
            if parsed is not None:
                posts.append(parsed)

    _blog_cache = posts
    _blog_cache_time = datetime.now()

    return posts


@app.route(rule="/gpg", methods=["GET"])
@app.route(rule="/key", methods=["GET"])
@limiter.limit(limit_value="10 per minute")
def gpg() -> Response:
    global _key_cache, _key_cache_time

    if _key_cache is None or (
        _key_cache_time and (datetime.now() - _key_cache_time) > timedelta(hours=1)
    ):
        with open(file="files/public_key.asc", mode="r") as f:
            _key_cache = f.read()
        _key_cache_time = datetime.now()

    return Response(response=f"<pre>{_key_cache}</pre>", mimetype="text/html")


@app.route(rule="/lshw-parser", methods=["GET"])
@limiter.limit(limit_value="5 per minute")
def lshw_parser() -> WerkzeugResponse:
    return redirect(
        location="https://github.com/ScarlettSamantha/lshw-parser",
        code=301,
    )


@app.route(rule="/lshw-parser/download", methods=["GET"])
@limiter.limit(limit_value="5 per minute")
def lshw_parser_download() -> WerkzeugResponse:
    zip_url: Optional[str] = fetch_latest_package_zip(
        author="ScarlettSamantha",
        package="lshw-parser",
    )

    if zip_url:
        return redirect(location=zip_url)

    return Response(
        response='{"error": "Unable to find the latest release zip URL."}',
        status=404,
        mimetype="application/json",
    )


@app.route(rule="/openciv", methods=["GET"])
@limiter.limit(limit_value="5 per minute")
def openciv() -> WerkzeugResponse:
    return redirect(
        location="https://git.scarlettbytes.nl/scarlett/panda-openciv",
        code=301,
    )


@app.route(rule="/openciv/download", methods=["GET"])
@limiter.limit(limit_value="5 per minute")
def openciv_download() -> WerkzeugResponse:
    zip_url: Optional[str] = fetch_latest_package_zip(
        author="ScarlettSamantha",
        package="OpenCiv",
    )

    if zip_url:
        return redirect(location=zip_url)

    return Response(
        response='{"error": "Unable to find the latest release zip URL."}',
        status=404,
        mimetype="application/json",
    )


@app.route(rule="/json-inspector", methods=["GET"])
@limiter.limit(limit_value="10 per minute")
def json_inspector() -> WerkzeugResponse:
    return redirect(
        location="https://git.scarlettbytes.nl/scarlett/json-inspector",
        code=301,
    )


@app.route(rule="/json-inspector/download", methods=["GET"])
@limiter.limit(limit_value="10 per minute")
def json_inspector_download() -> WerkzeugResponse:
    zip_url: Optional[str] = fetch_latest_package_zip(
        author="ScarlettSamantha",
        package="json_inspector",
    )

    if zip_url:
        return redirect(location=zip_url)

    return Response(
        response='{"error": "Unable to find the latest release zip URL."}',
        status=404,
        mimetype="application/json",
    )


@app.route(rule="/cv/download", methods=["GET"])
@limiter.limit(limit_value="10 per minute")
def cv_download() -> Response:
    return send_file(
        path_or_file="files/scarlett_verheul_cv.pdf",
        mimetype="application/pdf",
        as_attachment=True,
    )


@app.route(rule="/cv/download/key", methods=["GET"])
@limiter.limit(limit_value="10 per minute")
def cv_download_key() -> Response:
    return send_file(
        path_or_file="files/cv.pdf.sig",
        mimetype="application/pgp-signature",
        as_attachment=True,
    )


@app.route(rule="/cv", methods=["GET"])
@limiter.limit(limit_value="10 per minute")
def cv() -> Response:
    return send_file(
        path_or_file="files/scarlett_verheul_cv.pdf",
        mimetype="application/pdf",
    )


@app.route(rule="/blog", methods=["GET"])
@limiter.limit(limit_value="10 per minute")
def blog_index() -> str:
    git_info: Dict[str, str] = get_git_info(
        author="ScarlettSamantha",
        repo="scarlettbytes",
    )

    posts: List[BlogPost] = get_blog_posts()

    return render_template(
        template_name_or_list="blog_index.j2",
        commit_hash=git_info["commit_hash"],
        branch_name=git_info["branch_name"],
        posts=posts,
        **default_template_vars,
    )


@app.route(rule="/blog/<slug>", methods=["GET"])
@limiter.limit(limit_value="10 per minute")
def blog_post(slug: str) -> str:
    git_info: Dict[str, str] = get_git_info(
        author="ScarlettSamantha",
        repo="scarlettbytes",
    )

    posts: List[BlogPost] = get_blog_posts()
    post: Optional[BlogPost] = None

    for candidate in posts:
        if candidate["slug"] == slug:
            post = candidate
            break

    if post is None:
        abort(404)

    return render_template(
        template_name_or_list="blog_post.j2",
        commit_hash=git_info["commit_hash"],
        branch_name=git_info["branch_name"],
        post=post,
        **default_template_vars,
    )


@app.route(rule="/", defaults={"path": ""})
@app.route(rule="/<path:path>")
@limiter.limit(limit_value="10 per minute")
def catch_all(path: str) -> str:
    git_info: Dict[str, str] = get_git_info(
        author="ScarlettSamantha",
        repo="scarlettbytes",
    )

    recent_commits: List[CommitInfo] = fetch_user_recent_commits(
        username="ScarlettSamantha",
        limit=5,
    )

    blog_posts: List[BlogPost] = get_blog_posts()
    recent_posts: List[BlogPost] = blog_posts[:3]

    return render_template(
        template_name_or_list="home.j2",
        commit_hash=git_info["commit_hash"],
        branch_name=git_info["branch_name"],
        recent_commits=recent_commits,
        recent_posts=recent_posts,
        **default_template_vars,
    )


@app.route(rule="/equipment", methods=["GET"])
@limiter.limit("10 per minute")
def equipment() -> str:
    git_info: Dict[str, str] = get_git_info(
        author="ScarlettSamantha",
        repo="scarlettbytes",
    )
    return render_template(
        template_name_or_list="equipment.j2",
        commit_hash=git_info["commit_hash"],
        branch_name=git_info["branch_name"],
        **default_template_vars,
    )


@app.route(rule="/datetime", methods=["GET"])
@limiter.limit(limit_value="10 per minute")
def datetime_endpoint() -> Response | str:
    default_format: str = "%Y-%m-%d %H:%M:%S"

    format_str: str = request.args.get(key="format", default=default_format)
    live: bool = request.args.get(key="live", default="false").lower() == "true"
    interval_str: str = request.args.get(key="interval", default="1000")

    if not re.match(pattern=r"^[%A-Za-z0-9\s\-\:\./]+$", string=format_str):
        return Response(response="Invalid format string.", status=400)

    if not interval_str.isdigit() or int(interval_str) <= 0:
        return Response(response="Invalid interval.", status=400)

    interval: int = int(interval_str)

    try:
        now: datetime = datetime.now()
        formatted_datetime: str = now.strftime(format=format_str)

        return render_template(
            template_name_or_list="datetime.j2",
            live=live,
            format_str=format_str,
            interval=interval,
            formatted_datetime=formatted_datetime,
        )
    except Exception as exc:
        app.logger.error("Error in datetime_endpoint: %s", exc, exc_info=True)
        return Response(response="Error formatting datetime.", status=500)
