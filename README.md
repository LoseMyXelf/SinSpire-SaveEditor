# Sin Spire Save Editor

A native Windows desktop app for opening, inspecting, and repairing Sin Spire Unreal Engine `.sav` files. The project is Python and can be opened as a folder in VSCodium.

Current app version: **0.1.0**.

On first launch, the app asks the user to acknowledge the save safety warning. The acknowledgement is stored in the current Windows user's local app data folder.

The app uses a deep navy interface, mint accents, clearer section hierarchy, and roomier tables for a more comfortable editing view. The Sin Spire logo appears in the app header, with a matching artwork icon in the window title bar and taskbar.
The **Helper** tab explains the storage types and the edit/save workflow. The **Info** tab states that this is an unofficial community project, lists its credits, and links to Krasue Games' Patreon.

## Credits

Sin Spire was created by **Krasue Games**. The save editor was created by **LoseMyXelf (LMX)**. This is an unofficial fan-made utility and is not affiliated with or endorsed by Krasue Games.

## Run

1. Install Python 3.10 or newer with Tkinter (the standard Windows Python installer includes it).
2. Open this folder in VSCodium, or open PowerShell in this folder.
3. Install the parser dependency once:

   ```powershell
   py -3 -m pip install -r requirements.txt
   ```

4. Start the desktop app:

   ```powershell
   py -3 .\save_editor_gui.py
   ```

   Or double-click `launch_editor.bat`.
5. Choose **Open / Import .sav**, edit values by double-clicking them, and choose **Save edited copy**. Pick an output folder; the app saves the copy with the original filename, leaves the imported save untouched, and opens the output folder when finished. Select the saved copy in the game to use it.

## Build a Windows executable

From the project folder, double-click `build_exe.bat`. It installs the packaging tool into the project virtual environment and creates:

```text
dist\Sin Spire Save Editor.exe
```

The one-file executable bundles Python, the GVAS parser, and the logo assets, so another Windows PC does not need VSCodium or a separate Python installation. Building needs an internet connection the first time to install PyInstaller. The executable is Windows-specific.

To edit in VSCodium, open the `SinSpire Save Editor` folder. The included `.vscode/launch.json` provides an F5 launch configuration when the Python extension is installed.

## What it can edit

- Numeric player fields such as health, stamina, sanity, shards, keys, money, lust, and playtime
- Skill levels
- Numeric values in `CurrentStats`, weapon ammo, consumables, unique items, and `WorldEvents`
- Weapon records in a dedicated table, including weapon name, durability, loaded ammo, and class; durability and loaded ammo can be edited, and **Repair all to 100** sets durability only while leaving ammo unchanged

Perks and read notes are shown for reference. The program saves to a different file and refuses to overwrite the save you opened.

If the file is damaged enough that its GVAS structure cannot be parsed, this version cannot recover data from it. The bundled parser source is under `pygvas/`; its license is in `PARSER-LICENSE`.
