"""Tuya Cloud IR API client."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any

from aiohttp import ClientSession


class TuyaIrApiError(Exception):
    """Raised when Tuya returns an unsuccessful response."""


TOKEN_INVALID_CODES = {"1010", "1011", "1012", "1013", "1014"}


class TuyaIrApi:
    """Small client for the Tuya Cloud infrared endpoints."""

    def __init__(
        self,
        session: ClientSession,
        endpoint: str,
        client_id: str,
        client_secret: str,
    ) -> None:
        self._session = session
        self._endpoint = endpoint.rstrip("/")
        self._client_id = client_id
        self._client_secret = client_secret
        self._access_token = ""
        self._token_expires_at = 0

    async def async_get_access_token(self) -> None:
        """Refresh the access token."""
        self._access_token = ""
        self._token_expires_at = -1
        response = await self._async_request("GET", "/v1.0/token?grant_type=1")
        result = response["result"]
        self._access_token = result["access_token"]
        expires_in = result.get("expire_time", result.get("expire", 3600))
        self._token_expires_at = int(time.time()) + int(expires_in)

    async def async_get_ac_status(self, ir_hub_id: str, remote_id: str) -> dict[str, Any]:
        """Return the current cloud-side AC remote status."""
        response = await self._async_request(
            "GET", f"/v2.0/infrareds/{ir_hub_id}/remotes/{remote_id}/ac/status"
        )
        return response["result"]

    async def async_send_ac_scene(
        self,
        ir_hub_id: str,
        remote_id: str,
        *,
        power: bool,
        mode: str,
        temperature: int,
        fan: str,
    ) -> None:
        """Send a full AC IR state packet."""
        await self._async_request(
            "POST",
            f"/v2.0/infrareds/{ir_hub_id}/air-conditioners/{remote_id}/scenes/command",
            {
                "power": 1 if power else 0,
                "mode": int(mode),
                "temp": int(temperature),
                "wind": int(fan),
            },
        )

    async def async_get_remote_keys(self, ir_hub_id: str, remote_id: str) -> dict[str, Any]:
        """Return raw key metadata for a saved non-AC IR remote."""
        response = await self._async_request(
            "GET", f"/v2.0/infrareds/{ir_hub_id}/remotes/{remote_id}/keys"
        )
        return response["result"]

    async def async_send_raw_key(
        self,
        ir_hub_id: str,
        remote_id: str,
        *,
        category_id: int,
        key_id: int,
        key: str,
    ) -> None:
        """Send a raw key for a saved IR remote."""
        await self._async_request(
            "POST",
            f"/v2.0/infrareds/{ir_hub_id}/remotes/{remote_id}/raw/command",
            {"category_id": category_id, "key_id": key_id, "key": key},
        )

    async def _async_request(
        self, method: str, path: str, body: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        if self._token_expired(path):
            await self.async_get_access_token()

        data = await self._async_send(method, path, body)
        if not data.get("success") and self._is_token_invalid(data, path):
            self._access_token = ""
            self._token_expires_at = 0
            await self.async_get_access_token()
            data = await self._async_send(method, path, body)

        if not data.get("success"):
            raise TuyaIrApiError(
                f"Tuya API error for {method} {path}: "
                f"{data.get('code')} {data.get('msg')}"
            )
        return data

    async def _async_send(
        self, method: str, path: str, body: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Send a signed request without refresh/retry handling."""
        body_text = json.dumps(body, separators=(",", ":")) if body is not None else ""
        timestamp = str(int(time.time() * 1000))
        headers = self._headers(method, path, timestamp, body_text)

        async with self._session.request(
            method,
            f"{self._endpoint}{path}",
            headers=headers,
            data=body_text or None,
        ) as response:
            return await response.json()

    def _token_expired(self, path: str) -> bool:
        if path.startswith("/v1.0/token"):
            return False
        return not self._access_token or int(time.time()) > self._token_expires_at - 30

    def _is_token_invalid(self, data: dict[str, Any], path: str) -> bool:
        if path.startswith("/v1.0/token"):
            return False
        return str(data.get("code")) in TOKEN_INVALID_CODES

    def _headers(
        self, method: str, path: str, timestamp: str, body_text: str
    ) -> dict[str, str]:
        payload = (
            self._client_id
            + self._access_token
            + timestamp
            + method
            + "\n"
            + hashlib.sha256(body_text.encode()).hexdigest()
            + "\n\n/"
            + path.lstrip("/")
        )
        signature = hmac.new(
            self._client_secret.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()
        return {
            "client_id": self._client_id,
            "access_token": self._access_token,
            "sign": signature.upper(),
            "t": timestamp,
            "sign_method": "HMAC-SHA256",
            "Content-Type": "application/json",
        }
