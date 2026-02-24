"""
Script to fetch data from APIs or databases
"""
import os
import logging
import gdown
import mimetypes
import requests
from urllib.parse import unquote

logger = logging.getLogger(__name__)

class DataFetcher:
    def __init__(self, output_folder="./public/"):
        """Initialize data fetcher with output folder."""
        self.output_folder = output_folder

    def get_filename_from_headers(self, drive_link: str) -> str | None:
        """Get filename from Google Drive headers."""
        file_id = drive_link.split("/")[-2]
        url = f"https://drive.google.com/uc?id={file_id}"

        response = requests.head(url, allow_redirects=True)
        content_disposition = response.headers.get("Content-Disposition")

        if content_disposition:
            filename = content_disposition.split("filename=")[-1].strip('"')
            return unquote(filename)
        
        return None

    def download_from_drive(self, drive_link: str, output_folder: str | None) -> str:
        """Download a file from Google Drive.
        
        Args:
            drive_link (str): The Google Drive shareable link
            output_folder (str, optional): Folder to save the file. Defaults to self.output_folder.
        
        Returns:
            str: Path to the downloaded file
        """
        output_folder = output_folder or self.output_folder
        os.makedirs(output_folder, exist_ok=True)
        
        file_id = drive_link.split("/")[-2]
        guessed_filename = self.get_filename_from_headers(drive_link)
        
        output_path = os.path.join(output_folder, guessed_filename or "downloaded_file")
        logger.info(f"Downloading file from Google Drive to {output_path}")
        
        gdown.download(f"https://drive.google.com/uc?id={file_id}", output_path, quiet=False)

        if not guessed_filename:
            file_type, _ = mimetypes.guess_type(output_path)
            if file_type:
                extension = mimetypes.guess_extension(file_type)
                if extension:
                    new_file_path = output_path + extension
                    os.rename(output_path, new_file_path)
                    logger.info(f"Renamed file to {new_file_path}")
                    return new_file_path

        return output_path

# Create a global instance for easy access
data_fetcher = DataFetcher()
