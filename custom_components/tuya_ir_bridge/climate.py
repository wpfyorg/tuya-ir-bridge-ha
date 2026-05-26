"""Climate platform for Tuya IR Bridge."""

from __future__ import annotations

from typing import Any

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import ClimateEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import TuyaIrApi
from .const import (
    CONF_AC_NAME,
    CONF_AC_REMOTE_ID,
    CONF_IR_HUB_ID,
    DEFAULT_FAN_MODE,
    DEFAULT_HVAC_MODE,
    DEFAULT_TARGET_TEMP,
    DOMAIN,
    FAN_TO_TUYA,
    HVAC_TO_TUYA,
    TUYA_TO_FAN,
    TUYA_TO_HVAC,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AC climate entities."""
    if CONF_AC_REMOTE_ID not in entry.data:
        return

    api = hass.data[DOMAIN][entry.entry_id]
    entity = TuyaIrAcClimate(api, entry)
    async_add_entities([entity])
    await entity.async_load_initial_state()


class TuyaIrAcClimate(ClimateEntity):
    """Assumed-state climate entity backed by Tuya IR AC commands."""

    _attr_has_entity_name = True
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = 18
    _attr_max_temp = 30
    _attr_target_temperature_step = 1
    _attr_hvac_modes = list(HVAC_TO_TUYA)
    _attr_fan_modes = list(FAN_TO_TUYA)
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )

    def __init__(self, api: TuyaIrApi, entry: ConfigEntry) -> None:
        self._api = api
        self._ir_hub_id = entry.data[CONF_IR_HUB_ID]
        self._remote_id = entry.data[CONF_AC_REMOTE_ID]
        self._attr_name = entry.data[CONF_AC_NAME]
        self._attr_unique_id = f"{entry.entry_id}_{self._remote_id}_climate"
        self._attr_hvac_mode = DEFAULT_HVAC_MODE
        self._attr_target_temperature = DEFAULT_TARGET_TEMP
        self._attr_fan_mode = DEFAULT_FAN_MODE

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._remote_id)},
            "manufacturer": "Tuya",
            "name": self._attr_name,
            "via_device": (DOMAIN, self._ir_hub_id),
        }

    async def async_load_initial_state(self) -> None:
        """Load the cloud-side assumed state if available."""
        status = await self._api.async_get_ac_status(self._ir_hub_id, self._remote_id)
        self._attr_hvac_mode = TUYA_TO_HVAC.get(
            str(status.get("mode")), DEFAULT_HVAC_MODE
        )
        self._attr_fan_mode = TUYA_TO_FAN.get(str(status.get("wind")), DEFAULT_FAN_MODE)
        if status.get("power") in ("0", 0, False):
            self._attr_hvac_mode = "off"
        if status.get("temp") is not None:
            self._attr_target_temperature = int(float(status["temp"]))
        self.async_write_ha_state()

    async def async_turn_on(self) -> None:
        """Turn the AC on using the current assumed state."""
        if self._attr_hvac_mode == "off":
            self._attr_hvac_mode = DEFAULT_HVAC_MODE
        await self._send_scene(power=True)

    async def async_turn_off(self) -> None:
        """Turn the AC off."""
        await self._send_scene(power=False)
        self._attr_hvac_mode = "off"
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set target temperature and optionally HVAC mode."""
        if ATTR_TEMPERATURE in kwargs:
            self._attr_target_temperature = int(kwargs[ATTR_TEMPERATURE])
        if (hvac_mode := kwargs.get("hvac_mode")) is not None:
            self._attr_hvac_mode = hvac_mode
        await self._send_scene(power=self._attr_hvac_mode != "off")

    async def async_set_hvac_mode(self, hvac_mode: str) -> None:
        """Set HVAC mode."""
        self._attr_hvac_mode = hvac_mode
        await self._send_scene(power=hvac_mode != "off")

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set fan mode."""
        self._attr_fan_mode = fan_mode
        await self._send_scene(power=self._attr_hvac_mode != "off")

    async def _send_scene(self, *, power: bool) -> None:
        mode = self._attr_hvac_mode
        if mode == "off":
            mode = DEFAULT_HVAC_MODE
        await self._api.async_send_ac_scene(
            self._ir_hub_id,
            self._remote_id,
            power=power,
            mode=HVAC_TO_TUYA[mode],
            temperature=int(self._attr_target_temperature),
            fan=FAN_TO_TUYA[self._attr_fan_mode],
        )
        self.async_write_ha_state()
