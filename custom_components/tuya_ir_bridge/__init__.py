"""Tuya IR Bridge integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import TuyaIrApi
from .const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_REGION,
    DOMAIN,
    REGION_ENDPOINTS,
)

PLATFORMS = [Platform.CLIMATE, Platform.BUTTON]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Tuya IR Bridge from a config entry."""
    endpoint = REGION_ENDPOINTS[entry.data[CONF_REGION]]
    api = TuyaIrApi(
        session=async_get_clientsession(hass),
        endpoint=endpoint,
        client_id=entry.data[CONF_CLIENT_ID],
        client_secret=entry.data[CONF_CLIENT_SECRET],
    )
    await api.async_get_access_token()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = api
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
