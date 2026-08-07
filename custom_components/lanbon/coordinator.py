"""LANBON API client + DataUpdateCoordinator."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_WS_DISABLED,
    DEFAULT_PORT,
    DOMAIN,
    WS_UNSUPPORTED_FAIL_THRESHOLD,
    product_is_http_only,
)

_LOGGER = logging.getLogger(__name__)


def _is_ws_unsupported_error(err: BaseException) -> bool:
    """True when the panel rejects WebSocket (not merely offline/unreachable)."""
    if isinstance(err, aiohttp.ClientResponseError):
        # L8 httpd: Upgrade → 400; missing URI → 404
        if err.status in (400, 403, 404, 405, 501):
            return True
    msg = str(err).lower()
    needles = (
        "upgrade",
        "websocket",
        "ws protocol",
        "400",
        "404",
        "not supported",
        "invalid status",
        "handshake",
    )
    return any(n in msg for n in needles)


class LanbonApi:
    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        port: int,
        token: str,
        entry: ConfigEntry | None = None,
    ) -> None:
        self.hass = hass
        self.host = host
        self.port = port or DEFAULT_PORT
        self.token = token
        self._entry = entry
        self._session = async_get_clientsession(hass)
        self._ws_task: asyncio.Task | None = None
        self._listeners: list = []
        self._ws_fail_count = 0
        self._ws_disabled = False
        if entry is not None:
            self._ws_disabled = bool(
                entry.options.get(CONF_WS_DISABLED)
                or entry.data.get(CONF_WS_DISABLED)
            )

    @property
    def base(self) -> str:
        return f"http://{self.host}:{self.port}"

    @property
    def ws_disabled(self) -> bool:
        return self._ws_disabled

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    async def async_get_info(self) -> dict[str, Any]:
        async with self._session.get(
            f"{self.base}/api/v1/info", headers=self._headers(), timeout=8
        ) as resp:
            if resp.status == 401:
                raise PermissionError("invalid token")
            resp.raise_for_status()
            return await resp.json(content_type=None)

    async def async_get_devices(self) -> dict[str, Any]:
        async with self._session.get(
            f"{self.base}/api/v1/devices", headers=self._headers(), timeout=8
        ) as resp:
            if resp.status == 401:
                raise PermissionError("invalid token")
            resp.raise_for_status()
            return await resp.json(content_type=None)

    async def async_command(self, payload: dict[str, Any]) -> dict[str, Any]:
        async with self._session.post(
            f"{self.base}/api/v1/command",
            headers={**self._headers(), "Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=8,
        ) as resp:
            if resp.status == 401:
                raise PermissionError("invalid token")
            resp.raise_for_status()
            return await resp.json(content_type=None)

    def add_listener(self, cb) -> None:
        self._listeners.append(cb)

    def should_skip_ws_from_snapshot(self, data: dict[str, Any] | None) -> bool:
        """HTTP-only product (e.g. L8) or explicit ws=false in payload."""
        if not isinstance(data, dict):
            return False
        host = data.get("host") if isinstance(data.get("host"), dict) else {}
        product = data.get("product") or host.get("product")
        if product is None:
            # some firmwares put product on the host row inside devices[]
            for dev in data.get("devices") or []:
                if isinstance(dev, dict) and dev.get("is_host"):
                    product = dev.get("product")
                    host = dev
                    break
        if product_is_http_only(product):
            return True
        if host.get("ws") is False or host.get("websocket") is False:
            return True
        return False

    def _persist_ws_disabled(self) -> None:
        """Remember HTTP-poll-only so reload does not hammer Upgrade again."""
        self._ws_disabled = True
        entry = self._entry
        if entry is None:
            return
        if entry.options.get(CONF_WS_DISABLED):
            return
        self.hass.config_entries.async_update_entry(
            entry,
            options={**entry.options, CONF_WS_DISABLED: True},
        )

    async def async_disable_ws(self, reason: str) -> None:
        """Stop WS loop permanently for this config entry (HTTP poll remains)."""
        if self._ws_disabled:
            return
        _LOGGER.warning(
            "LANBON WebSocket disabled (%s); using HTTP poll only for %s:%s",
            reason,
            self.host,
            self.port,
        )
        self._persist_ws_disabled()
        await self.async_stop_ws()

    async def async_start_ws(self, on_message) -> None:
        self.add_listener(on_message)
        if self._ws_disabled:
            _LOGGER.info(
                "LANBON WS already disabled for %s:%s (HTTP poll only)",
                self.host,
                self.port,
            )
            return
        if self._ws_task and not self._ws_task.done():
            return
        self._ws_task = self.hass.async_create_task(self._ws_loop())

    async def async_stop_ws(self) -> None:
        if self._ws_task:
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass
            self._ws_task = None

    async def _ws_loop(self) -> None:
        url = f"ws://{self.host}:{self.port}/api/v1/ws?token={self.token}"
        while not self._ws_disabled:
            try:
                async with self._session.ws_connect(url, heartbeat=30) as ws:
                    self._ws_fail_count = 0
                    _LOGGER.debug("LANBON WS connected %s:%s", self.host, self.port)
                    async for msg in ws:
                        if self._ws_disabled:
                            return
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            try:
                                data = json.loads(msg.data)
                            except json.JSONDecodeError:
                                continue
                            for cb in list(self._listeners):
                                cb(data)
                        elif msg.type in (
                            aiohttp.WSMsgType.CLOSED,
                            aiohttp.WSMsgType.ERROR,
                        ):
                            break
            except asyncio.CancelledError:
                raise
            except Exception as err:  # noqa: BLE001
                if _is_ws_unsupported_error(err):
                    self._ws_fail_count += 1
                    _LOGGER.warning(
                        "LANBON WS unsupported (%s/%s) on %s:%s: %s",
                        self._ws_fail_count,
                        WS_UNSUPPORTED_FAIL_THRESHOLD,
                        self.host,
                        self.port,
                        err,
                    )
                    if self._ws_fail_count >= WS_UNSUPPORTED_FAIL_THRESHOLD:
                        await self.async_disable_ws("handshake rejected by panel")
                        return
                else:
                    # Transient offline / network — keep retrying (L10 must not lock out).
                    self._ws_fail_count = 0
                    _LOGGER.warning("LANBON WS error: %s", err)
            await asyncio.sleep(5)


class LanbonCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, api: LanbonApi) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=None,  # push via WS; poll as fallback below
        )
        self.api = api
        from datetime import timedelta

        self.update_interval = timedelta(seconds=30)

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.api.async_get_devices()
        except PermissionError as err:
            raise UpdateFailed(str(err)) from err
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(str(err)) from err

    def handle_ws(self, data: dict[str, Any]) -> None:
        if not isinstance(data, dict):
            return
        if data.get("type") == "state" or "devices" in data:
            # Ensure coordinator update runs on HA event loop
            self.hass.loop.call_soon_threadsafe(self.async_set_updated_data, data)
