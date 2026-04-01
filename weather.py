"""Support for the Swedish weather institute weather service."""

from __future__ import annotations

from typing import Final

from homeassistant.components.weather import (
    ATTR_CONDITION_CLEAR_NIGHT,
    ATTR_CONDITION_CLOUDY,
    ATTR_CONDITION_FOG,
    ATTR_CONDITION_LIGHTNING,
    ATTR_CONDITION_LIGHTNING_RAINY,
    ATTR_CONDITION_PARTLYCLOUDY,
    ATTR_CONDITION_POURING,
    ATTR_CONDITION_RAINY,
    ATTR_CONDITION_SNOWY,
    ATTR_CONDITION_SNOWY_RAINY,
    ATTR_CONDITION_SUNNY,
    ATTR_FORECAST_CLOUD_COVERAGE,
    ATTR_FORECAST_CONDITION,
    ATTR_FORECAST_HUMIDITY,
    ATTR_FORECAST_NATIVE_PRECIPITATION,
    ATTR_FORECAST_NATIVE_PRESSURE,
    ATTR_FORECAST_NATIVE_TEMP,
    ATTR_FORECAST_NATIVE_TEMP_LOW,
    ATTR_FORECAST_NATIVE_WIND_GUST_SPEED,
    ATTR_FORECAST_NATIVE_WIND_SPEED,
    ATTR_FORECAST_TIME,
    ATTR_FORECAST_WIND_BEARING,
    Forecast,
    SingleCoordinatorWeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.const import (
    CONF_LATITUDE,
    CONF_LOCATION,
    CONF_LONGITUDE,
    UnitOfLength,
    UnitOfPrecipitationDepth,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import sun
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import SMHIConfigEntry
from .entity import SmhiEntity

# Used to map condition from API results
CONDITION_CLASSES: Final[dict[str, list[int]]] = {
    ATTR_CONDITION_CLOUDY: [5, 6],
    ATTR_CONDITION_FOG: [7],
    ATTR_CONDITION_LIGHTNING: [21],
    ATTR_CONDITION_LIGHTNING_RAINY: [11],
    ATTR_CONDITION_PARTLYCLOUDY: [3, 4],
    ATTR_CONDITION_POURING: [10, 20],
    ATTR_CONDITION_RAINY: [8, 9, 18, 19],
    ATTR_CONDITION_SNOWY: [15, 16, 17, 25, 26, 27],
    ATTR_CONDITION_SNOWY_RAINY: [12, 13, 14, 22, 23, 24],
    ATTR_CONDITION_SUNNY: [1, 2],
}
CONDITION_MAP: Final[dict[int, str]] = {
    code: condition
    for condition, codes in CONDITION_CLASSES.items()
    for code in codes
}


def _octas_to_pct(value: float | None) -> int | None:
    """Convert cloud cover from octas (0-8) to percentage."""
    if value is None:
        return None
    return round(value * 100 / 8)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SMHIConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add a weather entity from map location."""
    location = config_entry.data
    async_add_entities(
        [
            SmhiWeather(
                location[CONF_LOCATION][CONF_LATITUDE],
                location[CONF_LOCATION][CONF_LONGITUDE],
                coordinator=config_entry.runtime_data,
            )
        ]
    )


class SmhiWeather(SmhiEntity, SingleCoordinatorWeatherEntity):
    """Representation of a weather entity."""

    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_visibility_unit = UnitOfLength.KILOMETERS
    _attr_native_precipitation_unit = UnitOfPrecipitationDepth.MILLIMETERS
    _attr_native_wind_speed_unit = UnitOfSpeed.METERS_PER_SECOND
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_supported_features = (
        WeatherEntityFeature.FORECAST_DAILY
        | WeatherEntityFeature.FORECAST_HOURLY
    )
    _attr_name = None

    def update_entity_data(self) -> None:
        """Refresh the entity data."""
        if not (hourly := self.coordinator.data.weather.hourly):
            return
        d = hourly[0]
        self._attr_native_temperature = d.get("air_temperature")
        self._attr_humidity = d.get("relative_humidity")
        self._attr_native_wind_speed = d.get("wind_speed")
        self._attr_wind_bearing = d.get("wind_from_direction")
        self._attr_native_visibility = d.get("visibility_in_air")
        self._attr_native_pressure = d.get("air_pressure_at_mean_sea_level")
        self._attr_native_wind_gust_speed = d.get("wind_speed_of_gust")
        self._attr_cloud_coverage = _octas_to_pct(d.get("cloud_area_fraction"))
        self._attr_condition = CONDITION_MAP.get(d.get("symbol_code"))
        if self._attr_condition == ATTR_CONDITION_SUNNY and not sun.is_up(
            self.coordinator.hass
        ):
            self._attr_condition = ATTR_CONDITION_CLEAR_NIGHT

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.update_entity_data()
        super()._handle_coordinator_update()

    def _get_forecast_data(
        self, forecast_data: list[dict] | None
    ) -> list[Forecast] | None:
        """Get forecast data."""
        if forecast_data is None or len(forecast_data) < 2:
            return None

        data: list[Forecast] = []
        for forecast in forecast_data[1:]:
            condition = CONDITION_MAP.get(forecast.get("symbol_code"))
            if condition == ATTR_CONDITION_SUNNY and not sun.is_up(
                self.hass, forecast["valid_time"]
            ):
                condition = ATTR_CONDITION_CLEAR_NIGHT

            data.append(
                Forecast(
                    {
                        ATTR_FORECAST_TIME: forecast["valid_time"].isoformat(),
                        ATTR_FORECAST_NATIVE_TEMP: forecast.get("air_temperature"),
                        ATTR_FORECAST_NATIVE_TEMP_LOW: forecast.get(
                            "air_temperature"
                        ),
                        ATTR_FORECAST_NATIVE_PRECIPITATION: forecast.get(
                            "precipitation_amount_mean"
                        ),
                        ATTR_FORECAST_CONDITION: condition,
                        ATTR_FORECAST_NATIVE_PRESSURE: forecast.get(
                            "air_pressure_at_mean_sea_level"
                        ),
                        ATTR_FORECAST_WIND_BEARING: forecast.get(
                            "wind_from_direction"
                        ),
                        ATTR_FORECAST_NATIVE_WIND_SPEED: forecast.get("wind_speed"),
                        ATTR_FORECAST_HUMIDITY: forecast.get("relative_humidity"),
                        ATTR_FORECAST_NATIVE_WIND_GUST_SPEED: forecast.get(
                            "wind_speed_of_gust"
                        ),
                        ATTR_FORECAST_CLOUD_COVERAGE: _octas_to_pct(
                            forecast.get("cloud_area_fraction")
                        ),
                    }
                )
            )
        return data

    def _async_forecast_daily(self) -> list[Forecast] | None:
        """Service to retrieve the daily forecast."""
        return self._get_forecast_data(self.coordinator.data.weather.daily)

    def _async_forecast_hourly(self) -> list[Forecast] | None:
        """Service to retrieve the hourly forecast."""
        return self._get_forecast_data(self.coordinator.data.weather.hourly)
