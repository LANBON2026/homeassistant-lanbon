"""Unit tests for per-device LOIP display name helpers."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMP = ROOT / "custom_components" / "lanbon"


def _load_const():
    path = COMP / "const.py"
    spec = importlib.util.spec_from_file_location("lanbon_const_naming", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["lanbon_const_naming"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_child_uses_own_model_not_gateway():
    const = _load_const()
    assert (
        const.device_display_name(
            device_model="L8-3G",
            device_name="Light1",
            gateway_model="L8-SCENE",
        )
        == "L8-3G"
    )
    assert (
        const.device_model_label(device_model="L8-3G", gateway_model="L8-SCENE")
        == "L8-3G"
    )


def test_gateway_falls_back_to_info_model():
    const = _load_const()
    assert (
        const.device_display_name(
            device_model="L8-SCENE",
            device_name="Scene1",
            gateway_model="L8-SCENE",
        )
        == "L8-SCENE"
    )


def test_missing_model_uses_device_name_then_gateway():
    const = _load_const()
    assert (
        const.device_display_name(
            device_model=None,
            device_name="Light1",
            gateway_model="L8-SCENE",
        )
        == "Light1"
    )
    assert (
        const.device_display_name(
            device_model=None,
            device_name=None,
            gateway_model="L8-SCENE",
        )
        == "L8-SCENE"
    )
    assert const.device_model_label(device_model=None, gateway_model="L8-SCENE") == (
        "L8-SCENE"
    )
