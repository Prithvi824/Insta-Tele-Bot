import ssl
import time
import random
from typing import TypedDict
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials

class PickOne(TypedDict):
    kind: str
    mimeType: str
    id: str
    name: str

class DriveHandler:
    """
    Represents the drive object with custom functions and operations
    """

    def __init__(self, creds_file, folder_id):
        """
        @param creds_file: The name of the credentials file
        @param folder_id: The parent folder Id to interact with
        """

        # Initializes the authentication
        creds = Credentials.from_service_account_file(creds_file, scopes=['https://www.googleapis.com/auth/drive'])
        self.drive = build('drive', 'v3', credentials=creds)
        self.folder_id = folder_id

    def upload(self, file, file_type, file_name, folder_id = ""):
        """
        Uploads a file to drive

        => file: The path of the file to upload
        => type: The type of the file
        => file_name: The name of file to store on drive

        `returns`: The id of the uploaded file
        """
        folder = folder_id if folder_id else self.folder_id
        file_metadata = {'name': file_name, 'parents': [folder]}
        media = MediaFileUpload(file, mimetype=file_type, resumable=True)
        file = self.drive.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return file.get('id', None)
    
    def get_download_link(self, file_id):
        """
        Creates a downloadable link of a file
        => file_id: The id of the file of which link should be generated
        `returns` The download link of the file
        """
        # Change the permission to be available to anyone
        self.drive.permissions().create(fileId=file_id, body={'type': 'anyone', 'role': 'reader'}).execute()

        # Create the download link
        result = self.drive.files().get(fileId=file_id, fields='webContentLink').execute()

        # Return the download link
        return result.get('webContentLink')

    def list_subdirectories(self) -> list[dict]:
        """
        List the sub-directories of a folder
        """
        query = f"'{self.folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        results = self.drive.files().list(q=query, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])
        return items

    def get_list(self, folder_id = "") -> list:
        """
        To get the list of all the files and folders in the specified drive folder.
        
        @returns a list containing objects with `kind`, `mimeType`, `id`, `name` keys of each file/folder
        """
        files = []
        page_token = None
        folder = folder_id if folder_id else self.folder_id

        while True:
            response = self.drive.files().list(q=f"'{folder}' in parents and trashed=false",
                                            fields="nextPageToken, files(kind, mimeType, id, name)",
                                            pageToken=page_token).execute()
            files.extend(response.get('files', []))
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break

        return files

    def pick_one(self, folder_id = "") -> PickOne:
        """
        Used to pick a random file from drive
        @returns a random file object `kind`, `mimeType`, `id`, `name` keys
        """
        folder = folder_id if folder_id else self.folder_id
        files = self.get_list(folder)
        random_file = random.choice(files) if files else []
        return random_file

    def delete_one(self, file_id):
        """
        Deletes a file from drive based on its id
        @param file_id
        @returns {null}
        """
        max_retries = 5
        for attempt in range(max_retries):
            try:
                self.drive.files().delete(fileId=file_id).execute()
                return True
            except (HttpError, ssl.SSLEOFError) as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    return False
