# --- Filename: settings_ui.py ---
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, font, messagebox, Listbox
import os
from PIL import Image, ImageTk
import re

class AskLibraryTypeDialog(tk.Toplevel):
    def __init__(self, parent, available_types, title="Select Library Type"):
        super().__init__(parent)
        self.transient(parent)
        self.title(title)
        self.result = None
        self.parent = parent

        parent_x = parent.winfo_toplevel().winfo_x()
        parent_y = parent.winfo_toplevel().winfo_y()
        parent_width = parent.winfo_toplevel().winfo_width()
        parent_height = parent.winfo_toplevel().winfo_height()
        self_width = 300
        self_height = 150
        x = parent_x + (parent_width // 2) - (self_width // 2)
        y = parent_y + (parent_height // 2) - (self_height // 2)
        self.geometry(f"{self_width}x{self_height}+{x}+{y}")

        self.grab_set()
        
        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="What type of mods are in this library?").pack(pady=(0, 10))
        
        self.type_var = tk.StringVar()
        combobox = ttk.Combobox(
            main_frame, 
            textvariable=self.type_var, 
            values=available_types,
            state="readonly"
        )
        combobox.pack(pady=5, fill=tk.X, expand=True)
        combobox.set("Tracks") 

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=(15, 0), fill=tk.X, expand=True)

        ok_button = ttk.Button(btn_frame, text="OK", command=self.on_ok, bootstyle="success")
        ok_button.pack(side=tk.RIGHT, padx=(5,0))
        
        cancel_button = ttk.Button(btn_frame, text="Cancel", command=self.on_cancel, bootstyle="secondary")
        cancel_button.pack(side=tk.RIGHT)

        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.wait_window(self)

    def on_ok(self):
        self.result = self.type_var.get()
        self.destroy()

    def on_cancel(self):
        self.result = None
        self.destroy()


class SettingsFrame(ttk.Frame):
    name = "Settings"
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.bold_font = font.Font(family="Helvetica", size=12, weight="bold")
        self.header_photo = None
        
        self.canvas = tk.Canvas(self, highlightthickness=0)
        style = self.controller.style
        bg_color = style.lookup('TFrame', 'background')
        self.canvas.config(bg=bg_color)
        
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview, bootstyle="round")
        self.scrollable_frame = ttk.Frame(self.canvas, padding=(15, 15, 15, 0))

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.frame_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.canvas.bind('<Configure>', self.on_canvas_configure)

    def on_canvas_configure(self, event):
        self.canvas.itemconfig(self.frame_id, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _bind_recursive(self, widget, event, callback):
        widget.bind(event, callback)
        for child in widget.winfo_children():
            if isinstance(child, (tk.Listbox, tk.Text, ttk.ScrolledText)):
                continue 
            self._bind_recursive(child, event, callback)
        
    def build_ui(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
        header_path = self.controller.header_image_path
        if os.path.exists(header_path):
            try:
                img = Image.open(header_path)
                base_width = 400
                w_percent = (base_width / float(img.size[0]))
                h_size = int((float(img.size[1]) * float(w_percent)))
                img = img.resize((base_width, h_size), Image.Resampling.LANCZOS)
                
                self.header_photo = ImageTk.PhotoImage(img)
                header_label = ttk.Label(self.scrollable_frame, image=self.header_photo)
                header_label.pack(pady=(0, 20))
            except Exception as e:
                print(f"Failed to load settings header image: {e}")

        self.build_library_manager()

        game_config_order = ["Game Package Name", "Mods Subfolder Path", "Full Mods Path (Auto-generated)", "Game Activity Name"]
        sorted_categories = sorted(self.controller.setting_vars.keys(), key=lambda x: (x != "Game Configuration", x))

        for category in sorted_categories:
            settings = self.controller.setting_vars[category]
            if category == "LocalLibrary": continue
            
            cat_frame = ttk.Labelframe(self.scrollable_frame, text=category, padding=15)
            cat_frame.pack(padx=0, pady=10, fill='x')
            row = 0
            
            setting_items = []
            if category == "Game Configuration":
                settings_dict = {name: details for name, details in settings.items()}
                for name in game_config_order:
                    if name in settings_dict:
                        setting_items.append((name, settings_dict[name]))
            else:
                setting_items = settings.items()

            for name, details in setting_items:
                if name in ["Game Package Name", "Mods Subfolder Path"]:
                    details['var'].trace_add("write", self.controller.update_full_mods_path)

                ttk.Label(cat_frame, text=f"{name}:").grid(row=row, column=0, sticky='w', pady=5)
                entry = ttk.Entry(cat_frame, textvariable=details['var'])
                
                if details.get('readonly'):
                    entry.config(state='readonly')
                entry.grid(row=row + 1, column=0, columnspan=2, sticky='ew')
                
                if details.get('type') == 'file':
                    browse_button = ttk.Button(cat_frame, text="Browse...", bootstyle="outline", command=lambda var=details['var']: self.browse_file(var))
                    browse_button.grid(row=row + 1, column=2, padx=5)
                elif details.get('type') == 'folder':
                    browse_button = ttk.Button(cat_frame, text="Browse...", bootstyle="outline", command=lambda var=details['var']: self.browse_folder(var))
                    browse_button.grid(row=row + 1, column=2, padx=5)

                row += 2
            cat_frame.grid_columnconfigure(0, weight=1)

        theme_frame = ttk.Labelframe(self.scrollable_frame, text="Appearance", padding=15)
        theme_frame.pack(padx=0, pady=(10, 0), fill='x')
        ttk.Label(theme_frame, text="Theme:").pack(side='left', padx=(0,10))
        theme_selector = ttk.Combobox(master=theme_frame, values=self.controller.style.theme_names())
        theme_selector.pack(side='left', fill='x', expand=True)
        theme_selector.set(self.controller.style.theme_use())

        def change_theme(e):
            selected_theme = theme_selector.get()
            self.controller.style.theme_use(selected_theme)
            self.controller.saved_config['theme'] = selected_theme
            self.controller.save_config()
        theme_selector.bind("<<ComboboxSelected>>", change_theme)

        self._bind_recursive(self.scrollable_frame, "<MouseWheel>", self._on_mousewheel)


    def build_library_manager(self):
        lib_frame = ttk.Labelframe(self.scrollable_frame, text="Local Mod Library", padding=15)
        lib_frame.pack(padx=0, pady=10, fill='x')
        ttk.Label(lib_frame, text="Configure folders on your PC that contain your mod source files.").pack(anchor='w')
        list_frame = ttk.Frame(lib_frame)
        list_frame.pack(fill='x', expand=True, pady=5)

        self.library_listbox = Listbox(list_frame, height=5, relief=tk.FLAT)
        theme_colors = self.controller.style.colors
        self.library_listbox.config(bg=theme_colors.get('bg'), fg=theme_colors.get('fg'), selectbackground=theme_colors.get('primary'))
        self.library_listbox.pack(side='left', fill='x', expand=True)

        for lib_info in self.controller.get_local_library_paths():
            lib_type = lib_info.get('type', 'N/A')
            lib_path = lib_info.get('path', 'Invalid Path')
            display_text = f"[{lib_type}] {lib_path}"
            self.library_listbox.insert(tk.END, display_text)
            
        btn_frame = ttk.Frame(lib_frame)
        btn_frame.pack(fill='x', pady=(5,0))
        ttk.Button(btn_frame, text="Add Folder...", command=self.add_library_folder, bootstyle="outline").pack(side='left')
        ttk.Button(btn_frame, text="Change Type...", command=self.change_library_type, bootstyle="outline").pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Remove Selected", command=self.remove_library_folder, bootstyle="outline-danger").pack(side='left')
        
        # --- NEW: Add the Sync Mappings button to the right side ---
        ttk.Button(btn_frame, text="Sync Mappings", command=self.controller.sync_mod_mappings, bootstyle="outline-info").pack(side='right')

    def add_library_folder(self):
        folder = filedialog.askdirectory(title="Select a folder containing mods")
        if not folder: return

        current_libs = self.controller.get_local_library_paths()
        if any(lib.get('path') == folder for lib in current_libs):
            messagebox.showinfo("Duplicate", "That folder is already in the library.")
            return

        all_types = self.controller.get_available_library_types()
        dialog = AskLibraryTypeDialog(self, available_types=all_types)
        lib_type = dialog.result

        if lib_type:
            display_text = f"[{lib_type}] {folder}"
            self.library_listbox.insert(tk.END, display_text)
            self.save_library_changes()

    def remove_library_folder(self):
        selections = self.library_listbox.curselection()
        if not selections:
            messagebox.showwarning("No Selection", "Please select a folder to remove.")
            return
        for index in reversed(selections):
            self.library_listbox.delete(index)
        self.save_library_changes()

    def change_library_type(self):
        selections = self.library_listbox.curselection()
        if not selections:
            messagebox.showwarning("No Selection", "Please select a folder to change.")
            return
        if len(selections) > 1:
            messagebox.showwarning("Multiple Selections", "Please select only one folder to change its type.")
            return

        index = selections[0]
        current_text = self.library_listbox.get(index)
        
        match = re.match(r"\[(.*?)\] (.*)", current_text)
        if not match: return 

        old_type, path = match.groups()

        all_types = self.controller.get_available_library_types()
        dialog = AskLibraryTypeDialog(self, available_types=all_types)
        new_type = dialog.result

        if new_type and new_type != old_type:
            new_text = f"[{new_type}] {path}"
            self.library_listbox.delete(index)
            self.library_listbox.insert(index, new_text)
            self.library_listbox.selection_set(index) 
            self.save_library_changes()

    def save_library_changes(self):
        new_libs_data = []
        for item in self.library_listbox.get(0, tk.END):
            match = re.match(r"\[(.*?)\] (.*)", item)
            if match:
                lib_type, lib_path = match.groups()
                new_libs_data.append({'type': lib_type, 'path': lib_path})
        
        self.controller.update_local_library_paths(new_libs_data)
        self.controller.initial_local_scan()

    def browse_file(self, var_to_set):
        filename = filedialog.askopenfilename(title="Select File", filetypes=[("All files", "*.*")])
        if filename:
            var_to_set.set(filename)

    def browse_folder(self, var_to_set):
        foldername = filedialog.askdirectory(title="Select Folder")
        if foldername:
            var_to_set.set(foldername)