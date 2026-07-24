# LANBON local API contract

**Status:** frozen for HA integration **0.2.x** / firmware `HA_LOCAL_PROTO_VER = 1`  
**Rule:** breaking field/semantics → bump `proto` and HA major.minor together.

Server runs only on **Mesh root** (level == 1).

| Item | Value |
|---|---|
| Port | `8765` (`HA_LOCAL_API_PORT`) |
| Auth | `Authorization: Bearer <32-hex-token>` (NVS-persisted) |
| mDNS type | `_lanbon._tcp` |
| mDNS TXT | `mac`, `token`, `sw_type`, `type_name`, `path=/api/v1` |

---

## `GET /api/v1/info`

Auth required.

```json
{
  "proto": 1,
  "mac": "aabbccddeeff",
  "name": "<UI type label>",
  "type_name": "<UI type label>",
  "sw_type": 1,
  "mesh_level": 1,
  "is_root": true,
  "port": 8765
}
```

| Field | Notes |
|---|---|
| `mac` | 12 hex, no separators, lowercase from firmware helper |
| `type_name` / `name` | Same source as UI type picker string |
| `is_root` | Must be true for a usable host entry |

Errors: `401` unauthorized.

---

## `GET /api/v1/devices`

Auth required. Snapshot used by HA coordinator + WS `type=state`.

```json
{
  "proto": 1,
  "type": "state",
  "host": { "...device..." },
  "devices": [ { "...host + children..." } ]
}
```

### Device object

| Field | Type | Notes |
|---|---|---|
| `mac` | string | 12 hex |
| `is_host` | bool | |
| `available` | bool | children: keepalive > 0 |
| `sw_type` | number | firmware software type enum |
| `kind` | string | `switch` / `light` / `cover` / `cover_switch` / … |
| `name` | string | host type label (host only in builder) |
| `channel_names` | string[] | button labels |
| `status_raw` | number | |
| `switches` | bool[] | when kind is switch-like |
| `on` / `brightness` | | dimmer |
| `cover_state` / `covers` | | curtain |
| `keepalive` | number | child only |

### Channel name limits (important)

- UI / espnow button names: up to **8** slots (`UI_PORT_MAIN_CTRL_OBJ_NUM_MAX`)
- Mesh root **detail cache** `objName[]`: only **3** slots (`DM_LPOLD_DEV_CTRL_OBJ_NUM_MAX`)
- `name_set` with `index >= 3`: applied on target panel via espnow; **not** written into root detail list (OOB guard)

---

## `POST /api/v1/command`

Auth required. Body ≤ 1024 bytes. JSON.

Common fields:

```json
{ "mac": "aabbccddeeff", "op": "<op>", "...": "..." }
```

| `op` | Extra fields | Scope |
|---|---|---|
| `switch_set` | `index` 0–3, `on` bool/number | host or child |
| `light_set` | `on` and/or `brightness` 0–127 | dimmer |
| `cover_set` | `command`: `OPEN` / `CLOSE` / `STOP` | cover |
| `name_set` | `index` ≥0, `name` string | host local UI **or** child via espnow |

Success:

```json
{ "ok": true }
```

Failure:

```json
{ "ok": false, "err": <esp_err_t int> }
```

After most successful commands the root may push a full WS `state`.  
`name_set` intentionally **skips** that full sync (heap); HA should update the entity name locally.

---

## `WS /api/v1/ws?token=<token>`

- Query token (Bearer header not used for WS upgrade in firmware)
- Server answers WebSocket **PING** with **PONG** (aiohttp `heartbeat=30`)
- Push payload: same shape as devices root + `"type":"state"`

---

## Versioning

| `proto` | Meaning |
|---|---|
| `1` | Initial public contract (this document) |

When adding fields: prefer **additive** (old HA keeps working).  
When renaming/removing/changing meaning: **`proto` += 1** and document in Changelog.
