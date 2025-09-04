# --- Filename: mod_manager_ui.py ---
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledText
from tkinter import filedialog, font, messagebox
import os
import json
from src.shared_ui_components import ModListView, ModDisplayItem

class ModManagerFrame(ttk.Frame):
    name = "Mod Manager"
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.data_manager = controller.data_manager
        self.bold_font = font.Font(family="Helvetica", size=10, weight="bold")
        self.selected_library = tk.StringVar()
        self.selected_category = tk.StringVar()
        self.library_category_memory = {}
        
        self.source_folder_path = tk.StringVar()
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search_change)

        # --- Main Paned Window for resizable sections ---
        main_paned_window = ttk.PanedWindow(self, orient=VERTICAL)
        main_paned_window.pack(expand=True, fill='both', padx=15, pady=15)

        # Top Pane (will contain controls and the mod lists)
        main_pane = ttk.Frame(main_paned_window)
        main_paned_window.add(main_pane, weight=3)

        # Bottom Pane (will contain logs and console)
        bottom_frame_container = ttk.Frame(main_paned_window)
        main_paned_window.add(bottom_frame_container, weight=1)

        # --- New Two-Column Layout ---
        main_pane.grid_columnconfigure(0, weight=0)  # Controls column
        main_pane.grid_columnconfigure(1, weight=1)  # Mod list/main content column
        main_pane.grid_rowconfigure(0, weight=1)

        # --- Left-Hand Controls Panel ---
        controls_panel = ttk.Labelframe(main_pane, text="Controls", padding=10)
        controls_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        
        # Search Bar with Integrated Refresh
        search_frame = ttk.Frame(controls_panel)
        search_frame.pack(fill='x', expand=True, pady=(0, 5))
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side='left', fill='x', expand=True)
        refresh_button = ttk.Button(search_frame, text="↻", command=self.controller.refresh_local_data_and_ui, bootstyle="info-outline", width=2)
        refresh_button.pack(side='left', padx=(5,0))
        
        self.placeholder_color = 'grey'
        self.default_fg_color = self.search_entry.cget("foreground")
        self.search_entry.bind("<FocusIn>", self._on_search_focus_in)
        self.search_entry.bind("<FocusOut>", self._on_search_focus_out)
        self._on_search_focus_out(None)

        ttk.Separator(controls_panel, orient=HORIZONTAL).pack(fill='x', pady=10)

        # --- NEW: Quick Select Button Grid ---
        quick_select_frame = ttk.Frame(controls_panel)
        quick_select_frame.pack(fill='x', expand=True, pady=(0, 10))
        
        ttk.Label(quick_select_frame, text="Quick Select:").pack(fill='x', pady=(0, 5))

        button_grid = ttk.Frame(quick_select_frame)
        button_grid.pack()

        filter_options = {
            "All": "All",
            "Installed": "Installed",
            "Not Inst.": "Not Installed",
            "None": "None"
        }
        
        row, col = 0, 0
        for text, command_key in filter_options.items():
            btn = ttk.Button(button_grid, text=text, command=lambda k=command_key: self.apply_selection_filter(k), bootstyle="secondary-outline")
            btn.grid(row=row, column=col, padx=2, pady=2, sticky='ew')
            col += 1
            if col > 1:
                col = 0
                row += 1
        
        button_grid.grid_columnconfigure(0, weight=1)
        button_grid.grid_columnconfigure(1, weight=1)
        # --- END NEW SECTION ---

        ttk.Separator(controls_panel, orient=HORIZONTAL).pack(fill='x', pady=10)

        # Action Buttons
        self.install_button = ttk.Button(controls_panel, text="Install/Update Selected", command=self.on_push_mods, bootstyle="success")
        self.install_button.pack(fill='x', expand=True, pady=(0, 5))
        self.uninstall_button = ttk.Button(controls_panel, text="Uninstall Selected", command=self.on_uninstall_selected, bootstyle="danger")
        self.uninstall_button.pack(fill='x', expand=True)

        # --- Right-Hand Main Content Area ---
        right_pane = ttk.Frame(main_pane)
        right_pane.grid(row=0, column=1, sticky="nsew")

        # Frame for when libraries ARE configured
        self.local_frame_container = ttk.Labelframe(right_pane, text="On PC (Managed Mods)", padding=15)
        local_header = ttk.Frame(self.local_frame_container)
        local_header.pack(fill='x', pady=(0, 10))
        self.local_header_nav_area = ttk.Frame(local_header)
        self.local_header_nav_area.pack(side='left', fill='x', expand=True)
        self.local_mods_frame = ModListView(self.local_frame_container, self.controller, view_type='local')
        self.local_mods_frame.pack(expand=True, fill='both')

        # Frame for when NO libraries are configured
        self.no_library_frame = ttk.Labelframe(right_pane, text="Setup Required", padding=15)
        no_lib_content_frame = ttk.Frame(self.no_library_frame)
        no_lib_content_frame.pack(expand=True)
        ttk.Label(no_lib_content_frame, text="No local mod libraries have been configured.", font=("Helvetica", 12)).pack(pady=10)
        ttk.Label(no_lib_content_frame, text="Please add a folder that contains your mods to get started.", justify='center').pack(pady=(0, 20))
        ttk.Button(no_lib_content_frame, text="Go to Settings to Add a Library", command=lambda: self.controller.show_frame("Settings"), bootstyle="success").pack(pady=10)

        # --- Bottom section (logs, console) ---
        log_container = ttk.Frame(bottom_frame_container)
        log_container.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        log_header_frame = ttk.Frame(log_container)
        log_header_frame.pack(fill='x', pady=(0, 5))
        ttk.Label(log_header_frame, text="Log & Status Output", font=self.bold_font).pack(side='left')
        
        status_display_frame = ttk.Frame(log_header_frame)
        status_display_frame.pack(side='right')
        ttk.Label(status_display_frame, text="Emulator |", font=self.bold_font).pack(side='left')
        self.status_widget = ttk.Button(status_display_frame, text="Checking...", bootstyle="warning", state="disabled")
        self.status_widget.pack(side='left', padx=(5, 5))

        self.log_output_text = ScrolledText(log_container, wrap=tk.WORD, autohide=True, height=6)
        self.log_output_text.pack(expand=True, fill='both')
        self.log_output_text.text.config(state='disabled')

        console_container = ttk.Frame(bottom_frame_container)
        console_container.pack(side='left', fill='both', expand=True, padx=(5, 0))
        
        console_header = ttk.Frame(console_container)
        console_header.pack(fill='x', pady=(0,5))
        ttk.Label(console_header, text="ADB Console", font=self.bold_font).pack(side='left', anchor='w')

        game_controls_frame = ttk.Frame(console_header)
        game_controls_frame.pack(side='right')

        self.launch_game_button = ttk.Button(game_controls_frame, text="Launch Game", command=controller.launch_game, bootstyle="success-outline")
        self.launch_game_button.pack(side='left', padx=(0, 5))

        self.force_stop_button = ttk.Button(game_controls_frame, text="Force Stop", command=controller.force_stop_game, bootstyle="warning-outline")
        self.force_stop_button.pack(side='left', padx=(0, 5))

        self.console_output_text = ScrolledText(console_container, wrap=tk.WORD, autohide=True, height=6)
        self.console_output_text.pack(expand=True, fill='both')
        self.console_output_text.text.config(state='disabled')
        
        console_input_frame = ttk.Frame(console_container)
        console_input_frame.pack(fill='x', pady=(5,0))
        self.command_entry = ttk.Entry(console_input_frame, font=("Consolas", 10))
        self.command_entry.pack(side="left", fill='x', expand=True, padx=(0, 5))
        self.command_entry.bind("<Return>", self.send_command_event)
        send_button = ttk.Button(console_input_frame, text="Send", command=self.send_command_event, bootstyle="success")
        send_button.pack(side="right")
        
    def _on_search_focus_in(self, event):
        if self.search_var.get() == "Search...":
            self.search_var.set("")
            self.search_entry.config(foreground=self.default_fg_color)

    def _on_search_focus_out(self, event):
        if not self.search_var.get():
            self.search_var.set("Search...")
            self.search_entry.config(foreground=self.placeholder_color)

    def _on_search_change(self, *args):
        if self.search_var.get() != "Search...":
            self.update_mod_list()

    def update_control_state(self):
        can_mod = self.controller.is_adb_connected and self.controller.is_mods_folder_known_to_exist
        is_game_running = self.controller.is_game_running
        is_adb_connected = self.controller.is_adb_connected

        modding_state = tk.NORMAL if can_mod else tk.DISABLED
        self.install_button.config(state=modding_state)
        self.uninstall_button.config(state=modding_state)
        
        launch_state = tk.NORMAL if is_adb_connected and not is_game_running else tk.DISABLED
        stop_state = tk.NORMAL if is_game_running else tk.DISABLED
        
        self.launch_game_button.config(state=launch_state)
        self.force_stop_button.config(state=stop_state)
        
        for item in self.local_mods_frame.scrollable_frame.winfo_children():
            if isinstance(item, ModDisplayItem):
                if item.install_button:
                    item.install_button.config(state=modding_state)
                if item.uninstall_button:
                    item.uninstall_button.config(state=modding_state)

    def build_nav(self, data_manager):
        if not self.controller.get_local_library_paths():
            self.local_frame_container.pack_forget()
            self.no_library_frame.pack(expand=True, fill='both')
            self.local_mods_frame.clear_list()
            return
        
        self.no_library_frame.pack_forget()
        self.local_frame_container.pack(expand=True, fill='both')

        all_libraries = sorted(list(set(data_manager.local_data.keys()) | set(data_manager.managed_device_data.keys())))
        
        if not all_libraries:
            for widget in self.local_header_nav_area.winfo_children():
                widget.destroy()
            self.local_mods_frame.clear_list("No mods found in the configured library folder(s).")
            return

        if not self.selected_library.get() or self.selected_library.get() not in all_libraries:
            self.on_library_select(all_libraries[0])
            return
        self._redraw_nav()

    def on_library_select(self, lib_name):
        self.deselect_all()
        self.selected_library.set(lib_name)
        all_cats = sorted(list(set(self.data_manager.local_data.get(lib_name, {}).keys()) | set(self.data_manager.managed_device_data.get(lib_name, {}).keys())))
        new_cat = self.library_category_memory.get(lib_name)
        if not new_cat or new_cat not in all_cats:
            new_cat = "Uncategorized"
            is_uncat_empty = not (self.data_manager.local_data.get(lib_name, {}).get("Uncategorized", []) or self.data_manager.managed_device_data.get(lib_name, {}).get("Uncategorized", []))
            if "Uncategorized" not in all_cats or is_uncat_empty:
                for cat in all_cats:
                    if cat == "Uncategorized": continue
                    if not (self.data_manager.local_data.get(lib_name, {}).get(cat, []) or self.data_manager.managed_device_data.get(lib_name, {}).get(cat, [])):
                        continue
                    new_cat = cat
                    break
        self.selected_category.set(new_cat)
        self._redraw_nav()

    def on_category_select(self, cat_name):
        self.deselect_all()
        self.selected_category.set(cat_name)
        self.library_category_memory[self.selected_library.get()] = cat_name
        self._redraw_nav()

    def _redraw_nav(self):
        for widget in self.local_header_nav_area.winfo_children():
            widget.destroy()
        
        library_definitions = self.controller.get_local_library_paths()
        name_to_path_map = {os.path.basename(lib['path']): lib['path'] for lib in library_definitions}
        type_map = {os.path.basename(lib['path']): lib.get('type', '???') for lib in library_definitions}
        all_libraries = sorted(list(set(self.data_manager.local_data.keys()) | set(self.data_manager.managed_device_data.keys())))
        
        lib_frame = ttk.Frame(self.local_header_nav_area)
        lib_frame.pack(fill='x')

        current_lib_name = self.selected_library.get()
        current_lib_path = name_to_path_map.get(current_lib_name)
        open_lib_folder_btn = ttk.Button(lib_frame, text="📂", 
                                         command=lambda p=current_lib_path: self.controller.open_folder_in_explorer(p),
                                         bootstyle="info-outline", width=2)
        open_lib_folder_btn.pack(side='left', padx=(0, 10))
        if not current_lib_path:
            open_lib_folder_btn.config(state=tk.DISABLED)

        for lib_name in all_libraries:
            lib_type = type_map.get(lib_name, '???')
            btn_text = f"[{lib_type}] {lib_name}"
            style = "primary" if lib_name == self.selected_library.get() else "secondary"
            btn = ttk.Button(lib_frame, text=btn_text, bootstyle=style,
                            command=lambda l=lib_name: self.on_library_select(l))
            btn.pack(side='left', padx=(0,2))

        cat_container = ttk.Frame(self.local_header_nav_area)
        cat_container.pack(fill='x', expand=True, pady=(4,0))
        
        # --- Category Open Folder Button ---
        current_cat_name = self.selected_category.get()
        open_cat_folder_btn = ttk.Button(cat_container, text="📂",
                                     bootstyle="info-outline", width=2)
        open_cat_folder_btn.pack(side='left', padx=(0, 10), anchor='n')
        
        current_cat_path = None
        # Determine path for category folder, ensuring it's not "Uncategorized"
        if current_lib_path and current_cat_name and current_cat_name != "Uncategorized":
            current_cat_path = os.path.join(current_lib_path, f"c_{current_cat_name}")
        
        if current_cat_path and os.path.isdir(current_cat_path):
            open_cat_folder_btn.config(command=lambda p=current_cat_path: self.controller.open_folder_in_explorer(p))
        else:
            open_cat_folder_btn.config(state=tk.DISABLED) # Disable for "Uncategorized" or if path doesn't exist

        # --- Scrollable Area for Category Buttons ---
        scroll_area = ttk.Frame(cat_container)
        scroll_area.pack(side='left', fill='x', expand=True)

        cat_canvas = tk.Canvas(scroll_area, highlightthickness=0, bg=self.winfo_toplevel().style.lookup('TFrame', 'background'))
        cat_scrollbar = ttk.Scrollbar(scroll_area, orient="horizontal", command=cat_canvas.xview, bootstyle="round")
        cat_canvas.configure(xscrollcommand=cat_scrollbar.set)
        
        scrollable_cat_frame = ttk.Frame(cat_canvas)
        cat_canvas.create_window((0, 0), window=scrollable_cat_frame, anchor="nw")
        
        def on_cat_frame_configure(event):
            cat_canvas.configure(scrollregion=cat_canvas.bbox("all"), height=scrollable_cat_frame.winfo_height())
        
        scrollable_cat_frame.bind("<Configure>", on_cat_frame_configure)
        cat_canvas.pack(side="top", fill="x", expand=True)
        cat_scrollbar.pack(side="top", fill="x", expand=True)

        current_lib = self.selected_library.get()
        all_categories = sorted(list(set(self.data_manager.local_data.get(current_lib, {}).keys()) | set(self.data_manager.managed_device_data.get(current_lib, {}).keys())))
        if "Uncategorized" in all_categories:
            all_categories.remove("Uncategorized")
            all_categories.insert(0, "Uncategorized")
        
        has_content = False
        for cat_name in all_categories:
            is_empty = not (self.data_manager.local_data.get(current_lib, {}).get(cat_name, []) or self.data_manager.managed_device_data.get(current_lib, {}).get(cat_name, []))
            if is_empty: continue
            has_content = True
            style = "info" if cat_name == self.selected_category.get() else "secondary-outline"
            btn = ttk.Button(scrollable_cat_frame, text=cat_name, bootstyle=style, command=lambda c=cat_name: self.on_category_select(c))
            btn.pack(side='left', padx=(0,2))
        
        if not has_content:
            cat_scrollbar.pack_forget()
        
        self.update_mod_list()

    def update_mod_list(self):
        lib = self.selected_library.get()
        cat = self.selected_category.get()
        
        all_mods = self.data_manager.local_data.get(lib, {}).get(cat, [])
        search_term = self.search_var.get().lower()

        if search_term and self.search_var.get() != "Search...":
            mods_to_display = [mod for mod in all_mods if search_term in mod['name'].lower()]
            msg = f"No mods found matching '{self.search_var.get()}'."
        else:
            mods_to_display = all_mods
            msg = "No mods in this category."

        self.local_mods_frame.display_list(mods_to_display, msg)
        self.update_control_state()

    def apply_selection_filter(self, selection_type):
        if selection_type == "None":
            self.deselect_all()
            return

        mods_on_display = [child.mod_data for child in self.local_mods_frame.scrollable_frame.winfo_children() if hasattr(child, 'mod_data')]
        
        keys_to_select = []
        if selection_type == "All":
            keys_to_select = [mod['full_path'] for mod in mods_on_display]
        elif selection_type == "Installed":
            keys_to_select = [mod['full_path'] for mod in mods_on_display if mod['status'] == 'Installed']
        elif selection_type == "Not Installed":
            keys_to_select = [mod['full_path'] for mod in mods_on_display if mod['status'] != 'Installed']
            
        self.local_mods_frame.select_items(keys_to_select)

    def deselect_all(self):
        self.local_mods_frame.clear_selection()
        
    def on_uninstall_selected(self):
        selected_keys = self.local_mods_frame.get_selected_keys()
        if not selected_keys: return
        
        installed_mods_to_uninstall = [p for p in selected_keys if p in self.controller.mod_mappings]
        if not installed_mods_to_uninstall:
            messagebox.showinfo("Nothing to Uninstall", "None of the selected mods are currently installed on the device.")
            return
            
        mod_names = "\n - ".join([os.path.basename(p) for p in installed_mods_to_uninstall])
        if messagebox.askyesno("Confirm Uninstall", f"Are you sure you want to uninstall {len(installed_mods_to_uninstall)} mod(s)?\n\n - {mod_names}"):
            self.controller.run_in_thread(self.controller.uninstall_mods, installed_mods_to_uninstall)

    def on_install_single(self, path):
        mod_name = os.path.basename(path)
        if messagebox.askyesno("Confirm Install", f"Are you sure you want to install this mod?\n\n- {mod_name}"):
            lib = self.selected_library.get()
            cat = self.selected_category.get()
            self.controller.run_in_thread(self.controller.install_mods, [path], lib, cat)

    def on_uninstall_single(self, path):
        mod_name = os.path.basename(path)
        if messagebox.askyesno("Confirm Uninstall", f"Are you sure you want to uninstall this mod?\n\n- {mod_name}"):
            self.controller.run_in_thread(self.controller.uninstall_mods, [path])

    def on_push_mods(self):
        selected_keys = self.local_mods_frame.get_selected_keys()
        if not selected_keys:
            self.log("ERROR: No mods selected.")
            return
        
        lib = self.selected_library.get()
        cat = self.selected_category.get()
        mod_names = "\n - ".join([os.path.basename(p) for p in selected_keys])
        
        if messagebox.askyesno("Confirm Install/Update", f"Are you sure you want to process {len(selected_keys)} mod(s)?\n\n - {mod_names}"):
            self.controller.run_in_thread(self.controller.install_mods, selected_keys, lib, cat)
        
    def log(self, message):
        self.log_output_text.text.config(state='normal')
        self.log_output_text.insert(tk.END, str(message).strip() + "\n")
        self.log_output_text.see(tk.END)
        self.log_output_text.text.config(state='disabled')
        
    def console_log(self, message):
        self.console_output_text.text.config(state='normal')
        self.console_output_text.insert(tk.END, str(message).strip() + "\n")
        self.console_output_text.see(tk.END)
        self.console_output_text.text.config(state='disabled')
        
    def send_command_event(self, event=None):
        user_input = self.command_entry.get().strip()
        if not user_input: return
        self.console_log(f"$ {user_input}")
        self.command_entry.delete(0, tk.END)
        command_to_run = user_input
        if command_to_run.lower().startswith("adb "):
            command_to_run = command_to_run[4:]
        self.controller.run_in_thread(self.controller.adb.send_adb_command, command_to_run, self.console_log)