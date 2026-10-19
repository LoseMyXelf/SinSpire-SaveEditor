# Sin Spire Save Editor

An unofficial Windows desktop tool by **LoseMyXelf (LMX)** for viewing and editing supported *Sin Spire* save files. Open a `.sav` file, adjust commonly used player and progression values, and save your changes as a separate copy.


**Current version:** 0.2.0

> This is an independent community project. It is not made by, affiliated with, sponsored by, or endorsed by Krasue Games. Back up your save before editing; unsupported changes may make a save unusable.

## Features

- **Simple mode** focuses on commonly used player values, skills, inventory and progress, and weapons.
- **Expert mode** reveals additional save data and technical details.
- Drag and drop a `.sav` file into the app, or click the drop area to choose one.
- Edit supported player values, skill levels, inventory and progress data, weapon durability, and loaded ammunition.
- Repair all weapon durability values to 100 without changing loaded ammunition.
- Create a timestamped, byte-for-byte backup of the source save.
- Save edits as a separate copy; the imported source file remains untouched.

The editor can only handle save structures supported by its bundled parser. It cannot restore data from a save that is too damaged to parse, and modified saves are not guaranteed to work in game.

## Download and run

Download the Windows executable from the project's [GitHub Releases](../../releases) page. The app does not require a Python installation.

To run from source, use Windows 10 or later with Python 3.10+ and Tkinter:

```powershell
py -3 -m pip install -r requirements.txt
py -3 .\save_editor_gui.py
```

You can also launch it by double-clicking `launch_editor.bat`.

## Build the Windows executable

Create the virtual environment once, then run the build script:

```powershell
py -3 -m venv .venv
```

Double-click `build_exe.bat`. It installs the build dependencies and creates:

```text
dist\Sin Spire Save Editor.exe
```

The first build requires an internet connection to install PyInstaller and dependencies.

## Credits and links

- *Sin Spire*, its game content, name, logo, and artwork are by **Krasue Games** and their respective rights holders. Visit the [Sin Spire Steam page](https://store.steampowered.com/app/3221770/Sin_Spire/) or [Krasue Games on Patreon](https://www.patreon.com/c/KrasueGames47/home).
- This save editor was created by **LoseMyXelf (LMX)**. It is an independent fan-made utility and is not an official game tool.
- The bundled `pygvas` parser includes a separate license and attribution: **Robin Eric Fredericksen, CC BY-NC-SA 4.0**. See [`pygvas/LICENSE`](pygvas/LICENSE) for the full terms. This applies to the parser material, not automatically to the save editor's own code.
- The app icon is original artwork created for this save editor; it is not an official *Sin Spire* asset.

No separate license has been selected for the save editor's own code. The game name, logo, and artwork are not licensed by this project or by the parser license; their inclusion here does not imply endorsement or ownership by the save editor author.
