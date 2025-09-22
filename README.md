# SMX Mod Manager

![SMX Mod Manager Banner](/assets/SMX%20Mod%20Manager.png)

<div align="center">

**[Latest Release](https://github.com/kBeQ/SMX-Mod-Manager/releases) • [License](/LICENSE)**

</div>

SMX Mod Manager since SMX: Supermoto Vs. Motocross v7.17.13

A powerful, user-friendly desktop application for organizing, installing, and managing mods for SMX on the Google Play Games on PC emulator.

This tool is specifically designed for **SMX: Supermoto Vs. Motocross v8.0.4+**.
---


## ✨ Key Features

*   **Organize Your Mods:** Set up "Libraries" for your `Tracks`, `Suits`, & `Sounds`, and organize them with custom categories.
*   **One-Click Install/Update:** Select one or more mods and push them to the emulator with a single click.
*   **Rich Mod Previews:** The UI automatically validates mod `.zip` archives and shows previews for textures and required files.
*   **Sync & Recover:** Re-link mods on your device to your local files using the "Sync Mappings" recovery tool.
*   **Built-in ADB Console:** A console for power users to send custom commands directly to the emulator.
*   **Game Launch Control:** Launch or force-stop the game directly from the tool.
*   **Customizable Interface:** Choose from several themes to personalize your experience.

## 🖥️ A Tour of the Application

### The Mod Manager Tab: Your Local Library
This is your main workspace. It displays all the mod `.zip` files the manager has found in the Library folders you've set up on your PC.

![SMX Mod Manager Main UI](/docs/SMXMM-On%20PC.png)

*   **Library & Category Navigation:** At the top, you can switch between your main libraries (`[Tracks] Tracks`, `[Suits] Suits`, etc.) and then filter by the categories you created in your folders (`Uncategorized`, `Games`, etc.).
*   **The Controls Panel:** The panel on the left contains your main actions: Search, Quick Select buttons, the **Sync Mappings** recovery tool, and the primary Install/Uninstall buttons.
*   **The Mod Card:** Each mod is displayed on its own card, which validates critical files found inside the `.zip` archive (like `Track.smxlevel`) and provides quick action buttons.


## ⚠️ Prerequisites

To use this tool, you **MUST** have the **Developer Emulator** version of Google Play Games on PC installed.

*   **Download Link:** [Google Play Games for PC (Developer Emulator)](https://developer.android.com/games/playgames/emulator)

**The standard public version of Google Play Games will not work!**


## 🚀 Installation

1.  Download the latest `SMX_Mod_Manager_Build.zip` file.
2.  Unzip the folder to a permanent location on your computer (e.g., `C:\Program Files`).
3.  Run `smx_mod_manager.exe` from inside the unzipped folder. (Create a shortcut if you want)

## 📖 How to Use

### 1. First-Time Setup
The Mod Manager works by linking to the folders on your PC where you store your mod `.zip` files. Each folder you add is called a "Library" and must contain only one type of mod.

*   Open the Mod Manager and go to the **Settings** tab.
*   Under "Local Mod Library," click **"Add Folder..."**.

![SMX Mod Manager Libraries](/docs/SMXMM-Libraries.png)*

Select the folder that contains your **Tracks** (e.g., a folder on your PC named `My Tracks`).
*   When prompted, set the library type to **'Tracks'**.

    ![SMX Mod Manager Libraries](/docs/SMXMM-LibraryType.png)

*   **Repeat this process for your `Suits` and `Sounds` library folders.**
*   **Flexibility:** You can add multiple libraries of the same type. For example, if you have tracks in `C:\Downloads\Tracks` and `D:\MyMods\SupermotoTracks`, you can add both as separate 'Tracks' libraries.

> ### The Golden Rule: Library vs. Mod File
> A common mistake is selecting a category folder (like `c_Supermoto`) or an individual mod's `.zip` file as a Library. You must select the parent folder that *contains* your categories and `.zip` files.
>
> **✅ Do This:** Add the parent folder containing your mods.
> ```
> # Correct Library Path:
> D:/My SMX Mods/Tracks/
> ```
>
> **❌ Don't Do This:** Add a category folder or a single mod file.
> ```
> # Incorrect Library Paths:
> D:/My SMX Mods/Tracks/c_My Tracks/
> D:/My SMX Mods/Tracks/My Awesome Track.zip
> ```

### 2. Organizing Your Local Mods
The manager scans for `.zip` files inside each Library folder you've added. The way you organize them depends on the mod type.

#### For Tracks and Suits (Using `c_` prefix)
To create categories, make subfolders with a `c_` prefix.

*   **For Categories:** Create subfolders like `c_4-Stroke` or `c_Supermoto`. Place your mod `.zip` files inside them.
*   **For Uncategorized Mods:** Place mod `.zip` files directly inside the main Library folder.

#### For Sounds (No prefix needed)
Sound libraries are special. **Do not use the `c_` prefix.** Any subfolder is automatically treated as a category.

*   **For Categories:** Simply create a normal subfolder (e.g., `Spaceship Sounds`). Place the `.zip` file for that sound mod inside it.

For more info see https://github.com/kBeQ/SMX-Sound-Creator and navigate to "Here's what you can expect on export" section and the "⚡ Seamless Workflow with SMX Mod Manager" section.

#### Example Structure:
Let's group everything together,
This example shows a "My SMX Mods" folder containing three libraries. Notice the difference between the `Sounds` library and the others.

```
📁 My SMX Mods/
├── 📁 Sounds/  <-- Added as a [Sounds] Library in Settings
├── 📁 Suits/   <-- Added as a [Suits] Library in Settings
└── 📁 Tracks/  <-- Added as a [Tracks] Library in Settings
```
```
📁 Sounds/
├── 📁 Spaceship Motor Sound/
│   ├── 📄 GRF250 Spaceship.zip
│   │   └── 📁 GRF250/
│   │       ├── 🔊 engine.wav
│   │       ├── 🔊 high.wav
│   │       ├── 🔊 idle.wav
│   │       ├── 🔊 low.wav
│   │       └── 🖼️ preview.png
│   ├── 📄 GRF450 Spaceship.zip
│   ├── 📄 Y250 Spaceship.zip
│   ├── 📄 Y450 Spaceship.zip
│   └── 📄 etc.zip
│
└── 📄 Uncategorized Y250 Sound Mod.zip
```
```
📁 Suits/
├── 📁 c_Mx/
│   └── 📄 My First Mx Suit.zip
│       └── 📁 My Suit Name/
│           ├── 🤵 gear_suit.png
│           ├── 🤵 gear_suit_normal.png
│           ├── 🖼️ icon.png
│           └── 🖼️ preview.png
│
└── 📄 Uncategorized Suit.zip
```
```
📁 Tracks/
├── 📁 c_Supermoto/
│   └── 📄 My First Track.zip
│       └── 📁 My Track Name/
│           ├── 🏁 MyTrack.smxlevel
│           └── 🖼️ preview.png
│
└── 📄 Uncategorized Track.zip
```

### 3 . Installing Mods
1.  Launch SMX Mod Manager.
2.  Launch the Google Play Games Developer Emulator. The status should turn yellow ("Emulator Connected").
3.  Launch SMX. You can use the **"Launch Game"** button in the tool.
4.  Wait for the status indicator to turn green ("Game Running").
5.  Select the mod(s) you want to install. You can **Ctrl+Click** to select multiple.
6.  Click the **"Install/Update Selected"** button. The log at the bottom will show the progress.

For a more detailed walkthrough, see the **"Mod Helper"** tab inside the application.


## 🤔 Frequently Asked Questions (FAQ)

**Q: I've seen guides that mention creating a `mod_0_...` folder. Do I need to do that?**
**A:** No, you don't! The tool handles this for you automatically. When you install a mod from a `.zip` file, the tool unzips it, creates the correctly named `mod_i_...` folder on your device, and saves a link in its `mod_mappings.json` file. This mapping is how the tool knows the status of your mods and allows it to update or uninstall them correctly.

**Q: What is the "Sync Mappings" button for?**
**A:** It's a recovery tool. If your `mod_mappings.json` file gets deleted, or if you want the manager to "adopt" mods you copied to the device manually, this button will help. It scans the device and tries to match the installed mod folders with your local `.zip` files based on their names. This will overwrite any existing mappings.


## 🚀 Publishing your Mods
For a guide on the recommended way to package your final mod files for distribution, see the guide on mod.io. The structure required by this tool is the same structure you should use for publishing.
*   **[Guide: Zipping the Files for Release](https://mod.io/g/smx/r/zipping-the-files)**

> **Note:** Zipping the Files guide was approved and is editable by the game's developer to ensure it stays up-to-date with best practices.

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

1.  Clone this repository: `git clone https://github.com/kBeQ/SMX-Mod-Manager.git`
2.  Navigate into the project folder: `cd SMX-Mod-Manager`
3.  Create and activate a Python virtual environment:
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```
4.  Install the required packages: `pip install -r requirements.txt`
5.  Make sure your environment is valid by running: `build & run.bat`

## 📄 License
This project is licensed under the MIT License - see the `LICENSE` file for details.

---

## 🛠️ More SMX Modding Tools

Check out other tools in the SMX Modding suite:

<table width="100%">
 <tr>
  <td align="center" width="50%">
    <h3>SMX Mod Manager</h3>
    <a href="https://github.com/kBeQ/SMX-Mod-Manager">
      <img src="https://raw.githubusercontent.com/kBeQ/SMX-Mod-Manager/main/assets/Ico_smx_mod_manager.png" width="250" alt="SMX Mod Manager Banner">
    </a>
  </td>
  <td align="center" width="50%">
    <h3>SMX Sound Creator</h3>
    <a href="https://github.com/kBeQ/SMX-Sound-Creator">
      <img src="https://raw.githubusercontent.com/kBeQ/SMX-Sound-Creator/main/assets/smx_sound_creator.png" width="250" alt="SMX Sound Creator Banner">
    </a>
  </td>
 </tr>
</table>