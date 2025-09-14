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
import time
import ctypes
from PIL import Image, ImageTk
from pathlib import Path
import importlib.util

from src.mod_manager_ui import ModManagerFrame
from src.settings_ui import SettingsFrame
from src.adb_handler import AdbHandler
from src.data_manager import DataManager
from src.extensions_ui import ExtensionsFrame
from src.github_handler import GitHubHandler

CONFIG_FILE = "config.json"
MAPPINGS_FILE = "mod_mappings.json"
EXTENSIONS_SETTINGS_FILE = "extensions_settings.json" 
APP_VERSION = "8.0.5" # Version bump for critical architecture fix

def get_resource_path(filename):
    if getattr(sys, "frozen", False): base_dir = sys._MEIPASS
    else: base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, 'assets', filename)

class SplashScreen:
    def __init__(self, parent):
        self.parent = parent
        self.splash = tk.Toplevel(parent)
        self.splash.overrideredirect(True)
        splash_image_path = get_resource_path("SMX Mod Manager.png")
        if not os.path.exists(splash_image_path):
            self.parent.after(100, self.close_splash)
            return
        self.splash_image = ImageTk.PhotoImage(Image.open(splash_image_path))
        img_width, img_height = self.splash_image.width(), self.splash_image.height()
        screen_width, screen_height = self.splash.winfo_screenwidth(), self.splash.winfo_screenheight()
        x, y = (screen_width // 2) - (img_width // 2), (screen_height // 2) - (img_height // 2)
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

class App(ttk.Window):
    def __init__(self, themename="superhero"):
        super().__init__(themename=themename)
        self.withdraw()
        SplashScreen(self)
        self.title(f"SMX Mod Manager v{APP_VERSION}")
        self.geometry("1400x850")

        try:
            icon_path = get_resource_path("smx_mod_manager.ico")
            if os.path.exists(icon_path): self.iconbitmap(icon_path)
        except Exception as e: print(f"Could not set application icon: {e}")
        
        self.TEMP_ICON_DIR = os.path.join(tempfile.gettempdir(), "smx_mod_manager_icons")
        if os.path.exists(self.TEMP_ICON_DIR): shutil.rmtree(self.TEMP_ICON_DIR)
        os.makedirs(self.TEMP_ICON_DIR)

        self.github_handler = GitHubHandler()
        self.extensions = {}
        
        # --- THE FIX IS HERE ---
        # 1. Define base types and a registry for extension scanners.
        # This state is now reliable and not based on appending to a list.
        self.base_library_types = ["Tracks", "Sounds", "Suits"]
        self.custom_library_scanners = {}
        
        self.setting_vars = {}
        self.saved_config = {}
        self.mod_mappings = {}
        self.extension_settings = {}
        self.load_config()

        if self.saved_config.get("window_geometry"):
            try: self.geometry(self.saved_config["window_geometry"])
            except tk.TclError as e: print(f"WARNING: Could not restore geometry: {e}")

        self.load_mappings()
        self._load_extension_settings()
        self.is_mods_folder_known_to_exist = self.saved_config.get("mods_folder_exists", False)

        self.register_setting("Game Configuration", "Game Package Name", "com.Evag.SMX")
        self.register_setting("Game Configuration", "Mods Subfolder Path", "files/Mods/")
        self.full_mods_path_var = self.register_setting("Game Configuration", "Full Mods Path (Auto-generated)", "", readonly=True)
        self.register_setting("Game Configuration", "Game Activity Name", "com.unity3d.player.UnityPlayerActivity")
        default_gpg_adb_path = r"C:\Program Files\Google\Play Games Developer Emulator\current\emulator\adb.exe"
        self.register_setting("Advanced", "ADB Executable Override", default_gpg_adb_path, setting_type='file')
        self.register_setting("LocalLibrary", "Paths", [], setting_type='internal')
        
        self._migrate_library_config()
        self.update_full_mods_path()
        self.ensure_initial_config()

        self.ADB_PATH = self.find_adb_path()
        if not self.ADB_PATH: messagebox.showerror("ADB Not Found", "Could not find adb.exe. Please configure its location in Settings.")

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
        
        self.core_frames = ["Mod Manager", "Extensions", "Settings"]
        for name in self.core_frames:
            button = ttk.Button(self.nav_frame, text=name, command=lambda n=name: self.show_frame(n), bootstyle="secondary", padding=(0, 10))
            button.pack(side="left", fill="x", expand=True, padx=(0,1))
            self.nav_buttons[name] = button

        self.container = ttk.Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        self.frames = {}
        
        for F in (ModManagerFrame, ExtensionsFrame, SettingsFrame):
            frame = F(self.container, self)
            self.frames[F.name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        if self.extensions:
            print(f"INFO: Initializing {len(self.extensions)} loaded extension(s)...")
            for ext in self.extensions.values():
                try: ext.initialize(self)
                except Exception as e: print(f"ERROR: Failed to initialize extension '{ext.name}': {e}")
            print("--- Extension initialization complete ---")

        self.show_frame("Mod Manager")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        monitor_thread = threading.Thread(target=self._connection_monitoring_loop, daemon=True)
        monitor_thread.start()

    def get_script_directory(self):
        if getattr(sys, 'frozen', False): return os.path.dirname(sys.executable)
        else: return os.path.dirname(os.path.abspath(__file__))

    def _load_extensions(self):
        ext_dir = Path(self.get_script_directory()) / "Extensions"
        if not ext_dir.is_dir(): return
        print("--- Scanning for local extensions ---")
        for d in ext_dir.iterdir():
            if d.is_dir() and (d / "manifest.json").is_file() and (d / "plugin.py").is_file():
                try:
                    name = f"extensions.{d.name}.plugin"
                    spec = importlib.util.spec_from_file_location(name, d / "plugin.py")
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[name] = module
                    spec.loader.exec_module(module)
                    if hasattr(module, "SMXExtension"):
                        inst = module.SMXExtension()
                        if inst.name in self.extensions: continue
                        self.extensions[inst.name] = inst
                        print(f"  OK: Loaded extension '{inst.name}'")
                except Exception as e: print(f"ERROR: Failed to load extension from '{d.name}': {e}")
        print(f"--- Found {len(self.extensions)} valid local extension(s) ---")

    def add_extension_tab(self, name, frame_class):
        if name in self.frames: return
        btn = ttk.Button(self.nav_frame, text=name, command=lambda n=name: self.show_frame(n), bootstyle="secondary", padding=(0, 10))
        btn.pack(side="left", fill="x", expand=True, padx=(0,1))
        self.nav_buttons[name] = btn
        frame = frame_class(self.container, self)
        self.frames[name] = frame
        frame.grid(row=0, column=0, sticky="nsew")
        print(f"  -> Extension '{name}' successfully added a UI tab.")
    
    def register_library_scanner(self, type_name, func):
        if type_name in self.base_library_types:
            print(f"ERROR: Extension tried to overwrite a built-in library type: '{type_name}'")
            return
        if type_name in self.custom_library_scanners:
             print(f"WARNING: An extension is overwriting a custom scanner for type: '{type_name}'")
        self.custom_library_scanners[type_name] = func
        print(f"  -> Extension registered scanner for type: '{type_name}'")

    def get_available_library_types(self):
        all_types = self.base_library_types + list(self.custom_library_scanners.keys())
        return sorted(list(set(all_types)))

    def _load_extension_settings(self):
        try:
            with open(EXTENSIONS_SETTINGS_FILE, 'r') as f: self.extension_settings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError): self.extension_settings = {}

    def get_extension_setting(self, ext_name, key, default=None):
        return self.extension_settings.get(ext_name, {}).get(key, default)

    def save_extension_setting(self, ext_name, key, value):
        if ext_name not in self.extension_settings: self.extension_settings[ext_name] = {}
        self.extension_settings[ext_name][key] = value
        with open(EXTENSIONS_SETTINGS_FILE, 'w') as f: json.dump(self.extension_settings, f, indent=4)
        print(f"INFO: Setting '{key}' for extension '{ext_name}' saved.")

    def _migrate_library_config(self):
        paths = self.setting_vars.get("LocalLibrary", {}).get("Paths", {}).get('value')
        if not paths or isinstance(paths[0], dict): return
        print("INFO: Migrating old library config format.")
        new_paths = [{'type': 'Tracks', 'path': p} for p in paths if isinstance(p, str)]
        self.setting_vars["LocalLibrary"]["Paths"]['value'] = new_paths
        self.save_config()

    def update_full_mods_path(self, *args):
        pkg = self.setting_vars["Game Configuration"]["Game Package Name"]['var'].get()
        sub = self.setting_vars["Game Configuration"]["Mods Subfolder Path"]['var'].get()
        full_path = os.path.join(f"/sdcard/Android/data/{pkg}/", sub).replace("\\", "/")
        if not full_path.endswith('/'): full_path += '/'
        self.full_mods_path_var.set(full_path)

    def ensure_initial_config(self):
        if not os.path.exists(CONFIG_FILE): self.save_config()

    def find_adb_path(self):
        local = os.path.join(self.get_script_directory(), "bin", "adb.exe")
        if os.path.exists(local): return local
        settings_var = self.setting_vars.get("Advanced", {}).get("ADB Executable Override", {}).get('var')
        if settings_var:
            settings_path = settings_var.get()
            if settings_path and os.path.exists(settings_path): return settings_path
        return None

    def _connection_monitoring_loop(self):
        init = True
        while not self.stop_monitoring.is_set():
            if self._perform_connection_check(is_initial_check=init): init = False
            time.sleep(2.5)

    def _perform_connection_check(self, is_initial_check=False, is_manual_refresh=False):
        if not self.ADB_PATH:
            self.is_adb_connected = self.is_game_running = False
            self.after(0, self._update_ui_on_connection_change)
            return True
        connected = self.adb.is_device_connected()
        running = self.adb.is_game_process_running(self.setting_vars["Game Configuration"]["Game Package Name"]['var'].get()) if connected else False
        changed = (connected != self.is_adb_connected) or (running != self.is_game_running)
        if changed or is_initial_check:
            self.is_adb_connected, self.is_game_running = connected, running
            self.after(0, self._update_ui_on_connection_change)
            return True
        return False

    def manual_refresh_connection(self):
        self.frames["Mod Manager"].status_widget.config(text="Checking...", state="disabled")
        self.run_in_thread(self._perform_connection_check, is_initial_check=True, is_manual_refresh=True)

    def _update_ui_on_connection_change(self):
        status_widget = self.frames["Mod Manager"].status_widget
        if self.is_game_running:
            status_widget.config(text="Game Running", bootstyle="success", state="disabled")
            if not self.device_has_been_scanned: self.refresh_data_and_ui()
        elif self.is_adb_connected:
            status_widget.config(text="Emulator Connected", bootstyle="info", state="disabled")
            self.clear_device_data()
        else:
            status_widget.config(text="Not Detected", bootstyle="danger", state="normal", command=self.manual_refresh_connection)
            self.clear_device_data()
        self.frames["Mod Manager"].update_control_state()

    def clear_device_data(self):
        if self.device_has_been_scanned:
            self.data_manager.managed_device_data, self.data_manager.unmanaged_device_data = {}, []
            self.device_has_been_scanned = False
            self.frames["Mod Manager"].build_nav(self.data_manager)

    def initial_local_scan(self):
        self.show_loading_overlay("Scanning Local Files...")
        self.run_in_thread(self._threaded_initial_scan)

    def refresh_local_data_and_ui(self): self.initial_local_scan()
        
    def _threaded_initial_scan(self):
        try:
            self.data_manager.refresh_all(scan_device=False)
            self.after(0, self.frames["Mod Manager"].build_nav, self.data_manager)
        finally: self.after(100, self.hide_loading_overlay)

    def refresh_data_and_ui(self):
        if not self.is_adb_connected: return
        self.show_loading_overlay("Scanning Device...")
        self.device_has_been_scanned = True
        self.run_in_thread(self._threaded_refresh)

    def _threaded_refresh(self):
        try:
            self.data_manager.refresh_all(scan_device=True)
            self.after(0, self.frames["Mod Manager"].build_nav, self.data_manager)
        finally: self.after(100, self.hide_loading_overlay)

    def _update_ui_after_mod_operation(self, paths, new_status):
        for path in paths:
            for cats in self.data_manager.local_data.values():
                for mods in cats.values():
                    for mod in mods:
                        if mod['full_path'] == path: mod['status'] = new_status
        for widget in self.frames["Mod Manager"].local_mods_frame.scrollable_frame.winfo_children():
            if hasattr(widget, 'mod_data') and widget.mod_data.get('full_path') in paths:
                widget.update_ui_for_status(new_status)
        self.frames["Mod Manager"].update_control_state()

    def install_mods(self, paths, lib, cat):
        if not self.is_adb_connected: return
        target = self.full_mods_path_var.get()
        success = []
        for p in paths:
            mod_name = os.path.basename(p)
            try:
                if p in self.mod_mappings:
                    map_info = self.mod_mappings[p]
                    self.log_to_ui(f"\n--- Updating '{mod_name}' ---")
                    self.adb.delete_device_folder(f"{target}{map_info['device_folder']}", self.log_to_ui)
                    self.adb.push_mod(p, map_info['device_folder'], target, self.log_to_ui)
                    map_info.update({'library': lib, 'category': cat})
                else:
                    self.log_to_ui(f"\n--- Installing '{mod_name}' ---")
                    dev_mods = self.adb.list_device_files(target) or []
                    indices = {int(re.search(r'mod_(\d+)_', m).group(1)) for m in dev_mods if re.search(r'mod_(\d+)_', m)}
                    idx = 0
                    while idx in indices: idx += 1
                    safe_name = re.sub(r'[^\w.-]', '_', os.path.splitext(mod_name)[0])
                    dev_folder = f"mod_{idx}_{safe_name}"
                    self.adb.push_mod(p, dev_folder, target, self.log_to_ui)
                    self.mod_mappings[p] = {'index': idx, 'device_folder': dev_folder, 'library': lib, 'category': cat}
                self.save_mappings()
                self.log_to_ui(f"SUCCESS: '{mod_name}' processed.")
                success.append(p)
            except Exception as e: self.log_to_ui(f"--- FAILED for '{mod_name}' ---: {e}")
        if success: self.after(0, self._update_ui_after_mod_operation, success, "Installed")

    def uninstall_mods(self, paths):
        if not self.is_adb_connected: return
        target = self.full_mods_path_var.get()
        success = []
        for p in paths:
            if p in self.mod_mappings:
                self.log_to_ui(f"\n--- Uninstalling '{os.path.basename(p)}' ---")
                try:
                    self.adb.delete_device_folder(f"{target}{self.mod_mappings[p]['device_folder']}", self.log_to_ui)
                    del self.mod_mappings[p]
                    self.save_mappings()
                    self.log_to_ui("SUCCESS! Mod uninstalled.")
                    success.append(p)
                except Exception as e: self.log_to_ui(f"--- UNINSTALL FAILED ---: {e}")
        if success: self.after(0, self._update_ui_after_mod_operation, success, "Not Installed")

    def launch_game(self): self.run_in_thread(self.adb.launch_game_activity, self.setting_vars["Game Configuration"]["Game Package Name"]['var'].get(), self.setting_vars["Game Configuration"]["Game Activity Name"]['var'].get(), self.log_to_ui)
    def force_stop_game(self): self.run_in_thread(self.adb.force_stop_package, self.setting_vars["Game Configuration"]["Game Package Name"]['var'].get(), self.log_to_ui)

    def open_folder_in_explorer(self, path):
        if not path: return
        target = os.path.dirname(path) if os.path.isfile(path) else path
        try:
            if sys.platform == "win32": os.startfile(os.path.normpath(target))
            else: subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", target])
        except Exception as e: messagebox.showerror("Error", f"Could not open folder: {e}")

    def log_to_ui(self, msg): self.frames["Mod Manager"].log(msg)
    
    def show_loading_overlay(self, text="Working..."):
        if self.loading_overlay: return
        self.loading_overlay = tk.Toplevel(self)
        self.loading_overlay.transient(self)
        self.loading_overlay.overrideredirect(True)
        style = ttk.Style()
        self.loading_overlay.configure(bg=style.colors.get('bg'))
        x, y = self.winfo_x() + (self.winfo_width() - 250) // 2, self.winfo_y() + (self.winfo_height() - 100) // 2
        self.loading_overlay.geometry(f"250x100+{x}+{y}")
        label = ttk.Label(self.loading_overlay, text=text, wraplength=230, justify='center', background=style.colors.get('bg'), foreground=style.colors.get('fg'), font=("Helvetica", 12, "bold"))
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
        data = {}
        for cat, settings in self.setting_vars.items():
            data[cat] = {}
            for name, details in settings.items():
                data[cat][name] = details['var'].get() if details.get('var') else details['value']
        data['mods_folder_exists'] = self.is_mods_folder_known_to_exist
        if self.state() == 'normal': data['window_geometry'] = self.winfo_geometry()
        with open(CONFIG_FILE, 'w') as f: json.dump(data, f, indent=4)

    def load_mappings(self):
        try:
            with open(MAPPINGS_FILE, 'r') as f: self.mod_mappings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError): self.mod_mappings = {}

    def save_mappings(self):
        with open(MAPPINGS_FILE, 'w') as f: json.dump(self.mod_mappings, f, indent=4)

    def on_closing(self):
        for ext in self.extensions.values():
            try: ext.on_close()
            except Exception as e: print(f"ERROR on_close for '{ext.name}': {e}")
        self.stop_monitoring.set()
        self.save_config()
        self.save_mappings()
        if os.path.exists(self.TEMP_ICON_DIR): shutil.rmtree(self.TEMP_ICON_DIR, ignore_errors=True)
        self.destroy()

    def show_frame(self, page_name):
        if page_name in self.frames:
            frame = self.frames[page_name]
            if page_name == "Settings": frame.build_ui()
            frame.tkraise()
            for name, btn in self.nav_buttons.items():
                btn.config(bootstyle="primary" if name == page_name else "secondary")
    
    def run_in_thread(self, target, *args, **kwargs):
        threading.Thread(target=target, args=args, kwargs=kwargs, daemon=True).start()

    def get_local_library_paths(self): return self.setting_vars["LocalLibrary"]["Paths"]['value']
    def update_local_library_paths(self, paths):
        self.setting_vars["LocalLibrary"]["Paths"]['value'] = paths
        self.save_config()

    def set_source_folder_from_local_mod(self, paths):
        self.frames["Mod Manager"].source_folder_path.set(json.dumps(paths))
        self.log_to_ui(f"Selected {len(paths)} mod(s).")
    def clear_source_folder_selection(self):
        if self.frames["Mod Manager"].source_folder_path.get():
            self.frames["Mod Manager"].source_folder_path.set("")
            self.log_to_ui("Selection cleared.")
            
    def sync_mod_mappings(self):
        if not self.is_adb_connected:
            messagebox.showerror("Not Connected", "Cannot sync mappings because the emulator is not connected.")
            return
        if not messagebox.askyesno("Confirm Sync", 
            "This will scan the device and re-link installed mods to your local library files based on their .zip filename.\n\nThis is a recovery tool and will overwrite existing mappings. Continue?"):
            return
        self.show_loading_overlay("Syncing Mappings...")
        self.run_in_thread(self._threaded_sync)

    def _threaded_sync(self):
        try:
            target_dir = self.full_mods_path_var.get()
            device_folders = self.adb.list_device_files(target_dir) or []
            
            local_mods_map = {
                os.path.splitext(os.path.basename(mod["full_path"]))[0]: mod
                for lib in self.data_manager.local_data.values()
                for cat in lib.values()
                for mod in cat
            }
            
            found, unlinked = 0, 0
            new_mappings = {}

            for device_folder in device_folders:
                match = re.search(r'mod_(\d+)_(.*)', device_folder)
                if not match: continue
                index_str, device_name = match.groups()
                
                if device_name in local_mods_map:
                    local_mod = local_mods_map[device_name]
                    local_path = local_mod["full_path"]
                    lib_path_obj = Path(local_path)
                    lib_root = next((lib['path'] for lib in self.get_local_library_paths() if Path(lib['path']) in lib_path_obj.parents), None)
                    
                    parent_folder_name = lib_path_obj.parent.name
                    category = parent_folder_name.replace("c_", "", 1) if parent_folder_name.startswith("c_") else parent_folder_name
                    if lib_root and Path(lib_root) == lib_path_obj.parent:
                        category = "Uncategorized"

                    new_mappings[local_path] = {
                        'index': int(index_str),
                        'device_folder': device_folder,
                        'library': os.path.basename(lib_root) if lib_root else "Unknown",
                        'category': category
                    }
                    found += 1
                else:
                    unlinked += 1
            
            self.mod_mappings = new_mappings
            self.save_mappings()
            self.after(0, self._report_sync_results, found, unlinked)
        except Exception as e:
            self.after(0, messagebox.showerror, "Sync Error", f"An error occurred during sync: {e}")
        finally:
            self.after(100, self.hide_loading_overlay)
            self.after(100, self.refresh_local_data_and_ui)

    def _report_sync_results(self, found, unlinked):
        messagebox.showinfo("Sync Complete", 
            f"Sync process finished.\n\nSuccessfully re-linked {found} mod(s).\nFound {unlinked} mod(s) on device with no matching local file.\n\nThe UI has been refreshed.")

    def restart_app(self):
        self.on_closing()
        os.execv(sys.executable, ['python'] + [sys.argv[0]])

if __name__ == "__main__":
    if sys.platform == "win32":
        myappid = f'kbeq.smxmodmanager.v{APP_VERSION}'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    app = App()
    app.mainloop()