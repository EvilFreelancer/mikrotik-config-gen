# Cloud Router Switch (CRS) series

Switches with a switch chip that also run RouterOS (dual-boot SwitchOS on many).
Copper is `ether1..N`; fibre is `sfp-sfpplusN` (10G), `sfp28-N` (25G),
`qsfpplusN-M` (40G) / `qsfp28-N` (100G). For line-rate switching, use bridge
**hardware offload** and the switch's VLAN table; RouterOS bridge VLAN filtering
is offloaded on CRS3xx.

## CRS3xx (Marvell, gigabit + SFP+)

| Model | Copper | Fibre | PoE-out | Notes |
|-------|--------|-------|---------|-------|
| CRS326-24G-2S+ | 24× 1G (`ether1-24`) | 2× **10G** (`sfp-sfpplus1-2`) | — | classic 24-port GbE + 2×10G |
| CRS328-24P-4S+ | 24× 1G (`ether1-24`) | 4× **10G** (`sfp-sfpplus1-4`) | 802.3af/at on `ether1-24` | PoE switch |
| CRS328-4C-20S-4S+ | 4× combo (`ether1-4`) | 20× 1G (`sfp1-20`) + 4× **10G** (`sfp-sfpplus1-4`) | — | fibre aggregation |
| CRS309-1G-8S+ | 1× 1G (`ether1`, mgmt) | 8× **10G** (`sfp-sfpplus1-8`) | — | desktop 10G |
| CRS317-1G-16S+ | 1× 1G (`ether1`, mgmt) | 16× **10G** (`sfp-sfpplus1-16`) | — | 16×10G rackmount |
| CRS354-48G-4S+2Q+ | 48× 1G (`ether1-48`) | 4× **10G** (`sfp-sfpplus1-4`) + 2× **40G** (`qsfpplus1-1..2-1`) | — | 48-port aggregation |

## CRS3xx 2.5G / multi-gig

| Model | Copper | Fibre | Notes |
|-------|--------|-------|-------|
| CRS310-8G+2S+ | 8× **2.5G** (`ether1-8`) | 2× **10G** (`sfp-sfpplus1-2`) | multi-gig access |
| CRS312-4C+8XG | 8× **10G** copper (`ether1-8`) | 4× combo **10G** (`sfp-sfpplus1-4`) | 10GBASE-T |

## CRS5xx (100G-capable)

| Model | Copper | Fibre | Notes |
|-------|--------|-------|-------|
| CRS518-16XS-2XQ | 1× 1G (`ether1`, mgmt) | 16× **25G** (`sfp28-1-16`) + 2× **100G** (`qsfp28-1-2`) | 100G aggregation |
| CRS504-4XQ | — | 4× **100G** (`qsfp28-1-4`, breakout-capable) | "100G desktop" |

## Config hints
- `ether1` on the SFP-heavy models (CRS309/317/518) is **management**, not a data
  port — put it in a `MGMT` list.
- Switching config lives in the **bridge**: add ports to one `bridge`, set
  `hw=yes`, enable `vlan-filtering=yes` **after** building the VLAN table, and do
  it in safe mode (you can cut your management link otherwise).
- QSFP ports appear as breakout sub-interfaces: a 40G `qsfpplus1` shows as
  `qsfpplus1-1..4`; a 100G `qsfp28-1` can break out to 4× 25G `sfp28`.
- CRS is a **switch first**: if the box is doing L3/routing plus switching,
  route on a VLAN interface over the bridge, not on individual physical ports.
- PoE-out models (CRS328-24P, CRS354-48P variants) are 802.3af/at — safe for
  standard PoE devices, unlike the passive PoE on SOHO units.
