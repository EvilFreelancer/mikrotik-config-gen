# RouterBOARD (RB) series

Higher-port wired routers. Ethernet `ether1..N`; many have multiple switch
groups (ports in the same group share a switch chip and can be bridged with
hardware offload).

| Model | Ethernet | SFP / SFP+ | Wi-Fi | USB | PoE | Notes |
|-------|----------|------------|-------|-----|-----|-------|
| RB2011UiAS-2HnD | 5× 1G (`ether1-5`) + 5× 100M (`ether6-10`) | 1× 1G `sfp1` | 2.4G `wlan1` (legacy) | 1 | passive-in `ether10` | LCD; two switch groups (GbE / FE) |
| RB3011UiAS-RM | 10× 1G (`ether1-10`) | 1× 1G `sfp1` | — | 1 (USB 3.0) | passive-in `ether1` | rackmount; two GbE switch groups (`ether1-5`, `ether6-10`) |
| RB4011iGS+RM | 10× 1G (`ether1-10`) | 1× **10G** `sfp-sfpplus1` | — | 1 (USB 3.0) | — | rackmount; SFP+ uplink |
| RB4011iGS+5HacQ2HnD | 10× 1G (`ether1-10`) | 1× **10G** `sfp-sfpplus1` | 2.4G `wlan1` + 5G `wlan2` (legacy) | 1 | — | wireless variant of RB4011 |
| RB5009UG+S+IN | 1× **2.5G** (`ether1`) + 7× 1G (`ether2-8`) | 1× **10G** `sfp-sfpplus1` | — | 1 (USB 3.0) | 802.3af/at-in on `ether1` | ARM64; `ether1` (2.5G) or SFP+ = WAN |
| RB5009UPr+S+IN | 1× 2.5G (`ether1`) + 7× 1G (`ether2-8`) | 1× 10G `sfp-sfpplus1` | — | 1 | **PoE-out** 802.3af/at on `ether1-8` | PoE variant, powers 8 APs |
| RB1100AHx4 | 13× 1G (`ether1-13`) | — | — | — | — | rackmount; two switch groups + Ethernet bypass |
| RB1100AHx4 Dude | 13× 1G (`ether1-13`) | — | — | — | — | with Dude server + dual PSU |

## Switch groups (why it matters)
Ports inside one switch group can be bridged with `hw=yes` hardware offload;
bridging across groups (or with the SFP/SFP+) falls back to CPU. Typical groups:
- **RB3011 / RB2011:** two groups — put the LAN in one group's bridge for line-rate.
- **RB4011:** two GbE groups (`ether1-5`, `ether6-10`) + SFP+ on the CPU path.
- **RB5009:** a single switch fabric across all copper + SFP+ (offloaded bridging).

## Config hints
- **RB5009** is the common modern edge/core SOHO+ box: use `ether1` (2.5G) as WAN
  for a fast uplink, or `sfp-sfpplus1` for a 10G uplink; bridge `ether2-8` as LAN.
- **RB4011:** `sfp-sfpplus1` is the 10G uplink; `ether1` the default copper WAN.
- Keep the WAN port out of the LAN bridge and in the `WAN` interface list.
- For the wireless RB4011 variant use the legacy `/interface wireless` menu.
