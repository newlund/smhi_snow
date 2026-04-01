# SMHI Snow - Home Assistant Custom Component

A Home Assistant integration for [SMHI](https://www.smhi.se/) (Swedish Meteorological and Hydrological Institute) weather data using their open data API.

## Features

- Weather entity with current conditions and forecasts (daily + hourly)
- 25 sensors covering:
  - Thunder probability, precipitation probability, precipitation amounts (mean/min/max/median)
  - Cloud cover (total, low, medium, high), cloud base/top altitude
  - Precipitation category, frozen precipitation, visibility
  - Fire risk: FWI index, fire weather index, grass fire risk, forest dryness, spread rate, drought code, and more
- Swedish and English translations

## Installation

Copy the `smhi_snow` folder to your Home Assistant `custom_components` directory:

```
custom_components/
└── smhi_snow/
    ├── __init__.py
    ├── config_flow.py
    ├── const.py
    ├── coordinator.py
    ├── entity.py
    ├── icons.json
    ├── manifest.json
    ├── sensor.py
    ├── strings.json
    ├── translations/
    │   ├── en.json
    │   └── sv.json
    └── weather.py
```

Restart Home Assistant, then add the integration via Settings → Devices & Services → Add Integration → SMHI Snow.

## API

This component calls the SMHI Open Data APIs directly (no external Python libraries required):

- Weather forecasts: `snow1g/version/1` — [Documentation](https://opendata.smhi.se/metfcst/snow1gv1/introduction)
- Fire risk forecasts: `fwif1g/version/1` — [Documentation](https://opendata.smhi.se/metfcst/fwif/introduction)

Data is polled every 31 minutes. Fire data is fetched separately and fails gracefully — weather data always updates even if the fire API is unavailable.

## License

Data provided by SMHI under their [open data terms](https://www.smhi.se/data/oppna-data/Information-om-oppna-data/villkor-for-anvandning).
