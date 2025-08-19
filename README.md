# SMX Mod Manager

<!-- The path starts from the root of your project -->
![SMX Mod Manager Banner](/assets/SMX%20Mod%20Manager.png)

<div align="center">


**[Latest Release](/releases) • [License](/LICENSE)**

</div>

A powerful, user-friendly desktop application for organizing, installing, and managing mods for SMX on the Google Play Games on PC emulator.

This tool is specifically designed for **SMX: Supermoto Vs. Motocross v7.17.13**.

---



## ✨ Key Features

*   **Organize Your Mods:** Set up "Libraries" for your `Tracks`, `Suits`, & `Sounds`, and organize them with custom categories.
*   **One-Click Install/Update:** Select one or more mods and push them to the emulator with a single click.
*   **Rich Mod Previews:** The UI automatically validates mod folders and shows previews for textures and required files.
*   **Clean Up In-Game Mods:** The "On Device" tab lets you see and delete mods downloaded from the in-game browser.
*   **Built-in ADB Console:** A console for power users to send custom commands directly to the emulator.
*   **Game Launch Control:** Launch or force-stop the game directly from the tool.
*   **Customizable Interface:** Choose from several themes to personalize your experience.

## 🖥️ A Tour of the Application

### The Mod Manager Tab: Your Local Library
This is your main workspace. It displays all the mods the manager has found in the Library folders you've set up on your PC.

![SMX Mod Manager Main UI](/docs/SMXMM-On%20PC.png)

*   **Library & Category Navigation:** At the top, you can switch between your main libraries (`[Tracks] Tracks`, `[Suits] Suits`, etc.) and then filter by the categories you created in your folders (`Uncategorized`, `Games`, etc.).
*   **The Controls Panel:** The panel on the left contains your main actions: Search, Quick Select buttons, and the primary Install/Uninstall buttons.
*   **The Mod Card:** Each mod is displayed on its own card, which validates critical files (like `Track.smxlevel`) and provides quick action buttons.

### The On Device Tab: Cleaning Up In-Game Mods
This tab is your solution for managing mods you've downloaded from the in-game mod.io browser.

![On Device Library](/docs/SMXMM-OnDevice.png)

*   **Scan Your Device:** See a full list of all "unmanaged" mods currently installed on the emulator.
*   **Filter and Delete:** Quickly filter by mod type and select one or more mods to permanently remove them from your device.



## ⚠️ Prerequisites

To use this tool, you **MUST** have the **Developer Emulator** version of Google Play Games on PC installed.

*   **Download Link:** [Google Play Games for PC (Developer Emulator)](https://developer.android.com/games/playgames/emulator)

**The standard public version of Google Play Games will not work!**


## 🚀 Installation

1.  Download the latest `SMX_Mod_Manager.zip` file.
2.  Unzip the folder to a permanent location on your computer (e.g., `C:\Program Files`).
3.  Run `smx_mod_manager.exe` from inside the unzipped folder. (Create a shortcut if you want)

## 📖 How to Use

### 1. First-Time Setup
The Mod Manager works by linking to the folders on your PC where you store your mods. Each folder you add is called a "Library" and must contain only one type of mod.

*   Open the Mod Manager and go to the **Settings** tab.
*   Under "Local Mod Library," click **"Add Folder..."**.
![SMX Mod Manager Libraries](/docs/SMXMM-Libraries.png)
*   Select the folder that contains your **Tracks** (e.g., a folder on your PC named `My Tracks`).
*   When prompted, set the library type to **'Tracks'**.
![SMX Mod Manager Libraries](/docs/SMXMM-LibraryType.png)

*   **Repeat this process for your `Suits` and `Sounds` folders.**
*   **Flexibility:** You can add multiple libraries of the same type. For example, if you have tracks in `C:\Downloads\Tracks` and `D:\MyMods\SupermotoTracks`, you can add both as separate 'Tracks' libraries.

> ### The Golden Rule: Library vs. Mod Folder
> A common mistake is selecting an individual mod's folder as a Library. You must select the parent folder that *contains* your mod folders.
>
> **✅ Do This:** Add the parent folder containing your mods.
> ```
> # Correct Library Path:
> D:/My SMX Mods/Tracks/
> ```
>
> **❌ Don't Do This:** Add the folder for a single mod.
> ```
> # Incorrect Library Path:
> D:/My SMX Mods/Tracks/My Track/
> D:/My SMX Mods/Tracks/c_My Tracks/
> ```

### 2. Organizing Your Local Mods
The manager expects a specific structure *inside* each Library folder you've added.

*   **For Categories:** Create subfolders with a `c_` prefix (e.g., `c_4-Stroke`). Place your individual mod folders inside these category folders.
*   **For Uncategorized Mods:** Place individual mod folders directly inside the Library folder. They will appear in the "Uncategorized" category for that Library.

![SMX Mod Manager Libraries Categories](/docs/SMXMM-Libraries-Cat.png)



**Example Structure:**
```
    Sounds/
    ├── c_4-Stroke/
    │   └── My First Sound Mod/   <----  "Sounds/4-Stroke/"
    │       ├── engine.wav
    │       ├── high.wav
    │       ├── idle.wav
    │       ├── low.wav
    │       └── preview.jpg
    │
    └── Sound 0/   <----  "Uncategorized/"
        ├── engine.wav
        ├── high.wav
        ├── idle.wav
        ├── low.wav
        └── preview.jpg


    Suits/
    ├── c_Mx/
    │   └── My First Mx Suit/   <----  "Suits/Mx/"
    │       ├── gear_suit.png
    │       ├── gear_suit_normal.png
    │       ├── preview.jpg
    │       └── icon.jpg
    │
    └── Suit 0/   <----  "Uncategorized/"
        ├── gear_suit.png
        ├── gear_suit_normal.png
        ├── preview.jpg
        └── icon.jpg


    Tracks/
    ├── c_Supermoto/
    │   └── My First Track/   <----  "Tracks/SuperMoto/"
    │       ├── Track1.smxlevel
    │       └── preview.jpg
    │
    └── Track 0/   <----  "Uncategorized/"
        ├── Track2.smxlevel
        └── preview.jpg


________________________________________________________________________________________________________
Let's see a "default Library" structure:

    LibraryFolder/
        ├── c_Category 1/
        │   └── Categorized Mod Folder 1/   <----  "LibraryFolder/Category 1/"
        │       ├── Mod File.extension
        │       └── preview.jpg
        ├── c_Category 2/
        │   └── Categorized Mod Folder 2/   <----  "LibraryFolder/Category 2/"
        │       ├── Mod File.extension
        │       └── preview.jpg
        │
        └── Uncategorized Mod Folder 1/   <----  "Uncategorized/"
            ├── Mod File.extension
            └── preview.jpg
```


### 3 . Installing Mods
1.  Launch SMX Mod Manager.
2.  Launch the Google Play Games Developer Emulator. The status should turn yellow.
3.  Launch SMX. You can use the **"Launch Game"** button in the tool!
4.  Wait for the status indicator to turn green and say "Connected".
5.  Select the mod(s) you want to install. You can **Ctrl+Click** to select multiple.
6.  Click the **"Install/Update Selected"** button. The log at the bottom will show the progress.

*The "Mod Helper" tab in the application contains a detailed guide to all features.*


## 🤔 Frequently Asked Questions (FAQ)

**Q: I've seen official guides that mention creating a `mod_0_...` folder. Do I need to do that?**
**A:** No, you don't! The tool handles this for you automatically.

The game requires mods to be in a specially named folder (like `mod_0_MyMod`). When you install a mod, the tool does two things:
1.  It creates the correctly named `mod_i_...` folder on your device.
2.  It saves a link in its `mod_mappings.json` file to remember which local mod corresponds to which folder on the device.

This mapping file is how the tool "manages" your mods, allowing it to know their status and uninstall them correctly. You just need to focus on your source folders, and the tool handles all the complex parts!


## 🚀 Publishing your Mods
For a guide on the recommended way to package your final mod files for distribution, see the guide on mod.io:
*   **[Guide: Zipping the Files for Release](https://mod.io/g/smx/r/zipping-the-files)**

> **Note:** This guide was approved and is editable by the game's developer to ensure it stays up-to-date with best practices.

## 💬 Community & Support
**[Join the OE Games Discord Server](https://discord.gg/mJmb4HaRWN)**  to discuss the game, share mods, and get help from the community!

> ### ⚠️ **Important: Where to Ask for Help**
> Please use the appropriate channel for support:
> *   For questions or issues about the **game itself**, use the official Discord.
> *   For bugs, feature requests, or problems with **this Mod Manager tool**, please **[open an issue on GitHub](https://github.com/kBeQ/SMX-Mod-Manager/issues)**.
>
> This ensures that game-related questions go to the developer, and tool-related issues are tracked here. **Please do not ask for Mod Manager support in the Discord.**


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
5.  Make sure your environment is valid by running: `build & run.bat`

## 📄 License
This project is licensed under the MIT License - see the `LICENSE` file for details.