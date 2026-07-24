"""Pure unit tests (no Home Assistant runtime required)."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
COMP = ROOT / "custom_components" / "lanbon"


def _load(name: str, filename: str):
    path = COMP / filename
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_manifest_version_and_zeroconf():
    import json

    data = json.loads((COMP / "manifest.json").read_text(encoding="utf-8"))
    assert data["domain"] == "lanbon"
    assert data["config_flow"] is True
    assert data["iot_class"] == "local_push"
    assert "_lanbon._tcp.local." in data["zeroconf"]
    assert data["version"] == "0.2.0"


def test_dev_type_name_maps():
    dt = _load("lanbon_device_types", "device_types.py")
    assert "开关" in dt.dev_type_name(0xD3, lang="zh")
    assert "4gang" in dt.dev_type_name(0xD3, lang="en").lower()
    assert dt.dev_type_name(None) == "LANBON"
    assert dt.dev_type_name("nope") == "LANBON"


def test_const_defaults():
    const = _load("lanbon_const", "const.py")
    assert const.DOMAIN == "lanbon"
    assert const.DEFAULT_PORT == 8765
    assert const.SERVICE_SET_CHANNEL_NAME == "set_channel_name"


def test_api_doc_mentions_proto_1():
    api = (ROOT / "docs" / "API.md").read_text(encoding="utf-8")
    assert "proto" in api.lower()
    assert "8765" in api
    assert "name_set" in api
