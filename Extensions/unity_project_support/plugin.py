# --- Filename: Extensions/unity_project_support/plugin.py ---
import os

class SMXExtension:
    """
    This extension registers the 'Suits (Unity Project)' library type
    and provides the custom logic to scan its unique folder structure,
    turning a Unity project folder into a live mod library.
    """
    def __init__(self):
        # New metadata reflecting the extension's true purpose
        self.name = "Unity Project Support"
        self.description = "Adds support for reading a Unity project's suit database structure as a live mod library."
        self.version = "1.0.0"
        self.app = None

    def initialize(self, app):
        """Called by the main application to let the extension integrate itself."""
        print(f"INFO: Initializing extension '{self.name}' v{self.version}")
        self.app = app
        
        # Register the new library type and the function that will handle scanning it
        self.app.register_library_scanner(
            library_type_name="Suits (Unity Project)", 
            scanner_function=self.scan_unity_project_folder
        )

    def on_close(self):
        """Called when the main application is closing."""
        print(f"INFO: Closing extension '{self.name}'.")

    def scan_unity_project_folder(self, base_path):
        """
        The custom scanning logic for 'Suits (Unity Project)' libraries.
        This is called by the main DataManager when it encounters this library type.
        
        :param base_path: The root path of the library (e.g., ".../Assets/SuitDatabase").
        :return: A dictionary of scanned mod data, formatted for the main app.
        """
        library_data = {}
        
        try:
            # In this mode, each direct subfolder of the base_path is a category.
            for category_name in os.listdir(base_path):
                category_path = os.path.join(base_path, category_name)
                if not os.path.isdir(category_path):
                    continue
                
                library_data[category_name] = []
                
                # Each subfolder inside the category is a specific mod's folder.
                for mod_name in os.listdir(category_path):
                    mod_path = os.path.join(category_path, mod_name)
                    if not os.path.isdir(mod_path):
                        continue
                    
                    # The zip file is expected to be inside the mod folder, named accordingly.
                    zip_file_path = os.path.join(mod_path, f"{mod_name}.zip")
                    
                    if os.path.exists(zip_file_path):
                        # Use the main app's public helper function to read the zip's contents.
                        # We tell it the mod is of type "Suits" so it knows what files to look for inside.
                        details = self.app.data_manager.get_local_mod_details_from_zip(zip_file_path, "Suits")
                        if details:
                            library_data[category_name].append(details)
            
            # Sort the mods within each category alphabetically for a clean display.
            for category in library_data:
                library_data[category].sort(key=lambda x: x['name'])

        except Exception as e:
            # Use the main app's UI logger to safely report any errors during scanning.
            self.app.log_to_ui(f"Error reading Unity library at '{base_path}': {e}")
        
        return library_data