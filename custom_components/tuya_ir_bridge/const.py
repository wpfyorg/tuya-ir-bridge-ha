"""Constants for Tuya IR Bridge."""

from __future__ import annotations

from homeassistant.components.climate.const import (
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    HVACMode,
)

DOMAIN = "tuya_ir_bridge"

CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"
CONF_REGION = "region"
CONF_IR_HUB_ID = "ir_hub_id"
CONF_AC_REMOTE_ID = "ac_remote_id"
CONF_AC_NAME = "ac_name"
CONF_GENERIC_REMOTE_ID = "generic_remote_id"
CONF_GENERIC_REMOTE_NAME = "generic_remote_name"

DEFAULT_AC_NAME = "Tuya IR AC"
DEFAULT_GENERIC_REMOTE_NAME = "Tuya IR Remote"

REGION_ENDPOINTS = {
    "CN": "https://openapi.tuyacn.com",
    "EU": "https://openapi.tuyaeu.com",
    "IN": "https://openapi.tuyain.com",
    "SG": "https://openapi-sg.iotbing.com",
    "US": "https://openapi.tuyaus.com",
}

TUYA_TO_HVAC = {
    "0": HVACMode.COOL,
    "1": HVACMode.HEAT,
    "2": HVACMode.AUTO,
    "3": HVACMode.FAN_ONLY,
    "4": HVACMode.DRY,
}

HVAC_TO_TUYA = {value: key for key, value in TUYA_TO_HVAC.items()}

TUYA_TO_FAN = {
    "0": FAN_AUTO,
    "1": FAN_LOW,
    "2": FAN_MEDIUM,
    "3": FAN_HIGH,
}

FAN_TO_TUYA = {value: key for key, value in TUYA_TO_FAN.items()}

DEFAULT_HVAC_MODE = HVACMode.COOL
DEFAULT_FAN_MODE = FAN_AUTO
DEFAULT_TARGET_TEMP = 24
