# Device reference — ports, adapters, interface names

Take real interface names and port layouts from here instead of guessing. Each
family file lists, per model: copper Ethernet count and speed, SFP/SFP+/SFP28/
QSFP ports, wireless bands and driver, USB, PoE-in / PoE-out, switch grouping,
and the **default WAN port** convention.

> **Accuracy caveat.** These tables cover the common, current models and their
> interface **naming**, which is stable and is the part you need for a config.
> Exact PoE-out port lists, amperage, and combo-port behaviour vary by revision
> — for anything load-bearing, confirm against the model's datasheet on
> mikrotik.com. If a model is **not** listed here, use generic `etherN` names
> and add "verify interface names for <model>" to the fill-in checklist.

## Interface naming conventions (RouterOS v7)

| Port type | Name pattern | Example |
|-----------|--------------|---------|
| Gigabit / Fast Ethernet | `etherN` (1-based) | `ether1`, `ether5` |
| SFP (1G) | `sfpN` | `sfp1` |
| SFP+ (10G) | `sfp-sfpplusN` | `sfp-sfpplus1` |
| SFP28 (25G) | `sfp28-N` | `sfp28-1` |
| QSFP+ (40G) / QSFP28 (100G) | `qsfpplusN-M` / `qsfp28-N` | `qsfpplus1-1` |
| Combo (copper+SFP shared) | `etherN` or `sfpN` (one active) | `combo1` on some units |
| Wireless — **legacy** driver | `wlanN` (`/interface wireless`) | `wlan1` 2.4, `wlan2` 5 |
| Wireless — **new** ax driver | `wifiN` (`/interface wifi`) | `wifi1`, `wifi2` |
| PPPoE / tunnels | user-named | `pppoe-out1`, `wg-s2s` |

**Wi-Fi driver split matters.** "ac" and older models use the legacy
`/interface wireless` menu with `wlan1`/`wlan2`. "ax" (Wi-Fi 6) models use the
newer `/interface wifi` (a.k.a. wifiwave2/wifi-qcom) menu with `wifi1`/`wifi2`.
Do not mix the two menus for one interface. Each family file marks which driver
a model uses.

## Default WAN convention

The MikroTik factory default (RouterOS `default-configuration`) usually makes
`ether1` the WAN (DHCP client) and bridges the remaining ports as the LAN. On
SFP-heavy boxes (CRS309, CCR2004-1G-12S+) the single copper port is management
and an SFP+ is the uplink. Always confirm the WAN port against the user's
cabling — never assume, note it as a placeholder if unknown.

## Files
- `soho-hex-hap.md` — hEX / hAP SOHO routers and access points
- `rb-series.md` — RouterBOARD (RB2011/3011/4011/5009/1100)
- `ccr-series.md` — Cloud Core Router (CCR1xxx / CCR2xxx)
- `crs-series.md` — Cloud Router Switch (CRS3xx / CRS5xx)
