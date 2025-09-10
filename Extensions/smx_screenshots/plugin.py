# --- Filename: Extensions/smx_screenshots/plugin.py ---
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from pathlib import Path
import os
from PIL import Image, ImageTk

class ScreenshotsFrame(ttk.Frame):
    """The UI frame for the Screenshots extension."""
    name = "SMX Screenshots"
    DEVICE_PATH = "/sdcard/Pictures/SMX/" # Standard path for Pictures on Android

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.screenshots = {}
        self.thumbnails = {} # To prevent garbage collection

        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(fill=BOTH, expand=True)

        # --- Header ---
        header = ttk.Frame(main_frame)
        header.pack(fill=X, pady=(0, 10))
        self.refresh_button = ttk.Button(header, text="Refresh Screenshots", command=self.refresh_screenshots)
        self.refresh_button.pack(side=LEFT)
        self.status_label = ttk.Label(header, text="  Click Refresh to scan for screenshots.")
        self.status_label.pack(side=LEFT)

        # --- Treeview for displaying screenshots ---
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=BOTH, expand=True)

        self.tree = ttk.Treeview(tree_frame, columns=('filename',), show='tree headings', selectmode='extended')
        self.tree.heading('#0', text='Preview')
        self.tree.heading('filename', text='Filename')
        self.tree.column('#0', width=120, stretch=False)
        self.tree.column('filename', width=400, stretch=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        self.tree.bind("<Double-1>", self.on_double_click)

        # --- Footer ---
        footer = ttk.Frame(main_frame)
        footer.pack(fill=X, pady=(10, 0))
        self.download_button = ttk.Button(footer, text="Download Selected to PC", command=self.download_selected, bootstyle="success")
        self.download_button.pack()

    def refresh_screenshots(self):
        """Starts the process of scanning the device for screenshots."""
        if not self.controller.is_adb_connected:
            messagebox.showwarning("Not Connected", "Please connect to the emulator before refreshing screenshots.")
            return

        self.status_label.config(text="  Scanning...")
        self.tree.delete(*self.tree.get_children())
        self.screenshots.clear()
        self.thumbnails.clear()
        self.controller.run_in_thread(self._threaded_scan)

    def _threaded_scan(self):
        """Scans the device in a separate thread to not freeze the UI."""
        filenames = self.controller.adb.list_device_files(self.DEVICE_PATH)
        if filenames is None:
            self.controller.after(0, self.on_scan_complete, None)
            return

        screenshot_data = []
        for fname in filenames:
            if fname.lower().endswith(('.jpg', '.jpeg', '.png')):
                device_file_path = f"{self.DEVICE_PATH}{fname}"
                temp_local_path = os.path.join(self.controller.TEMP_ICON_DIR, f"ss_{fname}")
                
                if self.controller.adb.pull_file(device_file_path, temp_local_path):
                    screenshot_data.append({'name': fname, 'local_path': temp_local_path})
        
        self.controller.after(0, self.on_scan_complete, screenshot_data)

    def on_scan_complete(self, data):
        """Populates the treeview once the scan is complete."""
        if data is None:
            self.status_label.config(text="  Error scanning device. Is the folder accessible?")
            return
        
        for item_data in data:
            try:
                img = Image.open(item_data['local_path'])
                img.thumbnail((100, 100))
                thumb = ImageTk.PhotoImage(img)
                
                # --- THE FIX IS HERE ---
                # Added `text=""` to explicitly set the first column's text to nothing.
                item_id = self.tree.insert('', 'end', text="", image=thumb, values=(item_data['name'],))
                self.thumbnails[item_id] = thumb # Keep reference
                self.screenshots[item_id] = item_data['name'] # Store original name
            except Exception as e:
                print(f"Could not process screenshot {item_data['name']}: {e}")

        self.status_label.config(text=f"  Found {len(self.screenshots)} screenshot(s).")

    def on_double_click(self, event):
        """Handles double-clicking on a filename to initiate renaming."""
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        column = self.tree.identify_column(event.x)
        if column != "#1": # Column '#1' is our 'filename' column
            return
        
        selected_item = self.tree.focus()
        if not selected_item:
            return

        # Get the position of the cell to place the entry widget
        bbox = self.tree.bbox(selected_item, "filename")
        if not bbox: return
        
        entry = ttk.Entry(self.tree)
        entry.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])
        
        current_name = self.tree.item(selected_item, "values")[0]
        entry.insert(0, current_name)
        entry.focus_force()
        entry.select_range(0, 'end')

        entry.bind("<Return>", lambda e, item=selected_item, entry_widget=entry: self.finish_rename(item, entry_widget))
        entry.bind("<FocusOut>", lambda e, item=selected_item, entry_widget=entry: self.finish_rename(item, entry_widget))

    def finish_rename(self, item_id, entry_widget):
        """Executes the rename command on the device."""
        new_name = entry_widget.get().strip()
        entry_widget.destroy() # Always remove the entry widget

        old_name = self.screenshots.get(item_id)
        if not new_name or new_name == old_name:
            return # No change, do nothing

        # Simple validation
        if any(c in new_name for c in '/\\:*?"<>|'):
            messagebox.showerror("Invalid Name", "Filename contains invalid characters.")
            return

        log = self.controller.log_to_ui
        log(f"Attempting to rename '{old_name}' to '{new_name}'...")
        
        old_path = f"{self.DEVICE_PATH}{old_name}"
        new_path = f"{self.DEVICE_PATH}{new_name}"
        
        # Use adb.send_adb_command to show output in the console
        self.controller.adb.send_adb_command(f"shell mv \"{old_path}\" \"{new_path}\"", log)
        
        # Update UI
        self.tree.item(item_id, values=(new_name,))
        self.screenshots[item_id] = new_name
        log("Rename complete.")


    def download_selected(self):
        """Downloads selected screenshots to the PC's Downloads folder."""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo("No Selection", "Please select at least one screenshot to download.")
            return

        try:
            downloads_path = Path.home() / "Downloads"
            os.makedirs(downloads_path, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error", f"Could not access your Downloads folder: {e}")
            return
        
        self.controller.show_loading_overlay(f"Downloading {len(selected_items)} file(s)...")
        self.controller.run_in_thread(self._threaded_download, selected_items, downloads_path)

    def _threaded_download(self, items, pc_path):
        """Handles the file pulling in a background thread."""
        success_count = 0
        for item_id in items:
            filename = self.screenshots.get(item_id)
            if not filename: continue
            
            device_file = f"{self.DEVICE_PATH}{filename}"
            local_file = os.path.join(pc_path, filename)

            if self.controller.adb.pull_file(device_file, local_file):
                success_count += 1
        
        self.controller.after(0, self.on_download_complete, success_count, len(items), pc_path)

    def on_download_complete(self, success_count, total, pc_path):
        """Shows a confirmation message after downloading."""
        self.controller.hide_loading_overlay()
        messagebox.showinfo("Download Complete", f"Successfully downloaded {success_count} of {total} screenshot(s) to:\n\n{pc_path}")


class SMXExtension:
    """This is the main entry point for the SMX Screenshots extension."""
    def __init__(self):
        self.name = "SMX Screenshots"
        self.description = "Browse, rename, and download in-game screenshots from your device."
        self.version = "1.0.0"

    def initialize(self, app):
        """Called by the main application to let the extension integrate itself."""
        print(f"INFO: Initializing extension '{self.name}' v{self.version}")
        self.app = app
        self.app.add_extension_tab(self.name, ScreenshotsFrame)

    def on_close(self):
        """Called when the main application is closing."""
        print(f"INFO: Closing extension '{self.name}'.")
        pass