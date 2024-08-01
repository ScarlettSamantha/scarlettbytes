from flask import Flask, Response, send_file, render_template, redirect
import requests
from typing import Optional, Dict, Any
from werkzeug import Response as WerkzeugResponse
from datetime import datetime, timedelta

app = Flask(import_name=__name__)

# Cache for the GPG key and the time it was last updated
_key_cache: str | None = None
_key_cache_time: datetime | None = None


CACHE_TIMEOUT: int = 300  # Cache timeout in seconds
git_cache: Dict[Any, Any] = {}


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
def lshw_parser() -> WerkzeugResponse:
    return redirect(
        location="https://github.com/ScarlettSamantha/lshw-parser", code=301
    )


@app.route("/lshw-parser/download", methods=["GET"])
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
def openciv() -> WerkzeugResponse:
    return redirect(location="https://github.com/ScarlettSamantha/OpenCiv", code=301)


@app.route("/openciv/download", methods=["GET"])
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
def cv_download() -> Response:
    # Serve the CV PDF file and force it to download
    return send_file(
        path_or_file="files/scarlett_verheul_cv.pdf",
        mimetype="application/pdf",
        as_attachment=True,
    )


@app.route(rule="/cv/download/key", methods=["GET"])
def cv_download_key() -> Response:
    # Serve the PGP signature for the CV and force it to download
    return send_file(
        path_or_file="files/cv.pdf.sig",
        mimetype="application/pgp-signature",
        as_attachment=True,
    )


@app.route(rule="/cv", methods=["GET"])
def cv() -> Response:
    # Serve the CV PDF file
    return send_file(
        path_or_file="files/scarlett_verheul_cv.pdf", mimetype="application/pdf"
    )


@app.route(rule="/", defaults={"path": ""})
@app.route(rule="/<path:path>")
def catch_all(path: str) -> str:
    # Render the home page template for any undefined routes
    return render_template(template_name_or_list="home.j2")


if __name__ == "__main__":
    # Run the Flask application
    app.run(host="0.0.0.0", port=8000)
