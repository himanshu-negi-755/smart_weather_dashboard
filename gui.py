"""
gui.py
------
GUIManager class — builds and manages every widget.

Uses ttk with the 'clam' theme so that custom colours render correctly
on every platform (the macOS system Tk ignores bg/fg on classic
tk widgets, which makes the UI appear blank/white).
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, List, Optional

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from models import WeatherData, ForecastData

# ---------------------------------------------------------------------------
# Colour palettes
# ---------------------------------------------------------------------------
THEMES = {
    "dark": {
        "bg":           "#1a1a2e",
        "panel_bg":     "#16213e",
        "card_bg":      "#0f3460",
        "accent":       "#e94560",
        "accent2":      "#533483",
        "fg":           "#eaeaea",
        "fg_dim":       "#a0a0b0",
        "entry_bg":     "#0f3460",
        "entry_fg":     "#ffffff",
        "btn_bg":       "#e94560",
        "btn_fg":       "#ffffff",
        "btn2_bg":      "#533483",
        "btn2_fg":      "#ffffff",
        "list_bg":      "#0f3460",
        "list_fg":      "#eaeaea",
        "list_sel_bg":  "#e94560",
        "list_sel_fg":  "#ffffff",
        "chart_bg":     "#0f3460",
        "chart_fg":     "#eaeaea",
        "chart_grid":   "#1e4070",
        "chart_line":   "#e94560",
        "separator":    "#533483",
    },
    "light": {
        "bg":           "#f0f4f8",
        "panel_bg":     "#ffffff",
        "card_bg":      "#e8f0fe",
        "accent":       "#1a73e8",
        "accent2":      "#34a853",
        "fg":           "#202124",
        "fg_dim":       "#5f6368",
        "entry_bg":     "#ffffff",
        "entry_fg":     "#202124",
        "btn_bg":       "#1a73e8",
        "btn_fg":       "#ffffff",
        "btn2_bg":      "#34a853",
        "btn2_fg":      "#ffffff",
        "list_bg":      "#ffffff",
        "list_fg":      "#202124",
        "list_sel_bg":  "#1a73e8",
        "list_sel_fg":  "#ffffff",
        "chart_bg":     "#ffffff",
        "chart_fg":     "#202124",
        "chart_grid":   "#e0e0e0",
        "chart_line":   "#1a73e8",
        "separator":    "#dadce0",
    },
}

# Condition-to-emoji mapping for weather icons in plain text
CONDITION_EMOJI = {
    "Clear": "☀️",
    "Clouds": "☁️",
    "Rain": "🌧️",
    "Drizzle": "🌦️",
    "Thunderstorm": "⛈️",
    "Snow": "❄️",
    "Mist": "🌫️",
    "Smoke": "🌫️",
    "Haze": "🌫️",
    "Dust": "🌪️",
    "Fog": "🌫️",
    "Sand": "🌪️",
    "Ash": "🌋",
    "Squall": "💨",
    "Tornado": "🌪️",
}


class GUIManager:
    """
    Responsible for constructing, styling, and updating every widget.

    All theming is done through ttk.Style ('clam' theme) so colours work
    consistently on macOS, Windows, and Linux.
    """

    def __init__(
        self,
        root: tk.Tk,
        on_search: Callable,
        on_add_favorite: Callable,
        on_remove_favorite: Callable,
        on_favorite_click: Callable,
        on_toggle_theme: Callable,
        on_toggle_unit: Callable,
        on_toggle_refresh: Callable,
    ) -> None:
        self._root = root
        self._on_search = on_search
        self._on_add_favorite = on_add_favorite
        self._on_remove_favorite = on_remove_favorite
        self._on_favorite_click = on_favorite_click
        self._on_toggle_theme = on_toggle_theme
        self._on_toggle_unit = on_toggle_unit
        self._on_toggle_refresh = on_toggle_refresh

        self._theme_name = "dark"
        self._unit = "C"
        self._chart_canvas: Optional[FigureCanvasTkAgg] = None
        self._chart_figure: Optional[Figure] = None

        # ttk style engine — 'clam' renders custom colours on every OS
        self._style = ttk.Style(self._root)
        self._style.theme_use("clam")

        self._build_root()
        self._configure_styles()
        self._build_layout()
        self._apply_widget_colors()

    # ------------------------------------------------------------------
    # Root window setup
    # ------------------------------------------------------------------

    def _build_root(self) -> None:
        """Configure the root window."""
        self._root.title("Smart Weather Dashboard")
        self._root.geometry("980x680")
        self._root.minsize(820, 580)
        self._root.resizable(True, True)

    # ------------------------------------------------------------------
    # ttk style configuration
    # ------------------------------------------------------------------

    def _configure_styles(self) -> None:
        """(Re)configure all ttk styles for the current theme."""
        t = self._t()
        s = self._style

        s.configure("App.TFrame", background=t["bg"])
        s.configure("Panel.TFrame", background=t["panel_bg"])
        s.configure("Card.TFrame", background=t["card_bg"])
        s.configure("Sep.TFrame", background=t["separator"])

        s.configure("Title.TLabel", background=t["panel_bg"],
                    foreground=t["accent"], font=("Helvetica", 16, "bold"))
        s.configure("Heading.TLabel", background=t["panel_bg"],
                    foreground=t["accent"], font=("Helvetica", 12, "bold"))
        s.configure("City.TLabel", background=t["panel_bg"],
                    foreground=t["fg"], font=("Helvetica", 18, "bold"))
        s.configure("Icon.TLabel", background=t["panel_bg"],
                    foreground=t["fg"], font=("Helvetica", 28))
        s.configure("Temp.TLabel", background=t["panel_bg"],
                    foreground=t["accent"], font=("Helvetica", 44, "bold"))
        s.configure("Cond.TLabel", background=t["panel_bg"],
                    foreground=t["fg"], font=("Helvetica", 14, "bold"))
        s.configure("Dim.TLabel", background=t["panel_bg"],
                    foreground=t["fg_dim"], font=("Helvetica", 11))
        s.configure("Loading.TLabel", background=t["panel_bg"],
                    foreground=t["fg_dim"], font=("Helvetica", 12, "italic"))
        s.configure("CardKey.TLabel", background=t["card_bg"],
                    foreground=t["fg_dim"], font=("Helvetica", 9))
        s.configure("CardVal.TLabel", background=t["card_bg"],
                    foreground=t["fg"], font=("Helvetica", 11, "bold"))
        s.configure("Placeholder.TLabel", background=t["panel_bg"],
                    foreground=t["fg_dim"], font=("Helvetica", 12, "italic"))

        s.configure("Primary.TButton", background=t["btn_bg"],
                    foreground=t["btn_fg"], font=("Helvetica", 11, "bold"),
                    borderwidth=0, focuscolor=t["btn_bg"], padding=(14, 7))
        s.map("Primary.TButton",
              background=[("active", t["accent2"]), ("pressed", t["accent2"])])

        s.configure("Secondary.TButton", background=t["btn2_bg"],
                    foreground=t["btn2_fg"], font=("Helvetica", 10, "bold"),
                    borderwidth=0, focuscolor=t["btn2_bg"], padding=(10, 5))
        s.map("Secondary.TButton",
              background=[("active", t["accent"]), ("pressed", t["accent"])])

        s.configure("Toggle.TCheckbutton", background=t["panel_bg"],
                    foreground=t["fg"], font=("Helvetica", 10),
                    focuscolor=t["panel_bg"])
        s.map("Toggle.TCheckbutton",
              background=[("active", t["panel_bg"])],
              foreground=[("active", t["fg"])])

    # ------------------------------------------------------------------
    # Layout construction
    # ------------------------------------------------------------------

    def _build_layout(self) -> None:
        """Create and pack every section of the UI."""
        # ── Top bar ──────────────────────────────────────────────────
        self._top_bar = ttk.Frame(self._root, style="Panel.TFrame", padding=(0, 10))
        self._top_bar.pack(side=tk.TOP, fill=tk.X)
        self._build_top_bar()

        # ── Body (left panel + center+chart) ─────────────────────────
        self._body = ttk.Frame(self._root, style="App.TFrame", padding=(8, 6))
        self._body.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Left panel
        self._left_panel = ttk.Frame(self._body, style="Panel.TFrame", width=200)
        self._left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 6))
        self._left_panel.pack_propagate(False)
        self._build_favorites_panel()

        # Right side (weather card + chart)
        self._right_side = ttk.Frame(self._body, style="App.TFrame")
        self._right_side.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Weather card
        self._center_panel = ttk.Frame(self._right_side, style="Panel.TFrame")
        self._center_panel.pack(side=tk.TOP, fill=tk.X, pady=(0, 6))
        self._build_weather_card()

        # Chart area
        self._chart_panel = ttk.Frame(self._right_side, style="Panel.TFrame")
        self._chart_panel.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self._build_chart_placeholder()

    # ------------------------------------------------------------------
    # Top bar
    # ------------------------------------------------------------------

    def _build_top_bar(self) -> None:
        """Search bar, buttons and theme/unit toggles."""
        ttk.Label(
            self._top_bar, text="⛅  Smart Weather Dashboard", style="Title.TLabel"
        ).pack(side=tk.LEFT, padx=(16, 24))

        # Search entry (classic tk.Entry; recoloured in _apply_widget_colors)
        self._search_var = tk.StringVar()
        self._search_entry = tk.Entry(
            self._top_bar,
            textvariable=self._search_var,
            font=("Helvetica", 13),
            relief=tk.FLAT,
            width=22,
            highlightthickness=1,
        )
        self._search_entry.pack(side=tk.LEFT, ipady=6, padx=(0, 6))
        self._search_entry.bind("<Return>", lambda _e: self._trigger_search())

        self._btn_search = ttk.Button(
            self._top_bar, text="🔍  Search", style="Primary.TButton",
            command=self._trigger_search, cursor="hand2",
        )
        self._btn_search.pack(side=tk.LEFT, padx=(0, 6))

        self._btn_fav = ttk.Button(
            self._top_bar, text="★  Add Favorite", style="Secondary.TButton",
            command=self._trigger_add_favorite, cursor="hand2",
        )
        self._btn_fav.pack(side=tk.LEFT, padx=(0, 20))

        # Right-side controls
        right_frame = ttk.Frame(self._top_bar, style="Panel.TFrame")
        right_frame.pack(side=tk.RIGHT, padx=16)

        self._refresh_var = tk.BooleanVar(value=False)
        self._chk_refresh = ttk.Checkbutton(
            right_frame, text="Auto-refresh", variable=self._refresh_var,
            style="Toggle.TCheckbutton", command=self._on_toggle_refresh,
            cursor="hand2",
        )
        self._chk_refresh.pack(side=tk.LEFT, padx=(0, 12))

        self._btn_unit = ttk.Button(
            right_frame, text="°C / °F", style="Secondary.TButton",
            command=self._on_toggle_unit, cursor="hand2",
        )
        self._btn_unit.pack(side=tk.LEFT, padx=(0, 8))

        self._btn_theme = ttk.Button(
            right_frame, text="☀️  Light", style="Secondary.TButton",
            command=self._on_toggle_theme, cursor="hand2",
        )
        self._btn_theme.pack(side=tk.LEFT)

    # ------------------------------------------------------------------
    # Favorites panel
    # ------------------------------------------------------------------

    def _build_favorites_panel(self) -> None:
        """Left panel with favorites listbox."""
        ttk.Label(
            self._left_panel, text="★  Favorites", style="Heading.TLabel",
            padding=(10, 8),
        ).pack(fill=tk.X)

        ttk.Frame(self._left_panel, style="Sep.TFrame", height=1).pack(
            fill=tk.X, padx=8)

        list_frame = ttk.Frame(self._left_panel, style="Panel.TFrame")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        self._fav_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            font=("Helvetica", 12),
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0,
            activestyle="none",
            cursor="hand2",
        )
        scrollbar.config(command=self._fav_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._fav_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._fav_listbox.bind("<Double-Button-1>", self._trigger_favorite_click)
        self._fav_listbox.bind("<Return>", self._trigger_favorite_click)

        self._btn_remove = ttk.Button(
            self._left_panel, text="✕  Remove", style="Primary.TButton",
            command=self._trigger_remove_favorite, cursor="hand2",
        )
        self._btn_remove.pack(pady=(0, 10))

    # ------------------------------------------------------------------
    # Weather card
    # ------------------------------------------------------------------

    def _build_weather_card(self) -> None:
        """Center panel showing current weather details."""
        # Loading label (hidden by default)
        self._loading_label = ttk.Label(
            self._center_panel, text="⏳  Fetching weather data…",
            style="Loading.TLabel",
        )

        outer = ttk.Frame(self._center_panel, style="Panel.TFrame",
                          padding=(16, 12))
        outer.pack(fill=tk.X)

        # City name row
        city_row = ttk.Frame(outer, style="Panel.TFrame")
        city_row.pack(fill=tk.X)
        self._lbl_city = ttk.Label(
            city_row, text="—  No city loaded", style="City.TLabel")
        self._lbl_city.pack(side=tk.LEFT)

        self._lbl_icon = ttk.Label(city_row, text="", style="Icon.TLabel")
        self._lbl_icon.pack(side=tk.RIGHT, padx=(0, 8))

        # Main stats row
        stats_row = ttk.Frame(outer, style="Panel.TFrame")
        stats_row.pack(fill=tk.X, pady=(4, 0))

        self._lbl_temp = ttk.Label(stats_row, text="—", style="Temp.TLabel")
        self._lbl_temp.pack(side=tk.LEFT)

        cond_frame = ttk.Frame(stats_row, style="Panel.TFrame")
        cond_frame.pack(side=tk.LEFT, padx=20, anchor="s")
        self._lbl_condition = ttk.Label(cond_frame, text="", style="Cond.TLabel")
        self._lbl_condition.pack(anchor="w")
        self._lbl_description = ttk.Label(cond_frame, text="", style="Dim.TLabel")
        self._lbl_description.pack(anchor="w")

        self._lbl_feels = ttk.Label(stats_row, text="", style="Dim.TLabel")
        self._lbl_feels.pack(side=tk.LEFT, padx=10, anchor="s")

        ttk.Frame(outer, style="Sep.TFrame", height=1).pack(fill=tk.X, pady=6)

        # Detail tiles row (humidity, wind, pressure, visibility)
        tiles_row = ttk.Frame(outer, style="Panel.TFrame")
        tiles_row.pack(fill=tk.X)

        self._detail_tiles: dict = {}
        tile_defs = [
            ("humidity",   "💧 Humidity",    "—"),
            ("wind",       "💨 Wind",        "—"),
            ("pressure",   "🔵 Pressure",    "—"),
            ("visibility", "👁  Visibility",  "—"),
        ]
        for key, label, default in tile_defs:
            tile = self._build_detail_tile(tiles_row, label, default)
            self._detail_tiles[key] = tile

    def _build_detail_tile(self, parent: ttk.Frame, label: str, value: str) -> ttk.Label:
        """Create a small card widget for one weather metric."""
        frame = ttk.Frame(parent, style="Card.TFrame", padding=(12, 8))
        frame.pack(side=tk.LEFT, padx=6, expand=True, fill=tk.X)
        ttk.Label(frame, text=label, style="CardKey.TLabel").pack(anchor="w")
        val_lbl = ttk.Label(frame, text=value, style="CardVal.TLabel")
        val_lbl.pack(anchor="w")
        return val_lbl

    # ------------------------------------------------------------------
    # Chart placeholder
    # ------------------------------------------------------------------

    def _build_chart_placeholder(self) -> None:
        """Show an empty chart area until real data arrives."""
        self._chart_placeholder = ttk.Label(
            self._chart_panel,
            text="📈  Search a city to see the temperature trend chart",
            style="Placeholder.TLabel",
        )
        self._chart_placeholder.pack(expand=True)

    # ------------------------------------------------------------------
    # Public update methods (called by WeatherApp)
    # ------------------------------------------------------------------

    def show_loading(self, visible: bool) -> None:
        """Show or hide the loading label."""
        if visible:
            self._loading_label.pack(pady=10)
        else:
            self._loading_label.pack_forget()

    def update_weather(self, weather: WeatherData, unit: str = "C") -> None:
        """Populate the weather card with *weather* data."""
        d = weather.to_display_dict(unit)
        emoji = CONDITION_EMOJI.get(weather.condition, "🌡️")
        self._lbl_icon.config(text=emoji)
        self._lbl_city.config(text=d["city"])
        self._lbl_temp.config(text=d["temperature"])
        self._lbl_condition.config(text=d["condition"])
        self._lbl_description.config(text=d["description"])
        self._lbl_feels.config(text=f"Feels like {d['feels_like']}")
        self._detail_tiles["humidity"].config(text=d["humidity"])
        self._detail_tiles["wind"].config(text=d["wind_speed"])
        self._detail_tiles["pressure"].config(text=d["pressure"])
        self._detail_tiles["visibility"].config(text=d["visibility"])

    def update_chart(self, forecast: ForecastData, unit: str = "C") -> None:
        """Render or re-render the temperature trend chart inside the GUI."""
        t = self._t()

        # Remove placeholder
        self._chart_placeholder.pack_forget()

        # Destroy old canvas if present
        if self._chart_canvas is not None:
            self._chart_canvas.get_tk_widget().destroy()
            plt.close(self._chart_figure)

        labels = forecast.time_labels()
        temps = forecast.temperatures_c() if unit == "C" else forecast.temperatures_f()
        unit_label = "°C" if unit == "C" else "°F"

        fig = Figure(figsize=(7, 2.6), dpi=96)
        fig.patch.set_facecolor(t["chart_bg"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(t["chart_bg"])

        x_indices = list(range(len(labels)))
        ax.plot(
            x_indices, temps,
            color=t["chart_line"], linewidth=2.2,
            marker="o", markersize=4, zorder=3,
        )
        ax.fill_between(x_indices, temps, alpha=0.15, color=t["chart_line"])

        step = max(1, len(labels) // 10)
        ax.set_xticks(x_indices[::step])
        ax.set_xticklabels(labels[::step], fontsize=7, color=t["chart_fg"])
        ax.tick_params(axis="y", labelsize=8, colors=t["chart_fg"])
        ax.tick_params(axis="x", colors=t["chart_fg"])
        ax.set_ylabel(f"Temp ({unit_label})", fontsize=8, color=t["chart_fg"])
        ax.set_title(
            f"5-Day Temperature Trend — {forecast.city}",
            fontsize=10, color=t["chart_fg"], pad=6,
        )
        ax.grid(True, color=t["chart_grid"], linewidth=0.6,
                linestyle="--", alpha=0.7)
        for spine in ax.spines.values():
            spine.set_edgecolor(t["chart_grid"])

        fig.tight_layout(pad=1.2)
        self._chart_figure = fig

        canvas = FigureCanvasTkAgg(fig, master=self._chart_panel)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        self._chart_canvas = canvas

    def update_favorites(self, favorites: List[str]) -> None:
        """Refresh the favorites listbox with *favorites*."""
        self._fav_listbox.delete(0, tk.END)
        for city in favorites:
            self._fav_listbox.insert(tk.END, f"  {city}")

    def get_search_text(self) -> str:
        """Return the current text in the search entry."""
        return self._search_var.get().strip()

    def set_search_text(self, text: str) -> None:
        """Set the text in the search entry."""
        self._search_var.set(text)

    def get_selected_favorite(self) -> Optional[str]:
        """Return the currently selected city name or None."""
        selection = self._fav_listbox.curselection()
        if not selection:
            return None
        raw = self._fav_listbox.get(selection[0])
        return raw.strip()

    def apply_theme(self, theme_name: str) -> None:
        """Switch the entire UI to *theme_name* ('dark' or 'light')."""
        self._theme_name = theme_name
        btn_label = "🌙  Dark" if theme_name == "light" else "☀️  Light"
        self._configure_styles()
        self._apply_widget_colors()
        self._btn_theme.config(text=btn_label)
        self._root.update_idletasks()

    def apply_unit(self, unit: str) -> None:
        """Update stored unit string (°C or °F)."""
        self._unit = unit

    def set_auto_refresh(self, value: bool) -> None:
        """Sync the auto-refresh checkbox state."""
        self._refresh_var.set(value)

    def show_error(self, title: str, message: str) -> None:
        """Display an error dialog."""
        messagebox.showerror(title, message, parent=self._root)

    def show_info(self, title: str, message: str) -> None:
        """Display an info dialog."""
        messagebox.showinfo(title, message, parent=self._root)

    # ------------------------------------------------------------------
    # Private trigger helpers
    # ------------------------------------------------------------------

    def _trigger_search(self) -> None:
        city = self.get_search_text()
        if city:
            self._on_search(city)

    def _trigger_add_favorite(self) -> None:
        city = self.get_search_text()
        if city:
            self._on_add_favorite(city)

    def _trigger_remove_favorite(self) -> None:
        city = self.get_selected_favorite()
        if city:
            self._on_remove_favorite(city)

    def _trigger_favorite_click(self, _event=None) -> None:
        city = self.get_selected_favorite()
        if city:
            self._on_favorite_click(city)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _t(self) -> dict:
        """Shorthand: return the current theme colour palette."""
        return THEMES[self._theme_name]

    def _apply_widget_colors(self) -> None:
        """
        Recolour the classic tk widgets (root, Entry, Listbox) that are not
        controlled by ttk styles.
        """
        t = self._t()
        self._root.configure(bg=t["bg"])
        self._search_entry.configure(
            bg=t["entry_bg"],
            fg=t["entry_fg"],
            insertbackground=t["entry_fg"],
            highlightbackground=t["separator"],
            highlightcolor=t["accent"],
        )
        self._fav_listbox.configure(
            bg=t["list_bg"],
            fg=t["list_fg"],
            selectbackground=t["list_sel_bg"],
            selectforeground=t["list_sel_fg"],
        )
