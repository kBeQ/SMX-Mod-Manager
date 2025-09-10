# --- Filename: Extensions/mod_helper/plugin.py ---
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import font

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
        ttk.Label(link_frame, text="URL:", font=self.bold_font).pack(side='left')
        link_entry = ttk.Entry(link_frame)
        link_entry.insert(0, "https://developer.android.com/games/playgames/emulator")
        link_entry.config(state="readonly")
        link_entry.pack(side='left', fill='x', expand=True, padx=5)

        mm_content = self.create_collapsible_pane(self.scrollable_frame, "① The Mod Manager Tab")
        self.create_section_text(mm_content, "This is the primary screen for managing the collection of mods stored on your computer. To get started, you need to set up your local mod folders correctly.")
        
        self.create_section_header(mm_content, "Recommended Folder Structure")
        self.create_section_text(mm_content, "Below is a visual guide. Go to the 'Settings' tab to add your main library folder (e.g., 'My SMX Mods'). Inside that folder, create subfolders for each mod type. For further organization, you can use category folders with a `c_` prefix.")
        self.create_treeview_example(mm_content)
        
        self.create_section_header(mm_content, "Install, Update & Uninstall")
        self.create_section_text(mm_content, "Select one or more mods by clicking on them (use Ctrl+Click to select multiple). Then use the buttons in the 'Controls' panel on the left to install or uninstall them. The game must be running in the emulator for these actions to work.")
        
        od_content = self.create_collapsible_pane(self.scrollable_frame, "② The On Device Tab")
        self.create_section_header(od_content, "See What's on the Emulator")
        self.create_section_text(od_content, "This tab shows you mods that are currently on the device but are not being tracked by this tool (e.g., mods you copied manually).")
        
        self.create_section_header(od_content, "Unmanaged Mods")
        self.create_section_text(od_content, "If you manually copied mods to your device in the past, they will appear here as 'Unmanaged'. This tool can't automatically update them, but it provides an easy way to delete them if you want to replace them with a managed version from the Mod Manager tab.")

        self.create_section_header(od_content, "Filter & Delete")
        self.create_section_text(od_content, "You can filter the list by mod type. To clean up, select one or more unmanaged mods and click 'Delete Selected'. This action permanently removes the mod from the device and cannot be undone.")
        
        s_content = self.create_collapsible_pane(self.scrollable_frame, "③ The Settings Tab")
        self.create_section_header(s_content, "Configure the Tool")
        self.create_section_text(s_content, "This is where you set up the application to work with your specific mod folders and game configuration.")
        
        self.create_section_header(s_content, "Local Mod Library")
        self.create_section_text(s_content, "This is the most important setting. Click 'Add Folder...' to tell the manager where your mods are stored on your PC. You can add multiple library folders. For each folder, you must specify if it contains Tracks, Sounds, or Suits.")

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
        tree_frame = ttk.Frame(parent, padding=(0, 10, 0, 10))
        tree_frame.pack(fill='x', expand=True)

        tree = ttk.Treeview(tree_frame, height=7, bootstyle="info")
        tree.pack(fill='x', expand=True)

        lib_root = tree.insert("", "end", text=" 📁 My SMX Mods (Your Library Folder in Settings)")
        tracks_folder = tree.insert(lib_root, "end", text=" 📁 Tracks")
        tree.insert(lib_root, "end", text=" 📁 Sounds")
        tree.insert(lib_root, "end", text=" 📁 Suits")
        cat_1 = tree.insert(tracks_folder, "end", text=" 📁 c_Supermoto (Category)")
        cat_2 = tree.insert(tracks_folder, "end", text=" 📁 c_Enduro (Category)")
        tree.insert(cat_1, "end", text=" └─ 📁 My Awesome Track (Mod Folder)")
        tree.insert(tracks_folder, "end", text=" 📁 Uncategorized Track 1 (Mod Folder)")
        tree.insert(tracks_folder, "end", text=" 📁 Uncategorized Track 2 (Mod Folder)")

        tree.bind("<<TreeviewSelect>>", lambda e: "break")

    def create_section_header(self, parent, text):
        ttk.Label(parent, text=text, font=self.bold_font).pack(anchor='w', pady=(10, 2))
        
    def create_section_text(self, parent, text):
        ttk.Label(parent, text=text, wraplength=750).pack(anchor='w', fill='x', padx=5, pady=(0,5))

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