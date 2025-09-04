# --- Filename: Extensions/smx_cmm_unity_export/plugin.py ---
import tkinter as tk
from tkinter import filedialog # Import filedialog directly
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import os

class CMMUnityExportFrame(ttk.Frame):
    """The UI frame that will be displayed in the new tab."""
    name = "SMX CMM Unity Export"

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.extension_name = "SMX CMM Unity Export" # Consistent name for settings

        # --- Settings Variable ---
        self.unity_project_path_var = tk.StringVar()
        
        # --- Load the saved setting using the new API ---
        saved_path = self.controller.get_extension_setting(
            extension_name=self.extension_name,
            setting_key='unity_project_path',
            default=""
        )
        self.unity_project_path_var.set(saved_path)

        # --- UI ---
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(expand=True, fill=BOTH, padx=10, pady=10)

        ttk.Label(main_frame, text=self.extension_name, font=("Helvetica", 16, "bold")).pack(pady=(0,10), anchor='w')
        ttk.Label(main_frame, text="This extension helps streamline exporting mods from your Unity project.", wraplength=600).pack(pady=(0, 20), anchor='w')

        # --- Settings UI is now part of this frame ---
        settings_frame = ttk.Labelframe(main_frame, text="Settings", padding=15)
        settings_frame.pack(fill=X, pady=10)

        ttk.Label(settings_frame, text="Unity Project Path:").grid(row=0, column=0, sticky='w', pady=(0, 5))
        
        path_entry = ttk.Entry(settings_frame, textvariable=self.unity_project_path_var, state="readonly")
        path_entry.grid(row=1, column=0, sticky='ew')
        
        browse_button = ttk.Button(settings_frame, text="Browse...", command=self.browse_for_unity_project, bootstyle="outline")
        browse_button.grid(row=1, column=1, sticky='w', padx=(10, 0))
        
        settings_frame.grid_columnconfigure(0, weight=1) # Make the entry expand

        # --- Action Area ---
        action_frame = ttk.Labelframe(main_frame, text="Actions", padding=15)
        action_frame.pack(fill=X, pady=20)
        
        ttk.Button(action_frame, text="Export Build (Example)", state="disabled").pack()
        ttk.Label(action_frame, text="(Functionality to be implemented)").pack()

    def browse_for_unity_project(self):
        """Opens a dialog to select the Unity project folder and saves the setting."""
        folder_path = filedialog.askdirectory(title="Select your Unity Project Folder")
        if folder_path:
            self.unity_project_path_var.set(folder_path)
            # --- Save the setting using the new API ---
            self.controller.save_extension_setting(
                extension_name=self.extension_name,
                setting_key='unity_project_path',
                value=folder_path
            )

class SMXExtension:
    """This is the main entry point for the extension."""
    def __init__(self):
        self.name = "SMX CMM Unity Export"
        self.description = "Helps export builds from Unity directly to the mod manager."
        self.version = "1.0.1" # Bump version for the change

    def initialize(self, app):
        """Called by the main application to let the extension integrate itself."""
        print(f"INFO: Initializing extension '{self.name}' v{self.version}")
        self.app = app

        # --- REMOVED: Settings are no longer registered here ---

        # --- Integration Step: Add the UI Tab ---
        self.app.add_extension_tab(self.name, CMMUnityExportFrame)

    def on_close(self):
        """Called when the main application is closing."""
        print(f"INFO: Closing extension '{self.name}'.")
        pass