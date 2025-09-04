# --- Filename: smx_mod_manager.py ---
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import font, messagebox
import os
import sys
import threading
import json
import tempfile
import shutil
import re
import psutil
import time
import ctypes
from PIL import Image, ImageTk

# --- NEW: Imports for the extension system ---
import importlib.util
from pathlib import Path

# Import other modules...
from src.mod_manager_ui import ModManagerFrame
from src.on_device_ui import OnDeviceFrame
from src.mod_helper_ui import ModHelperFrame
from src.settings_ui import SettingsFrame
from src.adb_handler import AdbHandler
from src.data_manager import DataManager
# --- NEW: Import the new UI frame and handler ---
from src.extensions_ui import ExtensionsFrame
from src.github_handler import GitHubHandler


# --- Global Constants ---
CONFIG_FILE = "config.json"
MAPPINGS_FILE = "mod_mappings.json"
EXTENSIONS_SETTINGS_FILE = "extensions_settings.json" 
APP_VERSION = "7.18.0" # Version updated to reflect new features

# THIS FUNCTION is now part of the App class below. It has been moved.

def get_resource_path(filename):
    """Return the correct path to a resource file,
    both when running from source and when frozen with PyInstaller."""
    if getattr(sys, "frozen", False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, 'assets', filename)

# --- Splash Screen Class ---
class SplashScreen:
    def __init__(self, parent):
        self.parent = parent
        self.splash = tk.Toplevel(parent)
        self.splash.overrideredirect(True) # Remove window borders

        splash_image_path = get_resource_path("SMX Mod Manager.png")
        if not os.path.exists(splash_image_path):
            self.parent.after(100, self.close_splash)
            return

        self.splash_image = ImageTk.PhotoImage(Image.open(splash_image_path))
        
        img_width = self.splash_image.width()
        img_height = self.splash_image.height()
        
        screen_width = self.splash.winfo_screenwidth()
        screen_height = self.splash.winfo_screenheight()
        x = (screen_width // 2) - (img_width // 2)
        y = (screen_height // 2) - (img_height // 2)

        self.splash.geometry(f'{img_width}x{img_height}+{x}+{y}')
        
        transparency_key_color = 'fuchsia' 
        self.splash.config(bg=transparency_key_color)
        label = tk.Label(self.splash, image=self.splash_image, bg=transparency_key_color)
        label.pack()
        self.splash.wm_attributes('-transparentcolor', transparency_key_color)
        self.splash.after(2000, self.close_splash)

    def close_splash(self):
        self.splash.destroy()
        self.parent.deiconify()
        self.parent.after(150, self.parent.initial_local_scan)


# --- Main Application Class ---
class App(ttk.Window):
    def __init__(self, themename="superhero"):
        super().__init__(themename=themename)
        self.withdraw()
        
        SplashScreen(self)

        self.title(f"SMX Mod Manager v{APP_VERSION}")
        self.geometry("1400x850")

        try:
            icon_path = get_resource_path("smx_mod_manager.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception as e:
            print(f"Could not set application icon: {e}")
        
        self.TEMP_ICON_DIR = os.path.join(tempfile.gettempdir(), "smx_mod_manager_icons")
        if os.path.exists(self.TEMP_ICON_DIR): shutil.rmtree(self.TEMP_ICON_DIR)
        os.makedirs(self.TEMP_ICON_DIR)

        self.github_handler = GitHubHandler()
        self.extensions = {}
        self.setting_vars = {}
        self.saved_config = {}
        self.mod_mappings = {}
        self.extension_settings = {}
        self.load_config()
        self.load_mappings()
        self._load_extension_settings()
        self.is_mods_folder_known_to_exist = self.saved_config.get("mods_folder_exists", False)

        self.register_setting("Game Configuration", "Game Package Name", "com.Evag.SMX")
        self.register_setting("Game Configuration", "Mods Subfolder Path", "files/Mods/")
        self.full_mods_path_var = self.register_setting("Game Configuration", "Full Mods Path (Auto-generated)", "", readonly=True)
        self.register_setting("Game Configuration", "Game Activity Name", "com.unity3d.player.UnityPlayerActivity")
        default_gpg_adb_path = r"C:\Program Files\Google\Play Games Developer Emulator\current\emulator\adb.exe"
        self.register_setting("Advanced", "ADB Executable Override", default_gpg_adb_path, setting_type='file')
        self.register_setting("LocalLibrary", "Paths", [], 'internal')
        
        self._migrate_library_config()
        self.update_full_mods_path()
        self.ensure_initial_config()

        self.ADB_PATH = self.find_adb_path()
        if not self.ADB_PATH:
            messagebox.showerror("ADB Not Found",
                                 "Could not find adb.exe in the application folder or at the configured path.\n\n"
                                 "Please place adb.exe in the app folder or configure its location in the 'Advanced' section of the Settings tab.")

        self.adb = AdbHandler(self)
        self.data_manager = DataManager(self)
        self.loading_overlay = None
        self.device_has_been_scanned = False
        self.is_adb_connected = False
        self.is_game_running = False
        self.stop_monitoring = threading.Event()
        self.header_image_path = get_resource_path("SMX Mod Manager.png")

        self._load_extensions()

        self.nav_frame = ttk.Frame(self)
        self.nav_frame.pack(side="top", fill="x", padx=1, pady=1)
        self.nav_buttons = {}
        
        self.core_frames = ["Mod Manager", "On Device", "Extensions", "Mod Helper", "Settings"]
        for name in self.core_frames:
            button = ttk.Button(self.nav_frame, text=name, command=lambda n=name: self.show_frame(n), bootstyle="secondary", padding=(0, 10))
            button.pack(side="left", fill="x", expand=True, padx=(0,1))
            self.nav_buttons[name] = button

        self.container = ttk.Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        self.frames = {}
        
        for F in (ModManagerFrame, OnDeviceFrame, ExtensionsFrame, ModHelperFrame, SettingsFrame):
            frame = F(self.container, self)
            self.frames[F.name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        if self.extensions:
            print(f"INFO: Initializing {len(self.extensions)} loaded extension(s)...")
            for ext in self.extensions.values():
                try:
                    ext.initialize(self)
                except Exception as e:
                    print(f"ERROR: Failed to initialize extension '{ext.name}': {e}")
            print("--- Extension initialization complete ---")

        self.show_frame("Mod Manager")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        monitor_thread = threading.Thread(target=self._connection_monitoring_loop, daemon=True)
        monitor_thread.start()

    # --- THE FIX IS HERE ---
    # Moved get_script_directory INSIDE the App class to make it a method.
    def get_script_directory(self):
        """Gets the directory of the running script or frozen executable."""
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        else:
            return os.path.dirname(os.path.abspath(__file__))

    def _load_extensions(self):
        """Discovers and loads all valid extensions from the local directory."""
        ext_dir = Path(self.get_script_directory()) / "Extensions" # Now calls the method
        if not ext_dir.is_dir():
            print("INFO: No 'Extensions' directory found. Skipping extension loading.")
            return

        print("--- Scanning for local extensions ---")
        for potential_ext_dir in ext_dir.iterdir():
            manifest_file = potential_ext_dir / "manifest.json"
            plugin_file = potential_ext_dir / "plugin.py"
            if potential_ext_dir.is_dir() and manifest_file.is_file() and plugin_file.is_file():
                module_name = f"extensions.{potential_ext_dir.name}.plugin"
                try:
                    spec = importlib.util.spec_from_file_location(module_name, plugin_file)
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)

                    if hasattr(module, "SMXExtension"):
                        ext_instance = module.SMXExtension()
                        if ext_instance.name in self.extensions:
                            print(f"WARNING: Duplicate extension name '{ext_instance.name}'. Skipping.")
                            continue
                        self.extensions[ext_instance.name] = ext_instance
                        print(f"  OK: Loaded extension '{ext_instance.name}'")
                    else:
                        print(f"WARNING: '{plugin_file}' does not contain an SMXExtension class.")
                except Exception as e:
                    print(f"ERROR: Failed to load extension from '{potential_ext_dir.name}': {e}")
        print(f"--- Found {len(self.extensions)} valid local extension(s) ---")

    def add_extension_tab(self, name, frame_class):
        """API for extensions to add their own UI tabs."""
        if name in self.frames:
            print(f"WARNING: A frame with the name '{name}' already exists. Cannot add extension tab.")
            return

        button = ttk.Button(self.nav_frame, text=name, command=lambda n=name: self.show_frame(n), bootstyle="secondary", padding=(0, 10))
        button.pack(side="left", fill="x", expand=True, padx=(0,1))
        self.nav_buttons[name] = button

        frame = frame_class(self.container, self)
        self.frames[name] = frame
        frame.grid(row=0, column=0, sticky="nsew")
        print(f"  -> Extension '{name}' successfully added a UI tab.")

    # --- NEW METHODS: API for extensions to manage their settings ---

    def _load_extension_settings(self):
        """Loads the settings for all extensions from a dedicated JSON file."""
        try:
            with open(EXTENSIONS_SETTINGS_FILE, 'r') as f:
                self.extension_settings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.extension_settings = {}

    def get_extension_setting(self, extension_name, setting_key, default=None):
        """
        Allows an extension to retrieve one of its saved settings.
        
        :param extension_name: The unique name of the extension (e.g., 'SMX CMM Unity Export').
        :param setting_key: The name of the setting to retrieve (e.g., 'unity_project_path').
        :param default: The value to return if the setting is not found.
        :return: The stored value or the default.
        """
        return self.extension_settings.get(extension_name, {}).get(setting_key, default)

    def save_extension_setting(self, extension_name, setting_key, value):
        """
        Allows an extension to save a setting. The settings are saved to disk immediately.
        
        :param extension_name: The unique name of the extension.
        :param setting_key: The name of the setting to save.
        :param value: The value to store.
        """
        if extension_name not in self.extension_settings:
            self.extension_settings[extension_name] = {}
        
        self.extension_settings[extension_name][setting_key] = value
        
        # Save immediately to ensure data persistence
        with open(EXTENSIONS_SETTINGS_FILE, 'w') as f:
            json.dump(self.extension_settings, f, indent=4)
        
        print(f"INFO: Setting '{setting_key}' for extension '{extension_name}' saved.")

    def _migrate_library_config(self):
        lib_setting = self.setting_vars.get("LocalLibrary", {}).get("Paths")
        if not lib_setting: return

        current_libs = lib_setting['value']
        if not current_libs or isinstance(current_libs[0], dict):
            return

        print("INFO: Old library config format detected. Migrating to new format.")
        new_libs_data = []
        for path in current_libs:
            if isinstance(path, str):
                new_libs_data.append({'type': 'Tracks', 'path': path})
        
        self.setting_vars["LocalLibrary"]["Paths"]['value'] = new_libs_data
        self.save_config()

    def update_full_mods_path(self, *args):
        package = self.setting_vars["Game Configuration"]["Game Package Name"]['var'].get()
        subfolder = self.setting_vars["Game Configuration"]["Mods Subfolder Path"]['var'].get()
        old_path = self.full_mods_path_var.get()
        
        base_path = f"/sdcard/Android/data/{package}/".replace("\\", "/")
        full_path = os.path.join(base_path, subfolder).replace("\\", "/")
        if not full_path.endswith('/'):
            full_path += '/'
        self.full_mods_path_var.set(full_path)
        
        if old_path and old_path != full_path:
            self.is_mods_folder_known_to_exist = False
            self.log_to_ui("INFO: Game path changed. Re-verification of mods folder is required.")

    def ensure_initial_config(self):
        if not os.path.exists(CONFIG_FILE):
            print("INFO: config.json not found, creating with default values.")
            self.save_config()

    def find_adb_path(self):
        local_adb_path = os.path.join(self.get_script_directory(), "bin", "adb.exe") # Now calls the method
        if os.path.exists(local_adb_path):
            return local_adb_path

        settings_adb_path_var = self.setting_vars.get("Advanced", {}).get("ADB Executable Override", {}).get('var')
        if settings_adb_path_var:
            settings_adb_path = settings_adb_path_var.get()
            if settings_adb_path and os.path.exists(settings_adb_path):
                return settings_adb_path
        return None

    def _connection_monitoring_loop(self):
        initial_check = True
        while not self.stop_monitoring.is_set():
            if self._perform_connection_check(is_initial_check=initial_check):
                initial_check = False
            time.sleep(2.5)

    def _perform_connection_check(self, is_initial_check=False, is_manual_refresh=False):
        if is_manual_refresh:
            self.log_to_ui("--- Manual Refresh Triggered ---")

        self.ADB_PATH = self.find_adb_path()
        if not self.ADB_PATH:
            if is_manual_refresh: self.log_to_ui("ADB Executable not found. Please check settings.")
            self.is_adb_connected = False
            self.is_game_running = False
            self.after(0, self._update_ui_on_connection_change)
            return True

        game_package_name = self.setting_vars["Game Configuration"]["Game Package Name"]['var'].get()
        
        adb_connected_now = self.adb.is_device_connected()
        
        if adb_connected_now and not self.is_mods_folder_known_to_exist:
            full_mods_path = self.full_mods_path_var.get().strip()
            if full_mods_path.endswith('/'):
                full_mods_path = full_mods_path[:-1]
            if self.adb.directory_exists(full_mods_path, self.log_to_ui):
                self.log_to_ui("INFO: Game mods folder found on device. Modding is now enabled.")
                self.is_mods_folder_known_to_exist = True
                self.save_config()

        game_running_now = self.adb.is_game_process_running(game_package_name) if adb_connected_now else False
        state_has_changed = (adb_connected_now != self.is_adb_connected) or (game_running_now != self.is_game_running)

        if state_has_changed or is_initial_check:
            self.is_adb_connected = adb_connected_now
            self.is_game_running = game_running_now
            self.after(0, self._update_ui_on_connection_change)
            return True
        
        return False

    def manual_refresh_connection(self):
        self.frames["Mod Manager"].status_widget.config(text="Checking...", state="disabled")
        self.run_in_thread(self._perform_connection_check, is_initial_check=True, is_manual_refresh=True)

    def _update_ui_on_connection_change(self):
        mod_manager_frame = self.frames["Mod Manager"]
        
        if self.is_game_running:
            mod_manager_frame.status_widget.config(text="Game Running", bootstyle="success", state="disabled", command=None)
            if not self.device_has_been_scanned:
                 self.refresh_data_and_ui()
        elif self.is_adb_connected:
            if self.is_mods_folder_known_to_exist:
                mod_manager_frame.status_widget.config(text="Emulator Connected (Ready)", bootstyle="info", state="disabled", command=None)
            else:
                mod_manager_frame.status_widget.config(text="Emulator - Run Game Once", bootstyle="warning", state="disabled", command=None)
            self.clear_device_data()
        else:
            mod_manager_frame.status_widget.config(text="Not Detected (Refresh)", bootstyle="danger", state="normal", command=self.manual_refresh_connection)
            self.clear_device_data()

        self.frames["Mod Manager"].update_control_state()
        self.frames["On Device"].update_control_state()

    def clear_device_data(self):
        if self.device_has_been_scanned:
            self.data_manager.managed_device_data = {}
            self.data_manager.unmanaged_device_data = []
            self.device_has_been_scanned = False
            self.frames["Mod Manager"].build_nav(self.data_manager)
            self.frames["On Device"].update_mod_list()

    def initial_local_scan(self):
        self.show_loading_overlay("Scanning Local Files...")
        self.run_in_thread(self._threaded_initial_scan)

    def refresh_local_data_and_ui(self):
        self.show_loading_overlay("Refreshing Local Mods...")
        self.run_in_thread(self._threaded_initial_scan)
        
    def _threaded_initial_scan(self):
        try:
            self.data_manager.refresh_all(scan_device=False)
            self.after(0, self.frames["Mod Manager"].build_nav, self.data_manager)
            self.after(0, self.frames["On Device"].update_mod_list)
        except Exception as e:
            self.log_to_ui(f"Error during initial scan: {e}")
        finally:
            self.after(100, self.hide_loading_overlay)

    def refresh_data_and_ui(self):
        if not self.is_adb_connected:
            messagebox.showerror("Not Connected", "Cannot scan device because the emulator is not connected.")
            return
        self.show_loading_overlay("Scanning Device...")
        self.device_has_been_scanned = True
        self.run_in_thread(self._threaded_refresh)

    def _threaded_refresh(self):
        try:
            self.data_manager.refresh_all(scan_device=True)
            self.after(0, self.frames["Mod Manager"].build_nav, self.data_manager)
            self.after(0, self.frames["On Device"].update_mod_list)
        except Exception as e:
            self.log_to_ui(f"Error during refresh: {e}")
        finally:
            self.after(100, self.hide_loading_overlay)

    def install_mods(self, local_paths, library, category):
        if not self.is_adb_connected or not self.is_mods_folder_known_to_exist:
            messagebox.showerror("Cannot Install", "Emulator not connected or game mods folder not found. Please connect and run the game once.")
            return
            
        target_dir = self.full_mods_path_var.get()
        log_func = self.log_to_ui
        for path in local_paths:
            mod_name = os.path.basename(path)
            try:
                if path in self.mod_mappings:
                    mapping = self.mod_mappings[path]
                    log_func(f"\n--- Updating '{mod_name}' ---")
                    self.adb.delete_device_folder(f"{target_dir}{mapping['device_folder']}", log_func)
                    self.adb.push_mod(path, mapping['device_folder'], target_dir, log_func)
                    mapping.update({'library': library, 'category': category})
                else:
                    log_func(f"\n--- Installing '{mod_name}' ---")
                    device_mods = self.adb.list_device_files(target_dir) or []
                    existing_indices = {int(re.search(r'mod_(\d+)_', mod).group(1)) for mod in device_mods if re.search(r'mod_(\d+)_', mod)}
                    next_index = 0
                    while next_index in existing_indices: next_index += 1
                    safe_mod_name = re.sub(r'[^\w.-]', '_', mod_name)
                    new_device_folder = f"mod_{next_index}_{safe_mod_name}"
                    self.adb.push_mod(path, new_device_folder, target_dir, log_func)
                    self.mod_mappings[path] = {'index': next_index, 'device_folder': new_device_folder, 'library': library, 'category': category}
                self.save_mappings()
                log_func(f"SUCCESS: '{mod_name}' processed.")
            except Exception as e:
                log_func(f"--- FAILED for '{mod_name}' ---: {e}")
        self.after(0, self.refresh_data_and_ui)

    def uninstall_mods(self, local_paths):
        if not self.is_adb_connected or not self.is_mods_folder_known_to_exist:
            messagebox.showerror("Cannot Uninstall", "Emulator not connected or game mods folder not found. Please connect and run the game once.")
            return

        target_dir = self.full_mods_path_var.get()
        log_func = self.log_to_ui
        for path in local_paths:
            if path in self.mod_mappings:
                mapping = self.mod_mappings[path]
                log_func(f"\n--- Uninstalling '{os.path.basename(path)}' ---")
                try:
                    folder_to_delete = f"{target_dir}{mapping['device_folder']}"
                    self.adb.delete_device_folder(folder_to_delete, log_func)
                    del self.mod_mappings[path]
                    self.save_mappings()
                    log_func("SUCCESS! Mod uninstalled and unlinked.")
                except Exception as e:
                    log_func(f"--- UNINSTALL FAILED ---: {e}")
        self.after(0, self.refresh_data_and_ui)

    def launch_game(self):
        if self.is_adb_connected and not self.is_game_running:
            package_name = self.setting_vars["Game Configuration"]["Game Package Name"]['var'].get()
            activity_name = self.setting_vars["Game Configuration"]["Game Activity Name"]['var'].get()
            self.run_in_thread(self.adb.launch_game_activity, package_name, activity_name, self.log_to_ui)

    def force_stop_game(self):
        if self.is_game_running:
            package_name = self.setting_vars["Game Configuration"]["Game Package Name"]['var'].get()
            self.run_in_thread(self.adb.force_stop_package, package_name, self.log_to_ui)

    def open_folder_in_explorer(self, path):
        if not path or not os.path.isdir(path):
            messagebox.showerror("Path Not Found", f"The folder path could not be found:\n\n{path}")
            return
        try:
            if sys.platform == "win32": os.startfile(os.path.normpath(path))
            elif sys.platform == "darwin": subprocess.Popen(["open", path])
            else: subprocess.Popen(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while trying to open the folder:\n\n{e}")

    def log_to_ui(self, message):
        self.frames["Mod Manager"].log(message)

    def show_loading_overlay(self, text="Working..."):
        if not self.loading_overlay:
            self.loading_overlay = tk.Toplevel(self)
            self.loading_overlay.transient(self)
            self.loading_overlay.overrideredirect(True)
            self.loading_overlay.geometry("250x100")
            style = ttk.Style()
            bg_color = style.colors.get('bg')
            fg_color = style.colors.get('fg')
            self.loading_overlay.configure(bg=bg_color)
            x = self.winfo_x() + self.winfo_width() // 2 - 125
            y = self.winfo_y() + self.winfo_height() // 2 - 50
            self.loading_overlay.geometry(f"+{x}+{y}")
            label = ttk.Label(self.loading_overlay, text=text, wraplength=230, justify='center', background=bg_color, foreground=fg_color, font=("Helvetica", 12, "bold"))
            label.pack(expand=True, fill='both', padx=10, pady=10)
            self.loading_overlay.grab_set()

    def hide_loading_overlay(self):
        if self.loading_overlay:
            self.loading_overlay.grab_release()
            self.loading_overlay.destroy()
            self.loading_overlay = None

    def register_setting(self, category, name, default_value, setting_type='text', readonly=False):
        if category not in self.setting_vars: self.setting_vars[category] = {}
        current_value = self.saved_config.get(category, {}).get(name, default_value)
        var = tk.StringVar(value=current_value) if setting_type != 'internal' else None
        self.setting_vars[category][name] = {'var': var, 'type': setting_type, 'readonly': readonly, 'value': current_value}
        return var

    def load_config(self):
        try:
            with open(CONFIG_FILE, 'r') as f: self.saved_config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError): self.saved_config = {}

    def save_config(self):
        self.update_full_mods_path()
        data_to_save = {}
        for category, settings in self.setting_vars.items():
            data_to_save[category] = {}
            for name, details in settings.items():
                if details.get('var'):
                    data_to_save[category][name] = details['var'].get()
                elif details['type'] == 'internal':
                    data_to_save[category][name] = details['value']
        data_to_save['mods_folder_exists'] = self.is_mods_folder_known_to_exist
        with open(CONFIG_FILE, 'w') as f: json.dump(data_to_save, f, indent=4)

    def load_mappings(self):
        try:
            with open(MAPPINGS_FILE, 'r') as f: self.mod_mappings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError): self.mod_mappings = {}

    def save_mappings(self):
        with open(MAPPINGS_FILE, 'w') as f: json.dump(self.mod_mappings, f, indent=4)

    def on_closing(self):
        print("INFO: Shutting down extensions...")
        for ext in self.extensions.values():
            try:
                ext.on_close()
            except Exception as e:
                print(f"ERROR during on_close for extension '{ext.name}': {e}")

        self.stop_monitoring.set()
        self.save_config()
        self.save_mappings()
        if os.path.exists(self.TEMP_ICON_DIR):
            try:
                shutil.rmtree(self.TEMP_ICON_DIR)
            except Exception as e:
                print(f"Note: Could not remove temp directory on exit: {e}")
        self.destroy()

    def show_frame(self, page_name):
        if page_name in self.frames:
            frame = self.frames[page_name]
            if page_name == "Settings":
                frame.build_ui()
            frame.tkraise()
            for name, button in self.nav_buttons.items():
                button.config(bootstyle="primary" if name == page_name else "secondary")
    
    def run_in_thread(self, target_func, *args, **kwargs):
        threading.Thread(target=target_func, args=args, kwargs=kwargs, daemon=True).start()

    def get_local_library_paths(self):
        return self.setting_vars["LocalLibrary"]["Paths"]['value']

    def update_local_library_paths(self, new_paths):
        self.setting_vars["LocalLibrary"]["Paths"]['value'] = new_paths
        self.save_config()

    def set_source_folder_from_local_mod(self, paths):
        self.frames["Mod Manager"].source_folder_path.set(json.dumps(paths))
        log_msg = f"Selected {len(paths)} mod(s)." if len(paths) != 1 else f"Selected source: {os.path.basename(paths[0])}"
        self.log_to_ui(log_msg)

    def clear_source_folder_selection(self):
        if self.frames["Mod Manager"].source_folder_path.get():
            self.frames["Mod Manager"].source_folder_path.set("")
            self.log_to_ui("Selection cleared.")

    def restart_app(self):
        """Restarts the current application."""
        print("INFO: Application restart requested.")
        self.on_closing() # Perform normal cleanup
        
        # Relaunch the application
        # sys.executable is the path to the python interpreter or the frozen .exe
        # sys.argv[0] is the path to the script that was originally run
        os.execv(sys.executable, ['python'] + [sys.argv[0]])

if __name__ == "__main__":
    if sys.platform == "win32":
        myappid = f'kbeq.smxmodmanager.v{APP_VERSION}'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    
    app = App()
    app.mainloop()