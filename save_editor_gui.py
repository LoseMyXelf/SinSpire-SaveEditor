from __future__ import annotations

import os
import shutil
import tkinter as tk
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk
from PIL import Image
from tkinterdnd2 import DND_FILES, TkinterDnD
from pygvas.gvas_file import GVASFile


NUMERIC_TYPES = {"IntProperty", "DoubleProperty", "FloatProperty", "Int64Property", "UInt64Property"}
MAP_PREFIXES = ("CurrentConsumables", "CurrentWeaponAmmo", "CurrentStats", "UniqueItems")
FIELD_LABELS = {
    "CurrentWeapon": "Active weapon",
    "CurrentHealth": "Health",
    "CurrentStamina": "Stamina",
    "CurrentSanity": "Sanity",
    "CurrentShards": "Shards",
    "CurrentGoldKeys": "Gold keys",
    "CurrentSilverKeys": "Silver keys",
    "CurrentMoney": "Money",
    "CurrentLust": "Lust",
    "Playtime": "Play time",
    "SavedDiff": "Difficulty",
}
MAP_LABELS = {
    "CurrentStats": "Stats",
    "CurrentWeaponAmmo": "Weapon ammo",
    "CurrentConsumables": "Consumables",
    "UniqueItems": "Unique items",
    "WorldEvents": "World events",
}
PLAYER_FIELD_ORDER = (
    "CurrentHealth", "CurrentStamina", "CurrentSanity", "CurrentShards",
    "CurrentMoney", "CurrentGoldKeys", "CurrentSilverKeys", "CurrentWeapon",
    "CurrentLust", "Playtime", "SavedDiff",
)
SKILL_ORDER = ("Vitality", "Strength", "Stamina", "Agility", "Mind", "Infusion")
STATS_ORDER = ("Consumables Collected", "Containers Opened", "Equipment Found", "Notes Read", "Damage Taken")
REFERENCE_ORDER = ("MapName", "SavedDiff", "CurrentPerks", "ReadNotes", "Date")
APP_VERSION = "0.2.0"
DEVELOPER_PATREON_URL = "https://www.patreon.com/c/KrasueGames47/home"
SIN_SPIRE_STEAM_URL = "https://store.steampowered.com/app/3221770/Sin_Spire/"
COLORS = {
    "window": "#141316",
    "panel": "#211e23",
    "panel_raised": "#302b32",
    "line": "#41383f",
    "text": "#f2eee9",
    "muted": "#c0b8b5",
    "accent": "#74343b",
    "accent_hover": "#8e454c",
    "accent_soft": "#a9b49b",
    "select": "#3c2a32",
    "input": "#18171b",
}


def styled_frame(parent, style="App.TFrame", **kwargs):
    card = style == "Card.TFrame"
    kwargs.pop("padding", None)
    kwargs.pop("style", None)
    return ctk.CTkFrame(
        parent,
        fg_color=COLORS["panel"] if card else "transparent",
        corner_radius=16 if card else 0,
        border_width=1 if card else 0,
        border_color=COLORS["line"],
        **kwargs,
    )


def styled_label(parent, text, style="Subtitle.TLabel", **kwargs):
    defaults = {
        "Title.TLabel": (COLORS["text"], ("Segoe UI", 32, "bold")),
        "Kicker.TLabel": (COLORS["muted"], ("Segoe UI", 11, "bold")),
        "Credit.TLabel": (COLORS["muted"], ("Segoe UI", 11)),
        "Subtitle.TLabel": (COLORS["muted"], ("Segoe UI", 13)),
        "Hint.TLabel": (COLORS["muted"], ("Segoe UI", 11, "bold")),
        "File.TLabel": (COLORS["text"], ("Segoe UI", 13, "bold")),
        "Status.TLabel": (COLORS["accent_soft"], ("Segoe UI", 12, "bold")),
    }
    default_color, default_font = defaults.get(style, defaults["Subtitle.TLabel"])
    foreground = kwargs.pop("foreground", default_color)
    kwargs.pop("background", None)
    kwargs.pop("style", None)
    return ctk.CTkLabel(
        parent,
        text=text,
        text_color=foreground,
        fg_color="transparent",
        font=kwargs.pop("font", default_font),
        **kwargs,
    )


def find_prop(props: dict, prefix: str):
    return next(((key, value) for key, value in props.items() if key.startswith(prefix + "_")), None)


def nice_name(key: str) -> str:
    return key.split("_")[0]


def display_field_name(key: str) -> str:
    short_name = nice_name(key)
    return FIELD_LABELS.get(short_name, short_name.replace("_", " "))


def _order_index(value, order):
    """Return a known item's display priority; stable sorting leaves unknown items after it."""
    normalized = str(value).strip().casefold()
    return next((index for index, item in enumerate(order) if str(item).casefold() == normalized), len(order))


def format_number(value, number_type):
    if number_type in ("DoubleProperty", "FloatProperty") and isinstance(value, (int, float)):
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return value


class SaveEditor(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)
        self.title("Sin Spire Save Editor")
        icon_path = Path(__file__).resolve().with_name("sinspire_icon.ico")
        try:
            self.iconbitmap(default=str(icon_path))
            self.iconbitmap(str(icon_path))
        except tk.TclError:
            png_icon = Path(__file__).resolve().with_name("sinspire_icon.png")
            if png_icon.exists():
                self._app_icon = tk.PhotoImage(file=str(png_icon))
                self.iconphoto(True, self._app_icon)
        self.geometry("1240x840")
        self.minsize(960, 650)
        self.configure(fg_color=COLORS["window"])
        self.source: Path | None = None
        self.save: GVASFile | None = None
        self.document: dict | None = None
        self.tables: list[dict] = []
        self.expert_mode = False
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
        ctk.set_appearance_mode("dark")
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", background=COLORS["input"], fieldbackground=COLORS["input"], foreground=COLORS["text"], rowheight=42, font=("Segoe UI", 13), borderwidth=0, relief="flat")
        style.configure("Treeview", bordercolor=COLORS["line"], lightcolor=COLORS["line"], darkcolor=COLORS["line"])
        style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
        style.map("Treeview", background=[("selected", COLORS["select"])], foreground=[("selected", COLORS["text"])])
        style.configure("Treeview.Heading", background=COLORS["panel_raised"], foreground=COLORS["text"], font=("Segoe UI", 12, "bold"), padding=(12, 12), relief="flat")
        style.map("Treeview.Heading", background=[("active", COLORS["panel_raised"])])
        style.configure("Helper.Treeview", background=COLORS["input"], fieldbackground=COLORS["input"], foreground=COLORS["text"], rowheight=34, font=("Segoe UI", 12), borderwidth=0, relief="flat")
        style.configure("Helper.Treeview", bordercolor=COLORS["line"], lightcolor=COLORS["line"], darkcolor=COLORS["line"])
        style.layout("Helper.Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
        style.configure("Helper.Treeview.Heading", background=COLORS["panel_raised"], foreground=COLORS["text"], font=("Segoe UI", 12, "bold"), padding=(10, 11), relief="flat")
        style.map("Helper.Treeview", background=[("selected", COLORS["select"])], foreground=[("selected", COLORS["accent"])])
        style.configure("TScrollbar", background=COLORS["panel_raised"], troughcolor=COLORS["input"], bordercolor=COLORS["input"], arrowcolor=COLORS["muted"])
        style.configure("TEntry", fieldbackground=COLORS["input"], foreground=COLORS["text"], insertcolor=COLORS["text"], bordercolor=COLORS["line"], padding=5)

    def _build(self):
        root = styled_frame(self)
        root.pack(fill="both", expand=True, padx=18, pady=(14, 12))
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(2, weight=1)
        top = styled_frame(root)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        header_icon_path = Path(__file__).resolve().with_name("sinspire_icon.png")
        if header_icon_path.exists():
            header_icon = Image.open(header_icon_path)
            self._header_icon = ctk.CTkImage(light_image=header_icon, dark_image=header_icon, size=(64, 64))
            icon_badge = ctk.CTkFrame(top, fg_color=COLORS["panel_raised"], corner_radius=14, border_width=1, border_color=COLORS["line"])
            icon_badge.pack(side="left", padx=(0, 16), pady=4)
            ctk.CTkLabel(icon_badge, image=self._header_icon, text="", fg_color="transparent").pack(padx=5, pady=5)
        title_block = styled_frame(top)
        title_block.pack(side="left", fill="x", expand=True)
        styled_label(title_block, f"SAVE WORKSHOP  /  SIN SPIRE   ·   v{APP_VERSION}", "Kicker.TLabel").pack(anchor="w", pady=(0, 5))
        styled_label(title_block, "Save editor", "Title.TLabel").pack(anchor="w")
        styled_label(title_block, "Review your save and restore the progress you want to keep.", "Subtitle.TLabel").pack(anchor="w", pady=(4, 0))
        styled_label(title_block, "Sin Spire by Krasue Games  ·  Save editor by LoseMyXelf (LMX)", "Credit.TLabel").pack(anchor="w", pady=(5, 0))
        actions = styled_frame(top)
        actions.pack(side="right", anchor="center", padx=(18, 0))
        self.expert_mode_var = ctk.BooleanVar(value=False)
        self.expert_mode_switch = ctk.CTkSwitch(actions, text="Expert mode", variable=self.expert_mode_var, command=self._apply_display_mode, onvalue=True, offvalue=False, width=48, switch_width=38, switch_height=20, progress_color=COLORS["accent"], button_color=COLORS["text"], button_hover_color=COLORS["muted"], text_color=COLORS["muted"], font=("Segoe UI", 12))
        self.expert_mode_switch.pack(side="left", padx=(0, 16))
        self.backup_button = ctk.CTkButton(actions, text="Create backup", command=self.create_backup, width=156, height=46, corner_radius=12, fg_color=COLORS["panel_raised"], hover_color=COLORS["line"], text_color=COLORS["text"], font=("Segoe UI", 12), state="disabled")
        self.backup_button.pack(side="left", padx=(0, 8))
        ctk.CTkButton(actions, text="Open save", command=self.open_save, width=144, height=46, corner_radius=12, fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"], text_color=COLORS["text"], font=("Segoe UI", 12, "bold")).pack(side="left")

        file_card = styled_frame(root, "Card.TFrame")
        file_card.grid(row=1, column=0, sticky="ew", pady=(0, 14))
        save_header = styled_frame(file_card)
        save_header.pack(fill="x", padx=16, pady=(10, 0))
        styled_label(save_header, "CURRENT SAVE", "Hint.TLabel").pack(side="left", anchor="w")
        self.format_label = ctk.CTkLabel(save_header, text="WAITING FOR SAVE", text_color=COLORS["accent_soft"], fg_color=COLORS["panel_raised"], corner_radius=9, font=("Segoe UI", 10, "bold"), padx=10, pady=5)
        self.format_label.pack(side="right")
        self.file_label = styled_label(file_card, "No save loaded  ·  Choose a .sav file to begin", "File.TLabel", anchor="w", justify="left", wraplength=1100)
        self.file_label.pack(fill="x", anchor="w", padx=16, pady=(5, 12))

        self.notebook = ctk.CTkTabview(root, corner_radius=14, border_width=0, fg_color=COLORS["panel"], segmented_button_fg_color=COLORS["window"], segmented_button_selected_color=COLORS["panel_raised"], segmented_button_selected_hover_color=COLORS["panel_raised"], segmented_button_unselected_color=COLORS["window"], segmented_button_unselected_hover_color=COLORS["panel_raised"], text_color=COLORS["muted"], anchor="w")
        self.notebook.grid(row=2, column=0, sticky="nsew")
        for tab_name in ("Player values", "Skills", "Inventory & progress", "Weapons", "Other saved data", "Helper", "Info"):
            self.notebook.add(tab_name)
        self.notebook._segmented_button.configure(font=("Segoe UI", 13), height=40, corner_radius=10)
        self.player_tab = self.notebook.tab("Player values")
        self.skills_tab = self.notebook.tab("Skills")
        self.data_tab = self.notebook.tab("Inventory & progress")
        self.weapons_tab = self.notebook.tab("Weapons")
        self.reference_tab = self.notebook.tab("Other saved data")
        self.helper_tab = self.notebook.tab("Helper")
        self.info_tab = self.notebook.tab("Info")
        for tab in (self.player_tab, self.skills_tab, self.data_tab, self.weapons_tab, self.reference_tab, self.helper_tab, self.info_tab):
            tab.configure(fg_color="transparent")
        self.player_context = self._make_table(self.player_tab, "Character status", "Double-click a value to edit it.", ("field", "value", "type"), (410, 250, 200), ("value",))
        self.skill_context = self._make_table(self.skills_tab, "Skill progression", "Double-click a skill level to edit it.", ("skill", "id", "level"), (390, 350, 170), ("level",))
        self.weapons_context = self._make_table(self.weapons_tab, "Weapons", "Edit durability or loaded ammo. Repair all changes durability only.", ("name", "durability", "ammo", "class"), (230, 150, 140, 500), ("durability", "ammo"), action=("Repair all to 100", self._repair_all_weapons))
        self.reference_context = self._make_table(self.reference_tab, "Other saved data", "These collections are shown for reference and cannot be edited here.", ("category", "entries"), (350, 700), ())
        self._build_helper()
        self._build_info()

        data_top = styled_frame(self.data_tab)
        data_top.pack(fill="both", expand=True)
        self.data_notebook = ctk.CTkTabview(data_top, corner_radius=14, border_width=0, fg_color="transparent", segmented_button_fg_color=COLORS["panel"], segmented_button_selected_color=COLORS["accent"], segmented_button_selected_hover_color=COLORS["accent_hover"], segmented_button_unselected_color=COLORS["panel_raised"], segmented_button_unselected_hover_color=COLORS["line"], text_color=COLORS["text"], anchor="w")
        self.data_notebook.pack(fill="both", expand=True, padx=12, pady=(6, 12))
        self.data_notebook._segmented_button.configure(font=("Segoe UI", 13), height=40, corner_radius=10)
        self.data_tables: dict[str, dict] = {}
        self.data_tab_names: list[str] = []
        footer = styled_frame(root)
        footer.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        footer_left = styled_frame(footer)
        footer_left.pack(side="left", fill="x", expand=True)
        self.status = styled_label(footer_left, "Open a save to inspect and edit it.", "Status.TLabel", anchor="w")
        self.status.pack(fill="x", pady=(0, 4))
        styled_label(footer_left, "Your original save stays untouched. Edits are written to a separate copy.", "Subtitle.TLabel").pack(anchor="w")
        self.save_button = ctk.CTkButton(footer, text="Save edited copy", command=self.save_copy, width=204, height=46, corner_radius=12, fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"], text_color=COLORS["text"], font=("Segoe UI", 12, "bold"), state="disabled")
        self.save_button.pack(side="right")
        self._apply_display_mode()

    def _apply_display_mode(self):
        """Show the everyday editing tools by default; reveal technical sections in Expert mode."""
        self.expert_mode = bool(self.expert_mode_var.get())
        advanced_tabs = {"Other saved data", "Helper", "Info"}
        selected_tab = self.notebook.get()
        if not self.expert_mode and selected_tab in advanced_tabs:
            self.notebook.set("Player values")
        main_tabs = ["Player values", "Skills", "Inventory & progress", "Weapons"]
        if self.expert_mode:
            main_tabs.extend(("Other saved data", "Helper", "Info"))
        self.notebook._segmented_button.configure(values=main_tabs)
        self.notebook.set(self.notebook.get())

        technical_columns = {
            self.player_context["tree"]: {"type"},
            self.skill_context["tree"]: {"id"},
            self.weapons_context["tree"]: {"class"},
        }
        for context in self.data_tables.values():
            technical_columns[context["tree"]] = {"type"}
        for tree, hidden_columns in technical_columns.items():
            columns = tuple(tree["columns"])
            tree.configure(displaycolumns=columns if self.expert_mode else tuple(column for column in columns if column not in hidden_columns))
            self._fit_table_columns(tree)

        if not self.expert_mode and self.data_notebook.get() == "World events":
            other_tabs = [name for name in self.data_tab_names if name != "World events"]
            if other_tabs:
                self.data_notebook.set(other_tabs[0])
        visible_data_tabs = list(self.data_tab_names)
        if not self.expert_mode and len(visible_data_tabs) > 1:
            visible_data_tabs = [name for name in visible_data_tabs if name != "World events"]
        if visible_data_tabs:
            self.data_notebook._segmented_button.configure(values=visible_data_tabs)
            self.data_notebook.set(self.data_notebook.get())

    @staticmethod
    def _fit_table_columns(tree):
        """Fit visible table columns to the available width, including Expert details."""
        available = tree.winfo_width() - 24
        if available < 120:
            return
        visible = tuple(tree.cget("displaycolumns"))
        if not visible or visible == ("#all",):
            visible = tuple(tree.cget("columns"))
        weights = {
            "field": 0.46, "value": 0.29, "type": 0.25,
            "skill": 0.42, "id": 0.24, "level": 0.34,
            "name": 0.22, "durability": 0.14, "ammo": 0.20, "class": 0.44,
            "key": 0.46, "category": 0.28, "entries": 0.72,
        }
        total_weight = sum(weights.get(column, 1.0) for column in visible)
        for column in visible:
            width = max(72, int(available * weights.get(column, 1.0) / total_weight))
            tree.column(column, width=width, minwidth=min(width, 72))

    def _build_helper(self):
        styled_label(self.helper_tab, "A quick guide to the save editor", "Title.TLabel", font=("Segoe UI", 21, "bold"), justify="center").pack(fill="x", pady=(0, 4))
        styled_label(self.helper_tab, "Save values include a type that tells the game how to read them.", "Subtitle.TLabel", justify="center").pack(fill="x", pady=(0, 14))

        card = styled_frame(self.helper_tab, "Card.TFrame")
        card.pack(fill="both", expand=True)
        types = ttk.Treeview(card, columns=("kind", "meaning", "example"), show="headings", selectmode="none", height=11, style="Helper.Treeview")
        types.heading("kind", text="Storage type", anchor="center")
        types.heading("meaning", text="Meaning", anchor="center")
        types.heading("example", text="Example", anchor="center")
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
        type_scroll = ctk.CTkScrollbar(card, orientation="vertical", command=types.yview, fg_color=COLORS["panel"], button_color=COLORS["panel_raised"], button_hover_color=COLORS["line"])
        types.configure(yscrollcommand=type_scroll.set)
        types.pack(side="left", fill="both", expand=True, padx=(12, 0), pady=12)
        type_scroll.pack(side="right", fill="y", padx=(0, 12), pady=12)

        notes = styled_frame(self.helper_tab)
        notes.pack(fill="x", pady=(12, 0))
        styled_label(notes, "Editing", "Kicker.TLabel").pack(anchor="w")
        styled_label(notes, "Double-click a value to edit it. Weapon durability and loaded ammo are in Weapons; inventory and progress are under their own tab.", "Subtitle.TLabel", wraplength=1100, justify="left").pack(anchor="w", fill="x", pady=(3, 8))
        styled_label(notes, "Saving", "Kicker.TLabel").pack(anchor="w")
        styled_label(notes, "Choose where to save a separate copy. It keeps the original filename, and your imported save remains unchanged.", "Subtitle.TLabel", wraplength=1100, justify="left").pack(anchor="w", fill="x", pady=(3, 0))

    def _build_info(self):
        styled_label(self.info_tab, "About this save editor", "Title.TLabel", font=("Segoe UI", 21, "bold"), justify="center").pack(fill="x", pady=(0, 4))
        styled_label(self.info_tab, "Project details and attribution", "Subtitle.TLabel", justify="center").pack(fill="x", pady=(0, 14))

        card = styled_frame(self.info_tab, "Card.TFrame")
        card.pack(fill="x", anchor="n", pady=(0, 12))
        styled_label(card, "UNOFFICIAL COMMUNITY TOOL", "Kicker.TLabel").pack(anchor="w", padx=18, pady=(16, 8))
        styled_label(
            card,
            "An independent project by LoseMyXelf (LMX). It is not an official Sin Spire product and is not affiliated with, sponsored by, or endorsed by Krasue Games.",
            "Subtitle.TLabel",
            wraplength=1000,
            justify="left",
        ).pack(anchor="w", fill="x", padx=18, pady=(0, 16))

        credits = styled_frame(self.info_tab, "Card.TFrame")
        credits.pack(fill="x", anchor="n")
        styled_label(credits, "CREDITS", "Kicker.TLabel").pack(anchor="w", padx=18, pady=(16, 10))
        developer_credit = styled_frame(credits)
        developer_credit.pack(fill="x", padx=18, pady=(0, 8))
        styled_label(developer_credit, "Sin Spire by Krasue Games", "Subtitle.TLabel").pack(side="left", anchor="w", expand=True)
        ctk.CTkButton(
            developer_credit,
            text="Sin Spire on Steam",
            command=lambda: webbrowser.open(SIN_SPIRE_STEAM_URL),
            width=190,
            height=44,
            corner_radius=12,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["text"],
            font=("Segoe UI", 12, "bold"),
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            developer_credit,
            text="Krasue Games on Patreon",
            command=lambda: webbrowser.open(DEVELOPER_PATREON_URL),
            width=210,
            height=44,
            corner_radius=12,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["text"],
            font=("Segoe UI", 12, "bold"),
        ).pack(side="right")
        styled_label(credits, "Save editor by LoseMyXelf (LMX)", "Subtitle.TLabel").pack(anchor="w", padx=18, pady=(0, 16))

    def _make_table(self, parent, section_title, hint, columns, widths, editable, action=None):
        section_bar = ctk.CTkFrame(parent, fg_color=COLORS["panel_raised"], corner_radius=12)
        section_bar.pack(fill="x", pady=(0, 12))
        section_content = styled_frame(section_bar)
        section_content.pack(side="left", fill="x", expand=True, padx=14, pady=9)
        styled_label(section_content, section_title.upper(), "Hint.TLabel", foreground=COLORS["accent_soft"]).pack(anchor="w")
        styled_label(section_content, hint, "Subtitle.TLabel", wraplength=1100, justify="left", anchor="w").pack(anchor="w", fill="x", pady=(2, 0))
        badge_text = "EDITABLE" if editable else "REFERENCE"
        badge_color = COLORS["accent"] if editable else COLORS["line"]
        if action:
            action_text, action_command = action
            action_button = ctk.CTkButton(section_bar, text=action_text, command=action_command, width=190, height=38, corner_radius=10, fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"], text_color=COLORS["text"], font=("Segoe UI", 12, "bold"), state="disabled")
            action_button.pack(side="right", padx=(0, 8), pady=8)
            if section_title.casefold() == "weapons":
                self.repair_weapons_button = action_button
        ctk.CTkLabel(section_bar, text=badge_text, text_color=COLORS["text"], fg_color=badge_color, corner_radius=9, font=("Segoe UI", 10, "bold"), padx=10, pady=5).pack(side="right", padx=14)
        wrap = styled_frame(parent, "Card.TFrame")
        wrap.pack(fill="both", expand=True)
        tree = ttk.Treeview(wrap, columns=columns, show="headings", selectmode="browse")
        tree.tag_configure("even", background=COLORS["input"])
        tree.tag_configure("odd", background=COLORS["panel"])
        for col, width in zip(columns, widths):
            tree.heading(col, text={"field": "Player field", "skill": "Skill", "id": "Code", "level": "Level", "value": "Value", "type": "Storage type", "name": "Weapon", "durability": "Durability", "ammo": "Loaded ammo", "class": "Internal class", "key": "Key", "category": "Saved collection", "entries": "Contents"}.get(col, col.title()), anchor="center")
            tree.column(col, width=width, anchor="w" if col in ("field", "skill", "id", "type", "name", "class", "key", "category", "entries") else "e", stretch=(col not in ("type", "class")))
        ybar = ctk.CTkScrollbar(wrap, orientation="vertical", command=tree.yview, fg_color=COLORS["panel"], button_color=COLORS["panel_raised"], button_hover_color=COLORS["line"])
        tree.configure(yscrollcommand=ybar.set)
        tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        ybar.pack(side="right", fill="y", padx=(0, 10), pady=10)
        tree.bind("<Configure>", lambda _event, widget=tree: self._fit_table_columns(widget), add="+")
        empty_panel = ctk.CTkFrame(wrap, fg_color=COLORS["panel"], corner_radius=14, border_width=1, border_color=COLORS["line"])
        empty_content = ctk.CTkFrame(empty_panel, fg_color="transparent")
        empty_content.place(relx=0.5, rely=0.5, anchor="center")
        empty_title = styled_label(empty_content, "Drop a save file here", "Title.TLabel", font=("Segoe UI", 22, "bold"), justify="center")
        empty_title.pack(pady=(0, 8))
        empty_label = styled_label(empty_content, "Drop a .sav file here, or click anywhere in this area to browse.", "Subtitle.TLabel", justify="center", wraplength=560)
        empty_label.pack()
        for widget in (empty_panel, empty_content, empty_title, empty_label):
            widget.drop_target_register(DND_FILES)
            widget.dnd_bind("<<Drop>>", self._drop_save)
            widget.dnd_bind("<<DropEnter>>", lambda event, panel=empty_panel: self._set_drop_highlight(panel, True))
            widget.dnd_bind("<<DropLeave>>", lambda event, panel=empty_panel: self._set_drop_highlight(panel, False))
        for widget in (empty_panel, empty_content, empty_title, empty_label):
            widget.bind("<Button-1>", lambda _event: self.open_save())
        empty_panel.place(relx=0.5, rely=0.5, relwidth=0.98, relheight=0.96, anchor="center")
        context = {"tree": tree, "editable": set(editable), "rows": {}, "details": {}, "empty_panel": empty_panel, "empty_label": empty_label, "empty_title": empty_title}
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
        self.load_save(name)

    def _drop_save(self, event):
        self._set_drop_highlight(event.widget, False)
        try:
            paths = self.tk.splitlist(event.data)
        except tk.TclError:
            paths = (event.data.strip("{}"),)
        if not paths:
            return "break"
        if len(paths) != 1:
            messagebox.showinfo("Choose one save", "Please drop one save file at a time.", parent=self)
            return "break"
        self.load_save(paths[0])
        return "break"

    @staticmethod
    def _set_drop_highlight(panel, active):
        try:
            panel.configure(border_color=COLORS["accent_soft"] if active else COLORS["line"])
        except (tk.TclError, ValueError):
            pass

    def load_save(self, name):
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
            self.file_label.configure(text=str(candidate))
            self.format_label.configure(text=f"{version_text}  ·  {compression_text}")
            self.status.configure(text="Save loaded. Edit values, then save a separate copy.")
            self.save_button.configure(state="normal")
            self.backup_button.configure(state="normal")
        except Exception as exc:
            messagebox.showerror("Could not open save", f"The file could not be read as a supported GVAS save.\n\n{exc}", parent=self)

    def _clear(self, tree):
        tree.delete(*tree.get_children())
        context = next((ctx for ctx in self.tables if ctx["tree"] is tree), None)
        if context:
            context["rows"].clear()

    def _add_row(self, context, iid, values, setter, number_type=None):
        tree = context["tree"]
        tag = "even" if len(tree.get_children()) % 2 == 0 else "odd"
        display_values = list(values)
        columns = list(tree["columns"])
        numeric_column = next((column for column in ("value", "level") if column in columns), None)
        if numeric_column and number_type in ("DoubleProperty", "FloatProperty"):
            value_index = columns.index(numeric_column)
            display_values[value_index] = format_number(display_values[value_index], number_type)
        tree.insert("", "end", iid=iid, values=display_values, tags=(tag,))
        context["rows"][iid] = {"setter": setter, "number_type": number_type}

    @staticmethod
    def _update_empty_state(context, has_save):
        tree = context["tree"]
        if tree.get_children():
            context["empty_panel"].place_forget()
        else:
            context["empty_title"].configure(text=("Nothing to show in this section" if has_save else "Drop a save file here"))
            context["empty_label"].configure(text=("This save has no editable values in this section." if context["editable"] else "This save has no entries in this section.") if has_save else "Drop a .sav file here, or click anywhere in this area to browse.")
            context["empty_panel"].place(relx=0.5, rely=0.5, relwidth=0.98, relheight=0.96, anchor="center")

    def _populate(self):
        for context in self.tables:
            self._clear(context["tree"])
        self.tables = [self.player_context, self.skill_context, self.weapons_context, self.reference_context]
        for tab_name in self.data_tab_names:
            self.data_notebook.delete(tab_name)
        self.data_tab_names.clear()
        self.data_tables.clear()
        props = self.document["properties"]["PlayerState"]["value"]

        player_ctx = self.player_context
        player_rows = []
        for key, prop in props.items():
            if prop.get("type") in NUMERIC_TYPES and "value" in prop:
                player_rows.append((key, display_field_name(key), prop, False))
        for key, prop in self.document["properties"].items():
            if key != "PlayerState" and prop.get("type") in NUMERIC_TYPES and "value" in prop:
                player_rows.append((key, "Save / " + display_field_name(key), prop, True))
        player_rows.sort(key=lambda row: (row[3], _order_index(nice_name(row[0]), PLAYER_FIELD_ORDER)))
        for key, label, prop, is_save_level in player_rows:
            iid = "save_" + key if is_save_level else key
            self._add_row(player_ctx, iid, (label, prop["value"], prop["type"]), lambda value, p=prop: p.__setitem__("value", value), prop["type"])

        skill_ctx = self.skill_context
        skills = find_prop(props, "CurrentSkills")
        if skills:
            skill_rows = []
            for i, item in enumerate(skills[1].get("values", [])):
                row = item.get("value", {})
                name = next((p.get("history", {}).get("source_string") for k, p in row.items() if k.startswith("Name_") and p.get("type") == "TextProperty"), "Skill")
                code = next((p.get("value", "") for k, p in row.items() if k.startswith("ID_") and p.get("type") == "NameProperty"), "")
                count_key = next((k for k, p in row.items() if k.startswith("Count_") and p.get("type") == "IntProperty"), None)
                if count_key:
                    counter = row[count_key]
                    skill_rows.append((i, name, code, counter))
            skill_rows.sort(key=lambda row: _order_index(row[1], SKILL_ORDER))
            for i, name, code, counter in skill_rows:
                self._add_row(skill_ctx, str(i), (name, code, counter["value"]), lambda value, p=counter: p.__setitem__("value", value), "IntProperty")

        for prefix in MAP_PREFIXES:
            found = find_prop(props, prefix)
            if found:
                map_key = nice_name(found[0])
                self._add_map_tab(MAP_LABELS.get(map_key, map_key), found[1])
        world_events = self.document["properties"].get("WorldEvents")
        if world_events and world_events.get("type") == "MapProperty":
            self._add_map_tab(MAP_LABELS["WorldEvents"], world_events)

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
                tag = "even" if len(weapon_tree.get_children()) % 2 == 0 else "odd"
                weapon_tree.insert("", "end", iid=str(i), values=(weapon_id, f"{durability_value:.1f}" if isinstance(durability_value, (int, float)) else durability_value, ammo_value, class_short), tags=(tag,))
                weapon_ctx["rows"][str(i)] = {"durability": durability, "ammo": ammo}
        self.repair_weapons_button.configure(state="normal" if weapon_tree.get_children() else "disabled")
        ref_tree = ref_ctx["tree"]
        ref_ctx["details"].clear()
        ref_tree.configure(columns=("category", "entries"))
        for col, title, width in (("category", "Saved collection", 250), ("entries", "Contents · double-click to view all", 800)):
            ref_tree.heading(col, text=title)
            ref_tree.column(col, width=width, anchor="w")
        ref_tree.bind("<Double-1>", self._show_reference_detail, add="+")
        arrays = ("CurrentPerks", "ReadNotes")
        reference_labels = {
            "CurrentPerks": "Perks",
            "ReadNotes": "Notes read",
            "MapName": "Current map",
            "SavedDiff": "Difficulty",
            "Date": "Save date",
        }
        reference_rows = {}
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
            contents = ", ".join(map(str, vals))
            if len(contents) > 88:
                contents = contents[:85].rsplit(" ", 1)[0] + "…"
            reference_rows[label] = (contents, ", ".join(map(str, vals)))
        for label in ("MapName", "SavedDiff", "Date"):
            value = self.document["properties"].get(label)
            if value:
                shown = value.get("value", value.get("comment", ""))
                if isinstance(shown, dict):
                    shown = shown.get("comment", shown.get("datetime", ""))
                reference_rows[label] = (str(shown), str(shown))
        for label in REFERENCE_ORDER:
            if label not in reference_rows:
                continue
            preview, details = reference_rows[label]
            if label in arrays and len(preview) > 88:
                preview = preview[:85].rsplit(" ", 1)[0] + "…"
            tag = "even" if len(ref_tree.get_children()) % 2 == 0 else "odd"
            iid = "ref_" + label
            ref_tree.insert("", "end", iid=iid, values=(reference_labels.get(label, label), preview), tags=(tag,))
            ref_ctx["details"][iid] = details
        ref_ctx["editable"].clear()
        for context in self.tables:
            self._update_empty_state(context, has_save=self.save is not None)
        if self.data_tab_names:
            self.data_notebook.set(self.data_tab_names[0])
        self._apply_display_mode()

    def _add_map_tab(self, name, prop):
        self.data_notebook.add(name)
        self.data_tab_names.append(name)
        tab = self.data_notebook.tab(name)
        tab.configure(fg_color="transparent")
        title = name.upper()
        context = self._make_table(tab, title, "Double-click a number to edit it. Names and event keys stay unchanged.", ("key", "value", "type"), (550, 220, 180), ("value",))
        self.data_tables[name] = context
        map_rows = [(i, pair) for i, pair in enumerate(prop.get("values", [])) if len(pair) == 2]
        if name == MAP_LABELS["CurrentStats"]:
            map_rows.sort(key=lambda row: _order_index(row[1][0].get("value", ""), STATS_ORDER))
        for i, pair in map_rows:
            key_prop, value_prop = pair
            key = key_prop.get("value", "")
            value = value_prop.get("value", "")
            if value_prop.get("type") in NUMERIC_TYPES:
                self._add_row(context, str(i), (key, value, value_prop.get("type")), lambda new, p=value_prop: p.__setitem__("value", new), value_prop.get("type"))

    def _show_reference_detail(self, event):
        tree = self.reference_context["tree"]
        if tree.identify_region(event.x, event.y) != "cell":
            return
        row = tree.identify_row(event.y)
        if not row:
            return
        category, preview = tree.item(row, "values")
        contents = self.reference_context["details"].get(row, preview)
        dialog = ctk.CTkToplevel(self)
        dialog.title(str(category))
        dialog.geometry("760x500")
        dialog.minsize(520, 320)
        dialog.transient(self)
        dialog.configure(fg_color=COLORS["window"])
        panel = ctk.CTkFrame(dialog, fg_color=COLORS["panel"], corner_radius=14)
        panel.pack(fill="both", expand=True, padx=16, pady=16)
        styled_label(panel, str(category), "Title.TLabel", font=("Segoe UI", 22, "bold")).pack(anchor="w", padx=16, pady=(14, 8))
        text_box = ctk.CTkTextbox(panel, wrap="word", font=("Segoe UI", 13), text_color=COLORS["text"], fg_color=COLORS["input"], corner_radius=10)
        text_box.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        text_box.insert("1.0", str(contents))
        text_box.configure(state="disabled")
        ctk.CTkButton(panel, text="Close", command=dialog.destroy, width=110, height=38, corner_radius=11, fg_color=COLORS["panel_raised"], hover_color=COLORS["line"], text_color=COLORS["text"], font=("Segoe UI", 12)).pack(anchor="e", padx=16, pady=(0, 14))
        dialog.grab_set()

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

    def create_backup(self):
        if not self.source or not self.source.exists():
            messagebox.showerror("No save loaded", "Open a save before creating a backup.", parent=self)
            return
        backup_dir = filedialog.askdirectory(
            title="Choose a folder for the original save backup",
            initialdir=str(self.source.parent),
            mustexist=True,
        )
        if not backup_dir:
            return
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        backup_path = Path(backup_dir).expanduser().resolve() / f"{self.source.name}.{stamp}.bak"
        try:
            shutil.copy2(self.source, backup_path)
            self.status.configure(text=f"Original save backed up to: {backup_path}")
            messagebox.showinfo(
                "Backup created",
                f"A byte-for-byte copy of the original save was created at:\n{backup_path}",
                parent=self,
            )
        except OSError as exc:
            messagebox.showerror("Could not create backup", f"The backup could not be written.\n\n{exc}", parent=self)


if __name__ == "__main__":
    SaveEditor().mainloop()

