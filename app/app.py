import warnings
from flask import Flask, Response, send_file, render_template, redirect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests
from pymemcache.client import base
from typing import Optional, Dict, Any
from werkzeug import Response as WerkzeugResponse
from datetime import datetime, timedelta

# Suppress the specific warning about in-memory storage for Flask-Limiter
warnings.filterwarnings(
    "ignore",
    message="Using the in-memory storage for tracking rate limits as no storage was explicitly specified",
)

app = Flask(import_name=__name__)

# Initialize Flask-Limiter with Memcached storage
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memcached://memcached:11211",
    app=app,
    default_limits=["200 per day", "50 per hour"],
)

# Configure Memcached client
mc = base.Client(server=("memcached", 11211))

# Cache for the GPG key and the time it was last updated
_key_cache: str | None = None
_key_cache_time: datetime | None = None

CACHE_TIMEOUT: int = 300  # Cache timeout in seconds
git_cache: Dict[Any, Any] = {}


def get_git_info(author: str, repo: str) -> Dict[str, str]:
    """
    Get the short hash and branch name of the latest commit from the GitHub repository.

    :param author: The author of the repository
    :param repo: The name of the repository
    :return: Dictionary containing the short hash and branch name
    """
    api_url = f"https://api.github.com/repos/{author}/{repo}/commits"
    response = requests.get(api_url)

    if response.status_code == 200:
        latest_commit = response.json()[0]
        commit_hash = latest_commit["sha"][:7]
        branch_name = "main"  # Assuming the main branch is 'main'
        return {"commit_hash": commit_hash, "branch_name": branch_name}
    else:
        return {"commit_hash": "unknown", "branch_name": "unknown"}


def fetch_latest_package_zip(
    author: str, package: str, bypass_cache: bool = False
) -> Optional[str]:
    """
    Fetch the latest release zip URL for a given GitHub repository.

    :param author: The author of the repository
    :param package: The name of the repository
    :param bypass_cache: Whether to bypass the cache and fetch fresh data
    :return: The URL of the latest release zip file, or None if not found
    """
    cache_key: str = f"{author}/{package}"

    # Check cache first
    if not bypass_cache and cache_key in git_cache:
        cached_entry: Any = git_cache[cache_key]
        if datetime.now() - cached_entry["timestamp"] < CACHE_TIMEOUT:
            return cached_entry["zip_url"] + {"cached": True}

    # GitHub API URL to get the latest release information
    api_url: str = f"https://api.github.com/repos/{author}/{package}/releases/latest"

    # Make a GET request to the GitHub API
    response: requests.Response = requests.get(url=api_url)

    if response.status_code == 200:
        # Parse the JSON response to get the zipball_url
        latest_release: Any = response.json()
        zip_url: Any = latest_release.get("zipball_url")

        # Update cache
        git_cache[cache_key] = {"zip_url": zip_url, "timestamp": datetime.now()}

        return zip_url
    else:
        return None


@app.route(rule="/gpg", methods=["GET"])
@app.route(rule="/key", methods=["GET"])
@limiter.limit(limit_value="10 per minute")
def gpg() -> Response:
    global _key_cache, _key_cache_time
    # Check if the cache is empty or older than an hour
    if _key_cache is None or (
        _key_cache_time and (datetime.now() - _key_cache_time) > timedelta(hours=1)
    ):
        # Read the public key from the file
        with open(file="files/public_key.asc", mode="r") as f:
            _key_cache = f.read()
        # Update the cache time
        _key_cache_time = datetime.now()
    # Return the key in a preformatted HTML response
    return Response(response=f"<pre>{_key_cache}</pre>", mimetype="text/html")


@app.route(rule="/lshw-parser", methods=["GET"])
@limiter.limit(limit_value="5 per minute")
def lshw_parser() -> WerkzeugResponse:
    return redirect(
        location="https://github.com/ScarlettSamantha/lshw-parser", code=301
    )


@app.route(rule="/lshw-parser/download", methods=["GET"])
@limiter.limit(limit_value="5 per minute")
def lshw_parser_download() -> WerkzeugResponse:
    zip_url: str | None = fetch_latest_package_zip(
        author="ScarlettSamantha", package="lshw-parser"
    )

    if zip_url:
        return redirect(location=zip_url)
    else:
        return Response(
            response='{"error": "Unable to find the latest release zip URL."}',
            status=404,
            mimetype="application/json",
        )


@app.route(rule="/openciv", methods=["GET"])
@limiter.limit(limit_value="5 per minute")
def openciv() -> WerkzeugResponse:
    return redirect(location="https://github.com/ScarlettSamantha/OpenCiv", code=301)


@app.route(rule="/openciv/download", methods=["GET"])
@limiter.limit(limit_value="5 per minute")
def openciv_download() -> WerkzeugResponse:
    zip_url: str | None = fetch_latest_package_zip(
        author="ScarlettSamantha", package="OpenCiv"
    )

    if zip_url:
        return redirect(location=zip_url)
    else:
        return Response(
            response='{"error": "Unable to find the latest release zip URL."}',
            status=404,
            mimetype="application/json",
        )


@app.route(rule="/cv/download", methods=["GET"])
@limiter.limit(limit_value="10 per minute")
def cv_download() -> Response:
    # Serve the CV PDF file and force it to download
    return send_file(
        path_or_file="files/scarlett_verheul_cv.pdf",
        mimetype="application/pdf",
        as_attachment=True,
    )


@app.route(rule="/cv/download/key", methods=["GET"])
@limiter.limit(limit_value="10 per minute")
def cv_download_key() -> Response:
    # Serve the PGP signature for the CV and force it to download
    return send_file(
        path_or_file="files/cv.pdf.sig",
        mimetype="application/pgp-signature",
        as_attachment=True,
    )


@app.route(rule="/cv", methods=["GET"])
@limiter.limit(limit_value="10 per minute")
def cv() -> Response:
    # Serve the CV PDF file
    return send_file(
        path_or_file="files/scarlett_verheul_cv.pdf", mimetype="application/pdf"
    )


@app.route(rule="/", defaults={"path": ""})
@app.route(rule="/<path:path>")
@limiter.limit("10 per minute")
def catch_all(path: str) -> str:
    print("test")
    # Get the current Git commit hash and branch name
    git_info = get_git_info(
        author="ScarlettSamantha", repo="repository-name"
    )  # Replace 'repository-name' with your actual repo name
    # Render the home page template with the git information
    return render_template(
        template_name_or_list="home.j2",
        commit_hash=git_info["commit_hash"],
        branch_name=git_info["branch_name"],
    )
