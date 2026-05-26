"""Config flow for Tuya IR Bridge."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import TuyaIrApi, TuyaIrApiError
from .const import (
    CONF_AC_NAME,
    CONF_AC_REMOTE_ID,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_GENERIC_REMOTE_ID,
    CONF_GENERIC_REMOTE_NAME,
    CONF_IR_HUB_ID,
    CONF_REGION,
    DEFAULT_AC_NAME,
    DEFAULT_GENERIC_REMOTE_NAME,
    DOMAIN,
    REGION_ENDPOINTS,
)


class TuyaIrBridgeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tuya IR Bridge."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Configure the integration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            cleaned = _clean_user_input(user_input)
            await self.async_set_unique_id(cleaned[CONF_IR_HUB_ID])
            self._abort_if_unique_id_configured()

            errors = await _validate_input(self.hass, cleaned)
            if not errors:
                return self.async_create_entry(
                    title=cleaned[CONF_NAME],
                    data=cleaned,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(user_input),
            errors=errors,
        )


def _schema(defaults: dict[str, Any] | None) -> vol.Schema:
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_NAME, default=defaults.get(CONF_NAME, "Tuya IR Bridge")
            ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
            vol.Required(CONF_REGION, default=defaults.get(CONF_REGION, "IN")): SelectSelector(
                SelectSelectorConfig(
                    options=sorted(REGION_ENDPOINTS),
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(CONF_CLIENT_ID, default=defaults.get(CONF_CLIENT_ID, "")): TextSelector(
                TextSelectorConfig(type=TextSelectorType.TEXT)
            ),
            vol.Required(CONF_CLIENT_SECRET): TextSelector(
                TextSelectorConfig(type=TextSelectorType.PASSWORD)
            ),
            vol.Required(CONF_IR_HUB_ID, default=defaults.get(CONF_IR_HUB_ID, "")): TextSelector(
                TextSelectorConfig(type=TextSelectorType.TEXT)
            ),
            vol.Optional(
                CONF_AC_REMOTE_ID, default=defaults.get(CONF_AC_REMOTE_ID, "")
            ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
            vol.Optional(
                CONF_AC_NAME, default=defaults.get(CONF_AC_NAME, DEFAULT_AC_NAME)
            ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
            vol.Optional(
                CONF_GENERIC_REMOTE_ID,
                default=defaults.get(CONF_GENERIC_REMOTE_ID, ""),
            ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
            vol.Optional(
                CONF_GENERIC_REMOTE_NAME,
                default=defaults.get(
                    CONF_GENERIC_REMOTE_NAME, DEFAULT_GENERIC_REMOTE_NAME
                ),
            ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
        }
    )


def _clean_user_input(user_input: dict[str, Any]) -> dict[str, Any]:
    cleaned = {
        key: value.strip() if isinstance(value, str) else value
        for key, value in user_input.items()
    }
    if not cleaned.get(CONF_AC_REMOTE_ID):
        cleaned.pop(CONF_AC_REMOTE_ID, None)
        cleaned.pop(CONF_AC_NAME, None)
    if not cleaned.get(CONF_GENERIC_REMOTE_ID):
        cleaned.pop(CONF_GENERIC_REMOTE_ID, None)
        cleaned.pop(CONF_GENERIC_REMOTE_NAME, None)
    return cleaned


async def _validate_input(
    hass: HomeAssistant, user_input: dict[str, Any]
) -> dict[str, str]:
    api = TuyaIrApi(
        session=async_get_clientsession(hass),
        endpoint=REGION_ENDPOINTS[user_input[CONF_REGION]],
        client_id=user_input[CONF_CLIENT_ID],
        client_secret=user_input[CONF_CLIENT_SECRET],
    )
    try:
        await api.async_get_access_token()
        if CONF_AC_REMOTE_ID in user_input:
            await api.async_get_ac_status(
                user_input[CONF_IR_HUB_ID], user_input[CONF_AC_REMOTE_ID]
            )
        if CONF_GENERIC_REMOTE_ID in user_input:
            await api.async_get_remote_keys(
                user_input[CONF_IR_HUB_ID], user_input[CONF_GENERIC_REMOTE_ID]
            )
    except TuyaIrApiError:
        return {"base": "cannot_connect"}
    return {}
