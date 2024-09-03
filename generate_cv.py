import os
import io
import gnupg
from typing import Optional
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, HttpRequest

# Define the scope and authenticate with the Google API
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
SERVICE_ACCOUNT_FILE = "path/to/your/service-account-file.json"

credentials: Credentials = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
service = build("drive", "v3", credentials=credentials)


def download_google_doc_as_pdf(file_id: str, destination: str) -> str:
    """
    Downloads a Google Docs file as a PDF and saves it to the destination.

    Args:
    file_id (str): The ID of the Google Docs file.
    destination (str): The path where the PDF will be saved.

    Returns:
    str: The path to the saved PDF file.
    """
    request: HttpRequest = service.files().export_media(
        fileId=file_id, mimeType="application/pdf"
    )
    with io.FileIO(destination, "wb") as fh:
        downloader: MediaIoBaseDownload = MediaIoBaseDownload(fh, request)
        done: bool = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Download {int(status.progress() * 100)}%")
    return destination


def sign_pdf_with_gpg(
    pdf_path: str, gpg_home: str, passphrase: str, output_folder: str
) -> str:
    """
    Signs a PDF file using GPG and saves the signature in the output folder.

    Args:
    pdf_path (str): The path to the PDF file to be signed.
    gpg_home (str): The home directory for GPG.
    passphrase (str): The passphrase for the GPG key.
    output_folder (str): The folder where the signed PDF and signature file will be saved.

    Returns:
    str: The path to the signed PDF file.
    """
    gpg = gnupg.GPG(gnupghome=gpg_home)
    output_path: str = os.path.join(output_folder, os.path.basename(pdf_path))
    signature_path: str = f"{output_path}.sig"

    with open(pdf_path, "rb") as f:
        signed_data: Optional[gnupg.SignResult] = gpg.sign_file(
            f, passphrase=passphrase, output=signature_path
        )

    if not signed_data:
        raise Exception("GPG signing failed")

    os.rename(pdf_path, output_path)
    return output_path


def main():
    # Configuration
    file_id = "your-google-doc-file-id"
    download_destination = "path/to/save/your.pdf"
    gpg_home = "path/to/your/.gnupg"
    passphrase = "your-gpg-passphrase"
    output_folder = "path/to/output/folder"

    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Download Google Docs as PDF
    pdf_path = download_google_doc_as_pdf(file_id, download_destination)

    # Sign PDF with GPG
    signed_pdf_path = sign_pdf_with_gpg(pdf_path, gpg_home, passphrase, output_folder)

    print(f"Signed PDF saved to: {signed_pdf_path}")
    print(f"Signature file saved to: {signed_pdf_path}.sig")


if __name__ == "__main__":
    main()
