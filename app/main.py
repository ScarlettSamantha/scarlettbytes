from flask import send_file, abort, Flask, request, safe_join
import os
import mimetypes
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Get the list of folders to serve from environment variable
serve_folders_env = os.getenv("SERVE_FOLDERS", "")
serve_folders = [
    os.path.abspath(folder.strip())
    for folder in serve_folders_env.split(",")
    if folder.strip()
]

if not serve_folders:
    logging.warning(
        "No folders specified in SERVE_FOLDERS environment variable. Defaulting to '/app/files'."
    )
    serve_folders = [os.path.abspath("/app/files")]

logging.info(f"Serving files from the following directories: {serve_folders}")


@app.route("/<path:filename>")
def serve_file(filename: str):
    for folder in serve_folders:
        try:
            file_path = safe_join(folder, filename)
            if file_path and os.path.exists(file_path):
                mime_type, _ = mimetypes.guess_type(file_path)
                as_attachment = mime_type is not None and mime_type.startswith(
                    "application/octet-stream"
                )
                return send_file(
                    file_path, mimetype=mime_type, as_attachment=as_attachment
                )
        except Exception as e:
            logging.error(f"Error serving file '{filename}': {e}")
    logging.error(f"File not found: {filename}")
    abort(404)


@app.errorhandler(404)
def not_found(error):
    return "File not found", 404


@app.errorhandler(500)
def server_error(error):
    return "Internal server error", 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
