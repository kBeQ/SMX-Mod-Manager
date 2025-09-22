# --- Filename: Extensions/mod_helper/plugin.py ---
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import font
import webbrowser

# --- This is the original ModHelperFrame class, moved here from mod_helper_ui.py ---
class ModHelperFrame(ttk.Frame):
    name = "Mod Helper"
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.bold_font = font.Font(family="Helvetica", size=10, weight="bold")
        self.header_font = font.Font(family="Helvetica", size=14, weight="bold")

        self.canvas = tk.Canvas(self, highlightthickness=0)
        style = self.controller.style
        bg_color = style.lookup('TFrame', 'background')
        self.canvas.config(bg=bg_color)
        
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview, bootstyle="round")
        self.scrollable_frame = ttk.Frame(self.canvas, padding=25)

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.frame_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.canvas.bind('<Configure>', self.on_canvas_configure)
        
        self.build_ui()

        self._bind_recursive(self.scrollable_frame, "<MouseWheel>", self._on_mousewheel)

    def build_ui(self):
        header = ttk.Label(self.scrollable_frame, text="Welcome to the SMX Mod Manager!", font=self.header_font)
        header.pack(anchor='w', pady=(0, 10))
        intro_text = "This tool is designed to make organizing, installing, and managing your game mods as simple as possible. Click on the sections below to expand them."
        ttk.Label(self.scrollable_frame, text=intro_text, wraplength=800).pack(anchor='w', pady=(0, 20), fill='x')

        gs_content = self.create_collapsible_pane(self.scrollable_frame, "⓪ Getting Started: The Right Emulator", start_expanded=True)
        self.create_section_header(gs_content, "IMPORTANT: Use the Developer Emulator")
        self.create_section_text(gs_content, "Google offers two versions of Google Play Games on PC. For modding, you MUST use the special 'Developer Emulator' version. The standard public version is locked down and will not allow this tool to access the game files.")
        
        self.create_section_header(gs_content, "Where to Download")
        self.create_section_text(gs_content, "You can find the official download and installation instructions for the developer emulator at the following URL:")
        
        link_frame = ttk.Frame(gs_content)
        link_frame.pack(fill='x', padx=5, pady=5)
        
        url = "https://developer.android.com/games/playgames/emulator"
        
        url_label = ttk.Label(link_frame, text=url, font=("Helvetica", 10, "underline"), cursor="hand2", bootstyle="info")
        url_label.pack(side='left', padx=(0, 10))
        
        open_browser_btn = ttk.Button(link_frame, text="Open in Browser", command=lambda u=url: webbrowser.open_new_tab(u), bootstyle="secondary-outline")
        open_browser_btn.pack(side='left')

        copied_label = ttk.Label(link_frame, text="Copied!", bootstyle="success")

        def on_url_click(event):
            self.clipboard_clear()
            self.clipboard_append(url)
            self.controller.update()
            copied_label.pack(side='left', padx=5)
            self.after(2000, copied_label.pack_forget)

        url_label.bind("<Button-1>", on_url_click)

        mm_content = self.create_collapsible_pane(self.scrollable_frame, "① The Mod Manager Tab")
        self.create_section_text(mm_content, "This is your main workspace. It displays all the mod `.zip` files found in the Library folders you've set up on your PC.")

        self.create_section_header(mm_content, "A Tour of the UI")
        self.create_section_text(mm_content, "The screen is divided into a few key areas:")
        
        tour_list_frame = ttk.Frame(mm_content, padding=(10, 5))
        tour_list_frame.pack(fill='x')
        self.create_list_item(tour_list_frame, "Library & Category Navigation:", "At the top, you can switch between your main libraries (`[Tracks]`, `[Suits]`, etc.) and then filter by the categories you created in your folders.")
        self.create_list_item(tour_list_frame, "The Controls Panel:", "The panel on the left contains your main actions: Search, Quick Select buttons, the 'Sync Mappings' recovery tool, and the primary Install/Uninstall buttons.")
        self.create_list_item(tour_list_frame, "The Mod Card:", "Each mod is displayed on its own card, which validates critical files (like `Track.smxlevel`), shows image previews, and provides quick action buttons.")
        
        self.create_section_header(mm_content, "How to Organize Your Files")
        
        org_container = ttk.Frame(mm_content)
        org_container.pack(fill='x', expand=True, pady=10)
        org_container.grid_columnconfigure(0, weight=2)
        org_container.grid_columnconfigure(1, weight=3)

        tree_frame = self.create_treeview_example(org_container)
        tree_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 15))

        text_frame = ttk.Frame(org_container)
        text_frame.grid(row=0, column=1, sticky="nsew")
        self.create_section_text(text_frame, "The manager scans for `.zip` files inside each Library folder you've added. The way you organize them depends on the mod type.")
        self.create_list_item(text_frame, "For Tracks and Suits:", "To create categories, make subfolders with a `c_` prefix (e.g., `c_Supermoto`). Mods placed directly in the root of the library folder will appear as 'Uncategorized'.")
        self.create_list_item(text_frame, "For Sounds (Special Rule):", "Sound libraries are different. **Do not use the `c_` prefix.** Any subfolder is automatically treated as a category (e.g., `Spaceship Motor Sound`).")
        
        self.create_section_header(mm_content, "Install, Update & Uninstall")
        self.create_section_text(mm_content, "Select one or more mods by clicking on them (use Ctrl+Click to select multiple). Then use the buttons in the 'Controls' panel on the left to install or uninstall them. If a mod is already installed, the 'Install' button will update it. The emulator must be connected for these actions to work.")

        self.create_section_header(mm_content, "Sync Mappings with Device")
        self.create_section_text(mm_content, "This is a powerful recovery tool. If your mappings file gets deleted or you manually add mods and want the manager to track them, this button will scan the device. It then tries to match the mods it finds with the local `.zip` files in your library based on their filenames. This will overwrite your existing mappings.")

        s_content = self.create_collapsible_pane(self.scrollable_frame, "② The Settings Tab")
        self.create_section_header(s_content, "Configure the Tool")
        self.create_section_text(s_content, "This is where you set up the application to work with your specific mod folders and game configuration.")
        
        self.create_section_header(s_content, "Local Mod Library")
        self.create_section_text(s_content, "This is the most important setting. Click 'Add Folder...' to tell the manager where your mods are stored on your PC. You can add multiple library folders. For each folder, you must specify what type of mod it contains (e.g., Tracks, Sounds, or Suits).")

        self.create_section_header(s_content, "Game Configuration")
        self.create_section_text(s_content, "These settings tell the tool how to find your game on the emulator. For most users, the default values should work perfectly fine and do not need to be changed.")
        
    def create_collapsible_pane(self, parent, title, start_expanded=False):
        container = ttk.Frame(parent, bootstyle="secondary")
        container.pack(fill='x', expand=True, pady=5)

        expanded_var = tk.BooleanVar(value=start_expanded)
        header = ttk.Checkbutton(
            container,
            text=title,
            variable=expanded_var,
            bootstyle="toolbutton,info"
        )
        header.pack(fill='x', expand=True, padx=2, pady=2)

        content_frame = ttk.Frame(container, padding=(15, 10))
        if start_expanded:
            content_frame.pack(fill='x', expand=True)

        def toggle():
            if expanded_var.get():
                content_frame.pack(fill='x', expand=True)
            else:
                content_frame.pack_forget()
            self.scrollable_frame.after(10, self.scrollable_frame.event_generate, "<Configure>")

        header.config(command=toggle)
        return content_frame

    def create_treeview_example(self, parent):
        tree_frame = ttk.Frame(parent)
        
        tree = ttk.Treeview(tree_frame, height=26, bootstyle="info")
        tree.pack(fill='both', expand=True)

        lib_root = tree.insert("", "end", text=" 📁 My SMX Mods (Library Root)")
        
        # Sounds
        sounds_folder = tree.insert(lib_root, "end", text=" 📁 Sounds")
        sound_cat_1 = tree.insert(sounds_folder, "end", text=" 📁 Spaceship Motor Sound (Category)")
        sound_zip = tree.insert(sound_cat_1, "end", text="  📄 GRF250 Spaceship.zip")
        sound_middleman = tree.insert(sound_zip, "end", text="   📁 GRF250")
        tree.insert(sound_middleman, "end", text="    ├─ 🔊 engine.wav")
        tree.insert(sound_middleman, "end", text="    ├─ 🔊 high.wav")
        tree.insert(sound_middleman, "end", text="    ├─ 🔊 idle.wav")
        tree.insert(sound_middleman, "end", text="    ├─ 🔊 low.wav")
        tree.insert(sound_middleman, "end", text="    └─ 🖼️ preview.png")
        tree.insert(sounds_folder, "end", text=" 📄 Uncategorized Y250 Sound Mod.zip")

        # Suits
        suits_folder = tree.insert(lib_root, "end", text=" 📁 Suits")
        suit_cat_1 = tree.insert(suits_folder, "end", text=" 📁 c_Mx (Category)")
        suit_zip = tree.insert(suit_cat_1, "end", text="  📄 My First Mx Suit.zip")
        suit_middleman = tree.insert(suit_zip, "end", text="   📁 My Suit Name")
        tree.insert(suit_middleman, "end", text="    ├─ 🤵 gear_suit.png")
        tree.insert(suit_middleman, "end", text="    ├─ 🤵 gear_suit_normal.png")
        tree.insert(suit_middleman, "end", text="    ├─ 🖼️ icon.png")
        tree.insert(suit_middleman, "end", text="    └─ 🖼️ preview.png")
        tree.insert(suits_folder, "end", text=" 📄 Uncategorized Suit.zip")

        # Tracks
        tracks_folder = tree.insert(lib_root, "end", text=" 📁 Tracks")
        track_cat_1 = tree.insert(tracks_folder, "end", text=" 📁 c_Supermoto (Category)")
        track_zip = tree.insert(track_cat_1, "end", text="  📄 My First Track.zip")
        track_middleman = tree.insert(track_zip, "end", text="   📁 My Track Name")
        tree.insert(track_middleman, "end", text="    ├─ 🏁 MyTrack.smxlevel")
        tree.insert(track_middleman, "end", text="    └─ 🖼️ preview.png")
        tree.insert(tracks_folder, "end", text=" 📄 Uncategorized Track.zip")
        
        # --- EXPAND ALL NODES BY DEFAULT FOR FULL VISIBILITY ---
        for item in [lib_root, sounds_folder, suits_folder, tracks_folder, sound_zip, suit_zip, track_zip, sound_middleman, suit_middleman, track_middleman]:
            tree.item(item, open=True)

        tree.bind("<<TreeviewSelect>>", lambda e: "break")
        return tree_frame

    def create_section_header(self, parent, text):
        ttk.Label(parent, text=text, font=self.bold_font).pack(anchor='w', pady=(10, 2))
        
    def create_section_text(self, parent, text):
        ttk.Label(parent, text=text, wraplength=750).pack(anchor='w', fill='x', padx=5, pady=(0,5))
    
    def create_list_item(self, parent, title, text):
        item_frame = ttk.Frame(parent)
        item_frame.pack(fill='x', anchor='w', pady=(2, 5))
        ttk.Label(item_frame, text=title, font=self.bold_font).pack(anchor='w')
        ttk.Label(item_frame, text=text, wraplength=730).pack(anchor='w', padx=(10, 0))

    def on_canvas_configure(self, event):
        self.canvas.itemconfig(self.frame_id, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _bind_recursive(self, widget, event, callback):
        widget.bind(event, callback)
        for child in widget.winfo_children():
            self._bind_recursive(child, event, callback)


# --- This is the required entry point for the extension system ---
class SMXExtension:
    def __init__(self):
        self.name = "Mod Helper"
        self.description = "Provides guidance and help for using the mod manager."
        self.version = "1.0.0"

    def initialize(self, app):
        """Called by the main application to let the extension integrate itself."""
        print(f"INFO: Initializing extension '{self.name}' v{self.version}")
        self.app = app
        self.app.add_extension_tab(self.name, ModHelperFrame)

    def on_close(self):
        """Called when the main application is closing."""
        print(f"INFO: Closing extension '{self.name}'.")
        pass