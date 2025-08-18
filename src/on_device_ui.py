# --- Filename: on_device_ui.py ---
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, font
from shared_ui_components import ModListView

class OnDeviceFrame(ttk.Frame):
    name = "On Device"
    def __init__(self, parent, controller):
        super().__init__(parent, padding=15)
        self.controller = controller
        self.data_manager = controller.data_manager
        self.bold_font = font.Font(family="Helvetica", size=10, weight="bold")
        self.active_filter = "All"
        self.filter_buttons = {}

        unmanaged_frame_container = ttk.Labelframe(self, text="On Device (Unmanaged Mods)", padding=15)
        unmanaged_frame_container.pack(expand=True, fill='both')
        
        # --- Header with Scan/Delete and Filters ---
        header_area = ttk.Frame(unmanaged_frame_container)
        header_area.pack(fill='x', pady=(0, 10))

        # Left side controls
        left_controls = ttk.Frame(header_area)
        left_controls.pack(side='left')
        self.scan_button = ttk.Button(left_controls, text="Scan Device", bootstyle="primary", 
                   command=self.controller.refresh_data_and_ui)
        self.scan_button.pack()
        
        # Right side controls
        right_controls = ttk.Frame(header_area)
        right_controls.pack(side='right')
        self.delete_button = ttk.Button(right_controls, text="Delete Selected", bootstyle="danger", 
                   command=self.on_delete_unmanaged_selected)
        self.delete_button.pack()

        # Center filter controls
        filter_frame = ttk.Frame(header_area)
        filter_frame.pack(side='top', pady=(0, 10))
        
        ttk.Label(filter_frame, text="Filter by type:").pack(side='left', padx=(0, 10))
        for category in ["All", "Tracks", "Sounds", "Suits"]:
            btn = ttk.Button(filter_frame, text=category,
                             command=lambda c=category: self.set_filter(c))
            btn.pack(side='left', padx=2)
            self.filter_buttons[category] = btn

        self.unmanaged_mods_frame = ModListView(unmanaged_frame_container, controller, view_type='unmanaged')
        self.unmanaged_mods_frame.pack(expand=True, fill='both', padx=5, pady=(0,5))
        
        self.set_filter("All") # Set initial filter state
        self.update_mod_list()

    def set_filter(self, category):
        self.active_filter = category
        for cat, btn in self.filter_buttons.items():
            if cat == category:
                btn.config(bootstyle="info")
            else:
                btn.config(bootstyle="secondary-outline")
        self.update_mod_list()

    def update_control_state(self, is_running):
        new_state = tk.NORMAL if is_running else tk.DISABLED
        self.scan_button.config(state=new_state)
        self.delete_button.config(state=new_state)

    def update_mod_list(self):
        all_unmanaged_mods = sorted(self.data_manager.unmanaged_device_data, key=lambda x: x['name'])
        
        if self.active_filter == "All":
            mods_to_display = all_unmanaged_mods
        else:
            mods_to_display = [mod for mod in all_unmanaged_mods if mod.get('mod_type') == self.active_filter]
        
        if self.controller.device_has_been_scanned:
            unmanaged_message = f"No unmanaged '{self.active_filter}' mods found on device."
        else:
            unmanaged_message = "Click 'Scan Device' to load mods."
        
        self.unmanaged_mods_frame.display_list(mods_to_display, unmanaged_message)

    def on_delete_unmanaged_selected(self):
        selected_keys = self.unmanaged_mods_frame.get_selected_keys()
        if not selected_keys: return
        self.delete_unmanaged_mods(selected_keys)

    def delete_unmanaged_mods(self, device_folders):
        if not device_folders: return
        mod_names = "\n - ".join(device_folders)
        
        title = "Confirm Delete Unmanaged"
        question = f"Are you sure you want to PERMANENTLY delete the following {len(device_folders)} unmanaged mod(s) from the device?\n\nThis cannot be undone.\n\n - {mod_names}"
        
        dialog = ttk.dialogs.Messagebox.yesno(question, title, parent=self)
        if not dialog == "Yes":
            return
            
        self.controller.run_in_thread(self._threaded_delete_unmanaged, device_folders)

    def _threaded_delete_unmanaged(self, device_folders):
        log_func = self.controller.frames["Mod Manager"].log
        target_dir = self.controller.full_mods_path_var.get()
        for folder in device_folders:
            log_func(f"\n--- Deleting unmanaged mod '{folder}' ---")
            try:
                folder_to_delete = f"{target_dir}{folder}"
                self.controller.adb.delete_device_folder(folder_to_delete, log_func)
                log_func(f"SUCCESS: Deleted '{folder}'.")
            except Exception as e:
                log_func(f"--- DELETE FAILED for '{folder}' ---: {e}")
        self.controller.after(0, self.controller.refresh_data_and_ui)