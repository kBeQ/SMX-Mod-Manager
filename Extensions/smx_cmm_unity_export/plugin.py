# --- Filename: Extensions/smx_cmm_unity_export/plugin.py ---
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import os

# 1. Define the UI for the new tab
class CMMUnityExportFrame(ttk.Frame):
    """The UI frame that will be displayed in the new tab."""
    # The 'name' attribute is not strictly needed here but good practice
    name = "SMX CMM Unity Export"

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller # The main App instance

        # Get the path from settings, if it exists
        unity_path_var = self.controller.setting_vars.get(self.name, {}).get("Unity Project Path", {}).get('var')
        
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(expand=True, fill=BOTH)

        ttk.Label(main_frame, text="SMX CMM Unity Export", font=("Helvetica", 16, "bold")).pack(pady=(0,10))
        ttk.Label(main_frame, text="This extension helps streamline exporting mods from your Unity project.", wraplength=600).pack(pady=(0, 20))

        path_frame = ttk.Labelframe(main_frame, text="Configured Unity Project Path", padding=10)
        path_frame.pack(fill=X, pady=10)
        
        if unity_path_var:
            path_label = ttk.Entry(path_frame, textvariable=unity_path_var, state="readonly")
            path_label.pack(side=LEFT, fill=X, expand=True, padx=(0,10))
            ttk.Button(path_frame, text="Go to Settings to change", command=lambda: self.controller.show_frame("Settings")).pack(side=LEFT)
        else:
            ttk.Label(path_frame, text="Path not configured. Please set it in the Settings tab.").pack()

        # Add other extension functionality here...
        ttk.Button(main_frame, text="Export Build (Example)", state="disabled").pack(pady=20)
        ttk.Label(main_frame, text="(Functionality to be implemented)").pack()


# 2. Define the main Extension class that the app will discover
class SMXExtension:
    """
    This is the main entry point for the extension.
    The main application will create an instance of this class.
    """
    def __init__(self):
        # These attributes are used by the main app to identify the extension
        self.name = "SMX CMM Unity Export"
        self.description = "Helps export builds from Unity directly to the mod manager."
        self.version = "1.0.0"

    def initialize(self, app):
        """
        This method is called by the main application to let the extension
        integrate itself.
        
        :param app: The instance of the main App class.
        """
        print(f"INFO: Initializing extension '{self.name}' v{self.version}")
        self.app = app

        # --- Integration Step 1: Register Settings ---
        # The category name should be unique, using self.name is a good idea.
        self.app.register_setting(
            category=self.name,
            name="Unity Project Path",
            default_value="",
            setting_type='folder' # This lets us re-use the existing file browser logic
        )

        # --- Integration Step 2: Add the UI Tab ---
        # The app needs a way to add our new frame as a tab.
        self.app.add_extension_tab(self.name, CMMUnityExportFrame)

    def on_close(self):
        """
        Called when the main application is closing.
        Good for any cleanup operations.
        """
        print(f"INFO: Closing extension '{self.name}'.")
        pass