import dropbox
import os
import logging

import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class DropboxSyncBot:
    def __init__(self, access_token, webhook_url):
        self.dbx = dropbox.Dropbox(access_token)
        self.webhook_url = webhook_url

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

    # def sync_folder(self, local_folder, dropbox_folder):
        # for root, dirs, files in os.walk(local_folder):
            # for dir in dirs.copy():  # We use .copy() to iterate over a copy of the list, so removing items won't cause issues
                # local_dir_path = os.path.join(root, dir)
                # relative_dir_path = os.path.relpath(local_dir_path, local_folder)
                # dropbox_dir_path = os.path.join(dropbox_folder, relative_dir_path)
                # if self.directory_exists(dropbox_dir_path):
                    # logging.info(f"Skipping existing directory: {dropbox_dir_path}")
                    # dirs.remove(dir)

            # for file in files:
                # if file == ".DS_Store":
                    # continue  # skip .DS_Store files
                
                # local_path = os.path.join(root, file)
                # relative_path = os.path.relpath(local_path, local_folder)
                # dropbox_path = os.path.join(dropbox_folder, relative_path)
                # if not self.file_exists(dropbox_path):
                    # logging.info(f"Attempting to upload: {local_path} to {dropbox_path}")
                    # self.upload_file(local_path, dropbox_path)
                    # logging.info(f"Uploaded {local_path} to {dropbox_path}")

    def send_discord_embed(self, title, directory_name, url, artist, page_type):
        data = {
            "embeds": [{
                "title": title,
                "color": 3066993,  # You can change this color if you want
                "fields": [
                    {
                        "name": "Artist",
                        "value": artist,
                        "inline": False
                    },
                    {
                        "name": "Page Type",
                        "value": page_type,
                        "inline": False
                    },
                    {
                        "name": "Directory Name",
                        "value": directory_name,
                        "inline": False
                    },
                    {
                        "name": "Link",
                        "value": f"[Open in Dropbox]({url})",
                        "inline": False
                    }
                ]
            }]
        }
        response = requests.post(self.webhook_url, json=data)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(err)
        else:
            print("Payload delivered successfully, code {}.".format(response.status_code))

    def sync_folder(self, local_folder, dropbox_folder):
        for root, dirs, files in os.walk(local_folder):

            for dir in dirs.copy():  # We use .copy() to iterate over a copy of the list, so removing items won't cause issues
                local_dir_path = os.path.join(root, dir)
                relative_dir_path = os.path.relpath(local_dir_path, local_folder)
                dropbox_dir_path = os.path.join(dropbox_folder, relative_dir_path)

                # Check if the directory is two levels down from the root (i.e., it's inside "feed" or "artist")
                is_two_levels_down = os.path.dirname(os.path.dirname(local_dir_path)) == local_folder

                if self.directory_exists(dropbox_dir_path) and is_two_levels_down:
                    logging.info(f"Skipping existing directory: {dropbox_dir_path}")
                    dirs.remove(dir)  # remove from dirs list to prevent further os.walk into this directory
                elif not self.directory_exists(dropbox_dir_path):
                    base_url = "https://www.dropbox.com/home"
                    full_link = f"{base_url}{dropbox_dir_path}"
                    # Extracting artist and page type
                    _, _, artist, page_type, _ = dropbox_dir_path.split('/')
                    directory_name = os.path.basename(dropbox_dir_path)  # extract the last part of the path
                    self.send_discord_embed("New Directory Synced to Dropbox", directory_name, full_link, artist, page_type)

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
