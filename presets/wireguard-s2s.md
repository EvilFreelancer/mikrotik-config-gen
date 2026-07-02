# Preset: site-to-site WireGuard

Encrypted tunnel between two RouterOS v7 routers, routing each site's LAN to the
other. WireGuard is native in v7 — keys are generated on-device. Configure both
ends; the template is for **Site A**, with the mirrored **Site B** values noted.

> **This is an overlay, not a standalone config.** It adds the tunnel on top of
> an already-hardened router (e.g. `presets/isp-edge.md`) and uses
> `place-before=[find comment="DEFAULT DROP ..."]` to slot its accept rules
> above the existing default-drops. Linting this block on its own reports
> "no default-drop" — expected; combine it with the base config, and the
> combined result lints clean.

## Gap questions
- Public endpoint of the *other* side (`<PEER_ENDPOINT>`) + UDP port (`<WG_PORT>`).
- Tunnel addressing: `<WG_LOCAL_IP>` / `<WG_PEER_IP>` (e.g. 10.10.10.1 / .2 /24).
- LAN subnets: this side `<LOCAL_LAN>`, remote `<REMOTE_LAN>`.
- Peer's **public key** `<WG_PEER_PUBKEY>` (exchange after both are created).
- Is at least one side behind NAT? (that side dials out with keepalive).

## Template (Site A)

```rsc
# --- SITE A — WireGuard s2s — RouterOS v7 — validate in safe mode ---

# --- WIREGUARD INTERFACE (key auto-generated) ---
/interface wireguard add name=wg-s2s listen-port=<WG_PORT> mtu=1420
;# read this router's public key to hand to the peer:
;# /interface wireguard print

# --- TUNNEL ADDRESS ---
/ip address add address=<WG_LOCAL_IP>/24 interface=wg-s2s comment="wg tunnel"

# --- PEER (Site B) ---
/interface wireguard peers add interface=wg-s2s \
    public-key="<WG_PEER_PUBKEY>" \
    endpoint-address=<PEER_ENDPOINT> endpoint-port=<WG_PORT> \
    allowed-address=<REMOTE_LAN>,<WG_PEER_IP>/32 \
    persistent-keepalive=25s comment="Site B"

# --- ROUTE REMOTE LAN THROUGH TUNNEL ---
/ip route add dst-address=<REMOTE_LAN> gateway=wg-s2s comment="to Site B LAN"

# --- FIREWALL: allow WG + tunnelled traffic ---
/interface list member add list=WAN interface=<WAN_IFACE>
/ip firewall filter
add chain=input action=accept protocol=udp dst-port=<WG_PORT> in-interface-list=WAN comment="accept WireGuard" place-before=[find comment="DEFAULT DROP INPUT"]
add chain=forward action=accept in-interface=wg-s2s out-interface-list=LAN comment="B->A LAN" place-before=[find comment="DEFAULT DROP FORWARD"]
add chain=forward action=accept in-interface-list=LAN out-interface=wg-s2s comment="A->B LAN" place-before=[find comment="DEFAULT DROP FORWARD"]

# --- DO NOT NAT tunnelled traffic (exempt before masquerade) ---
/ip firewall nat
add chain=srcnat action=accept dst-address=<REMOTE_LAN> src-address=<LOCAL_LAN> place-before=0 comment="no-NAT to Site B"
```

## Site B (mirror)
Swap the roles:
- `<WG_LOCAL_IP>` ↔ `<WG_PEER_IP>`
- `<LOCAL_LAN>` ↔ `<REMOTE_LAN>`
- `<PEER_ENDPOINT>` = Site A's public IP
- exchange the other public key
- the side **behind NAT** keeps `persistent-keepalive`; the side with a public
  IP and open UDP port may omit it.

## Notes
- This preset assumes each router already has the ISP-edge hardening in place;
  the WireGuard rules use `place-before` so they land above the default drops.
- MTU 1420 avoids fragmentation over most 1500-byte paths; lower to 1412 if the
  underlay is PPPoE.
- Keys never leave the device. Never paste a private key into the config — v7
  keeps it internal; you only exchange the **public** key.

## Fill these in
`<WG_PORT> <WG_LOCAL_IP> <WG_PEER_IP> <WG_PEER_PUBKEY> <PEER_ENDPOINT>
<LOCAL_LAN> <REMOTE_LAN> <WAN_IFACE>` (and the mirrored set for Site B).
