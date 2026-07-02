# Cloud Core Router (CCR) series

Multi-core routers for routing/BNG/edge at scale. No Wi-Fi. Copper is
`ether1..N`; fibre uses `sfpN` (1G), `sfp-sfpplusN` (10G), `sfp28-N` (25G),
`qsfp28-N` (100G). On combo/uplink boxes the SFP+ ports are the real uplinks.

## CCR1xxx (Tilera, older but common)

| Model | Ethernet | SFP / SFP+ | Notes |
|-------|----------|------------|-------|
| CCR1009-7G-1C-1S+ | 7× 1G (`ether1-7`) | 1× combo (`combo1`) + 1× **10G** `sfp-sfpplus1` | 9-core |
| CCR1016-12G | 12× 1G (`ether1-12`) | — | 16-core classic |
| CCR1036-12G-4S | 12× 1G (`ether1-12`) | 4× 1G (`sfp1-4`) | 36-core |
| CCR1036-8G-2S+ | 8× 1G (`ether1-8`) | 2× **10G** (`sfp-sfpplus1-2`) | 36-core, 10G uplinks |
| CCR1072-1G-8S+ | 1× 1G (`ether1`, mgmt) | 8× **10G** (`sfp-sfpplus1-8`) | 72-core, 8×10G |

## CCR2xxx (ARM, current)

| Model | Ethernet | SFP+ / SFP28 / QSFP | Notes |
|-------|----------|---------------------|-------|
| CCR2004-16G-2S+ | 16× 1G (`ether1-16`) | 2× **10G** (`sfp-sfpplus1-2`) | common edge/BNG |
| CCR2004-1G-12S+2XS | 1× 1G (`ether1`, mgmt) | 12× **10G** (`sfp-sfpplus1-12`) + 2× **25G** (`sfp28-1-2`) | fibre aggregation |
| CCR2116-12G-4S+ | 13× 1G (`ether1-13`) | 4× **10G** (`sfp-sfpplus1-4`) | 16-core, high throughput |
| CCR2216-1G-12XS-2XQ | 1× 1G (`ether1`, mgmt) | 12× **25G** (`sfp28-1-12`) + 2× **100G** (`qsfp28-1-2`) | flagship, 100G |

## Config hints
- On the `-1G-...S+` and `-1G-...XS` models the single copper `ether1` is
  **management only** — the data path is the SFP+/SFP28 ports. Put `ether1` in a
  `MGMT` list, not `LAN`.
- These are routers, not switches: prefer L3 (routed subinterfaces / VLANs on
  the SFP+ ports) over large bridges. Use `/interface vlan` on the trunk ports.
- For BNG (see `presets/pppoe-radius-bng.md`) terminate subscriber VLANs on the
  SFP+ trunk and run PPPoE per VLAN; watch CPU vs throughput on CCR1xxx.
- No hardware switch offload on most CCRs — forwarding is CPU/fastpath; enable
  `fasttrack` for established sessions where policy allows.
