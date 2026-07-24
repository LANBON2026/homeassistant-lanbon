"""Device type names aligned with firmware pDevTypeSelTab / uiLanguage (CN)."""
from __future__ import annotations

# enumSoftwareDevType values from uiParameterManagement.h
ESDT_NULL = 0xCF
ESDT_1GANG = 0xD0
ESDT_2GANG = 0xD1
ESDT_3GANG = 0xD2
ESDT_4GANG = 0xD3
ESDT_CURTAIN = 0xD4
ESDT_SCENE = 0xD5
ESDT_DIMMER = 0xD6
ESDT_HEATER = 0xD7
ESDT_THERMO = 0xD8
ESDT_FAN = 0xD9
ESDT_FAN_EX = 0xDA
ESDT_RGB = 0xDB
ESDT_DOUBLE_CUR = 0xDC
ESDT_1CUR1GANG = 0xDD
ESDT_1CUR2GANG = 0xDE
ESDT_SIG_REPEATER = 0xDF
ESDT_4GANG_NEW = 0xE0

# Display names = uiLanguage Chinese column (euslDevType*)
DEV_TYPE_NAME_CN: dict[int, str] = {
    ESDT_1GANG: "一位开关",
    ESDT_2GANG: "两位开关",
    ESDT_3GANG: "三位开关",
    ESDT_4GANG: "四位开关",
    ESDT_4GANG_NEW: "四位开关",
    ESDT_CURTAIN: "窗帘",
    ESDT_SCENE: "场景开关",
    ESDT_DIMMER: "调光器",
    ESDT_HEATER: "热水器",
    ESDT_THERMO: "恒温器",
    ESDT_FAN: "风扇开关",
    ESDT_FAN_EX: "风扇开关",
    ESDT_RGB: "彩色灯带",
    ESDT_DOUBLE_CUR: "两位窗帘",
    ESDT_1CUR1GANG: "窗帘&一位开关",
    ESDT_1CUR2GANG: "窗帘&两位开关",
    ESDT_SIG_REPEATER: "信号中继",
}

DEV_TYPE_NAME_EN: dict[int, str] = {
    ESDT_1GANG: "1gang Switch",
    ESDT_2GANG: "2gang Switch",
    ESDT_3GANG: "3gang Switch",
    ESDT_4GANG: "4gang Switch",
    ESDT_4GANG_NEW: "4gang Switch",
    ESDT_CURTAIN: "Curtain",
    ESDT_SCENE: "Scene",
    ESDT_DIMMER: "Dimmer",
    ESDT_HEATER: "Heater",
    ESDT_THERMO: "Thermostat",
    ESDT_FAN: "Fan Switch",
    ESDT_FAN_EX: "Fan Switch",
    ESDT_RGB: "RGB Lamp",
    ESDT_DOUBLE_CUR: "2Curtain",
    ESDT_1CUR1GANG: "1Cur&1Gang",
    ESDT_1CUR2GANG: "1Cur&2Gang",
    ESDT_SIG_REPEATER: "Repeater",
}


def dev_type_name(sw_type: int | str | None, *, lang: str = "zh") -> str:
    """Optional HA-side map. Discovery/title must use firmware type_name, not this."""
    try:
        code = int(sw_type) if sw_type is not None else None
    except (TypeError, ValueError):
        return "LANBON"
    if code is None:
        return "LANBON"
    table = DEV_TYPE_NAME_CN if lang.startswith("zh") else DEV_TYPE_NAME_EN
    return table.get(code, "LANBON")
