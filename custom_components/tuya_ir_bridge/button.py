"""Button platform for Tuya IR Bridge."""

from __future__ import annotations

from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import TuyaIrApi
from .const import (
    CONF_GENERIC_REMOTE_ID,
    CONF_GENERIC_REMOTE_NAME,
    CONF_IR_HUB_ID,
    DOMAIN,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up raw IR button entities."""
    if CONF_GENERIC_REMOTE_ID not in entry.data:
        return

    api = hass.data[DOMAIN][entry.entry_id]
    ir_hub_id = entry.data[CONF_IR_HUB_ID]
    remote_id = entry.data[CONF_GENERIC_REMOTE_ID]
    remote_name = entry.data[CONF_GENERIC_REMOTE_NAME]
    remote_data = await api.async_get_remote_keys(ir_hub_id, remote_id)
    category_id = remote_data["category_id"]

    async_add_entities(
        TuyaIrRawButton(
            api=api,
            entry_id=entry.entry_id,
            ir_hub_id=ir_hub_id,
            remote_id=remote_id,
            remote_name=remote_name,
            category_id=category_id,
            key_data=key_data,
        )
        for key_data in remote_data.get("key_list", [])
    )


class TuyaIrRawButton(ButtonEntity):
    """Button entity for one raw IR remote key."""

    _attr_has_entity_name = True

    def __init__(
        self,
        *,
        api: TuyaIrApi,
        entry_id: str,
        ir_hub_id: str,
        remote_id: str,
        remote_name: str,
        category_id: int,
        key_data: dict[str, Any],
    ) -> None:
        self._api = api
        self._ir_hub_id = ir_hub_id
        self._remote_id = remote_id
        self._remote_name = remote_name
        self._category_id = category_id
        self._key = key_data["key"]
        self._key_id = int(key_data["key_id"])
        self._attr_name = str(key_data.get("key_name") or self._key).replace("_", " ")
        self._attr_unique_id = f"{entry_id}_{remote_id}_{self._key_id}"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._remote_id)},
            "manufacturer": "Tuya",
            "name": self._remote_name,
            "via_device": (DOMAIN, self._ir_hub_id),
        }

    async def async_press(self) -> None:
        """Send the raw IR key."""
        await self._api.async_send_raw_key(
            self._ir_hub_id,
            self._remote_id,
            category_id=self._category_id,
            key_id=self._key_id,
            key=self._key,
        )
