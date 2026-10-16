from __future__ import annotations

import os
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from pygvas.gvas_file import GVASFile


NUMERIC_TYPES = {"IntProperty", "DoubleProperty", "FloatProperty", "Int64Property", "UInt64Property"}
MAP_PREFIXES = ("CurrentStats", "CurrentWeaponAmmo", "CurrentConsumables", "UniqueItems")
APP_VERSION = "0.1.0"
DEVELOPER_PATREON_URL = "https://www.patreon.com/c/KrasueGames47/home"
COLORS = {
    "window": "#100e0d",
    "panel": "#191614",
    "panel_raised": "#25201b",
    "line": "#4b4034",
    "text": "#eee6d8",
    "muted": "#b8aa96",
    "accent": "#c99a56",
    "accent_hover": "#e0b86f",
    "select": "#4a2928",
    "input": "#130f0d",
}


def find_prop(props: dict, prefix: str):
    return next(((key, value) for key, value in props.items() if key.startswith(prefix + "_")), None)


def nice_name(key: str) -> str:
    return key.split("_")[0]


class SaveEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sin Spire Save Editor")
        icon_path = Path(__file__).resolve().with_name("sinspire_icon.ico")
        try:
            self.iconbitmap(default=str(icon_path))
            self.iconbitmap(str(icon_path))
        except tk.TclError:
            png_icon = Path(__file__).resolve().with_name("sinspire_icon_small.png")
            if png_icon.exists():
                self._app_icon = tk.PhotoImage(file=str(png_icon))
                self.iconphoto(True, self._app_icon)
        self.geometry("1240x840")
        self.minsize(960, 650)
        self.configure(background=COLORS["window"])
        self.source: Path | None = None
        self.save: GVASFile | None = None
        self.document: dict | None = None
        self.tables: list[dict] = []
        self._style()
        self._build()
        self.after(150, self._show_first_run_warning)

    @staticmethod
    def _first_run_marker() -> Path:
        local_app_data = os.environ.get("LOCALAPPDATA")
        base = Path(local_app_data) if local_app_data else Path.home() / ".local" / "share"
        return base / "SinSpireSaveEditor" / "first_run_acknowledged"

    def _show_first_run_warning(self):
        marker = self._first_run_marker()
        if marker.exists():
            return

        understood = messagebox.askyesno(
            "Important: Protect your save",
            "Please make careful, reasonable edits. Incorrect or unsupported changes may make a save unusable or cause lost progress.\n\n"
            "Back up your original save before editing, and use Save Edited Copy so the imported file stays untouched.\n\n"
            "You are responsible for the changes you make. This tool cannot guarantee that modified saves will work or recover a save damaged by editing.\n\n"
            "Do you understand and want to continue?",
            icon="warning",
            parent=self,
        )
        if not understood:
            self.destroy()
            return

        try:
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text("Acknowledged\n", encoding="utf-8")
        except OSError:
            # If preferences cannot be written, still let the user use the app.
            pass

    def _style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(".", background=COLORS["window"], foreground=COLORS["text"], font=("Segoe UI", 10))
        style.configure("App.TFrame", background=COLORS["window"])
        style.configure("Card.TFrame", background=COLORS["panel"], borderwidth=1, relief="solid", bordercolor=COLORS["line"])
        style.configure("Header.TFrame", background=COLORS["window"])
        style.configure("Title.TLabel", background=COLORS["window"], foreground=COLORS["text"], font=("Segoe UI Semibold", 23))
        style.configure("Kicker.TLabel", background=COLORS["window"], foreground=COLORS["accent"], font=("Segoe UI Semibold", 9))
        style.configure("Credit.TLabel", background=COLORS["window"], foreground=COLORS["muted"], font=("Segoe UI", 8))
        style.configure("Subtitle.TLabel", background=COLORS["window"], foreground=COLORS["muted"], font=("Segoe UI", 10))
        style.configure("Hint.TLabel", background=COLORS["panel"], foreground=COLORS["muted"], font=("Segoe UI", 9))
        style.configure("File.TLabel", background=COLORS["panel"], foreground=COLORS["text"], font=("Segoe UI Semibold", 10))
        style.configure("Status.TLabel", background=COLORS["window"], foreground=COLORS["accent"], font=("Segoe UI", 9))
        style.configure("TButton", background=COLORS["panel_raised"], foreground=COLORS["text"], padding=(14, 9), borderwidth=0, focusthickness=0)
        style.map("TButton", background=[("active", "#352a20"), ("disabled", COLORS["panel"])], foreground=[("disabled", "#71665a")])
        style.configure("Accent.TButton", background=COLORS["accent"], foreground=COLORS["window"], font=("Segoe UI Semibold", 10), padding=(16, 10))
        style.map("Accent.TButton", background=[("active", COLORS["accent_hover"]), ("disabled", "#51483b")], foreground=[("disabled", "#201a14")])
        style.configure("Treeview", background=COLORS["input"], fieldbackground=COLORS["input"], foreground=COLORS["text"], rowheight=34, font=("Segoe UI", 10), borderwidth=0, relief="flat")
        style.map("Treeview", background=[("selected", COLORS["select"])], foreground=[("selected", COLORS["accent"])])
        style.configure("Treeview.Heading", background=COLORS["panel_raised"], foreground=COLORS["muted"], font=("Segoe UI Semibold", 9), padding=(10, 10), relief="flat")
        style.map("Treeview.Heading", background=[("active", "#352a20")])
        style.configure("Helper.Treeview", background=COLORS["input"], fieldbackground=COLORS["input"], foreground=COLORS["text"], rowheight=21, font=("Segoe UI", 9), borderwidth=0, relief="flat")
        style.configure("Helper.Treeview.Heading", background=COLORS["panel_raised"], foreground=COLORS["muted"], font=("Segoe UI Semibold", 9), padding=(8, 5), relief="flat")
        style.map("Helper.Treeview", background=[("selected", COLORS["select"])], foreground=[("selected", COLORS["accent"])])
        style.map("Helper.Treeview.Heading", background=[("active", "#352a20")])
        style.configure("TNotebook", background=COLORS["window"], borderwidth=0, tabmargins=(0, 0, 0, 0))
        style.configure("TNotebook.Tab", background=COLORS["window"], foreground=COLORS["muted"], padding=(16, 11), font=("Segoe UI Semibold", 10), borderwidth=0)
        style.map("TNotebook.Tab", background=[("selected", COLORS["panel"])], foreground=[("selected", COLORS["accent"])])
        style.configure("TNotebook.Tab", background=COLORS["window"], foreground=COLORS["muted"], padding=(14, 10), font=("Segoe UI", 9), borderwidth=0)
        style.map("TNotebook.Tab", background=[("selected", COLORS["panel"])], foreground=[("selected", COLORS["accent"])], font=[("selected", ("Segoe UI Semibold", 11))], padding=[("selected", (17, 11))])
        style.configure("TScrollbar", background=COLORS["panel_raised"], troughcolor=COLORS["input"], bordercolor=COLORS["input"], arrowcolor=COLORS["muted"])
        style.configure("TEntry", fieldbackground=COLORS["input"], foreground=COLORS["text"], insertcolor=COLORS["text"], bordercolor=COLORS["line"], padding=5)

    def _build(self):
        root = ttk.Frame(self, padding=(26, 14, 26, 10), style="App.TFrame")
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(2, weight=1)
        top = ttk.Frame(root, style="Header.TFrame")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        logo_path = Path(__file__).resolve().with_name("sinspire_logo_header.png")
        if logo_path.exists():
            self._header_logo = tk.PhotoImage(file=str(logo_path))
            ttk.Label(top, image=self._header_logo, background=COLORS["window"]).pack(side="left", padx=(0, 18))
        title_block = ttk.Frame(top, style="Header.TFrame")
        title_block.pack(side="left", fill="x", expand=True)
        ttk.Label(title_block, text=f"SAVE WORKSHOP  /  SIN SPIRE   ·   v{APP_VERSION}", style="Kicker.TLabel").pack(anchor="w", pady=(0, 4))
        ttk.Label(title_block, text="Save editor", style="Title.TLabel").pack(anchor="w")
        ttk.Label(title_block, text="Inspect your profile and Edit the progress you want to keep.", style="Subtitle.TLabel").pack(anchor="w", pady=(3, 0))
        ttk.Label(title_block, text="Sin Spire created by Krasue Games  ·  Save editor created by LoseMyXelf (LMX)", style="Credit.TLabel").pack(anchor="w", pady=(4, 0))
        ttk.Button(top, text="＋  Open save", command=self.open_save, style="Accent.TButton").pack(side="right", anchor="center", padx=(18, 0))

        file_card = ttk.Frame(root, padding=(14, 8), style="Card.TFrame")
        file_card.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        ttk.Label(file_card, text="CURRENT SAVE", style="Hint.TLabel").pack(anchor="w")
        self.file_label = ttk.Label(file_card, text="No save loaded  ·  Choose a .sav file to begin", style="File.TLabel")
        self.file_label.pack(fill="x", anchor="w", pady=(4, 0))

        self.notebook = ttk.Notebook(root)
        self.notebook.grid(row=2, column=0, sticky="nsew")
        self.player_tab = ttk.Frame(self.notebook, padding=12, style="App.TFrame")
        self.skills_tab = ttk.Frame(self.notebook, padding=12, style="App.TFrame")
        self.data_tab = ttk.Frame(self.notebook, padding=12, style="App.TFrame")
        self.weapons_tab = ttk.Frame(self.notebook, padding=12, style="App.TFrame")
        self.reference_tab = ttk.Frame(self.notebook, padding=12, style="App.TFrame")
        self.helper_tab = ttk.Frame(self.notebook, padding=12, style="App.TFrame")
        self.info_tab = ttk.Frame(self.notebook, padding=12, style="App.TFrame")
        self.notebook.add(self.player_tab, text="Player values")
        self.notebook.add(self.skills_tab, text="Skills")
        self.notebook.add(self.data_tab, text="Inventory & progress")
        self.notebook.add(self.weapons_tab, text="Weapons")
        self.notebook.add(self.reference_tab, text="Other saved data")
        self.notebook.add(self.helper_tab, text="Helper")
        self.notebook.add(self.info_tab, text="Info")
        self.player_context = self._make_table(self.player_tab, "Player values are editable. Double-click a value to change it.", ("field", "value", "type"), (410, 250, 200), ("value",))
        self.skill_context = self._make_table(self.skills_tab, "Double-click a skill level to edit it.", ("skill", "id", "level"), (390, 350, 170), ("level",))
        weapons_toolbar = ttk.Frame(self.weapons_tab, style="App.TFrame")
        weapons_toolbar.pack(fill="x", pady=(0, 8))
        self.repair_weapons_button = ttk.Button(
            weapons_toolbar,
            text="Repair all to 100  →",
            command=self._repair_all_weapons,
            state="disabled",
            style="Accent.TButton",
        )
        self.repair_weapons_button.pack(side="right")
        self.weapons_context = self._make_table(self.weapons_tab, "Double-click durability or loaded ammo to edit it. Repair all changes durability only; loaded ammo is left untouched.", ("name", "durability", "ammo", "class"), (230, 150, 140, 500), ("durability", "ammo"))
        self.reference_context = self._make_table(self.reference_tab, "Other collections are displayed for reference.", ("category", "entries"), (350, 700), ())
        self._build_helper()
        self._build_info()

        data_top = ttk.Frame(self.data_tab, style="Card.TFrame", padding=10)
        data_top.pack(fill="both", expand=True)
        self.data_notebook = ttk.Notebook(data_top)
        self.data_notebook.pack(fill="both", expand=True)
        self.data_tables: dict[str, dict] = {}
        footer = ttk.Frame(root, style="App.TFrame")
        footer.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        footer_left = ttk.Frame(footer, style="App.TFrame")
        footer_left.pack(side="left", fill="x", expand=True)
        self.status = ttk.Label(footer_left, text="Open a save to inspect and edit it.", style="Status.TLabel", anchor="w")
        self.status.pack(fill="x", pady=(0, 4))
        ttk.Label(footer_left, text="Your source save stays untouched. Edits are written to a separate copy.", style="Subtitle.TLabel").pack(anchor="w")
        self.save_button = ttk.Button(footer, text="Save edited copy  →", command=self.save_copy, state="disabled", style="Accent.TButton")
        self.save_button.pack(side="right")

    def _build_helper(self):
        ttk.Label(self.helper_tab, text="A quick guide to the save editor", font=("Segoe UI Semibold", 16), background=COLORS["window"], foreground=COLORS["text"]).pack(anchor="w", pady=(0, 4))
        ttk.Label(self.helper_tab, text="Unreal saves store values together with a type that tells the game how to read them.", style="Subtitle.TLabel").pack(anchor="w", pady=(0, 14))

        card = ttk.Frame(self.helper_tab, style="Card.TFrame", padding=8)
        card.pack(fill="both", expand=True)
        types = ttk.Treeview(card, columns=("kind", "meaning", "example"), show="headings", selectmode="none", height=11, style="Helper.Treeview")
        types.heading("kind", text="Storage type")
        types.heading("meaning", text="What it means")
        types.heading("example", text="Example in this save")
        types.column("kind", width=180, anchor="w", stretch=False)
        types.column("meaning", width=470, anchor="w", stretch=True)
        types.column("example", width=300, anchor="w", stretch=True)
        type_rows = [
            ("IntProperty", "A whole number.", "Money, keys, skill levels"),
            ("DoubleProperty", "A decimal number stored with high precision.", "Health, stamina, durability"),
            ("FloatProperty", "A decimal number, usually stored with less precision than Double.", "Some gameplay measurements"),
            ("NameProperty", "A short game identifier; it may look like a code or internal name.", "VIT, Pistol, Flashlight"),
            ("StrProperty", "A regular text string.", "Map and event names"),
            ("TextProperty", "Display text intended to be shown to the player.", "Skill names and descriptions"),
            ("ArrayProperty", "An ordered list of values or records.", "Skills, weapons, perks"),
            ("MapProperty", "A collection of key/value pairs.", "Ammo by type, inventory counts, world flags"),
            ("StructProperty", "A group of related fields stored as one record.", "A weapon's name, durability, and ammo"),
            ("ObjectProperty", "A reference to a game object or blueprint class.", "The weapon's internal class path"),
            ("DateTime", "A saved date and time value.", "The save timestamp"),
        ]
        for i, row in enumerate(type_rows):
            types.insert("", "end", values=row, tags=("even" if i % 2 == 0 else "odd",))
        types.tag_configure("even", background=COLORS["input"])
        types.tag_configure("odd", background=COLORS["panel"])
        type_scroll = ttk.Scrollbar(card, orient="vertical", command=types.yview)
        types.configure(yscrollcommand=type_scroll.set)
        types.pack(side="left", fill="both", expand=True)
        type_scroll.pack(side="right", fill="y")

        notes = ttk.Frame(self.helper_tab, style="App.TFrame")
        notes.pack(fill="x", pady=(8, 0))
        ttk.Label(notes, text="Editing", font=("Segoe UI Semibold", 11), background=COLORS["window"], foreground=COLORS["accent"]).pack(anchor="w")
        ttk.Label(notes, text="Double-click a numeric value to edit it. Weapon durability and loaded ammo are editable in the Weapons tab; inventory and progress values are in their own subtabs.", style="Subtitle.TLabel", wraplength=1060).pack(anchor="w", pady=(3, 7))
        ttk.Label(notes, text="Saving", font=("Segoe UI Semibold", 11), background=COLORS["window"], foreground=COLORS["accent"]).pack(anchor="w")
        ttk.Label(notes, text="Choose an output folder to save a separate copy with the original filename. The app opens that folder when saving finishes; your imported save stays untouched.", style="Subtitle.TLabel", wraplength=1060).pack(anchor="w", pady=(3, 0))

    def _build_info(self):
        ttk.Label(self.info_tab, text="About this save editor", font=("Segoe UI Semibold", 16), background=COLORS["window"], foreground=COLORS["text"]).pack(anchor="w", pady=(0, 4))
        ttk.Label(self.info_tab, text="Project details and attribution", style="Subtitle.TLabel").pack(anchor="w", pady=(0, 14))

        card = ttk.Frame(self.info_tab, style="Card.TFrame", padding=18)
        card.pack(fill="x", anchor="n")
        ttk.Label(card, text="UNOFFICIAL COMMUNITY TOOL", style="Kicker.TLabel").pack(anchor="w", pady=(0, 10))
        ttk.Label(
            card,
            text="This save editor is an independent project created by LoseMyXelf (LMX). It is not an official Sin Spire product, and its creator is not affiliated with, sponsored by, or endorsed by Krasue Games.",
            style="Subtitle.TLabel",
            wraplength=1000,
            justify="left",
        ).pack(anchor="w")

        credits = ttk.Frame(self.info_tab, style="Card.TFrame", padding=18)
        credits.pack(fill="x", anchor="n", pady=(12, 0))
        ttk.Label(credits, text="CREDITS", style="Kicker.TLabel").pack(anchor="w", pady=(0, 10))
        developer_credit = ttk.Frame(credits, style="App.TFrame")
        developer_credit.pack(fill="x", pady=(0, 5))
        ttk.Label(developer_credit, text="Sin Spire — created by Krasue Games", style="Subtitle.TLabel").pack(side="left", anchor="w", expand=True)
        ttk.Button(
            developer_credit,
            text="Krasue Games on Patreon  →",
            command=lambda: webbrowser.open(DEVELOPER_PATREON_URL),
            style="Accent.TButton",
        ).pack(side="right")
        ttk.Label(credits, text="Save editor — created by LoseMyXelf (LMX)", style="Subtitle.TLabel").pack(anchor="w")

    def _make_table(self, parent, hint, columns, widths, editable):
        ttk.Label(parent, text=hint, style="Subtitle.TLabel").pack(anchor="w", pady=(0, 10))
        wrap = ttk.Frame(parent, style="Card.TFrame", padding=8)
        wrap.pack(fill="both", expand=True)
        tree = ttk.Treeview(wrap, columns=columns, show="headings", selectmode="browse")
        for col, width in zip(columns, widths):
            tree.heading(col, text={"field": "Player field", "skill": "Skill", "id": "Code", "level": "Level", "value": "Value", "type": "Storage type"}.get(col, col.title()))
            tree.column(col, width=width, anchor="w" if col in ("field", "skill", "id", "type", "name", "class", "key", "category", "entries") else "e", stretch=(col not in ("type", "class")))
        ybar = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=ybar.set)
        tree.pack(side="left", fill="both", expand=True)
        ybar.pack(side="right", fill="y")
        context = {"tree": tree, "editable": set(editable), "rows": {}}
        self.tables.append(context)
        tree.bind("<Double-1>", lambda event, ctx=context: self._edit_cell(event, ctx))
        return context

    def _edit_cell(self, event, context):
        tree = context["tree"]
        if tree.identify_region(event.x, event.y) != "cell":
            return
        row = tree.identify_row(event.y)
        col_id = tree.identify_column(event.x)
        col_idx = int(col_id[1:]) - 1
        columns = tree["columns"]
        if not row or columns[col_idx] not in context["editable"]:
            return
        box = tree.bbox(row, col_id)
        if not box:
            return
        x, y, width, height = box
        entry = ttk.Entry(tree)
        entry.place(x=x, y=y, width=width, height=height)
        entry.insert(0, tree.set(row, columns[col_idx]))
        entry.select_range(0, "end")
        entry.focus_set()

        def commit(_event=None):
            val = entry.get().strip()
            row_data = context["rows"].get(row)
            try:
                column_name = columns[col_idx]
                prop = row_data.get(column_name) if row_data and column_name in row_data else None
                number_type = row_data.get("number_type") if row_data and "number_type" in row_data else (prop.get("type") if isinstance(prop, dict) else None)
                parsed = float(val) if number_type in ("DoubleProperty", "FloatProperty") else int(val)
                if not (-1e12 < parsed < 1e12):
                    raise ValueError
                if isinstance(parsed, float) and parsed.is_integer() and number_type not in ("DoubleProperty", "FloatProperty"):
                    parsed = int(parsed)
                if row_data and "setter" in row_data:
                    row_data["setter"](parsed)
                elif isinstance(prop, dict):
                    prop["value"] = parsed
                else:
                    raise ValueError
                vals = list(tree.item(row, "values"))
                vals[col_idx] = val
                tree.item(row, values=vals)
                self.status.configure(text="Unsaved edits. Choose Save Edited Copy when ready.")
            except (ValueError, TypeError):
                messagebox.showerror("Invalid value", "Enter a valid number for this field.", parent=self)
            entry.destroy()

        entry.bind("<Return>", commit)
        entry.bind("<FocusOut>", commit)
        entry.bind("<Escape>", lambda _e: entry.destroy())

    def _repair_all_weapons(self):
        if not self.save:
            return

        context = self.weapons_context
        tree = context["tree"]
        updates = []
        for iid, row in context["rows"].items():
            prop = row.get("durability")
            if isinstance(prop, dict) and "value" in prop and prop.get("type") in NUMERIC_TYPES:
                updates.append((iid, prop))

        if not updates:
            messagebox.showinfo("Nothing to repair", "No weapon durability values were found in this save.", parent=self)
            return

        if not messagebox.askyesno(
            "Repair all weapons?",
            f"Set durability to 100 for all {len(updates)} weapon(s) with a durability value?\n\n"
            "Loaded ammo will be left untouched.",
            icon="warning",
            parent=self,
        ):
            return

        durability_index = list(tree["columns"]).index("durability")
        for iid, prop in updates:
            new_value = 100.0 if prop.get("type") in ("DoubleProperty", "FloatProperty") else 100
            prop["value"] = new_value
            values = list(tree.item(iid, "values"))
            values[durability_index] = f"{new_value:.1f}" if isinstance(new_value, float) else new_value
            tree.item(iid, values=values)

        self.status.configure(text="All available weapon durability values set to 100. Loaded ammo was left unchanged. Save an edited copy when ready.")

    def open_save(self):
        name = filedialog.askopenfilename(title="Open Sin Spire save", filetypes=[("Save files", "*.sav *.save"), ("All files", "*.*")])
        if not name:
            return
        try:
            candidate = Path(name).resolve(strict=True)
            loaded = GVASFile.deserialize_gvas_file(str(candidate))
            doc = loaded.serialize_to_json()
            if "PlayerState" not in doc.get("properties", {}):
                raise ValueError("This save does not contain the expected Sin Spire PlayerState data.")
            self.save, self.document, self.source = loaded, doc, candidate
            self._populate()
            fmt = loaded.game_file_format
            game_version = getattr(fmt.game_version, "name", str(fmt.game_version))
            compression_type = getattr(fmt.compression_type, "name", str(fmt.compression_type))
            version_labels = {
                "DEFAULT": "Default format",
                "PALWORLD": "Palworld format",
                "UNKNOWN": "Unknown format",
            }
            compression_labels = {
                "NONE": "Uncompressed",
                "ZLIB": "Zlib compressed",
                "ZLIB_TWICE": "Zlib compressed twice",
                "PLZ": "PLZ compression",
                "UNKNOWN": "Unknown compression",
            }
            version_text = version_labels.get(game_version, game_version.replace("_", " ").title())
            compression_text = compression_labels.get(compression_type, compression_type.replace("_", " ").title())
            self.file_label.configure(text=f"{candidate}    ·    {version_text}  ·  {compression_text}")
            self.status.configure(text="Save loaded. Edit values, then save a separate copy.")
            self.save_button.configure(state="normal")
        except Exception as exc:
            messagebox.showerror("Could not open save", f"The file could not be read as a supported GVAS save.\n\n{exc}", parent=self)

    def _clear(self, tree):
        tree.delete(*tree.get_children())
        context = next((ctx for ctx in self.tables if ctx["tree"] is tree), None)
        if context:
            context["rows"].clear()

    def _add_row(self, context, iid, values, setter, number_type=None):
        tree = context["tree"]
        tree.insert("", "end", iid=iid, values=values)
        context["rows"][iid] = {"setter": setter, "number_type": number_type}

    def _populate(self):
        for context in self.tables:
            self._clear(context["tree"])
        self.tables = [self.player_context, self.skill_context, self.weapons_context, self.reference_context]
        for tab in self.data_notebook.tabs():
            self.data_notebook.forget(tab)
        self.data_tables.clear()
        props = self.document["properties"]["PlayerState"]["value"]

        player_ctx = self.player_context
        for key, prop in props.items():
            if prop.get("type") in NUMERIC_TYPES and "value" in prop:
                self._add_row(player_ctx, key, (nice_name(key), prop["value"], prop["type"]), lambda value, p=prop: p.__setitem__("value", value), prop["type"])
        for key, prop in self.document["properties"].items():
            if key != "PlayerState" and prop.get("type") in NUMERIC_TYPES and "value" in prop:
                self._add_row(player_ctx, "save_" + key, ("Save / " + key, prop["value"], prop["type"]), lambda value, p=prop: p.__setitem__("value", value), prop["type"])

        skill_ctx = self.skill_context
        skills = find_prop(props, "CurrentSkills")
        if skills:
            for i, item in enumerate(skills[1].get("values", [])):
                row = item.get("value", {})
                name = next((p.get("history", {}).get("source_string") for k, p in row.items() if k.startswith("Name_") and p.get("type") == "TextProperty"), "Skill")
                code = next((p.get("value", "") for k, p in row.items() if k.startswith("ID_") and p.get("type") == "NameProperty"), "")
                count_key = next((k for k, p in row.items() if k.startswith("Count_") and p.get("type") == "IntProperty"), None)
                if count_key:
                    counter = row[count_key]
                    self._add_row(skill_ctx, str(i), (name, code, counter["value"]), lambda value, p=counter: p.__setitem__("value", value), "IntProperty")

        for prefix in MAP_PREFIXES:
            found = find_prop(props, prefix)
            if found:
                self._add_map_tab(nice_name(found[0]), found[1])
        world_events = self.document["properties"].get("WorldEvents")
        if world_events and world_events.get("type") == "MapProperty":
            self._add_map_tab("WorldEvents", world_events)

        ref_ctx = self.reference_context
        weapon_ctx = self.weapons_context
        weapon_tree = weapon_ctx["tree"]
        weapon_tree.heading("name", text="Weapon")
        weapon_tree.heading("durability", text="Durability")
        weapon_tree.heading("ammo", text="Loaded ammo")
        weapon_tree.heading("class", text="Class")
        weapons = find_prop(props, "CurrentWeapons")
        if weapons:
            for i, item in enumerate(weapons[1].get("values", [])):
                record = item.get("value", {}) if isinstance(item, dict) else {}
                weapon_id = next((v.get("value", "") for k, v in record.items() if k.startswith("WeaponID_")), "Unknown weapon")
                durability = next((v for k, v in record.items() if k.startswith("Durability_")), None)
                ammo = next((v for k, v in record.items() if k.startswith("CurrentAmmo_")), None)
                class_prop = next((v for k, v in record.items() if k.startswith("Class_")), {})
                durability_value = durability.get("value", "") if durability else ""
                ammo_value = ammo.get("value", "") if ammo else ""
                class_value = class_prop.get("value", "")
                class_short = class_value.rsplit("/", 1)[-1].replace("_C", "") if class_value else ""
                weapon_tree.insert("", "end", iid=str(i), values=(weapon_id, f"{durability_value:.1f}" if isinstance(durability_value, (int, float)) else durability_value, ammo_value, class_short))
                weapon_ctx["rows"][str(i)] = {"durability": durability, "ammo": ammo}
        self.repair_weapons_button.configure(state="normal" if weapon_tree.get_children() else "disabled")
        ref_tree = ref_ctx["tree"]
        ref_tree.configure(columns=("category", "entries"))
        for col, title, width in (("category", "Saved collection", 350), ("entries", "Contents", 700)):
            ref_tree.heading(col, text=title)
            ref_tree.column(col, width=width, anchor="w")
        arrays = ("CurrentPerks", "ReadNotes")
        for label in arrays:
            found = find_prop(props, label)
            if not found:
                continue
            vals = []
            for item in found[1].get("values", []):
                if isinstance(item, str):
                    vals.append(item)
                    continue
                if isinstance(item, dict):
                    raw = item.get("value")
                    if isinstance(raw, str):
                        vals.append(raw)
                    elif isinstance(raw, dict):
                        vals.append(raw.get("value", ""))
            ref_tree.insert("", "end", values=(label, ", ".join(map(str, vals))))
        for label in ("MapName", "SavedDiff", "Date"):
            value = self.document["properties"].get(label)
            if value:
                shown = value.get("value", value.get("comment", ""))
                if isinstance(shown, dict):
                    shown = shown.get("comment", shown.get("datetime", ""))
                ref_tree.insert("", "end", values=(label, str(shown)))
        ref_ctx["editable"].clear()
        self.data_notebook.select(0) if self.data_notebook.tabs() else None

    def _add_map_tab(self, name, prop):
        tab = ttk.Frame(self.data_notebook, padding=10)
        self.data_notebook.add(tab, text=name)
        context = self._make_table(tab, "Double-click a numeric value to edit it. Names and event keys stay unchanged.", ("key", "value", "type"), (550, 220, 180), ("value",))
        self.data_tables[name] = context
        for i, pair in enumerate(prop.get("values", [])):
            if len(pair) != 2:
                continue
            key_prop, value_prop = pair
            key = key_prop.get("value", "")
            value = value_prop.get("value", "")
            if value_prop.get("type") in NUMERIC_TYPES:
                self._add_row(context, str(i), (key, value, value_prop.get("type")), lambda new, p=value_prop: p.__setitem__("value", new), value_prop.get("type"))

    def save_copy(self):
        if not self.save or not self.source:
            return
        output_dir = filedialog.askdirectory(
            title="Choose a folder for the edited save",
            initialdir=str(self.source.parent),
            mustexist=True,
        )
        if not output_dir:
            return
        dest = (Path(output_dir).expanduser().resolve() / self.source.name).resolve()
        if os.path.normcase(str(dest)) == os.path.normcase(str(self.source.resolve())):
            messagebox.showerror(
                "Choose another folder",
                "The selected folder contains the imported save. Choose a different folder to keep the original untouched.\n\n"
                f"The edited copy will be named {self.source.name}.",
                parent=self,
            )
            return
        if dest.exists() and not messagebox.askyesno("Replace existing file?", f"{dest} already exists. Replace it?", parent=self):
            return
        temp = dest.with_name(dest.name + ".tmp")
        try:
            updated = GVASFile.deserialize_json(self.document)
            updated.serialize_to_gvas_file(str(temp))
            os.replace(temp, dest)
            self.status.configure(text=f"Saved edited copy: {dest}")
            try:
                if os.name == "nt":
                    os.startfile(str(dest.parent))
                else:
                    webbrowser.open(dest.parent.as_uri())
            except OSError as exc:
                messagebox.showwarning(
                    "Save complete",
                    f"The edited save was written to:\n{dest}\n\n"
                    f"Your original save is unchanged, but the output folder could not be opened.\n{exc}",
                    parent=self,
                )
                return
            messagebox.showinfo(
                "Save complete",
                f"Edited save written to:\n{dest}\n\n"
                "The output folder has been opened. Your original save is unchanged.",
                parent=self,
            )
        except Exception as exc:
            messagebox.showerror("Could not save", f"The edited copy could not be written.\n\n{exc}", parent=self)
        finally:
            if temp.exists():
                temp.unlink()


if __name__ == "__main__":
    SaveEditor().mainloop()
