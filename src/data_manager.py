# --- Filename: data_manager.py ---
import os
import re
from tkinter import messagebox
import zipfile
import hashlib
from pathlib import Path

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
        # This is the single source of truth for local file scanning.
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
        custom_scanners = self.controller.custom_library_scanners
        if lib_type in custom_scanners:
            scanner_func = custom_scanners[lib_type]
            try:
                self.controller.log_to_ui(f"INFO: Using custom scanner for library type '{lib_type}'")
                return scanner_func(base_path)
            except Exception as e:
                self.controller.log_to_ui(f"ERROR: Custom scanner for '{lib_type}' failed: {e}")
                return {}

        library_data = {}
        uncategorized_mods = []
        try:
            for item_name in os.listdir(base_path):
                item_path = os.path.join(base_path, item_name)
                if item_name.lower().startswith(CATEGORY_PREFIX) and os.path.isdir(item_path):
                    cat_name = item_name[len(CATEGORY_PREFIX):]
                    if cat_name not in library_data: library_data[cat_name] = []
                    for mod_zip_name in os.listdir(item_path):
                        if mod_zip_name.lower().endswith('.zip'):
                            mod_zip_path = os.path.join(item_path, mod_zip_name)
                            details = self.get_local_mod_details_from_zip(mod_zip_path, lib_type)
                            if details: library_data[cat_name].append(details)
                elif item_name.lower().endswith('.zip') and os.path.isfile(item_path):
                    details = self.get_local_mod_details_from_zip(item_path, lib_type)
                    if details: uncategorized_mods.append(details)
            
            for cat_name in library_data:
                library_data[cat_name].sort(key=lambda x: x['name'])
            if uncategorized_mods:
                library_data['Uncategorized'] = sorted(uncategorized_mods, key=lambda x: x['name'])
        except Exception as e:
            self.controller.log_to_ui(f"Error reading folder {base_path}: {e}")
        return library_data

    def get_local_mod_details_from_zip(self, mod_zip_path, lib_type):
        try:
            if not zipfile.is_zipfile(mod_zip_path): return None
            mod_name = os.path.basename(mod_zip_path)[:-4]
            with zipfile.ZipFile(mod_zip_path, 'r') as zip_ref:
                namelist = zip_ref.namelist()
                if not namelist: return None
                files_in_zip = {os.path.basename(f).lower(): f for f in namelist if os.path.basename(f)}
                status = "Installed" if mod_zip_path in self.controller.mod_mappings else "Not Installed"
                mod_details = { 
                    "name": mod_name, "full_path": mod_zip_path, "file_count": len(namelist), 
                    "preview_path": None, "icon_path": None, "status": status, "library_type": lib_type
                }
                def extract_and_get_path(zip_member_path):
                    unique_prefix = hashlib.md5(mod_zip_path.encode()).hexdigest()[:8]
                    base_filename = os.path.basename(zip_member_path)
                    local_filename = f"{unique_prefix}_{base_filename}"
                    extracted_path = os.path.join(self.controller.TEMP_ICON_DIR, local_filename)
                    if not os.path.exists(extracted_path):
                        zip_ref.extract(zip_member_path, self.controller.TEMP_ICON_DIR)
                        os.rename(os.path.join(self.controller.TEMP_ICON_DIR, zip_member_path), extracted_path)
                    return extracted_path
                preview_path = files_in_zip.get("preview.jpg") or files_in_zip.get("preview.png")
                if preview_path: mod_details["preview_path"] = extract_and_get_path(preview_path)
                if lib_type == 'Tracks':
                    mod_details["map_file_name"] = next((os.path.basename(f) for f in namelist if f.lower().endswith(".smxlevel")), None)
                elif lib_type == 'Sounds':
                    mod_details["sound_files"] = {f: (f.lower() in files_in_zip) for f in REQUIRED_SOUNDS}
                elif lib_type == 'Suits':
                    suit_files_paths = {}
                    for key, filename in REQUIRED_SUIT_FILES.items():
                        member_path = files_in_zip.get(filename.lower())
                        suit_files_paths[key] = extract_and_get_path(member_path) if member_path else None
                    mod_details["suit_files"] = suit_files_paths
                if lib_type != 'Suits':
                    icon_path = files_in_zip.get("icon.jpg") or files_in_zip.get("icon.png")
                    if icon_path: mod_details["icon_path"] = extract_and_get_path(icon_path)
                return mod_details
        except Exception as e:
            self.controller.log_to_ui(f"ERROR: Failed to read details from {os.path.basename(mod_zip_path)}: {e}")
            return None

    def _get_all_device_mods(self):
        log_func = self.controller.log_to_ui
        log_func("\n--- Scanning Device For Mods ---")
        target_dir = self.controller.full_mods_path_var.get()
        device_folders = self.controller.adb.list_device_files(target_dir)
        if device_folders is None: return {}, []
        mapped_device_folders = {v['device_folder'] for v in self.controller.mod_mappings.values()}
        orphaned_keys = [lp for lp, mi in self.controller.mod_mappings.items() if mi['device_folder'] not in mapped_device_folders]
        if orphaned_keys:
            log_func(f"Found {len(orphaned_keys)} orphaned mapping(s). Pruning...")
            for key in orphaned_keys: del self.controller.mod_mappings[key]
            self.controller.save_mappings()
        unmanaged_folders = [f for f in device_folders if not f.startswith("mod_")]
        unmanaged_mod_details = [self._get_unmanaged_mod_details(folder) for folder in unmanaged_folders]
        managed_mod_details = self._build_managed_device_data()
        log_func("--- Device Scan Complete ---")
        return (managed_mod_details, [d for d in unmanaged_mod_details if d])

    # --- THE FIX IS HERE ---
    def _build_managed_device_data(self):
        """
        Builds the data structure for installed mods by looking up their details
        in the already-scanned self.local_data, ensuring custom scanners are respected.
        """
        # 1. Create a flat lookup table from file path to the mod's details dictionary.
        # This is our single source of truth, populated by the correct scanners.
        local_mod_lookup = {
            mod['full_path']: mod
            for library in self.local_data.values()
            for category in library.values()
            for mod in category
        }

        managed_libraries = {}
        for local_zip_path, mapping_info in self.controller.mod_mappings.items():
            # 2. Find the pre-scanned details for this installed mod.
            mod_details = local_mod_lookup.get(local_zip_path)
            
            if mod_details:
                lib_name = mapping_info.get('library', 'Unknown')
                cat_name = mapping_info.get('category', 'Unknown')
                if lib_name not in managed_libraries: managed_libraries[lib_name] = {}
                if cat_name not in managed_libraries[lib_name]: managed_libraries[lib_name][cat_name] = []
                
                # Create a copy to avoid modifying the original data
                managed_mod_details = mod_details.copy()
                managed_mod_details['device_folder'] = mapping_info['device_folder']
                managed_libraries[lib_name][cat_name].append(managed_mod_details)
                
        return managed_libraries

    def _get_unmanaged_mod_details(self, folder_name):
        target_dir = self.controller.full_mods_path_var.get()
        device_unmanaged_base_path = f"{target_dir}{folder_name}"
        top_level_contents = self.controller.adb.list_device_files(device_unmanaged_base_path)
        if not top_level_contents: return None
        actual_mod_folder_name = top_level_contents[0].strip() if top_level_contents else folder_name
        if not actual_mod_folder_name: return None
        safe_mod_name = re.sub(r'[\\/*?:"<>| ]', "_", actual_mod_folder_name)
        device_mod_path = f"{device_unmanaged_base_path}/{actual_mod_folder_name}"
        device_files = self.controller.adb.list_device_files(device_mod_path)
        files_on_device = {f.lower(): f for f in device_files} if device_files else {}
        mod_type = "Unknown"
        if any(f.lower().endswith(".smxlevel") for f in files_on_device): mod_type = "Tracks"
        elif REQUIRED_SUIT_FILES["gear"].lower() in files_on_device: mod_type = "Suits"
        elif any(f.lower().endswith(".wav") for f in files_on_device): mod_type = "Sounds"
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
                    if self.controller.adb.pull_file(device_path, local_path): suit_files[key] = local_path
                else: suit_files[key] = None
            mod_data['suit_files'] = suit_files
        preview_name = next((f for f in ["preview.jpg", "preview.png"] if f in files_on_device), None)
        if preview_name:
            device_path = f"{device_mod_path}/{preview_name}"
            local_path = os.path.join(self.controller.TEMP_ICON_DIR, f"unmanaged_{safe_mod_name}_preview.jpg")
            if self.controller.adb.pull_file(device_path, local_path): mod_data['preview_path'] = local_path
        return mod_data