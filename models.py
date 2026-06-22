"""
models.py
---------
Data models for the Smart Weather Dashboard application.
Contains WeatherData and ForecastEntry dataclasses.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class WeatherData:
    """Represents current weather conditions for a city."""

    city: str
    country: str
    temperature_c: float
    feels_like_c: float
    humidity: int
    wind_speed: float          # m/s
    wind_direction: int        # degrees
    condition: str             # e.g. "Clear", "Clouds"
    description: str           # e.g. "clear sky"
    icon: str                  # OWM icon code
    visibility: int            # metres
    pressure: int              # hPa
    sunrise: int               # UNIX timestamp
    sunset: int                # UNIX timestamp

    # ---------- derived helpers ----------
    @property
    def temperature_f(self) -> float:
        """Convert Celsius to Fahrenheit."""
        return round(self.temperature_c * 9 / 5 + 32, 1)

    @property
    def feels_like_f(self) -> float:
        """Convert feels-like Celsius to Fahrenheit."""
        return round(self.feels_like_c * 9 / 5 + 32, 1)

    @property
    def wind_speed_mph(self) -> float:
        """Convert wind speed from m/s to mph."""
        return round(self.wind_speed * 2.237, 1)

    def to_display_dict(self, unit: str = "C") -> dict:
        """Return a flat dict of values ready for GUI display."""
        if unit == "C":
            temp = f"{self.temperature_c:.1f} °C"
            feels = f"{self.feels_like_c:.1f} °C"
        else:
            temp = f"{self.temperature_f:.1f} °F"
            feels = f"{self.feels_like_f:.1f} °F"
        return {
            "city": f"{self.city}, {self.country}",
            "temperature": temp,
            "feels_like": feels,
            "condition": self.condition,
            "description": self.description.title(),
            "humidity": f"{self.humidity}%",
            "wind_speed": f"{self.wind_speed} m/s  ({self.wind_speed_mph} mph)",
            "pressure": f"{self.pressure} hPa",
            "visibility": f"{self.visibility / 1000:.1f} km",
            "icon": self.icon,
        }


@dataclass
class ForecastEntry:
    """Represents a single forecast data point (3-hour interval)."""

    dt: int                    # UNIX timestamp
    dt_txt: str                # human-readable datetime string
    temperature_c: float
    feels_like_c: float
    humidity: int
    wind_speed: float
    condition: str
    description: str
    icon: str
    pop: float                 # probability of precipitation 0-1

    @property
    def temperature_f(self) -> float:
        """Convert Celsius to Fahrenheit."""
        return round(self.temperature_c * 9 / 5 + 32, 1)


@dataclass
class ForecastData:
    """Holds the full 5-day forecast (list of ForecastEntry objects)."""

    city: str
    country: str
    entries: List[ForecastEntry] = field(default_factory=list)

    def temperatures_c(self) -> List[float]:
        """Return list of Celsius temperatures across all entries."""
        return [e.temperature_c for e in self.entries]

    def temperatures_f(self) -> List[float]:
        """Return list of Fahrenheit temperatures across all entries."""
        return [e.temperature_f for e in self.entries]

    def time_labels(self) -> List[str]:
        """Return short time labels suitable for chart x-axis."""
        labels = []
        for e in self.entries:
            # dt_txt format: "2024-01-15 12:00:00"
            parts = e.dt_txt.split(" ")
            date_part = parts[0][5:]   # "01-15"
            time_part = parts[1][:5]   # "12:00"
            labels.append(f"{date_part}\n{time_part}")
        return labels

    def daily_summary(self) -> List[dict]:
        """
        Aggregate entries by calendar day and return one summary per day.
        Returns up to 5 days.
        """
        daily: dict = {}
        for e in self.entries:
            day = e.dt_txt.split(" ")[0]
            if day not in daily:
                daily[day] = {"temps": [], "condition": e.condition, "icon": e.icon, "pop": e.pop}
            daily[day]["temps"].append(e.temperature_c)
        result = []
        for day, data in list(daily.items())[:5]:
            result.append({
                "date": day,
                "min_c": round(min(data["temps"]), 1),
                "max_c": round(max(data["temps"]), 1),
                "min_f": round(min(data["temps"]) * 9 / 5 + 32, 1),
                "max_f": round(max(data["temps"]) * 9 / 5 + 32, 1),
                "condition": data["condition"],
                "icon": data["icon"],
                "pop": round(data["pop"] * 100),
            })
        return result
