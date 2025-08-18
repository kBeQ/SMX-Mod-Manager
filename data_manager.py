# --- Filename: data_manager.py ---
import os
import re
from tkinter import messagebox

CATEGORY_PREFIX = "c_"
REQUIRED_SOUNDS = ["engine.wav", "high.wav", "idle.wav", "low.wav"]
REQUIRED_SUIT_FILES = {
    "icon": "icon.jpg",
    "gear": "gear_suit.png",
    "normal": "gear_suit_normal.png" # Optional, special handling
}

class DataManager:
    def __init__(self, controller):
        self.controller = controller
        self.local_data = {}
        self.managed_device_data = {}
        self.unmanaged_device_data = []

    def refresh_all(self, scan_device=True):
        self.local_data = self._scan_all_local_libs()
        if scan_device:
            self.managed_device_data, self.unmanaged_device_data = self._get_all_device_mods()
        else:
            self.managed_device_data = {}
            self.unmanaged_device_data = []

    def _scan_all_local_libs(self):
        all_local_data = {}
        library_definitions = self.controller.get_local_library_paths()
        for lib_info in library_definitions:
            lib_path = lib_info.get('path')
            lib_type = lib_info.get('type', 'Unknown')
            if not lib_path or not os.path.isdir(lib_path):
                continue
            lib_name = os.path.basename(lib_path)
            all_local_data[lib_name] = self._scan_single_library(lib_path, lib_type)
        return all_local_data

    def _scan_single_library(self, base_path, lib_type):
        library_data = {}
        uncategorized_mods = []
        try:
            for item_name in os.listdir(base_path):
                item_path = os.path.join(base_path, item_name)
                if not os.path.isdir(item_path): continue
                if item_name.lower().startswith(CATEGORY_PREFIX):
                    cat_name = item_name[len(CATEGORY_PREFIX):]
                    if cat_name not in library_data: library_data[cat_name] = []
                    for mod_name in os.listdir(item_path):
                        mod_path = os.path.join(item_path, mod_name)
                        if os.path.isdir(mod_path):
                            details = self._get_local_mod_details(mod_path, lib_type)
                            if details: library_data[cat_name].append(details)
                else:
                    details = self._get_local_mod_details(item_path, lib_type)
                    if details: uncategorized_mods.append(details)
            for cat_name in library_data:
                library_data[cat_name].sort(key=lambda x: x['name'])
            if uncategorized_mods:
                library_data['Uncategorized'] = sorted(uncategorized_mods, key=lambda x: x['name'])
        except Exception as e:
            self.controller.frames["Mod Manager"].log(f"Error reading folder {base_path}: {e}")
        return library_data

    def _get_local_mod_details(self, mod_path, lib_type):
        try:
            mod_name = os.path.basename(mod_path)
            child_contents = os.listdir(mod_path)
            if not child_contents: return None
            
            files_in_dir = {f.lower(): f for f in child_contents}
            status = "Installed" if mod_path in self.controller.mod_mappings else "Not Installed"
            
            mod_details = { 
                "name": mod_name, "full_path": mod_path, "file_count": len(child_contents), 
                "preview_path": None, "status": status, "library_type": lib_type
            }
            
            if lib_type == 'Tracks':
                mod_details["map_file_name"] = next((f for f in child_contents if f.lower().endswith(".smxlevel")), None)
            
            elif lib_type == 'Sounds':
                mod_details["sound_files"] = {f: (f.lower() in files_in_dir) for f in REQUIRED_SOUNDS}

            elif lib_type == 'Suits':
                suit_files_paths = {}
                for key, filename in REQUIRED_SUIT_FILES.items():
                    if filename.lower() in files_in_dir:
                        suit_files_paths[key] = os.path.join(mod_path, files_in_dir[filename.lower()])
                    else:
                        suit_files_paths[key] = None
                mod_details["suit_files"] = suit_files_paths

            if lib_type != 'Suits':
                if "icon.jpg" in files_in_dir:
                    mod_details["icon_path"] = os.path.join(mod_path, files_in_dir["icon.jpg"])
                elif "icon.png" in files_in_dir:
                    mod_details["icon_path"] = os.path.join(mod_path, files_in_dir["icon.png"])

            if "preview.jpg" in files_in_dir:
                mod_details["preview_path"] = os.path.join(mod_path, files_in_dir["preview.jpg"])
            elif "preview.png" in files_in_dir:
                mod_details["preview_path"] = os.path.join(mod_path, files_in_dir["preview.png"])

            return mod_details
        except Exception:
            return None

    def _get_all_device_mods(self):
        log_func = self.controller.frames["Mod Manager"].log
        log_func("\n--- Scanning Device For Mods ---")
        target_dir = self.controller.full_mods_path_var.get()
        
        device_folders = self.controller.adb.list_device_files(target_dir)
        if device_folders is None: return {}, []
            
        mapped_device_folders = {v['device_folder'] for v in self.controller.mod_mappings.values()}
        orphaned_keys = [lp for lp, mi in self.controller.mod_mappings.items() if mi['device_folder'] not in device_folders]
        if orphaned_keys:
            log_func(f"Found {len(orphaned_keys)} orphaned mapping(s). Pruning...")
            for key in orphaned_keys: del self.controller.mod_mappings[key]
            self.controller.save_mappings()

        unmanaged_folders = [f for f in device_folders if not f.startswith("mod_")]
        
        unmanaged_mod_details = [self._get_unmanaged_mod_details(folder) for folder in unmanaged_folders]
        
        managed_mod_details = self._build_managed_device_data()
        log_func("--- Device Scan Complete ---")
        return (managed_mod_details, [d for d in unmanaged_mod_details if d])

    def _build_managed_device_data(self):
        libraries = {}
        library_definitions = self.controller.get_local_library_paths()
        path_to_type_map = {lib['path']: lib.get('type', 'Unknown') for lib in library_definitions}

        for local_path, mapping_info in self.controller.mod_mappings.items():
            lib_root_path = os.path.dirname(local_path)
            if os.path.basename(lib_root_path).lower().startswith(CATEGORY_PREFIX):
                lib_root_path = os.path.dirname(lib_root_path)
            
            lib_type = path_to_type_map.get(lib_root_path, 'Unknown')
            mod_details = self._get_local_mod_details(local_path, lib_type)
            
            if mod_details:
                lib_name, cat_name = mapping_info.get('library', 'Unc'), mapping_info.get('category', 'Unc')
                if lib_name not in libraries: libraries[lib_name] = {}
                if cat_name not in libraries[lib_name]: libraries[lib_name][cat_name] = []
                mod_details['device_folder'] = mapping_info['device_folder']
                libraries[lib_name][cat_name].append(mod_details)
        return libraries

    def _get_unmanaged_mod_details(self, folder_name):
        target_dir = self.controller.full_mods_path_var.get()
        device_unmanaged_base_path = f"{target_dir}{folder_name}"
        top_level_contents = self.controller.adb.list_device_files(device_unmanaged_base_path)
        if not top_level_contents or (len(top_level_contents) > 0 and not top_level_contents[0]): return None
        
        actual_mod_folder_name = top_level_contents[0].strip() if top_level_contents else folder_name
        if not actual_mod_folder_name: return None
        
        # BUG FIX: Define safe_mod_name early so it's always available
        safe_mod_name = re.sub(r'[\\/*?:"<>| ]', "_", actual_mod_folder_name)

        device_mod_path = f"{device_unmanaged_base_path}/{actual_mod_folder_name}"
        device_files = self.controller.adb.list_device_files(device_mod_path)
        files_on_device = {f.lower(): f for f in device_files} if device_files else {}
        
        # REFINED LOGIC: Update mod type inference
        mod_type = "Unknown"
        if any(f.lower().endswith(".smxlevel") for f in files_on_device):
            mod_type = "Tracks"
        elif REQUIRED_SUIT_FILES["gear"].lower() in files_on_device:
            mod_type = "Suits"
        elif any(f.lower().endswith(".wav") for f in files_on_device):
            mod_type = "Sounds"

        mod_data = { 'name': actual_mod_folder_name, 'device_folder': folder_name, 'mod_type': mod_type }
        
        if mod_type == "Tracks":
            mod_data['map_file_name'] = next((f for f in device_files if f.lower().endswith(".smxlevel")), None)
        elif mod_type == "Sounds":
            mod_data['sound_files'] = {f: (f.lower() in files_on_device) for f in REQUIRED_SOUNDS}
        elif mod_type == "Suits":
            suit_files = {}
            for key, filename in REQUIRED_SUIT_FILES.items():
                if filename.lower() in files_on_device:
                    device_path = f"{device_mod_path}/{files_on_device[filename.lower()]}"
                    local_path = os.path.join(self.controller.TEMP_ICON_DIR, f"unmanaged_{safe_mod_name}_{key}.png")
                    if self.controller.adb.pull_file(device_path, local_path):
                        suit_files[key] = local_path
                else:
                    suit_files[key] = None
            mod_data['suit_files'] = suit_files
        
        preview_name = "preview.jpg" if "preview.jpg" in files_on_device else "preview.png" if "preview.png" in files_on_device else None
        if preview_name:
            device_path = f"{device_mod_path}/{preview_name}"
            local_path = os.path.join(self.controller.TEMP_ICON_DIR, f"unmanaged_{safe_mod_name}_preview.jpg")
            if self.controller.adb.pull_file(device_path, local_path):
                mod_data['preview_path'] = local_path

        return mod_data