# SMX Mod Manager

<!-- The path starts from the root of your project -->
![SMX Mod Manager Banner](/assets/SMX%20Mod%20Manager.png)

<div align="center">


**[Latest Release](/releases) • [License](/LICENSE)**

</div>

A powerful, user-friendly desktop application for organizing, installing, and managing mods for SMX on the Google Play Games on PC emulator.

---

<!-- This path points to the new docs folder -->
<!-- ![App Screenshot](/docs/AppScreenshot0.png) -->

## ✨ Key Features

*   **Organize Your Mods:** Set up "Libraries" (your main mod folders) and organize mods by type (`Tracks`, `Suits`, `Sounds`) and custom categories.
*   **One-Click Install & Update:** Select one or more mods and install or update them on the emulator with a single click. The manager automatically handles folder creation and file transfers.
*   **Rich Mod Previews:** The UI intelligently validates your mod folders, showing you:
    *   ✅ If required track (`.smxlevel`) or sound (`.wav`) files are present.
    *   ✅ Previews for `icon.jpg`, `gear_suit.png`, and `gear_suit_normal.png` for suit mods.
*   **On-Device Management:** Scan the emulator to find "unmanaged" mods (those you copied manually) and easily delete them to clean up your installation.
*   **Built-in ADB Console:** A console for power users to send custom ADB commands directly to the emulator.
*   **Customizable Interface:** Choose from several themes to personalize your experience.

## ⚠️ Prerequisites

To use this tool, you **MUST** have the **Developer Emulator** version of Google Play Games on PC installed. The standard public version is locked down and will not allow the Mod Manager to access the necessary game files.

*   **Download Link:** [Google Play Games for PC (Developer Emulator)](https://developer.android.com/games/playgames/emulator)

**The standard public version of Google Play Games will not work!**

## 🚀 Installation

1.  Go to the [**Releases Page**](https://github.com/kBeQ/SMX%20Mod%20Manager/releases) of this repository.
2.  Download the latest `SMX_Mod_Manager_Build.zip` file.
3.  Unzip the folder to a permanent location on your computer (e.g., your Desktop or `C:\Program Files`).
4.  Run `smx_mod_manager.exe` from inside the unzipped folder.

## 📖 How to Use

### 1. First-Time Setup
*   Open the Mod Manager and go to the **Settings** tab.
*   Under "Local Mod Library," click **"Add Folder..."**.
*   Select the main folder on your PC where you store all your mods (e.g., a folder called "My SMX Mods").
*   You will be prompted to select the **type** of mods this library contains (Tracks, Sounds, or Suits).

### 2. Organizing Your Local Mods
For the manager to find your mods, you need a simple folder structure. Inside the main Library folder you just added:

*   Create subfolders for each type: `Tracks`, `Sounds`, and `Suits`.
*   To create categories within a type, make a folder with a `c_` prefix (e.g., `c_Supermoto`).
*   Place each individual mod in its own folder.

![SMX Mod Manager Libraries](/docs/SMXMM-Libraries.png)

**Example Structure:**
```
    Sounds/
    ├── c_4-Stroke/
    │   └── My First Sound Mod/
    │       ├── engine.wav
    │       ├── high.wav
    │       ├── idle.wav
    │       ├── low.wav
    │       ├── preview.jpg
    │       └── icon.jpg
    │
    └── Uncategorized Sound/
        ├── engine.wav
        ├── high.wav
        ├── idle.wav
        ├── low.wav
        ├── preview.jpg
        └── icon.jpg


    Suits/
    ├── c_Mx/
    │   └── My First Suit/
    │       ├── gear_suit.png
    │       ├── gear_suit_normal.png
    │       ├── preview.jpg
    │       └── icon.jpg
    │
    └── Uncategorized Suit/
        ├── gear_suit.png
        ├── gear_suit_normal.png
        ├── preview.jpg
        └── icon.jpg


    Tracks/
    ├── c_Supermoto/
    │   └── My Awesome Track/
    │       ├── Track1.smxlevel
    │       └── preview.jpg
    │
    └── Uncategorized Track/
        ├── Track2.smxlevel
        └── preview.jpg
```

### 3. Installing Mods
1. Launch SMX Mod Manager.
1.a  Launch the Google Play Games Developer Emulator and wait for the status indicator to turn yellow and say "Emulator running. Please start the game."
2. Launch SMX. ** You can do so from the tool itself! Saving you the game's loading time to begin managing your mods!
3. Wait for the status indicator to turn green and say "Connected".
4. Select the mod(s) you want to install. You can **Ctrl+Click** to select multiple.
5. Click the **"Install/Update Selected"** button.
6. The log output at the bottom will show the progress!

The "Mod Helper" tab should have everything you need to know.


## 🛠️ Building from Source

If you want to modify the tool or build it yourself:

1.  Clone this repository: `git clone https://github.com/kBeQ/SMX Mod Manager.git`
2.  Navigate into the project folder: `cd SMX Mod Manager`
3.  Create and activate a Python virtual environment:
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```
4.  Install the required packages: `pip install -r requirements.txt`
5.  Run the build script: `build & run.bat`

## 📄 License

This project is licensed under the MIT License - see the `LICENSE` file for details.