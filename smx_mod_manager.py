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

# Import other modules...
from mod_manager_ui import ModManagerFrame
from on_device_ui import OnDeviceFrame
from mod_helper_ui import ModHelperFrame
from settings_ui import SettingsFrame
from adb_handler import AdbHandler
from data_manager import DataManager

# --- Global Constants ---
CONFIG_FILE = "config.json"
MAPPINGS_FILE = "mod_mappings.json"
APP_VERSION = "7.17.13"

def get_script_directory():
    """Gets the directory of the running script or frozen executable."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def get_resource_path(filename):
    """Return the correct path to a resource file, 
    both when running from source and when frozen with PyInstaller."""
    if getattr(sys, "frozen", False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, filename)

# --- Splash Screen Class ---
class SplashScreen:
    def __init__(self, parent):
        self.parent = parent
        self.splash = tk.Toplevel(parent)
        self.splash.overrideredirect(True)
        self.splash.attributes('-alpha', 0)

        splash_image_path = get_resource_path("SMX Mod Manager.png")
        if not os.path.exists(splash_image_path):
            # Fallback if image is missing, just close and show main app
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
        ttk.Label(self.splash, image=self.splash_image).pack()
        
        self.parent.after(100, self.fade_in)

    def fade_in(self, alpha=0):
        if alpha < 1:
            alpha += 0.05
            self.splash.attributes('-alpha', alpha)
            self.splash.after(20, lambda: self.fade_in(alpha))
        else:
            self.splash.attributes('-alpha', 1)
            self.splash.after(1300, self.fade_out)

    def fade_out(self, alpha=1):
        if alpha > 0:
            alpha -= 0.05
            self.splash.attributes('-alpha', alpha)
            self.splash.after(20, lambda: self.fade_out(alpha))
        else:
            self.close_splash()

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

        # --- Set window icon (works in both dev & frozen builds) ---
        try:
            icon_path = get_resource_path("smx_mod_manager.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception as e:
            print(f"Could not set application icon: {e}")
        
        # --- The rest of the original init method ---
        self.TEMP_ICON_DIR = os.path.join(tempfile.gettempdir(), "smx_mod_manager_icons")
        if os.path.exists(self.TEMP_ICON_DIR): shutil.rmtree(self.TEMP_ICON_DIR)
        os.makedirs(self.TEMP_ICON_DIR)

        self.setting_vars = {} 
        self.saved_config = {}
        self.mod_mappings = {}
        self.load_config() 
        self.load_mappings()

        # --- Settings Registration ---
        self.register_setting("Game Configuration", "Game Package Name", "com.Evag.SMX")
        self.register_setting("Game Configuration", "Mods Subfolder Path", "files/Mods/")
        self.full_mods_path_var = self.register_setting("Game Configuration", "Full Mods Path (Auto-generated)", "", readonly=True)
        self.register_setting("Game Configuration", "Game Activity Name", "com.unity3d.player.UnityPlayerActivity")
        
        default_gpg_adb_path = r"C:\Program Files\Google\Play Games Developer Emulator\current\emulator\adb.exe"
        self.register_setting("Advanced", "ADB Executable Override", default_gpg_adb_path, setting_type='file')
        self.register_setting("LocalLibrary", "Paths", [], 'internal')
        
        # --- Data Migration for Library Paths ---
        self._migrate_library_config()

        self.update_full_mods_path() # Initial calculation
        
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
        self.is_emulator_process_running = False
        self.is_game_running = False
        self.stop_monitoring = threading.Event()
        self.header_image_path = get_resource_path("SMX Mod Manager.png")

        nav_frame = ttk.Frame(self)
        nav_frame.pack(side="top", fill="x", padx=1, pady=1)
        self.nav_buttons = {}
        for name in ["Mod Manager", "On Device", "Mod Helper", "Settings"]:
            button = ttk.Button(nav_frame, text=name, command=lambda n=name: self.show_frame(n), bootstyle="secondary", padding=(0, 10))
            button.pack(side="left", fill="x", expand=True, padx=(0,1))
            self.nav_buttons[name] = button

        container = ttk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        self.frames = {}
        
        for F in (ModManagerFrame, OnDeviceFrame, ModHelperFrame, SettingsFrame):
            frame = F(container, self)
            self.frames[F.name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        
        self.show_frame("Mod Manager")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        monitor_thread = threading.Thread(target=self._connection_monitoring_loop, daemon=True)
        monitor_thread.start()

    def _migrate_library_config(self):
        """Converts old list-of-strings library paths to new list-of-dicts format."""
        lib_setting = self.setting_vars.get("LocalLibrary", {}).get("Paths")
        if not lib_setting: return

        current_libs = lib_setting['value']
        if not current_libs or isinstance(current_libs[0], dict):
            return # Already new format, empty, or invalid

        # Old format detected: a list of strings
        print("INFO: Old library config format detected. Migrating to new format.")
        new_libs_data = []
        for path in current_libs:
            if isinstance(path, str):
                # Default migrated libraries to "Tracks". The user can change this in settings.
                new_libs_data.append({'type': 'Tracks', 'path': path})
        
        self.setting_vars["LocalLibrary"]["Paths"]['value'] = new_libs_data
        self.save_config() # Save the migrated config immediately to prevent re-migration

    def update_full_mods_path(self, *args):
        """Constructs the full mods path from the package name and subfolder path."""
        package = self.setting_vars["Game Configuration"]["Game Package Name"]['var'].get()
        subfolder = self.setting_vars["Game Configuration"]["Mods Subfolder Path"]['var'].get()
        # Ensure path uses forward slashes and has a trailing slash
        base_path = f"/sdcard/Android/data/{package}/".replace("\\", "/")
        full_path = os.path.join(base_path, subfolder).replace("\\", "/")
        if not full_path.endswith('/'):
            full_path += '/'
        self.full_mods_path_var.set(full_path)

    def ensure_initial_config(self):
        """If config.json does not exist, create it with default values."""
        if not os.path.exists(CONFIG_FILE):
            print("INFO: config.json not found, creating with default values.")
            self.save_config()

    def find_adb_path(self):
        """Finds a usable adb.exe path using a priority system."""
        local_adb_path = os.path.join(get_script_directory(), "adb.exe")
        if os.path.exists(local_adb_path):
            return local_adb_path

        settings_adb_path_var = self.setting_vars.get("Advanced", {}).get("ADB Executable Override", {}).get('var')
        if settings_adb_path_var:
            settings_adb_path = settings_adb_path_var.get()
            if settings_adb_path and os.path.exists(settings_adb_path):
                return settings_adb_path
        return None

    def is_emulator_environment_running(self):
        if not self.ADB_PATH: return False
        for proc in psutil.process_iter(['name', 'exe']):
            try:
                if proc.info['name'] == 'adb.exe' and proc.info['exe'] and os.path.normcase(proc.info['exe']) == os.path.normcase(self.ADB_PATH):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False

    def _connection_monitoring_loop(self):
        initial_check = True
        while not self.stop_monitoring.is_set():
            self.ADB_PATH = self.find_adb_path()
            game_package_name = self.setting_vars["Game Configuration"]["Game Package Name"]['var'].get()
            
            emulator_env_running_now = self.is_emulator_environment_running()
            adb_connected_now = self.adb.is_device_connected() if emulator_env_running_now else False
            game_running_now = self.adb.is_game_process_running(game_package_name) if adb_connected_now else False

            state_has_changed = (adb_connected_now != self.is_adb_connected) or \
                                (emulator_env_running_now != self.is_emulator_process_running) or \
                                (game_running_now != self.is_game_running)

            if state_has_changed or initial_check:
                self.is_emulator_process_running = emulator_env_running_now
                self.is_adb_connected = adb_connected_now
                self.is_game_running = game_running_now
                self.after(0, self._update_ui_on_connection_change)
                initial_check = False
            
            time.sleep(2.5)

    def _update_ui_on_connection_change(self):
        mod_manager_frame = self.frames["Mod Manager"]
        
        if self.is_game_running:
            mod_manager_frame.status_label.config(text="Connected", bootstyle="success")
            if not self.device_has_been_scanned:
                 self.refresh_data_and_ui()
        elif self.is_adb_connected:
            mod_manager_frame.status_label.config(text="Emulator running. Please start the game.", bootstyle="warning")
            self.clear_device_data()
        else:
            mod_manager_frame.status_label.config(text="Not Detected", bootstyle="danger")
            self.clear_device_data()

        self.frames["Mod Manager"].update_control_state(self.is_adb_connected, self.is_game_running)
        self.frames["On Device"].update_control_state(self.is_game_running)

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
        """Refreshes just the local mod data and updates the UI."""
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
        if not self.is_game_running:
            messagebox.showerror("Not Connected", "Cannot scan device because the game is not running.")
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
        if not self.is_game_running:
            self.log_to_ui("INSTALL FAILED: Not connected to the game.")
            messagebox.showerror("Not Connected", "Cannot install mods because the game is not running.")
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
                    safe_mod_name = mod_name.replace(" ", "_")
                    new_device_folder = f"mod_{next_index}_{safe_mod_name}"
                    self.adb.push_mod(path, new_device_folder, target_dir, log_func)
                    self.mod_mappings[path] = {'index': next_index, 'device_folder': new_device_folder, 'library': library, 'category': category}
                self.save_mappings()
                log_func(f"SUCCESS: '{mod_name}' processed.")
            except Exception as e:
                log_func(f"--- FAILED for '{mod_name}' ---: {e}")
        self.after(0, self.refresh_data_and_ui)

    def uninstall_mods(self, local_paths):
        if not self.is_game_running:
            self.log_to_ui("UNINSTALL FAILED: Not connected to the game.")
            messagebox.showerror("Not Connected", "Cannot uninstall mods because the game is not running.")
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

    def log_to_ui(self, message):
        self.frames["Mod Manager"].log(message)

    def show_loading_overlay(self, text="Working..."):
        if not self.loading_overlay:
            self.loading_overlay = tk.Toplevel(self)
            self.loading_overlay.transient(self)
            self.loading_overlay.geometry("200x100")
            style = ttk.Style()
            bg_color = style.colors.get('bg')
            fg_color = style.colors.get('fg')
            self.loading_overlay.configure(bg=bg_color)
            self.loading_overlay.overrideredirect(True)
            x = self.winfo_x() + self.winfo_width() // 2 - 100
            y = self.winfo_y() + self.winfo_height() // 2 - 50
            self.loading_overlay.geometry(f"+{x}+{y}")
            ttk.Label(self.loading_overlay, text=text, background=bg_color, foreground=fg_color, font=("Helvetica", 12, "bold")).pack(expand=True)
            self.loading_overlay.grab_set()

    def hide_loading_overlay(self):
        if self.loading_overlay:
            self.loading_overlay.grab_release()
            self.loading_overlay.destroy()
            self.loading_overlay = None

    def register_setting(self, category, name, default_value, setting_type='text', readonly=False):
        if category not in self.setting_vars: self.setting_vars[category] = {}
        current_value = self.saved_config.get(category, {}).get(name, default_value)
        var = None
        if setting_type == 'list':
            var_value = ", ".join(current_value) if isinstance(current_value, list) else current_value
            var = tk.StringVar(value=var_value)
        elif setting_type != 'internal':
             var = tk.StringVar(value=current_value)
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
                    if details['type'] == 'list':
                        str_value = details['var'].get()
                        list_value = [item.strip() for item in str_value.split(',') if item.strip()]
                        data_to_save[category][name] = list_value
                        details['value'] = list_value
                    # Don't save the auto-generated path to the config file
                    elif name != "Full Mods Path (Auto-generated)":
                        data_to_save[category][name] = details['var'].get()
                elif details['type'] == 'internal':
                    data_to_save[category][name] = details['value']
        
        with open(CONFIG_FILE, 'w') as f: json.dump(data_to_save, f, indent=4)


    def load_mappings(self):
        try:
            with open(MAPPINGS_FILE, 'r') as f: self.mod_mappings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError): self.mod_mappings = {}

    def save_mappings(self):
        with open(MAPPINGS_FILE, 'w') as f: json.dump(self.mod_mappings, f, indent=4)

    def on_closing(self):
        self.stop_monitoring.set()
        self.save_config()
        self.save_mappings()
        if os.path.exists(self.TEMP_ICON_DIR):
            try:
                shutil.rmtree(self.TEMP_ICON_DIR)
            except Exception as e:
                # This prevents a file lock on a temp image from blocking the app closing
                print(f"Note: Could not remove temp directory on exit: {e}")
        self.destroy()

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        if page_name == "Settings":
            frame.build_ui()
        frame.tkraise()
        for name, button in self.nav_buttons.items():
            if name == page_name:
                button.config(bootstyle="primary")
            else:
                button.config(bootstyle="secondary")
    
    def run_in_thread(self, target_func, *args):
        threading.Thread(target=target_func, args=args, daemon=True).start()

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

if __name__ == "__main__":
    if sys.platform == "win32":
        myappid = f'kbeq.smxmodmanager.v{APP_VERSION}'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    
    app = App()
    app.mainloop()