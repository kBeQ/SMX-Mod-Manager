# --- Filename: Extensions/sound_mod_creator/sound_creator_ui.py ---
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, font

class SoundModCreatorFrame(ttk.Frame):
    # This name must match the name used in the plugin's `add_extension_tab` call
    name = "Sound Mod Creator"

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller  # This is the main App instance
        self.extension_name = "Sound Mod Creator" # Used for saving settings

        # --- Bike List (for future use) ---
        self.bike_models = [
            "Y250", "Y450", "E", "GRF250", "GRF450", "RM250", "RM450",
            "KW250", "KW450", "KTSX250", "KTSX450", "KTST250", "T250", "T450"
        ]

        # --- Main UI Construction ---
        self.build_ui()

    def build_ui(self):
        """Creates all the widgets for the UI tab."""
        # Use a scrolled frame in case we add many more options later
        scrollable_frame = ttk.ScrolledFrame(self, autohide=True, padding=20)
        scrollable_frame.pack(fill=BOTH, expand=True)

        # --- Settings Section ---
        settings_frame = ttk.Labelframe(scrollable_frame, text="Configuration", padding=15)
        settings_frame.pack(fill=X, expand=True, pady=(0, 20))
        settings_frame.grid_columnconfigure(1, weight=1) # Allow the entry to expand

        # --- Bike Thumbnail Source Folder Setting ---
        ttk.Label(settings_frame, text="Bike Thumbnails Folder:").grid(row=0, column=0, sticky=W, pady=5)
        
        # Create a StringVar to hold the path, making it easy to get/set
        self.thumbnail_path_var = tk.StringVar()
        
        # Load any previously saved path for this setting
        saved_path = self.controller.get_extension_setting(self.extension_name, "thumbnail_folder_path", "")
        self.thumbnail_path_var.set(saved_path)

        path_entry = ttk.Entry(settings_frame, textvariable=self.thumbnail_path_var, state="readonly")
        path_entry.grid(row=0, column=1, sticky=EW, padx=10)

        browse_button = ttk.Button(settings_frame, text="Browse...", command=self.browse_for_folder, bootstyle="outline")
        browse_button.grid(row=0, column=2, sticky=E)

        # --- Placeholder for future content ---
        ttk.Separator(scrollable_frame).pack(fill=X, pady=20)
        ttk.Label(scrollable_frame, text="Sound creation tools will be added here.", font=("Helvetica", 14, "italic")).pack()


    def browse_for_folder(self):
        """Opens a dialog to select a folder and saves the result."""
        # Ask the user to select a directory
        folder_selected = filedialog.askdirectory(title="Select Folder Containing Bike Thumbnails")

        # If the user selected a folder (and didn't cancel)
        if folder_selected:
            self.thumbnail_path_var.set(folder_selected)
            # Use the controller's public method to save the setting for our extension
            self.controller.save_extension_setting(
                ext_name=self.extension_name,
                key="thumbnail_folder_path",
                value=folder_selected
            )
            print(f"INFO: Bike thumbnail path saved for '{self.extension_name}': {folder_selected}")