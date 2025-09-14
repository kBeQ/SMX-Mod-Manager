# --- Filename: Extensions/sound_mod_creator/plugin.py ---
from .sound_creator_ui import SoundModCreatorFrame

class SMXExtension:
    """
    This extension adds a new tab to the Mod Manager dedicated to creating sound mods.
    """
    def __init__(self):
        self.name = "Sound Mod Creator"
        self.description = "Adds a tab for creating sound mods."
        self.version = "1.0.0"
        self.app = None

    def initialize(self, app):
        """Called by the main application to let the extension integrate itself."""
        print(f"INFO: Initializing extension '{self.name}' v{self.version}")
        self.app = app
        
        # This calls the function in the main app to add the tab to the top navigation bar.
        self.app.add_extension_tab(self.name, SoundModCreatorFrame)

    def on_close(self):
        """Called when the main application is closing."""
        print(f"INFO: Closing extension '{self.name}'.")