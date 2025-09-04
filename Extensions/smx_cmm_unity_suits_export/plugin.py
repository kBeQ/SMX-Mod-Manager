# --- Filename: Extensions/smx_cmm_unity_suits_export/plugin.py ---
import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import os
import zipfile
import shutil
import tempfile


class CMMUnitySuitsExportFrame(ttk.Frame):
    """The UI frame that will be displayed in the new tab."""
    name = "SMX CMM Unity Suits Export"

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.extension_name = "SMX CMM Unity Suits Export"
        self.found_mods = {}

        # --- Settings Variable & Loading ---
        self.unity_project_path_var = tk.StringVar()
        saved_path = self.controller.get_extension_setting(
            extension_name=self.extension_name,
            setting_key='unity_project_path',
            default=""
        )
        self.unity_project_path_var.set(saved_path)

        # --- UI ---
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(expand=True, fill=BOTH, padx=10, pady=10)

        ttk.Label(main_frame, text=self.extension_name, font=("Helvetica", 16, "bold")).pack(pady=(0,10), anchor='w')
        ttk.Label(main_frame, text="Scan a Unity project folder for zipped suit mods and export them to your library.", wraplength=800).pack(pady=(0, 20), anchor='w')

        # --- 1. Settings UI ---
        settings_frame = ttk.Labelframe(main_frame, text="Settings", padding=15)
        settings_frame.pack(fill=X, pady=10)
        
        ttk.Label(settings_frame, text="Unity 'SuitDatabase' Path:").grid(row=0, column=0, sticky='w', pady=(0, 5))
        path_entry = ttk.Entry(settings_frame, textvariable=self.unity_project_path_var, state="readonly")
        path_entry.grid(row=1, column=0, sticky='ew')
        browse_button = ttk.Button(settings_frame, text="Browse...", command=self.browse_for_unity_project, bootstyle="outline")
        browse_button.grid(row=1, column=1, sticky='w', padx=(10, 0))
        settings_frame.grid_columnconfigure(0, weight=1)

        # --- 2. Actions and Results UI ---
        action_frame = ttk.Labelframe(main_frame, text="Export Process", padding=15)
        action_frame.pack(fill=BOTH, expand=True, pady=20)
        action_frame.grid_columnconfigure(0, weight=1)
        action_frame.grid_rowconfigure(2, weight=1) # Allow listbox to expand vertically

        # Scan Button
        scan_button_frame = ttk.Frame(action_frame)
        scan_button_frame.grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0, 10))
        self.scan_button = ttk.Button(scan_button_frame, text="Scan for Zipped Mods", command=self.scan_for_mods)
        self.scan_button.pack(side=LEFT)
        self.scan_status_label = ttk.Label(scan_button_frame, text="")
        self.scan_status_label.pack(side=LEFT, padx=10)

        # Results Listbox
        ttk.Label(action_frame, text="Found Mods: (Category / Mod Name)").grid(row=1, column=0, columnspan=2, sticky='w')
        self.results_listbox = tk.Listbox(action_frame, selectmode='extended', height=8)
        self.results_listbox.grid(row=2, column=0, columnspan=2, sticky='nsew', pady=(5, 10))
        
        # Destination Library Dropdown
        dest_frame = ttk.Frame(action_frame)
        dest_frame.grid(row=3, column=0, columnspan=2, sticky='ew', pady=(5,0))
        ttk.Label(dest_frame, text="Destination Library:").pack(side=LEFT)
        self.destination_library_var = tk.StringVar()
        self.destination_combo = ttk.Combobox(dest_frame, textvariable=self.destination_library_var, state='readonly')
        self.destination_combo.pack(side=LEFT, expand=True, fill=X, padx=(10,0))
        self.populate_destination_libraries()

        # Export Button
        self.export_button = ttk.Button(action_frame, text="Export Selected to Library", command=self.export_selected_mods, state='disabled')
        self.export_button.grid(row=4, column=0, columnspan=2, pady=(15, 0))

    def populate_destination_libraries(self):
        """Finds all configured local libraries of type 'Suits' and adds them to the dropdown."""
        suit_libs = []
        library_definitions = self.controller.get_local_library_paths()
        for lib in library_definitions:
            if lib.get('type') == 'Suits':
                suit_libs.append(os.path.basename(lib['path']))
        
        self.destination_combo['values'] = suit_libs
        if suit_libs:
            self.destination_library_var.set(suit_libs[0])
        else:
            self.destination_library_var.set("No 'Suits' library found in settings!")

    def browse_for_unity_project(self):
        """Opens a dialog to select the Unity project folder and saves the setting."""
        folder_path = filedialog.askdirectory(title="Select your Unity 'SuitDatabase' Folder")
        if folder_path:
            self.unity_project_path_var.set(folder_path)
            self.controller.save_extension_setting(
                extension_name=self.extension_name,
                setting_key='unity_project_path',
                value=folder_path
            )

    def scan_for_mods(self):
        """Scans the configured path for categories and zipped mods."""
        self.results_listbox.delete(0, tk.END)
        self.found_mods.clear()
        self.export_button.config(state='disabled')
        
        base_path = self.unity_project_path_var.get()
        if not base_path or not os.path.isdir(base_path):
            self.scan_status_label.config(text="Error: Invalid or unset path.", bootstyle="danger")
            return

        self.scan_status_label.config(text="Scanning...", bootstyle="info")
        self.update_idletasks()
        
        count = 0
        for category_name in os.listdir(base_path):
            category_path = os.path.join(base_path, category_name)
            if os.path.isdir(category_path):
                for mod_name in os.listdir(category_path):
                    mod_path = os.path.join(category_path, mod_name)
                    if os.path.isdir(mod_path):
                        zip_file_name = f"{mod_name}.zip"
                        zip_file_path = os.path.join(mod_path, zip_file_name)
                        
                        display_text = f"{category_name} / {mod_name}"
                        self.found_mods[display_text] = {
                            'category': category_name,
                            'mod_name': mod_name,
                            'zip_path': zip_file_path if os.path.exists(zip_file_path) else None
                        }
                        
                        self.results_listbox.insert(tk.END, display_text)
                        if os.path.exists(zip_file_path):
                            self.results_listbox.itemconfig(tk.END, {'fg': 'lightgreen'})
                            count += 1
                        else:
                            self.results_listbox.itemconfig(tk.END, {'fg': 'orange'})

        self.scan_status_label.config(text=f"Scan complete. Found {count} valid zip(s).", bootstyle="success")
        self.export_button.config(state='normal' if count > 0 else 'disabled')

    def export_selected_mods(self):
        """Extracts the selected zipped mods into the chosen destination library, handling nested folders."""
        selected_indices = self.results_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("No Selection", "Please select one or more mods from the list to export.")
            return

        dest_lib_name = self.destination_library_var.get()
        dest_lib_path = None
        for lib in self.controller.get_local_library_paths():
            if os.path.basename(lib['path']) == dest_lib_name and lib.get('type') == 'Suits':
                dest_lib_path = lib['path']
                break
        
        if not dest_lib_path:
            messagebox.showerror("Error", "Selected destination library is not a valid 'Suits' library. Please check your settings.")
            return

        exported_count = 0
        skipped_count = 0
        
        self.controller.show_loading_overlay("Exporting mods...")

        for i in selected_indices:
            key = self.results_listbox.get(i)
            mod_info = self.found_mods.get(key)
            
            if not mod_info or not mod_info['zip_path']:
                skipped_count += 1
                continue

            temp_dir = None
            try:
                # 1. Define final destination paths
                category_folder_path = os.path.join(dest_lib_path, f"c_{mod_info['category']}")
                os.makedirs(category_folder_path, exist_ok=True)
                final_mod_path = os.path.join(category_folder_path, mod_info['mod_name'])

                # 2. Create a secure temporary directory for extraction
                temp_dir = tempfile.mkdtemp()
                
                # 3. Extract the entire zip to the temporary directory
                with zipfile.ZipFile(mod_info['zip_path'], 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # 4. Inspect contents to find the correct source for moving
                extracted_items = os.listdir(temp_dir)
                source_for_move = temp_dir
                
                if len(extracted_items) == 1 and os.path.isdir(os.path.join(temp_dir, extracted_items[0])):
                    source_for_move = os.path.join(temp_dir, extracted_items[0])
                    # Move all contents from the subfolder up one level
                    for item_name in os.listdir(source_for_move):
                        shutil.move(os.path.join(source_for_move, item_name), temp_dir)
                    # Remove the now-empty subfolder
                    os.rmdir(source_for_move)

                # 5. Clean up final destination and move the prepared files
                if os.path.exists(final_mod_path):
                    shutil.rmtree(final_mod_path)
                
                shutil.move(temp_dir, final_mod_path)
                temp_dir = None # Set to None to prevent double deletion in finally block
                
                exported_count += 1

            except Exception as e:
                print(f"ERROR exporting {mod_info['mod_name']}: {e}")
                messagebox.showerror("Export Error", f"An error occurred while exporting {mod_info['mod_name']}:\n\n{e}")
                break
            finally:
                # 6. Always clean up the temporary directory if it still exists
                if temp_dir and os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)

        self.controller.hide_loading_overlay()
        messagebox.showinfo("Export Complete", f"Successfully exported {exported_count} mod(s).\nSkipped {skipped_count} mod(s) (no zip found).")
        
        self.controller.refresh_local_data_and_ui()


class SMXExtension:
    """This is the main entry point for the extension."""
    def __init__(self):
        self.name = "SMX CMM Unity Suits Export"
        self.description = "Scans a Unity project folder for zipped suit mods and exports them to your library."
        self.version = "1.2.0" # Version bumped for new unzipping logic

    def initialize(self, app):
        """Called by the main application to let the extension integrate itself."""
        print(f"INFO: Initializing extension '{self.name}' v{self.version}")
        self.app = app
        self.app.add_extension_tab(self.name, CMMUnitySuitsExportFrame)

    def on_close(self):
        """Called when the main application is closing."""
        print(f"INFO: Closing extension '{self.name}'.")
        pass