# ⛅ Smart Weather Dashboard

A modern, fully-featured weather application built with Python 3, Tkinter, and the OpenWeatherMap API.

---

## ✨ Features

| Feature | Details |
|---|---|
| Current weather | Temperature, humidity, wind, pressure, visibility |
| 5-day forecast | 3-hour granularity, plotted as an interactive chart |
| Favourite cities | Persist across sessions via JSON file |
| Dark / Light mode | Toggle with a single button |
| °C / °F toggle | Instantly updates all displayed values and the chart |
| Auto-refresh | Re-fetches data every 5 minutes (opt-in) |
| Loading indicator | Spinner label while network calls run on a background thread |
| Exception handling | API errors, network errors, file errors — all shown as friendly dialogs |

---

## 📂 Project Structure

```
smart_weather_dashboard/
├── main.py            # WeatherApp controller & entry point
├── api.py             # WeatherAPI — OpenWeatherMap integration
├── gui.py             # GUIManager — all Tkinter widgets
├── file_manager.py    # FileManager — JSON persistence
├── models.py          # WeatherData, ForecastData, ForecastEntry dataclasses
├── requirements.txt   # Python dependencies
├── README.md          # This file
└── data/              # Auto-created at runtime
    ├── favorites.json
    └── config.json
```

---

## 🚀 Quick Start

### 1. Clone / download the project

```bash
git clone https://github.com/<your-username>/smart-weather-dashboard.git
cd smart_weather_dashboard
```

### 2. Create and activate a virtual environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate          # macOS / Linux
venv\Scripts\activate             # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

Tkinter ships with the standard Python distribution on macOS and Windows.  
On Debian/Ubuntu you may need:

```bash
sudo apt-get install python3-tk
```

### 4. Get a free OpenWeatherMap API key

1. Register at <https://openweathermap.org/api>
2. Navigate to **API keys** in your account dashboard
3. Copy the default key (it activates within a few minutes of registration)

### 5. Provide the API key

**Option A — environment variable (recommended for development):**

```bash
export OWM_API_KEY="your_key_here"   # macOS / Linux
set    OWM_API_KEY=your_key_here     # Windows CMD
```

**Option B — first-launch dialog:**  
Simply run the app without setting the variable; a dialog will ask you to paste the key. It is saved to `data/config.json` for future runs.

### 6. Run the application

```bash
python main.py
```

---

## 🖼 UI Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  ⛅ Smart Weather Dashboard  [Search…] [🔍 Search] [★ Favorite] │  ← Top bar
│                                         [Auto-refresh] [°C/°F] [Theme] │
├──────────────┬──────────────────────────────────────────────────┤
│ ★ Favorites  │  City, Country                          🌤        │
│  London      │  24.3 °C   Clear sky     Feels like 22.1 °C      │  ← Center card
│  Tokyo       │  💧 65%  💨 4.2 m/s  🔵 1012 hPa  👁 10 km      │
│  New York    ├──────────────────────────────────────────────────┤
│              │  📈  5-Day Temperature Trend (Matplotlib chart)  │  ← Chart
│  [✕ Remove] │                                                  │
└──────────────┴──────────────────────────────────────────────────┘
```

---

## 🔑 API Key Security

- **Never commit** your API key to version control.
- Prefer the `OWM_API_KEY` environment variable.
- The key is stored locally in `data/config.json` which is listed in `.gitignore`.

---

## 📦 Dependencies

| Package | Version | Purpose |
|---|---|---|
| `requests` | 2.31.0 | HTTP calls to OpenWeatherMap |
| `matplotlib` | 3.8.3 | Temperature trend chart |
| `tkinter` | stdlib | GUI framework |

---

## 🛡 Error Handling

| Scenario | Behaviour |
|---|---|
| Empty city input | Dialog: "Please enter a city name." |
| City not found (404) | Dialog: "City not found. Please check the spelling." |
| Invalid API key (401) | Dialog: "Invalid API key." |
| Rate limit exceeded (429) | Dialog: "API rate limit exceeded." |
| No internet connection | Dialog: "No internet connection." |
| Corrupt favorites file | Logged; empty list returned gracefully |
| Corrupt config file | Logged; default config used |

---

## 🧪 Class Diagram

```
WeatherApp ──uses──► WeatherAPI   ──returns──► WeatherData
          ──uses──► FileManager               ForecastData
          ──uses──► GUIManager                ForecastEntry
```

---

## 📄 License

MIT — free to use for academic and personal projects.
