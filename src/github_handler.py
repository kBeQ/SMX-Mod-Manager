# --- Filename: src/github_handler.py ---
import requests
import base64
import json
import os

# --- Configuration ---
# This points to your repository.
GITHUB_REPO_OWNER = "kbeq"  # Replace with your GitHub username
GITHUB_REPO_NAME = "SMX-Mod-Manager" # Replace with your repo name
EXTENSIONS_PATH_IN_REPO = "Extensions"
API_BASE_URL = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents/"

class GitHubHandler:
    """Handles fetching extension data from the central GitHub repository."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'Accept': 'application/vnd.github.v3+json'})

    def get_available_extensions(self):
        """
        Fetches the list of available extensions and their metadata from GitHub.
        Returns a dictionary of {extension_folder_name: metadata}.
        """
        extensions_url = f"{API_BASE_URL}{EXTENSIONS_PATH_IN_REPO}"
        available_extensions = {}
        
        try:
            response = self.session.get(extensions_url)
            response.raise_for_status() # Raises an exception for bad status codes (4xx or 5xx)
            
            for item in response.json():
                if item['type'] == 'dir':
                    extension_name = item['name']
                    manifest = self._get_manifest(extension_name)
                    if manifest:
                        available_extensions[extension_name] = manifest
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Could not fetch extension list from GitHub: {e}")
            return None # Indicates an error
            
        return available_extensions

    def _get_manifest(self, extension_name):
        """Fetches and parses the manifest.json for a specific extension."""
        manifest_url = f"{API_BASE_URL}{EXTENSIONS_PATH_IN_REPO}/{extension_name}/manifest.json"
        try:
            response = self.session.get(manifest_url)
            response.raise_for_status()
            content = base64.b64decode(response.json()['content']).decode('utf-8')
            return json.loads(content)
        except (requests.exceptions.RequestException, json.JSONDecodeError, KeyError) as e:
            print(f"ERROR: Could not get manifest for '{extension_name}': {e}")
            return None

    def download_extension(self, extension_name, target_base_path):
        """
        Downloads all files for a given extension into the target path.
        Returns True on success, False on failure.
        """
        local_extension_path = os.path.join(target_base_path, extension_name)
        os.makedirs(local_extension_path, exist_ok=True)
        
        api_path = f"{EXTENSIONS_PATH_IN_REPO}/{extension_name}"
        
        print(f"INFO: Starting download for extension '{extension_name}'...")
        return self._recursively_download(api_path, local_extension_path)

    def _recursively_download(self, repo_path, local_path):
        """Helper function to recursively download files and create directories."""
        contents_url = f"{API_BASE_URL}{repo_path}"
        try:
            response = self.session.get(contents_url)
            response.raise_for_status()
            
            for item in response.json():
                item_name = item['name']
                item_local_path = os.path.join(local_path, item_name)
                
                if item['type'] == 'dir':
                    os.makedirs(item_local_path, exist_ok=True)
                    self._recursively_download(item['path'], item_local_path)
                elif item['type'] == 'file':
                    file_response = self.session.get(item['download_url'])
                    file_response.raise_for_status()
                    with open(item_local_path, 'wb') as f:
                        f.write(file_response.content)
            return True
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Failed during download of '{repo_path}': {e}")
            return False