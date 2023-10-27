import dropbox
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class DropboxSyncBot:
    def __init__(self, access_token):
        self.dbx = dropbox.Dropbox(access_token)

    def upload_file(self, file_path, destination_path):
        with open(file_path, "rb") as f:
            self.dbx.files_upload(f.read(), destination_path, mode=dropbox.files.WriteMode("overwrite"))

    def directory_exists(self, path):
        try:
            self.dbx.files_get_metadata(path)
            return True
        except dropbox.exceptions.ApiError as e:
            if isinstance(e.error, dropbox.files.GetMetadataError) and \
               isinstance(e.error.get_path(), dropbox.files.LookupError):
                return False
        raise

    def file_exists(self, path):
        try:
            self.dbx.files_get_metadata(path)
            return True
        except dropbox.exceptions.ApiError as e:
            if isinstance(e.error, dropbox.files.GetMetadataError) and \
               isinstance(e.error.get_path(), dropbox.files.LookupError):
                return False
            raise

    def sync_folder(self, local_folder, dropbox_folder):
        for root, dirs, files in os.walk(local_folder):
            for dir in dirs.copy():  # We use .copy() to iterate over a copy of the list, so removing items won't cause issues
                local_dir_path = os.path.join(root, dir)
                relative_dir_path = os.path.relpath(local_dir_path, local_folder)
                dropbox_dir_path = os.path.join(dropbox_folder, relative_dir_path)
                if self.directory_exists(dropbox_dir_path):
                    logging.info(f"Skipping existing directory: {dropbox_dir_path}")
                    dirs.remove(dir)

            for file in files:
                if file == ".DS_Store":
                    continue  # skip .DS_Store files
                
                local_path = os.path.join(root, file)
                relative_path = os.path.relpath(local_path, local_folder)
                dropbox_path = os.path.join(dropbox_folder, relative_path)
                if not self.file_exists(dropbox_path):
                    logging.info(f"Attempting to upload: {local_path} to {dropbox_path}")
                    self.upload_file(local_path, dropbox_path)
                    logging.info(f"Uploaded {local_path} to {dropbox_path}")
