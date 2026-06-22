"""
file_manager.py
---------------
FileManager class — handles all persistent storage via JSON files.
Keeps file I/O concerns separate from the rest of the application.
"""

import json
import os
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# Default file paths (relative to project root)
_DEFAULT_FAVORITES_PATH = "data/favorites.json"
_DEFAULT_CONFIG_PATH = "data/config.json"

# Default application configuration
_DEFAULT_CONFIG = {
    "api_key": "",
    "unit": "C",          # "C" for Celsius, "F" for Fahrenheit
    "theme": "dark",      # "dark" | "light"
    "auto_refresh": False,
    "refresh_interval": 5,  # minutes
    "last_city": "",
}


class FileManagerError(Exception):
    """Raised when a file I/O operation fails."""
    pass


class FileManager:
    """
    Manages reading and writing of favorites and application config.

    Parameters
    ----------
    favorites_path : str
        Path to the JSON file storing favourite cities.
    config_path : str
        Path to the JSON file storing application configuration.
    """

    def __init__(
        self,
        favorites_path: str = _DEFAULT_FAVORITES_PATH,
        config_path: str = _DEFAULT_CONFIG_PATH,
    ) -> None:
        self._favorites_path = favorites_path
        self._config_path = config_path
        self._ensure_data_directory()

    # ------------------------------------------------------------------
    # Favourites
    # ------------------------------------------------------------------

    def load_favorites(self) -> List[str]:
        """
        Load the list of favourite city names from disk.

        Returns an empty list if the file does not exist yet.
        """
        if not os.path.exists(self._favorites_path):
            return []
        try:
            with open(self._favorites_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if not isinstance(data, list):
                raise FileManagerError("Favorites file has unexpected format.")
            return [str(city) for city in data]
        except json.JSONDecodeError as exc:
            logger.error("Favorites file is corrupted: %s", exc)
            raise FileManagerError(f"Could not parse favorites file: {exc}") from exc
        except OSError as exc:
            logger.error("Could not read favorites file: %s", exc)
            raise FileManagerError(f"Could not read favorites file: {exc}") from exc

    def save_favorites(self, favorites: List[str]) -> None:
        """
        Persist the list of favourite city names to disk.

        Parameters
        ----------
        favorites : List[str]
            Ordered list of city names to save.
        """
        try:
            with open(self._favorites_path, "w", encoding="utf-8") as fh:
                json.dump(favorites, fh, indent=2, ensure_ascii=False)
        except OSError as exc:
            logger.error("Could not write favorites file: %s", exc)
            raise FileManagerError(f"Could not write favorites file: {exc}") from exc

    def add_favorite(self, city: str) -> List[str]:
        """
        Add *city* to favorites (idempotent — ignores duplicates).

        Returns the updated list.
        """
        city = city.strip().title()
        favorites = self.load_favorites()
        if city not in favorites:
            favorites.append(city)
            self.save_favorites(favorites)
        return favorites

    def remove_favorite(self, city: str) -> List[str]:
        """
        Remove *city* from favorites.

        Returns the updated list.
        """
        favorites = self.load_favorites()
        updated = [c for c in favorites if c.lower() != city.lower()]
        self.save_favorites(updated)
        return updated

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def load_config(self) -> dict:
        """
        Load application configuration from disk.

        Returns default config if the file does not exist.
        """
        if not os.path.exists(self._config_path):
            return dict(_DEFAULT_CONFIG)
        try:
            with open(self._config_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            # Merge with defaults so new keys are always present
            merged = dict(_DEFAULT_CONFIG)
            merged.update(data)
            return merged
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Could not load config: %s", exc)
            return dict(_DEFAULT_CONFIG)

    def save_config(self, config: dict) -> None:
        """Persist application configuration to disk."""
        try:
            with open(self._config_path, "w", encoding="utf-8") as fh:
                json.dump(config, fh, indent=2, ensure_ascii=False)
        except OSError as exc:
            logger.error("Could not write config file: %s", exc)
            raise FileManagerError(f"Could not write config file: {exc}") from exc

    def update_config(self, **kwargs) -> dict:
        """
        Update one or more config values and persist.

        Example
        -------
        ``file_manager.update_config(unit="F", theme="light")``
        """
        config = self.load_config()
        config.update(kwargs)
        self.save_config(config)
        return config

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_data_directory(self) -> None:
        """Create the data directory if it does not already exist."""
        for path in (self._favorites_path, self._config_path):
            directory = os.path.dirname(path)
            if directory:
                try:
                    os.makedirs(directory, exist_ok=True)
                except OSError as exc:
                    logger.error("Cannot create data directory: %s", exc)
