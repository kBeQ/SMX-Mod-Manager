# --- Filename: shared_ui_components.py ---
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import os
import sys
import subprocess
from PIL import Image, ImageTk, ImageDraw, ImageFont

class ModDisplayItem(ttk.Frame):
    def __init__(self, parent, controller, list_view, mod_data, view_mode='local'):
        super().__init__(parent, cursor="hand2", padding=2)
        self.content_frame = ttk.Frame(self, bootstyle="dark")
        self.content_frame.pack(fill=BOTH, expand=True)

        self.controller = controller
        self.list_view = list_view
        self.mod_data = mod_data
        self.view_mode = view_mode
        self.install_button = None
        self.uninstall_button = None
        self.update_button = None
        self.details_frame = None
        self.suit_images = {} # To prevent garbage collection
        self.images_loaded = False # NEW: Lazy loading flag

        self.build_ui_placeholders()

    def update_ui_for_status(self, new_status):
        """Updates the mod's status and redraws the buttons without rebuilding the whole widget."""
        self.mod_data['status'] = new_status
        
        # Clear out the old buttons
        if self.details_frame:
            for widget in self.details_frame.winfo_children():
                widget.destroy()
            # Rebuild the buttons and labels within the same frame
            self._build_details_frame_content()

    def _build_details_frame_content(self):
        """Builds or rebuilds the content of the details frame (buttons, file count, etc.)."""
        # Reset button references so they can be garbage collected if they exist
        self.install_button = None
        self.uninstall_button = None
        self.update_button = None

        if self.view_mode == 'local':
            ttk.Label(self.details_frame, text=f"Files: {self.mod_data.get('file_count', 'N/A')}", font=("Helvetica", 9), bootstyle="inverse-dark").pack(side='left', padx=(0,10))
            if self.mod_data['status'] == 'Installed':
                self.update_button = ttk.Button(self.details_frame, text="Update", bootstyle="success-outline", command=lambda p=self.mod_data['full_path']: self.controller.frames["Mod Manager"].on_install_single(p))
                self.update_button.pack(side='left', padx=(0, 5))
                self.uninstall_button = ttk.Button(self.details_frame, text="Uninstall", bootstyle="danger-outline", command=lambda p=self.mod_data['full_path']: self.controller.frames["Mod Manager"].on_uninstall_single(p))
                self.uninstall_button.pack(side='left', padx=(0, 10))
            else:
                self.install_button = ttk.Button(self.details_frame, text="Install", bootstyle="success-outline", command=lambda p=self.mod_data['full_path']: self.controller.frames["Mod Manager"].on_install_single(p))
                self.install_button.pack(side='left', padx=(0, 10))
            ttk.Button(self.details_frame, text="Open Folder", bootstyle="secondary-outline", command=lambda p=self.mod_data['full_path']: self.open_folder_in_explorer(p)).pack(side='left')
        
        elif self.view_mode == 'unmanaged':
            ttk.Label(self.details_frame, text=f"Device Folder: '{self.mod_data['device_folder']}'", font=("Helvetica", 8), bootstyle="inverse-dark", wraplength=150).pack(side='left')
            mod_type_text = self.mod_data.get('mod_type', 'Unknown')
            ttk.Label(self.details_frame, text=f"Type: {mod_type_text}", font=("Helvetica", 8, "italic"), bootstyle="inverse-dark").pack(side='right', padx=(0,5))

    def build_ui_placeholders(self):
        """Builds the widget structure with placeholder images."""
        self.content_frame.grid_columnconfigure(0, weight=2)
        self.content_frame.grid_columnconfigure(1, weight=1)

        images_frame = ttk.Frame(self.content_frame, bootstyle="dark")
        images_frame.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        images_frame.grid_columnconfigure(0, weight=2)
        images_frame.grid_columnconfigure(1, weight=1)
        
        # --- Preview ---
        preview_box = self._create_image_box_placeholder(images_frame, "Preview", (180, 101))
        preview_box.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self.preview_image_label = preview_box.image_widget # Get the actual image label

        # --- DYNAMIC UI: Icon or File Status ---
        mod_type = self.mod_data.get('library_type') or self.mod_data.get('mod_type')

        if mod_type == 'Tracks':
            map_status_frame = ttk.Frame(images_frame, bootstyle="dark", width=100, height=120)
            map_status_frame.grid(row=0, column=1, sticky="nsew")
            map_status_frame.pack_propagate(False)
            map_file_name = self.mod_data.get('map_file_name')
            status_style = "success" if map_file_name else "danger"
            ttk.Label(map_status_frame, text="Track.smxlevel", font=("Helvetica", 9), bootstyle=status_style, justify='center').pack(expand=True)

        elif mod_type == 'Sounds':
            sound_status_frame = ttk.Frame(images_frame, bootstyle="dark", width=100, height=120, padding=(5,5))
            sound_status_frame.grid(row=0, column=1, sticky="nsew")
            sound_status_frame.pack_propagate(False)
            sound_files = self.mod_data.get('sound_files', {})
            REQUIRED_SOUNDS = ["engine.wav", "high.wav", "idle.wav", "low.wav"]
            for sound_file in REQUIRED_SOUNDS:
                style = "success" if sound_files.get(sound_file) else "danger"
                ttk.Label(sound_status_frame, text=sound_file, bootstyle=style, font=("Consolas", 9)).pack(anchor='w')

        elif mod_type == 'Suits':
            # --- Right side of top row: Icon placeholder ---
            self.icon_frame = ttk.Frame(images_frame, bootstyle="dark")
            self.icon_frame.grid(row=0, column=1, sticky="nsew")
            placeholder_icon = self._get_image_for_display(None, (80, 80), "...")
            self.suit_icon_label = ttk.Label(self.icon_frame, image=placeholder_icon, bootstyle="dark")
            self.suit_icon_label.image = placeholder_icon # Keep ref
            self.suit_icon_label.pack()
            self.suit_icon_filename_label = ttk.Label(self.icon_frame, text="icon.jpg", font=("Helvetica", 8), bootstyle="secondary")
            self.suit_icon_filename_label.pack()
            
            # --- Middle Row: Gear Textures placeholders ---
            gear_frame = ttk.Frame(self.content_frame, bootstyle="dark", padding=(0, 5))
            gear_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
            gear_frame.grid_columnconfigure(0, weight=1)
            gear_frame.grid_columnconfigure(1, weight=1)

            # --- Helper to create a single gear row placeholder ---
            def create_placeholder_gear_row(parent, text, size):
                row_frame = ttk.Frame(parent, bootstyle="dark")
                img = self._get_image_for_display(None, size, "...")
                image_label = ttk.Label(row_frame, image=img, bootstyle="dark")
                image_label.image = img # Keep ref
                image_label.pack(side='left', padx=(0, 5))
                filename_label = ttk.Label(row_frame, text=text, font=("Helvetica", 8), bootstyle="secondary")
                filename_label.pack(side='left', anchor='w')
                return row_frame, image_label, filename_label

            # --- Create and place the two gear rows ---
            gear_suit_widget, self.gear_suit_label, self.gear_suit_filename_label = create_placeholder_gear_row(gear_frame, 'gear_suit.png', (40, 40))
            gear_suit_widget.grid(row=0, column=0, sticky='w')
            
            gear_normal_widget, self.gear_normal_label, self.gear_normal_filename_label = create_placeholder_gear_row(gear_frame, 'gear_suit_normal.png', (40, 40))
            gear_normal_widget.grid(row=0, column=1, sticky='w')

        else:
            icon_box = self._create_image_box_placeholder(images_frame, "Icon", (90, 90))
            icon_box.grid(row=0, column=1, sticky="nsew")
            self.icon_image_label = icon_box.image_widget

        # --- Common Details Below ---
        name_frame = ttk.Frame(self.content_frame, bootstyle="dark")
        name_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=(5, 5))
        name_label = ttk.Label(name_frame, text=self.mod_data['name'], font=("Helvetica", 11, "bold"), wraplength=280, justify='left', bootstyle="inverse-dark")
        name_label.pack(side='left')

        if self.view_mode == 'unmanaged':
            ttk.Label(name_frame, text="[Unmanaged]", font=("Helvetica", 8, "bold"), bootstyle="warning").pack(side='left', padx=5)
        
        # Create the frame that will hold the buttons and give it a reference
        self.details_frame = ttk.Frame(self.content_frame, bootstyle="dark")
        self.details_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 8))
        
        # Call the helper to populate it for the first time
        self._build_details_frame_content()


    def load_images(self):
        """Loads the actual images for the widget, replacing placeholders."""
        if self.images_loaded:
            return
        
        # --- Load Preview ---
        preview_path = self.mod_data.get('preview_path')
        preview_img_obj = self._get_image_for_display(preview_path, (180, 101), "No Preview")
        self.preview_image_label.config(image=preview_img_obj)
        self.preview_image_label.image = preview_img_obj

        mod_type = self.mod_data.get('library_type') or self.mod_data.get('mod_type')
        if mod_type == 'Suits':
            suit_files = self.mod_data.get('suit_files', {})
            
            # --- Icon ---
            icon_path = suit_files.get('icon')
            icon_img = self._get_image_for_display(icon_path, (80, 80), "N/A")
            self.suit_images['icon'] = icon_img
            self.suit_icon_label.config(image=icon_img)
            self.suit_icon_filename_label.config(bootstyle="success" if icon_path else "danger")

            # --- Gear Suit ---
            gear_path = suit_files.get('gear')
            gear_img = self._get_image_for_display(gear_path, (40, 40), "N/A")
            self.suit_images['gear'] = gear_img
            self.gear_suit_label.config(image=gear_img)
            self.gear_suit_filename_label.config(bootstyle="success" if gear_path else "danger")

            # --- Gear Normal ---
            normal_path = suit_files.get('normal')
            normal_img = self._get_image_for_display(normal_path, (40, 40), "N/A")
            self.suit_images['normal'] = normal_img
            self.gear_normal_label.config(image=normal_img)
            self.gear_normal_filename_label.config(bootstyle="success" if normal_path else "warning")

        elif mod_type not in ['Tracks', 'Sounds']:
            icon_path = self.mod_data.get('icon_path')
            icon_img_obj = self._get_image_for_display(icon_path, (90, 90), "No Icon")
            if hasattr(self, 'icon_image_label'):
                self.icon_image_label.config(image=icon_img_obj)
                self.icon_image_label.image = icon_img_obj
        
        self.images_loaded = True

    def _create_image_box_placeholder(self, parent, label_text, size):
        box_frame = ttk.Frame(parent, bootstyle="darker")
        box_frame.pack_propagate(False)
        box_frame.config(width=size[0] + 10, height=size[1] + 30)
        
        image_label = ttk.Label(box_frame, bootstyle="darker")
        box_frame.image_widget = image_label # Store a reliable reference

        img_obj = self._get_image_for_display(None, size, "...")
        image_label.config(image=img_obj)
        image_label.image = img_obj
        image_label.pack(padx=5, pady=5)
        ttk.Label(box_frame, text=f"({label_text})", font=("Helvetica", 7), wraplength=size[0], bootstyle="inverse-darker").pack(pady=(0,5), padx=2)
        return box_frame

    def _get_image_for_display(self, path, size, placeholder_text):
        if path and os.path.exists(path):
            try:
                img = Image.open(path)
                img.thumbnail(size, Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(img)
            except Exception as e:
                if self.mod_data.get('library_type') != 'Suits' and self.mod_data.get('mod_type') != 'Suits':
                    self.controller.frames["Mod Manager"].log(f"ERROR: Failed to load image {path}: {e}")
        return self.list_view.get_placeholder(size, placeholder_text)

    def open_folder_in_explorer(self, path):
        if not path: return
        try:
            if sys.platform == "win32": os.startfile(os.path.normpath(path))
            elif sys.platform == "darwin": subprocess.Popen(["open", path])
            else: subprocess.Popen(["xdg-open", path])
        except Exception as e:
            self.controller.frames["Mod Manager"].log(f"Error opening folder: {e}")

class ModListView(ttk.Frame):
    def __init__(self, parent, controller, view_type='local'):
        super().__init__(parent)
        self.controller = controller
        self.view_type = view_type
        self.selected_widgets = {}
        self.placeholders = {}
        self.max_columns = 2

        self.canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self._on_scroll, bootstyle="round") # MODIFIED
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.scrollable_frame.bind("<MouseWheel>", self._on_mousewheel)
        self.bind("<Configure>", self.on_resize)
        
        self.style = self.winfo_toplevel().style
        labelframe_bg = self.style.lookup('TLabelframe', 'background')
        self.canvas.config(bg=labelframe_bg)

    def on_resize(self, event):
        new_max_columns = max(1, event.width // 350)
        if new_max_columns != self.max_columns:
            self.max_columns = new_max_columns
            self.redraw_grid()
        self.after(50, self._lazy_load_visible_widgets) # NEW: Check on resize

    def _on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def get_placeholder(self, size, text):
        if (size, text) in self.placeholders: return self.placeholders[(size, text)]
        try:
            colors = self.style.colors
            img = Image.new('RGB', size, color=colors.get('dark'))
            draw = ImageDraw.Draw(img)
            try:
                font_path = "arial.ttf" if sys.platform == "win32" else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
                font = ImageFont.truetype(font_path, 10)
            except IOError: font = ImageFont.load_default()
            draw.text((size[0]/2, size[1]/2), text, font=font, anchor="mm", fill=colors.get('light'))
            photo = ImageTk.PhotoImage(img)
            self.placeholders[(size, text)] = photo
            return photo
        except Exception: return None

    # NEW: Handle scrollbar movement
    def _on_scroll(self, *args):
        self.canvas.yview(*args)
        self.after(50, self._lazy_load_visible_widgets)

    # MODIFIED: Handle mouse wheel
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.after(50, self._lazy_load_visible_widgets)
    
    def clear_list(self, message=""):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        if message:
            self.scrollable_frame.grid_columnconfigure(0, weight=0)
            ttk.Label(self.scrollable_frame, text=message, font=("Helvetica", 10, "italic")).grid(row=0, column=0, pady=20)
    
    def get_selected_keys(self):
        return list(self.selected_widgets.keys())

    def on_mod_select(self, mod_key, widget, event):
        ctrl_pressed = (event.state & 0x0004) != 0

        if ctrl_pressed:
            if mod_key in self.selected_widgets:
                widget.config(style="TFrame") 
                del self.selected_widgets[mod_key]
            else:
                widget.config(bootstyle="primary")
                self.selected_widgets[mod_key] = widget
        else:
            is_only_selected = mod_key in self.selected_widgets and len(self.selected_widgets) == 1
            for w in self.selected_widgets.values():
                w.config(style="TFrame")
            self.selected_widgets.clear()
            if not is_only_selected:
                widget.config(bootstyle="primary")
                self.selected_widgets[mod_key] = widget

        if self.view_type == 'local':
            self.controller.set_source_folder_from_local_mod(list(self.selected_widgets.keys()))

    def clear_selection(self):
        for widget in self.selected_widgets.values():
            widget.config(style="TFrame")
        self.selected_widgets.clear()
        self.controller.clear_source_folder_selection()

    def select_items(self, mod_keys_to_select):
        self.clear_selection()
        all_widgets = {child.mod_data['full_path']: child for child in self.scrollable_frame.winfo_children() if hasattr(child, 'mod_data')}
        for key in mod_keys_to_select:
            if key in all_widgets:
                widget = all_widgets[key]
                widget.config(bootstyle="primary")
                self.selected_widgets[key] = widget
        if self.view_type == 'local':
            self.controller.set_source_folder_from_local_mod(list(self.selected_widgets.keys()))

    def redraw_grid(self):
        widgets = self.scrollable_frame.winfo_children()
        for i, widget in enumerate(widgets):
            row = i // self.max_columns
            col = i % self.max_columns
            widget.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        for i in range(self.max_columns):
            self.scrollable_frame.grid_columnconfigure(i, weight=1)

    def display_list(self, mod_list, message=""):
        self.clear_list()
        self.canvas.yview_moveto(0)
        if not mod_list:
            self.clear_list(message)
            return

        for mod_data in mod_list:
            self.create_mod_widget(mod_data, view_mode=self.view_type)
        
        self.redraw_grid()
        self.update_idletasks()
        self.after(10, self._lazy_load_visible_widgets) # NEW: Initial load

    # NEW: Core lazy loading logic
    def _lazy_load_visible_widgets(self):
        if not self.winfo_viewable():
            return

        try:
            visible_top = self.canvas.yview()[0] * self.scrollable_frame.winfo_height()
            visible_bottom = self.canvas.yview()[1] * self.scrollable_frame.winfo_height()

            for widget in self.scrollable_frame.winfo_children():
                if isinstance(widget, ModDisplayItem) and not widget.images_loaded:
                    y = widget.winfo_y()
                    height = widget.winfo_height()
                    if y < visible_bottom and (y + height) > visible_top:
                        widget.load_images()
        except tk.TclError:
            # This can happen if the window is being destroyed, it's safe to ignore.
            pass

    def create_mod_widget(self, mod_data, view_mode):
        try:
            widget = ModDisplayItem(self.scrollable_frame, self.controller, self, mod_data, view_mode=view_mode)
            widget.config(style="TFrame")
            widget.mod_data = mod_data
            
            mod_key = mod_data.get('full_path') if view_mode == 'local' else mod_data.get('device_folder')
            if not mod_key:
                self.controller.frames["Mod Manager"].log(f"ERROR: Could not create mod widget, mod_key is missing for data: {mod_data}")
                widget.destroy()
                return

            def _select_callback(event, key=mod_key, wid=widget): self.on_mod_select(key, wid, event)
            self._bind_recursive(widget, "<Button-1>", _select_callback)
            self._bind_recursive(widget, "<MouseWheel>", self._on_mousewheel)
            return widget
        except Exception as e:
            self.controller.frames["Mod Manager"].log(f"FATAL: Failed to create widget for {mod_data.get('name')}. Error: {e}")
            return None

    def _bind_recursive(self, widget, event, callback):
        widget.bind(event, callback)
        for child in widget.winfo_children():
            if not isinstance(child, ttk.Button):
                self._bind_recursive(child, event, callback)