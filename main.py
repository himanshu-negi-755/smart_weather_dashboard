"""
main.py
-------
WeatherApp — the central controller that wires together the GUI,
API layer, and file manager.  Entry point for the application.

Usage
-----
1. Set your OpenWeatherMap API key via the environment variable
   ``OWM_API_KEY`` **or** enter it through the first-launch dialog.

   export OWM_API_KEY="your_key_here"   # macOS / Linux
   set    OWM_API_KEY=your_key_here     # Windows CMD

2. Run:
   python main.py
"""

import os
import sys
import tkinter as tk
from tkinter import simpledialog, messagebox
import threading
import logging

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("WeatherApp")

# ---------------------------------------------------------------------------
# Local imports
# ---------------------------------------------------------------------------
from api import WeatherAPI, WeatherAPIError
from file_manager import FileManager, FileManagerError
from gui import GUIManager
from models import WeatherData, ForecastData


class WeatherApp:
    """
    Central controller for the Smart Weather Dashboard.

    Responsibilities
    ----------------
    * Bootstrap the application (config, API key, window)
    * Delegate UI construction to GUIManager
    * Orchestrate API calls (on a worker thread to keep GUI responsive)
    * Manage favourites via FileManager
    * Handle auto-refresh scheduling
    """

    _REFRESH_MIN = 5          # default auto-refresh interval (minutes)

    def __init__(self) -> None:
        self._root = tk.Tk()
        self._file_manager = FileManager()
        self._config = self._file_manager.load_config()
        self._api: WeatherAPI | None = None
        self._favorites: list[str] = []
        self._current_weather: WeatherData | None = None
        self._current_forecast: ForecastData | None = None
        self._refresh_job = None          # after() handle for auto-refresh
        self._busy = False                # guard against concurrent requests

        self._ensure_api_key()
        self._build_gui()
        self._load_favorites()
        self._restore_last_city()

    # ------------------------------------------------------------------
    # Bootstrap helpers
    # ------------------------------------------------------------------

    def _ensure_api_key(self) -> None:
        """
        Resolve the OWM API key from (in priority order):
          1. Environment variable OWM_API_KEY
          2. Saved config file
          3. First-launch dialog prompt
        """
        key = (
            os.environ.get("OWM_API_KEY", "").strip()
            or self._config.get("api_key", "").strip()
        )
        if not key:
            key = self._prompt_api_key()
        if not key:
            messagebox.showerror(
                "API Key Required",
                "No OpenWeatherMap API key provided.\n"
                "The application will exit.\n\n"
                "Get a free key at https://openweathermap.org/api",
            )
            sys.exit(1)
        self._config["api_key"] = key
        self._file_manager.save_config(self._config)
        self._api = WeatherAPI(key)

    def _prompt_api_key(self) -> str:
        """Show a dialog asking the user to enter their API key."""
        # We need a minimal root window just for the dialog
        dummy = tk.Tk()
        dummy.withdraw()
        key = simpledialog.askstring(
            "OpenWeatherMap API Key",
            "Enter your free OpenWeatherMap API key\n"
            "(get one at https://openweathermap.org/api):",
            parent=dummy,
        )
        dummy.destroy()
        return (key or "").strip()

    def _build_gui(self) -> None:
        """Instantiate GUIManager, injecting all callbacks."""
        self._gui = GUIManager(
            root=self._root,
            on_search=self._search_city,
            on_add_favorite=self._add_favorite,
            on_remove_favorite=self._remove_favorite,
            on_favorite_click=self._load_favorite_city,
            on_toggle_theme=self._toggle_theme,
            on_toggle_unit=self._toggle_unit,
            on_toggle_refresh=self._toggle_refresh,
        )
        # Apply saved preferences
        self._gui.apply_theme(self._config.get("theme", "dark"))
        self._gui.apply_unit(self._config.get("unit", "C"))
        self._gui.set_auto_refresh(self._config.get("auto_refresh", False))

    def _load_favorites(self) -> None:
        """Load favourites from disk and populate the listbox."""
        try:
            self._favorites = self._file_manager.load_favorites()
        except FileManagerError as exc:
            logger.error("Could not load favorites: %s", exc)
            self._favorites = []
        self._gui.update_favorites(self._favorites)

    def _restore_last_city(self) -> None:
        """Automatically load the last searched city on startup."""
        last = self._config.get("last_city", "").strip()
        if last:
            self._gui.set_search_text(last)
            self._search_city(last)

    # ------------------------------------------------------------------
    # Core actions
    # ------------------------------------------------------------------

    def _search_city(self, city: str) -> None:
        """
        Fetch current weather and forecast for *city* on a background thread
        so the GUI stays responsive.
        """
        if self._busy:
            return
        city = city.strip()
        if not city:
            self._gui.show_error("Empty Input", "Please enter a city name.")
            return

        self._busy = True
        self._gui.show_loading(True)
        thread = threading.Thread(
            target=self._fetch_weather_thread,
            args=(city,),
            daemon=True,
        )
        thread.start()

    def _fetch_weather_thread(self, city: str) -> None:
        """Worker thread: calls API and schedules GUI update back on main thread."""
        try:
            weather = self._api.get_current_weather(city)
            forecast = self._api.get_forecast(city)
            self._root.after(0, self._on_fetch_success, weather, forecast)
        except WeatherAPIError as exc:
            self._root.after(0, self._on_fetch_error, str(exc))
        except Exception as exc:
            logger.exception("Unexpected error during weather fetch")
            self._root.after(0, self._on_fetch_error, f"Unexpected error: {exc}")

    def _on_fetch_success(self, weather: WeatherData, forecast: ForecastData) -> None:
        """Called on the main thread after a successful API fetch."""
        self._busy = False
        self._gui.show_loading(False)
        unit = self._config.get("unit", "C")
        self._current_weather = weather
        self._current_forecast = forecast
        self._gui.update_weather(weather, unit)
        self._gui.update_chart(forecast, unit)
        # Save last city
        self._config["last_city"] = weather.city
        self._file_manager.save_config(self._config)
        logger.info("Weather loaded for %s, %s", weather.city, weather.country)

    def _on_fetch_error(self, message: str) -> None:
        """Called on the main thread when an API error occurs."""
        self._busy = False
        self._gui.show_loading(False)
        self._gui.show_error("Weather Fetch Failed", message)
        logger.error("Fetch error: %s", message)

    # ------------------------------------------------------------------
    # Favorites management
    # ------------------------------------------------------------------

    def _add_favorite(self, city: str) -> None:
        """Add *city* to favourites and refresh the listbox."""
        city = city.strip()
        if not city:
            self._gui.show_error("Empty Input", "Please enter a city name first.")
            return
        try:
            self._favorites = self._file_manager.add_favorite(city)
            self._gui.update_favorites(self._favorites)
            self._gui.show_info("Favorite Added", f'"{city.title()}" added to favorites.')
        except FileManagerError as exc:
            self._gui.show_error("File Error", str(exc))

    def _remove_favorite(self, city: str) -> None:
        """Remove *city* from favourites."""
        try:
            self._favorites = self._file_manager.remove_favorite(city)
            self._gui.update_favorites(self._favorites)
        except FileManagerError as exc:
            self._gui.show_error("File Error", str(exc))

    def _load_favorite_city(self, city: str) -> None:
        """Load weather for a city selected in the favourites list."""
        self._gui.set_search_text(city)
        self._search_city(city)

    # ------------------------------------------------------------------
    # Settings toggles
    # ------------------------------------------------------------------

    def _toggle_theme(self) -> None:
        """Switch between dark and light theme."""
        current = self._config.get("theme", "dark")
        new_theme = "light" if current == "dark" else "dark"
        self._config["theme"] = new_theme
        self._file_manager.save_config(self._config)
        self._gui.apply_theme(new_theme)
        # Re-render chart with new theme colours if data is available
        if self._current_forecast:
            unit = self._config.get("unit", "C")
            self._gui.update_chart(self._current_forecast, unit)

    def _toggle_unit(self) -> None:
        """Toggle between Celsius and Fahrenheit."""
        current = self._config.get("unit", "C")
        new_unit = "F" if current == "C" else "C"
        self._config["unit"] = new_unit
        self._file_manager.save_config(self._config)
        self._gui.apply_unit(new_unit)
        # Refresh display with new unit
        if self._current_weather:
            self._gui.update_weather(self._current_weather, new_unit)
        if self._current_forecast:
            self._gui.update_chart(self._current_forecast, new_unit)

    def _toggle_refresh(self) -> None:
        """Enable or disable auto-refresh."""
        current = self._config.get("auto_refresh", False)
        new_val = not current
        self._config["auto_refresh"] = new_val
        self._file_manager.save_config(self._config)
        if new_val:
            self._schedule_refresh()
            logger.info("Auto-refresh enabled every %d minutes.", self._REFRESH_MIN)
        else:
            self._cancel_refresh()
            logger.info("Auto-refresh disabled.")

    # ------------------------------------------------------------------
    # Auto-refresh scheduling
    # ------------------------------------------------------------------

    def _schedule_refresh(self) -> None:
        """Schedule the next auto-refresh in `_REFRESH_MIN` minutes."""
        interval_ms = self._config.get("refresh_interval", self._REFRESH_MIN) * 60 * 1000
        self._refresh_job = self._root.after(interval_ms, self._auto_refresh)

    def _cancel_refresh(self) -> None:
        """Cancel any pending auto-refresh callback."""
        if self._refresh_job is not None:
            self._root.after_cancel(self._refresh_job)
            self._refresh_job = None

    def _auto_refresh(self) -> None:
        """Called by the scheduler: re-fetch data for the current city."""
        last = self._config.get("last_city", "").strip()
        if last:
            logger.info("Auto-refresh: re-fetching %s", last)
            self._search_city(last)
        # Reschedule
        if self._config.get("auto_refresh", False):
            self._schedule_refresh()

    # ------------------------------------------------------------------
    # Application entry point
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Start the Tkinter event loop."""
        # Restore auto-refresh state
        if self._config.get("auto_refresh", False):
            self._schedule_refresh()
        self._root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._root.mainloop()

    def _on_close(self) -> None:
        """Clean up before closing the window."""
        self._cancel_refresh()
        self._file_manager.save_config(self._config)
        self._root.destroy()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app = WeatherApp()
    app.run()
