# --- Filename: Extensions/unity_project_support/plugin.py ---
import os

class SMXExtension:
    """
    This extension registers the 'Suits (Unity Project)' library type
    and provides the custom logic to scan its unique folder structure,
    turning a Unity project folder into a live mod library.
    """
    def __init__(self):
        self.name = "Unity Project Support"
        self.description = "Adds support for reading a Unity project's suit database structure as a live mod library."
        self.version = "1.0.1" # Version bump for corrected scanner logic
        self.app = None

    def initialize(self, app):
        """Called by the main application to let the extension integrate itself."""
        print(f"INFO: Initializing extension '{self.name}' v{self.version}")
        self.app = app
        
        # Corrected the keyword arguments to match the function definition
        self.app.register_library_scanner(
            type_name="Suits (Unity Project)", 
            func=self.scan_unity_project_folder
        )

    def on_close(self):
        """Called when the main application is closing."""
        print(f"INFO: Closing extension '{self.name}'.")

    def scan_unity_project_folder(self, base_path):
        """
        The custom scanning logic for 'Suits (Unity Project)' libraries.
        This correctly scans the structure: base_path/Category/ModName/ModName.zip
        """
        library_data = {}
        
        try:
            # Level 1: Iterate through CATEGORY folders (e.g., "Character", "Country")
            for category_folder_name in os.listdir(base_path):
                category_path = os.path.join(base_path, category_folder_name)
                if not os.path.isdir(category_path):
                    continue
                
                # Initialize the list for this category's mods
                library_data[category_folder_name] = []
                
                # --- THE FIX IS HERE ---
                # Level 2: Iterate through MOD folders inside the category (e.g., "Buster")
                for mod_folder_name in os.listdir(category_path):
                    mod_path = os.path.join(category_path, mod_folder_name)
                    if not os.path.isdir(mod_path):
                        continue

                    # Level 3: Look for the ZIP file inside the mod folder
                    # The zip is expected to have the same name as its containing folder.
                    zip_file_path = os.path.join(mod_path, f"{mod_folder_name}.zip")
                    
                    if os.path.exists(zip_file_path):
                        # Use the main app's public helper to get details from the zip.
                        # We tell it the mod is of type "Suits" so it knows what to look for inside.
                        details = self.app.data_manager.get_local_mod_details_from_zip(zip_file_path, "Suits")
                        if details:
                            library_data[category_folder_name].append(details)
            
            # Sort the mods within each category alphabetically for a clean display.
            for category in library_data:
                library_data[category].sort(key=lambda x: x['name'])

        except Exception as e:
            # Use the main app's UI logger to safely report any errors during scanning.
            self.app.log_to_ui(f"Error reading Unity library at '{base_path}': {e}")
        
        return library_data