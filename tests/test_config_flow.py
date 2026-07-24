"""Config flow unit tests — load modules by path (no full HA install)."""
from __future__ import annotations

import asyncio
import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

ROOT = Path(__file__).resolve().parents[1]
COMP = ROOT / "custom_components" / "lanbon"


def _ensure_stub(name: str) -> types.ModuleType:
    mod = sys.modules.get(name)
    if mod is None or getattr(mod, "__file__", None) is None:
        # Replace empty namespace packages with a plain module we can populate
        mod = types.ModuleType(name)
        sys.modules[name] = mod
    return mod


def _ha_stubs() -> None:
    _ensure_stub("homeassistant")
    core = _ensure_stub("homeassistant.core")
    core.HomeAssistant = type("HomeAssistant", (), {})
    conf = _ensure_stub("homeassistant.config_entries")
    const = _ensure_stub("homeassistant.const")
    flow = _ensure_stub("homeassistant.data_entry_flow")
    _ensure_stub("homeassistant.helpers")
    _ensure_stub("homeassistant.helpers.service_info")
    zc = _ensure_stub("homeassistant.helpers.service_info.zeroconf")
    aio_cli = _ensure_stub("homeassistant.helpers.aiohttp_client")
    uc = _ensure_stub("homeassistant.helpers.update_coordinator")
    aiohttp = _ensure_stub("aiohttp")
    aiohttp.WSMsgType = types.SimpleNamespace(TEXT=1, CLOSED=2, ERROR=3)
    # Prefer real voluptuous when installed
    try:
        import voluptuous as _vol

        sys.modules["voluptuous"] = _vol
    except ImportError:
        vol = _ensure_stub("voluptuous")
        vol.Schema = MagicMock(side_effect=lambda *a, **k: dict)
        vol.Required = lambda x, **k: x

    const.CONF_HOST = "host"
    const.CONF_PORT = "port"
    flow.FlowResult = dict
    zc.ZeroconfServiceInfo = type("ZeroconfServiceInfo", (), {})

    class DataUpdateCoordinator:
        def __init__(self, *a, **k):
            pass

        def __class_getitem__(cls, item):
            return cls

    uc.DataUpdateCoordinator = DataUpdateCoordinator
    uc.UpdateFailed = Exception
    aio_cli.async_get_clientsession = MagicMock(return_value=MagicMock())

    class _CFMeta(type):
        def __new__(mcs, name, bases, namespace, **kwargs):
            kwargs.pop("domain", None)
            return super().__new__(mcs, name, bases, namespace)

    class ConfigFlowBase(metaclass=_CFMeta):
        def __init__(self, *a, **k):
            self.context = {}
            self.hass = MagicMock()

        async def async_set_unique_id(self, unique_id):
            self._unique_id = unique_id

        def _abort_if_unique_id_configured(self, updates=None):
            return None

        def async_create_entry(self, *, title, data):
            return {"type": "create_entry", "title": title, "data": data}

        def async_show_form(self, **kwargs):
            return {"type": "form", **kwargs}

    conf.ConfigFlow = ConfigFlowBase


def _load(name: str, filename: str, inject: dict | None = None):
    path = COMP / filename
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    if inject:
        for k, v in inject.items():
            setattr(mod, k, v)
    # Pre-create package-ish attrs for relative imports
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def cf_mods():
    _ha_stubs()
    # const has no HA deps
    const = _load("lanbon_const_cf", "const.py")
    # coordinator needs stubs already
    # Patch relative imports: coordinator does `from .const import ...`
    # Loading by file path breaks relative imports — inject fake package
    pkg = types.ModuleType("lanbon_pkg")
    pkg.__path__ = [str(COMP)]
    pkg.__package__ = "lanbon_pkg"
    sys.modules["lanbon_pkg"] = pkg
    sys.modules["lanbon_pkg.const"] = const

    coord_spec = importlib.util.spec_from_file_location(
        "lanbon_pkg.coordinator", COMP / "coordinator.py", submodule_search_locations=[]
    )
    coord = importlib.util.module_from_spec(coord_spec)
    sys.modules["lanbon_pkg.coordinator"] = coord
    assert coord_spec.loader
    coord_spec.loader.exec_module(coord)

    cf_spec = importlib.util.spec_from_file_location(
        "lanbon_pkg.config_flow", COMP / "config_flow.py"
    )
    cf = importlib.util.module_from_spec(cf_spec)
    sys.modules["lanbon_pkg.config_flow"] = cf
    assert cf_spec.loader
    cf_spec.loader.exec_module(cf)
    return cf, coord


def _run(coro):
    return asyncio.run(coro)


def test_user_success(cf_mods):
    cf, coord = cf_mods
    flow = cf.LanbonConfigFlow()
    flow.hass = MagicMock()
    flow.context = {}
    api = MagicMock()
    api.async_get_info = AsyncMock(
        return_value={
            "mac": "aabbccddeeff",
            "is_root": True,
            "type_name": "4gang Switch",
            "sw_type": 224,
        }
    )
    cf.LanbonApi = MagicMock(return_value=api)
    result = _run(
        flow.async_step_user({"host": "192.168.0.1", "port": 8765, "token": "abc"})
    )
    assert result["type"] == "create_entry"
    assert result["title"] == "4gang Switch"
    assert result["data"]["mac"] == "AABBCCDDEEFF"


def test_user_invalid_auth(cf_mods):
    cf, coord = cf_mods
    flow = cf.LanbonConfigFlow()
    flow.hass = MagicMock()
    flow.context = {}
    api = MagicMock()
    api.async_get_info = AsyncMock(side_effect=PermissionError("bad"))
    cf.LanbonApi = MagicMock(return_value=api)
    result = _run(
        flow.async_step_user({"host": "192.168.0.1", "port": 8765, "token": "bad"})
    )
    assert result["errors"]["base"] == "invalid_auth"


def test_user_cannot_connect(cf_mods):
    cf, coord = cf_mods
    flow = cf.LanbonConfigFlow()
    flow.hass = MagicMock()
    flow.context = {}
    api = MagicMock()
    api.async_get_info = AsyncMock(side_effect=OSError("down"))
    cf.LanbonApi = MagicMock(return_value=api)
    result = _run(
        flow.async_step_user({"host": "192.168.0.1", "port": 8765, "token": "x"})
    )
    assert result["errors"]["base"] == "cannot_connect"


def test_user_not_root(cf_mods):
    cf, coord = cf_mods
    flow = cf.LanbonConfigFlow()
    flow.hass = MagicMock()
    flow.context = {}
    api = MagicMock()
    api.async_get_info = AsyncMock(
        return_value={"mac": "aa", "is_root": False, "type_name": "Node"}
    )
    cf.LanbonApi = MagicMock(return_value=api)
    result = _run(
        flow.async_step_user({"host": "192.168.0.1", "port": 8765, "token": "x"})
    )
    assert result["errors"]["base"] == "not_root"


def test_zeroconf_confirm_success(cf_mods):
    cf, coord = cf_mods
    flow = cf.LanbonConfigFlow()
    flow.hass = MagicMock()
    flow.context = {}
    flow._host = "192.168.0.106"
    flow._port = 8765
    flow._token = "tok"
    flow._mac = "DCDA0C3BC764"
    flow._type_name = "4gang Switch"
    api = MagicMock()
    api.async_get_info = AsyncMock(
        return_value={
            "mac": "dcda0c3bc764",
            "is_root": True,
            "type_name": "4gang Switch",
            "sw_type": 224,
        }
    )
    cf.LanbonApi = MagicMock(return_value=api)
    result = _run(flow.async_step_discovery_confirm({"token": "tok"}))
    assert result["type"] == "create_entry"
    assert result["data"]["host"] == "192.168.0.106"
