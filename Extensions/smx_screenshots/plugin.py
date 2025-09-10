# --- Filename: Extensions/smx_screenshots/plugin.py ---
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from pathlib import Path
import os
from PIL import Image, ImageTk, ImageOps

class ScreenshotItem(ttk.Frame):
    """A custom widget representing one screenshot in a 4:3 element."""
    def __init__(self, parent, controller, data):
        super().__init__(parent, padding=1)
        self.controller = controller # This is the main ScreenshotsFrame
        self.data = data
        self.is_selected = False

        # Frame to hold the content and show selection border
        self.content_frame = ttk.Frame(self, bootstyle="dark", padding=5)
        self.content_frame.pack(fill=BOTH, expand=True)
        self.content_frame.grid_columnconfigure(0, weight=1)

        # --- Header (Filename) ---
        self.name_var = tk.StringVar(value=data['name'])
        self.name_label = ttk.Label(
            self.content_frame, 
            textvariable=self.name_var, 
            anchor=CENTER, 
            bootstyle="inverse-dark",
            font=("Helvetica", 9, "bold")
        )
        self.name_label.grid(row=0, column=0, sticky='ew', pady=(0, 5))

        # --- Preview Image (processed to be 4:3) ---
        self.photo = self.create_display_image(data['local_path'], (200, 150))
        self.image_label = ttk.Label(self.content_frame, image=self.photo, bootstyle="dark")
        self.image_label.grid(row=1, column=0, sticky='nsew')
        
        # --- Bindings ---
        self.bind_all_children("<Button-1>", self.on_click)
        self.name_label.bind("<Double-1>", self.on_double_click_name)

    def create_display_image(self, path, size):
        """Opens an image, creates a thumbnail, and pastes it onto a 4:3 background."""
        try:
            # 1. Create a 4:3 dark background canvas
            background = Image.new('RGB', size, self.winfo_toplevel().style.colors.dark)
            
            # 2. Open the screenshot and create a thumbnail that fits within the size
            img = Image.open(path)
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # 3. Calculate position to center the thumbnail on the background
            x_offset = (size[0] - img.width) // 2
            y_offset = (size[1] - img.height) // 2
            
            # 4. Paste the thumbnail onto the background
            background.paste(img, (x_offset, y_offset))
            
            return ImageTk.PhotoImage(background)
        except Exception as e:
            print(f"Error creating display image for {path}: {e}")
            return None # Handle error gracefully

    def bind_all_children(self, event, callback):
        self.bind(event, callback)
        for child in self.content_frame.winfo_children():
            child.bind(event, callback)

    def on_click(self, event):
        ctrl_pressed = (event.state & 0x0004) != 0
        self.controller.on_item_select(self, ctrl_pressed)

    def on_double_click_name(self, event):
        self.controller.start_rename(self)

    def set_selected(self, selected):
        self.is_selected = selected
        style = "primary" if selected else "default"
        self.config(bootstyle=style)


class ScreenshotsFrame(ttk.Frame):
    """The main UI for the Screenshots extension, now using a proper grid."""
    name = "SMX Screenshots"
    DEVICE_PATH = "/sdcard/Pictures/SMX/"

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.screenshot_widgets = []
        self.max_columns = 4

        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(fill=BOTH, expand=True)

        header = ttk.Frame(main_frame)
        header.pack(fill=X, pady=(0, 10))
        self.refresh_button = ttk.Button(header, text="Refresh Screenshots", command=self.refresh_screenshots)
        self.refresh_button.pack(side=LEFT)
        self.status_label = ttk.Label(header, text="  Click Refresh to scan.")
        self.status_label.pack(side=LEFT)

        self.scroll_frame = ScrolledFrame(main_frame, autohide=True)
        self.scroll_frame.pack(fill=BOTH, expand=True)
        self.scroll_frame.bind("<Configure>", self.on_resize)

        footer = ttk.Frame(main_frame)
        footer.pack(fill=X, pady=(10, 0))
        self.download_button = ttk.Button(footer, text="Download Selected to PC", command=self.download_selected, bootstyle="success")
        self.download_button.pack()

    def on_resize(self, event):
        new_max_columns = max(1, event.width // 230) # Approx width of each element + padding
        if new_max_columns != self.max_columns:
            self.max_columns = new_max_columns
            self.redraw_grid()

    def redraw_grid(self):
        for i, widget in enumerate(self.screenshot_widgets):
            row = i // self.max_columns
            col = i % self.max_columns
            widget.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
        
        for i in range(self.max_columns):
            self.scroll_frame.grid_columnconfigure(i, weight=1)

    def refresh_screenshots(self):
        if not self.controller.is_adb_connected:
            messagebox.showwarning("Not Connected", "Please connect to the emulator first.")
            return

        self.status_label.config(text="  Scanning...")
        for widget in self.screenshot_widgets:
            widget.destroy()
        self.screenshot_widgets.clear()
        self.controller.run_in_thread(self._threaded_scan)

    def _threaded_scan(self):
        filenames = self.controller.adb.list_device_files(self.DEVICE_PATH)
        if filenames is None:
            self.controller.after(0, self.on_scan_complete, None)
            return

        screenshot_data = []
        for fname in sorted(filenames):
            if fname.lower().endswith(('.jpg', '.jpeg', '.png')):
                device_path = f"{self.DEVICE_PATH}{fname}"
                temp_path = os.path.join(self.controller.TEMP_ICON_DIR, f"ss_{fname}")
                if self.controller.adb.pull_file(device_path, temp_path):
                    screenshot_data.append({'name': fname, 'local_path': temp_path})
        
        self.controller.after(0, self.on_scan_complete, screenshot_data)

    def on_scan_complete(self, data):
        if data is None:
            self.status_label.config(text="  Error scanning device.")
            return

        for item_data in data:
            try:
                widget = ScreenshotItem(self.scroll_frame, self, item_data)
                self.screenshot_widgets.append(widget)
            except Exception as e:
                print(f"Could not create widget for {item_data['name']}: {e}")

        self.redraw_grid()
        self.status_label.config(text=f"  Found {len(self.screenshot_widgets)} screenshot(s).")

    def on_item_select(self, widget, ctrl_pressed):
        if not ctrl_pressed:
            for w in self.screenshot_widgets:
                if w != widget:
                    w.set_selected(False)
        
        widget.set_selected(not widget.is_selected)

    def start_rename(self, widget):
        entry = ttk.Entry(widget.name_label)
        entry.place(relwidth=1.0, relheight=1.0)
        
        current_name = widget.name_var.get()
        entry.insert(0, current_name)
        entry.focus_force()
        entry.select_range(0, 'end')

        entry.bind("<Return>", lambda e, w=widget, entry_widget=entry: self.finish_rename(w, entry_widget))
        entry.bind("<FocusOut>", lambda e, w=widget, entry_widget=entry: self.finish_rename(w, entry_widget))

    def finish_rename(self, widget, entry_widget):
        new_name = entry_widget.get().strip()
        entry_widget.destroy()

        old_name = widget.data['name']
        if not new_name or new_name == old_name:
            return

        if any(c in new_name for c in '/\\:*?"<>|'):
            messagebox.showerror("Invalid Name", "Filename contains invalid characters.")
            return

        log = self.controller.log_to_ui
        log(f"Attempting to rename '{old_name}' to '{new_name}'...")
        
        old_path = f"{self.DEVICE_PATH}{old_name}"
        new_path = f"{self.DEVICE_PATH}{new_name}"
        
        self.controller.adb.send_adb_command(f"shell mv \"{old_path}\" \"{new_path}\"", log)
        
        widget.data['name'] = new_name
        widget.name_var.set(new_name)
        log("Rename complete.")

    def download_selected(self):
        selected_widgets = [w for w in self.screenshot_widgets if w.is_selected]
        if not selected_widgets:
            messagebox.showinfo("No Selection", "Please select screenshots to download.")
            return

        downloads_path = Path.home() / "Downloads"
        os.makedirs(downloads_path, exist_ok=True)
        
        self.controller.show_loading_overlay(f"Downloading {len(selected_widgets)} file(s)...")
        self.controller.run_in_thread(self._threaded_download, selected_widgets, downloads_path)

    def _threaded_download(self, widgets, pc_path):
        success_count = 0
        for widget in widgets:
            filename = widget.data['name']
            device_file = f"{self.DEVICE_PATH}{filename}"
            local_file = pc_path / filename
            if self.controller.adb.pull_file(device_file, str(local_file)):
                success_count += 1
        
        self.controller.after(0, self.on_download_complete, success_count, len(widgets), pc_path)

    def on_download_complete(self, success_count, total, pc_path):
        self.controller.hide_loading_overlay()
        messagebox.showinfo("Download Complete", f"Downloaded {success_count} of {total} to:\n\n{pc_path}")


class SMXExtension:
    """This is the main entry point for the SMX Screenshots extension."""
    def __init__(self):
        self.name = "SMX Screenshots"
        self.description = "Browse, rename, and download in-game screenshots from your device."
        self.version = "1.2.0" # Version bumped for major UI overhaul

    def initialize(self, app):
        """Called by the main application to let the extension integrate itself."""
        print(f"INFO: Initializing extension '{self.name}' v{self.version}")
        self.app = app
        self.app.add_extension_tab(self.name, ScreenshotsFrame)

    def on_close(self):
        """Called when the main application is closing."""
        print(f"INFO: Closing extension '{self.name}'.")
        pass