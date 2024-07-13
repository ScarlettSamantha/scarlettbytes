from flask import send_file, abort, Flask
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


def get_mime_type_from_extension(extension: str):
    mime_types = {
        "txt": "text/plain",
        "html": "text/html",
        "json": "application/json",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "pdf": "application/pdf",
    }
    return mime_types.get(extension), mime_types


def find_possible_file_paths(base_filename: str):
    possible_files = [base_filename]
    _, mime_types = get_mime_type_from_extension("")
    possible_files.extend([f"{base_filename}.{ext}" for ext in mime_types.keys()])
    return possible_files


@app.route("/<path:filename>")
def serve_file(filename: str):
    # Separate the actual filename and the forced MIME type extension
    if "." in filename:
        base_filename, forced_extension = filename.rsplit(".", 1)
        forced_mime_type, _ = get_mime_type_from_extension(forced_extension)
    else:
        base_filename = filename
        forced_mime_type = None

    possible_files = (
        find_possible_file_paths(base_filename) if not forced_mime_type else [filename]
    )

    for folder in serve_folders:
        for possible_file in possible_files:
            try:
                # Construct the full file path
                file_path = os.path.abspath(os.path.join(folder, possible_file))
                # Ensure the file path is within the allowed folder
                if os.path.commonpath([file_path, folder]) == folder and os.path.exists(
                    file_path
                ):
                    mime_type = forced_mime_type or mimetypes.guess_type(file_path)[0]
                    as_attachment = mime_type is None or mime_type.startswith(
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
