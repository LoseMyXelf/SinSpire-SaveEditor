# Sin Spire Save Editor

An unofficial Windows desktop utility for inspecting and editing supported **Sin Spire** Unreal Engine `.sav` files. It is written in Python and uses a bundled GVAS parser.

Current version: **0.2.0**.

> **Unofficial community project:** This tool is not made by, affiliated with, or endorsed by Krasue Games. Use it at your own risk. Keep a backup of your save before editing.

## Features

- Open and inspect a `.sav` file.
- Edit player values, skill levels, inventory and progress values, and supported weapon fields.
- Repair all weapons by setting durability to 100 without changing loaded ammunition.
- Create a timestamped, byte-for-byte backup of the original save.
- Save an edited copy to a folder you choose. The source save is left untouched, and the copy keeps the original filename.
- Browse help about save storage types and project information in the app.

The app can only edit files its bundled parser can read. It cannot reconstruct data from a save whose structure is too damaged to parse.

## Run from source

### Requirements

- Windows 10 or later
- Python 3.10 or later, with Tkinter

### Start the app

1. Download or clone this repository.
2. Open PowerShell in the project folder.
3. Install the Python dependency:

   ```powershell
   py -3 -m pip install -r requirements.txt
   ```

4. Start the app:

   ```powershell
   py -3 .\save_editor_gui.py
   ```

   You can also double-click `launch_editor.bat`.

5. Choose **Open / Import .sav**, make your edits, then select **Save edited copy**. Choose the destination folder. The app writes a separate file with the original filename and opens the destination folder when finished. Select that copy in the game to load it.

Close the game before editing a save. Keep your own backup in case the game rejects an edited file.

## Build the Windows executable

Create the project virtual environment once, then run the build script:

```powershell
py -3 -m venv .venv
```

Now double-click `build_exe.bat` from the project folder. It installs the build dependencies in `.venv` and creates:

```text
dist\Sin Spire Save Editor.exe
```

The executable is for Windows. The first build requires an internet connection to install PyInstaller.

## Development

Open the project folder in VSCodium. The optional `.vscode/launch.json` configuration can launch the app with F5 when the Python extension is installed.

## Credits and project status

- **Sin Spire** was created by Krasue Games.
- **Save editor** created by LoseMyXelf (LMX).
- The save editor is an independent community project and is not an official game tool.

## License information

The bundled parser in `pygvas/` includes its own license. See [`pygvas/LICENSE`](pygvas/LICENSE) for the full text and attribution. That license file belongs with the parser; it is not a license chosen for the save editor's own code. No separate license for the save editor's code has been selected yet.

The game name, logo, and artwork are associated with Sin Spire and their respective rights holders; they are not licensed by the parser's license.
