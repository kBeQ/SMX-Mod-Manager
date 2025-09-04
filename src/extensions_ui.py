# --- Filename: src/extensions_ui.py ---
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
import os
import json

class ExtensionsFrame(ttk.Frame):
    name = "Extensions"

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller # Main App instance
        self.github_handler = controller.github_handler
        self.available_extensions = {}
        self.installed_extensions = {}

        # --- Main Layout ---
        main_pane = ttk.PanedWindow(self, orient=HORIZONTAL)
        main_pane.pack(fill=BOTH, expand=True, padx=15, pady=15)

        # --- Left Pane: Available Online ---
        left_frame = ttk.Labelframe(main_pane, text="Available for Download", padding=10)
        main_pane.add(left_frame, weight=1)

        header_frame = ttk.Frame(left_frame)
        header_frame.pack(fill=X, pady=(0, 10))
        ttk.Button(header_frame, text="Refresh List", command=self.refresh_online_list, bootstyle="info").pack(side=LEFT)
        self.status_label = ttk.Label(header_frame, text="Click Refresh to check for extensions.")
        self.status_label.pack(side=LEFT, padx=10)

        self.online_list_frame = ScrolledFrame(left_frame, autohide=True)
        self.online_list_frame.pack(fill=BOTH, expand=True)

        # --- Right Pane: Installed ---
        right_frame = ttk.Labelframe(main_pane, text="Installed Locally", padding=10)
        main_pane.add(right_frame, weight=1)
        self.installed_list_frame = ScrolledFrame(right_frame, autohide=True)
        self.installed_list_frame.pack(fill=BOTH, expand=True)

        # Initial population of installed extensions
        self.populate_installed_list()

    def refresh_online_list(self):
        self.status_label.config(text="Fetching from GitHub...")
        self.controller.run_in_thread(self._threaded_fetch_online)

    def _threaded_fetch_online(self):
        self.available_extensions = self.github_handler.get_available_extensions()
        self.controller.after(0, self.populate_online_list)
        
    def populate_online_list(self):
        for widget in self.online_list_frame.winfo_children():
            widget.destroy()

        if self.available_extensions is None:
            self.status_label.config(text="Error fetching list. Check console.", bootstyle="danger")
            return
        if not self.available_extensions:
            self.status_label.config(text="No extensions found online.")
            return

        self.status_label.config(text=f"Found {len(self.available_extensions)} extensions.", bootstyle="default")
        self.populate_installed_list() # Re-populate to update status

        for name, meta in self.available_extensions.items():
            card = ttk.Frame(self.online_list_frame, bootstyle="dark", padding=10)
            card.pack(fill=X, pady=5, padx=5)
            
            ttk.Label(card, text=meta['name'], font=("Helvetica", 11, "bold"), bootstyle="inverse-dark").pack(anchor=W)
            ttk.Label(card, text=meta['description'], wraplength=400, bootstyle="inverse-dark").pack(anchor=W, pady=(5,10))
            
            info_frame = ttk.Frame(card, bootstyle="dark")
            info_frame.pack(fill=X)
            ttk.Label(info_frame, text=f"Version: {meta['version']}", bootstyle="inverse-dark").pack(side=LEFT)
            ttk.Label(info_frame, text=f"By: {meta.get('author', 'Unknown')}", bootstyle="inverse-dark").pack(side=RIGHT)
            
            btn_frame = ttk.Frame(card, bootstyle="dark")
            btn_frame.pack(fill=X, pady=(10,0))
            
            # Logic to show Install / Update / Installed button
            if name in self.installed_extensions:
                installed_version = self.installed_extensions[name].get('version', '0.0.0')
                online_version = meta.get('version', '0.0.0')
                if online_version > installed_version:
                     ttk.Button(btn_frame, text="Update", command=lambda n=name: self.install_extension(n), bootstyle="success").pack(side=RIGHT)
                else:
                    ttk.Label(btn_frame, text="Installed", bootstyle="success-inverse").pack(side=RIGHT)
            else:
                ttk.Button(btn_frame, text="Install", command=lambda n=name: self.install_extension(n), bootstyle="primary").pack(side=RIGHT)

    def populate_installed_list(self):
        self.installed_extensions = {}
        ext_dir = os.path.join(self.controller.get_script_directory(), "Extensions")
        if not os.path.isdir(ext_dir):
            return

        for item_name in os.listdir(ext_dir):
            item_path = os.path.join(ext_dir, item_name)
            manifest_path = os.path.join(item_path, "manifest.json")
            if os.path.isdir(item_path) and os.path.isfile(manifest_path):
                try:
                    with open(manifest_path, 'r') as f:
                        self.installed_extensions[item_name] = json.load(f)
                except Exception as e:
                    print(f"Could not load manifest for installed extension '{item_name}': {e}")
        
        # Now, draw the UI
        for widget in self.installed_list_frame.winfo_children():
            widget.destroy()
            
        if not self.installed_extensions:
            ttk.Label(self.installed_list_frame, text="No extensions are installed locally.").pack(padx=10, pady=10)
            return
        
        for name, meta in self.installed_extensions.items():
            card = ttk.Frame(self.installed_list_frame, bootstyle="dark", padding=10)
            card.pack(fill=X, pady=5, padx=5)
            
            ttk.Label(card, text=meta['name'], font=("Helvetica", 11, "bold"), bootstyle="inverse-dark").pack(anchor=W)
            ttk.Label(card, text=f"Version: {meta['version']}", bootstyle="inverse-dark").pack(anchor=W)

            ttk.Button(card, text="Uninstall", bootstyle="danger-outline", command=lambda n=name: self.uninstall_extension(n)).pack(side=RIGHT, pady=5)
    
    def install_extension(self, extension_name):
        self.status_label.config(text=f"Installing {extension_name}...")
        self.controller.show_loading_overlay(f"Installing {extension_name}...")
        target_dir = os.path.join(self.controller.get_script_directory(), "Extensions")
        self.controller.run_in_thread(self._threaded_install, extension_name, target_dir)

    def _threaded_install(self, name, target_dir):
        success = self.github_handler.download_extension(name, target_dir)
        self.controller.after(0, self.on_install_complete, success)
        
    def on_install_complete(self, success):
        self.controller.hide_loading_overlay()
        if success:
            ttk.dialogs.Messagebox.ok("Installation complete. Please restart the application for the new extension to be active.", "Restart Required")
            self.refresh_online_list() # This will update button states
        else:
            ttk.dialogs.Messagebox.show_error("Installation failed. Check the console for more details.", "Error")
            self.status_label.config(text="Installation failed.", bootstyle="danger")

    def uninstall_extension(self, extension_name):
        if not ttk.dialogs.Messagebox.yesno(f"Are you sure you want to uninstall '{extension_name}'?", "Confirm Uninstall"):
            return
        
        ext_path = os.path.join(self.controller.get_script_directory(), "Extensions", extension_name)
        try:
            import shutil
            shutil.rmtree(ext_path)
            ttk.dialogs.Messagebox.ok("Uninstallation complete. Please restart the application for changes to take effect.", "Restart Required")
            self.populate_installed_list()
            self.populate_online_list()
        except Exception as e:
            ttk.dialogs.Messagebox.show_error(f"Could not uninstall extension: {e}", "Error")