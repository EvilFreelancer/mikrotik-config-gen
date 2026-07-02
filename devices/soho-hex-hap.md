# SOHO: hEX and hAP families

Small routers and access points. Ethernet is `ether1..N`; the default WAN is
`ether1` unless noted. "Wi-Fi driver" shows which menu to use.

## hEX routers (wired, no Wi-Fi)

| Model | Ethernet | SFP | USB | PoE-in | PoE-out | Notes |
|-------|----------|-----|-----|--------|---------|-------|
| hEX (RB750Gr3) | 5× 1G (`ether1-5`) | — | 1 | — | — | MT7621, default WAN `ether1` |
| hEX S (RB760iGS) | 5× 1G (`ether1-5`) | 1× 1G (`sfp1`) | 1 | passive on `ether1` | passive on `ether5` | uplink can be `sfp1` |
| hEX PoE (RB960PGS) | 5× 1G (`ether1-5`) | 1× 1G (`sfp1`) | 1 | passive on `ether1` | `ether2-5` (passive) | powers APs downstream |
| hEX lite (RB750r2) | 5× **100M** (`ether1-5`) | — | — | passive on `ether1` | — | Fast Ethernet only |
| hEX refresh (RB750Gr4) | 5× 1G (`ether1-5`) | — | 1 | passive on `ether1` | — | newer SoC |

## hAP access-point routers

| Model | Ethernet | Wi-Fi (driver) | SFP | USB | PoE-in | PoE-out | Notes |
|-------|----------|----------------|-----|-----|--------|---------|-------|
| hAP lite (RB941-2nD) | 4× **100M** (`ether1-4`) | 2.4G `wlan1` (legacy) | — | — | — | — | tiny SOHO |
| hAP ac² (RBD52G) | 5× 1G (`ether1-5`) | 2.4G `wlan1` + 5G `wlan2` (legacy) | — | 1 | passive `ether1` | — | dual-band ac |
| hAP ac³ (RBD53iG) | 5× 1G (`ether1-5`) | 2.4G `wlan1` + 5G `wlan2` (legacy) | — | 1 | passive `ether1` | `ether5` (passive) | external antennas |
| hAP ax² (C52iG) | 5× 1G (`ether1-5`) | 2.4G `wifi1` + 5G `wifi2` (**new**) | — | 1 (USB-C data) | passive `ether1` | — | Wi-Fi 6, `/interface wifi` |
| hAP ax³ (C53UiG+) | 1× **2.5G** (`ether1`) + 4× 1G (`ether2-5`) | 2.4G `wifi1` + 5G `wifi2` (**new**) | — | 1 (USB 3.0) | passive `ether1` | check datasheet | Wi-Fi 6, 2.5G uplink |
| hAP ax lite (L41G) | 4× 1G (`ether1-4`) | dual-band `wifi1/wifi2` (**new**) | — | — | passive `ether1` | — | entry Wi-Fi 6 |

## cAP / wAP (ceiling / outdoor APs — for reference)

| Model | Ethernet | Wi-Fi (driver) | PoE-in | Notes |
|-------|----------|----------------|--------|-------|
| cAP ac (RBcAPGi) | 2× 1G (`ether1-2`) | 2.4G `wlan1` + 5G `wlan2` (legacy) | 802.3af/at on `ether1` | ceiling AP, CAPsMAN-managed |
| cAP ax (cAPGi-5HaxD2HaxD) | 1× 1G (`ether1`) | dual `wifi1/wifi2` (**new**) | 802.3af/at | Wi-Fi 6 ceiling AP |
| wAP ac (RBwAPG) | 2× 1G (`ether1-2`) | 2.4G `wlan1` + 5G `wlan2` (legacy) | passive/af/at | outdoor |

## Config hints
- On hAP "ax" models use `/interface wifi` (`wifi1`/`wifi2`), **not**
  `/interface wireless`. On "ac" and older use `/interface wireless`
  (`wlan1`/`wlan2`).
- Bridge the LAN ports plus the Wi-Fi interfaces into one `bridge`; leave the
  WAN port (`ether1` by default) out of the bridge.
- hAP ax³: the 2.5G `ether1` is the natural WAN for a fast uplink; if the ISP is
  ≤1G either port works.
- PoE-out ports are **passive** on these SOHO units — match the powered device's
  voltage, or you can damage it. Flag PoE-out use in the checklist.
