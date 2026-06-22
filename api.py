"""
api.py
------
WeatherAPI class — handles all OpenWeatherMap HTTP requests.
Separates networking concerns from GUI and business logic.
"""

import requests
from typing import Optional, Tuple

from models import WeatherData, ForecastData, ForecastEntry


# Base URLs for OpenWeatherMap v2.5 REST API
_BASE_CURRENT = "https://api.openweathermap.org/data/2.5/weather"
_BASE_FORECAST = "https://api.openweathermap.org/data/2.5/forecast"
_TIMEOUT = 10  # seconds


class WeatherAPIError(Exception):
    """Raised when the API returns an error or the network is unavailable."""
    pass


class WeatherAPI:
    """
    Encapsulates all interactions with the OpenWeatherMap API.

    Parameters
    ----------
    api_key : str
        Your personal OpenWeatherMap API key.
    """

    def __init__(self, api_key: str) -> None:
        if not api_key or api_key.strip() == "":
            raise ValueError("API key must not be empty.")
        self._api_key = api_key.strip()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def get_current_weather(self, city: str) -> WeatherData:
        """
        Fetch current weather for *city*.

        Parameters
        ----------
        city : str
            City name (and optional country code), e.g. ``"London,GB"``.

        Returns
        -------
        WeatherData
            Parsed weather data model.

        Raises
        ------
        WeatherAPIError
            On network failure, invalid city, or API quota exceeded.
        """
        city = city.strip()
        if not city:
            raise WeatherAPIError("City name cannot be empty.")

        params = {
            "q": city,
            "appid": self._api_key,
            "units": "metric",
        }
        raw = self._get(_BASE_CURRENT, params)
        return self._parse_current(raw)

    def get_forecast(self, city: str) -> ForecastData:
        """
        Fetch 5-day / 3-hour forecast for *city*.

        Parameters
        ----------
        city : str
            City name.

        Returns
        -------
        ForecastData
            Parsed forecast data model.

        Raises
        ------
        WeatherAPIError
            On network failure, invalid city, or API quota exceeded.
        """
        city = city.strip()
        if not city:
            raise WeatherAPIError("City name cannot be empty.")

        params = {
            "q": city,
            "appid": self._api_key,
            "units": "metric",
        }
        raw = self._get(_BASE_FORECAST, params)
        return self._parse_forecast(raw)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get(self, url: str, params: dict) -> dict:
        """
        Perform a GET request and return parsed JSON.

        Raises
        ------
        WeatherAPIError
            Wraps requests exceptions and non-200 HTTP responses.
        """
        try:
            response = requests.get(url, params=params, timeout=_TIMEOUT)
        except requests.exceptions.ConnectionError:
            raise WeatherAPIError(
                "No internet connection. Please check your network and try again."
            )
        except requests.exceptions.Timeout:
            raise WeatherAPIError(
                "Request timed out. The server took too long to respond."
            )
        except requests.exceptions.RequestException as exc:
            raise WeatherAPIError(f"Network error: {exc}") from exc

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            raise WeatherAPIError(
                "Invalid API key. Please check your OpenWeatherMap key."
            )
        elif response.status_code == 404:
            raise WeatherAPIError(
                "City not found. Please check the spelling and try again."
            )
        elif response.status_code == 429:
            raise WeatherAPIError(
                "API rate limit exceeded. Please wait before making another request."
            )
        else:
            message = response.json().get("message", "Unknown error.")
            raise WeatherAPIError(f"API error {response.status_code}: {message}")

    @staticmethod
    def _parse_current(data: dict) -> WeatherData:
        """Parse the raw JSON response from the current-weather endpoint."""
        try:
            return WeatherData(
                city=data["name"],
                country=data["sys"]["country"],
                temperature_c=data["main"]["temp"],
                feels_like_c=data["main"]["feels_like"],
                humidity=data["main"]["humidity"],
                wind_speed=data["wind"]["speed"],
                wind_direction=data["wind"].get("deg", 0),
                condition=data["weather"][0]["main"],
                description=data["weather"][0]["description"],
                icon=data["weather"][0]["icon"],
                visibility=data.get("visibility", 0),
                pressure=data["main"]["pressure"],
                sunrise=data["sys"]["sunrise"],
                sunset=data["sys"]["sunset"],
            )
        except (KeyError, IndexError) as exc:
            raise WeatherAPIError(f"Unexpected API response format: {exc}") from exc

    @staticmethod
    def _parse_forecast(data: dict) -> ForecastData:
        """Parse the raw JSON response from the forecast endpoint."""
        try:
            entries = []
            for item in data["list"]:
                entry = ForecastEntry(
                    dt=item["dt"],
                    dt_txt=item["dt_txt"],
                    temperature_c=item["main"]["temp"],
                    feels_like_c=item["main"]["feels_like"],
                    humidity=item["main"]["humidity"],
                    wind_speed=item["wind"]["speed"],
                    condition=item["weather"][0]["main"],
                    description=item["weather"][0]["description"],
                    icon=item["weather"][0]["icon"],
                    pop=item.get("pop", 0.0),
                )
                entries.append(entry)
            city_info = data["city"]
            return ForecastData(
                city=city_info["name"],
                country=city_info["country"],
                entries=entries,
            )
        except (KeyError, IndexError) as exc:
            raise WeatherAPIError(f"Unexpected forecast response format: {exc}") from exc
