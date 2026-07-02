# RouterOS v7 notes and v6→v7 gotchas

This skill targets **RouterOS v7**. Confirm the version from the export header
(`# ... by RouterOS 7.x`) or ask. If the device is on v6, the syntax below does
not apply — say so.

## Syntax and CLI

- Both forms work; be consistent within one script:
  - classic: `/ip address add address=... interface=...`
  - path: `/ip/address/add address=... interface=...`
- Comments: `# ...` on its own line, or `;#` trailing on a command line.
- Scripting still uses `:global`, `:local`, `:for`, `:delay`, `[find ...]`.
- `/export` in v7 supports `show-sensitive` (off by default — passwords come out
  masked). Do not assume a pasted export contains real secrets.

## WireGuard — native in v7

v7 has first-class WireGuard; no packages, no manual key files.

```
/interface wireguard add name=wg0 listen-port=<WG_PORT>
;# public key is generated automatically; read it with:
;# /interface wireguard print
/interface wireguard peers add interface=wg0 \
    public-key="<WG_PEER_PUBKEY>" endpoint-address=<PEER_ENDPOINT> \
    endpoint-port=<WG_PORT> allowed-address=<REMOTE_LAN>,<WG_PEER_IP>/32 \
    persistent-keepalive=25s
/ip address add address=<WG_LOCAL_IP>/24 interface=wg0
```

Route the remote LAN through the tunnel and allow it in the firewall.

## Routing stack rewritten in v7

- `/routing` menus changed heavily from v6. BGP is `/routing bgp connection`
  (not `/routing bgp peer`). OSPF is `/routing ospf instance` +
  `/routing ospf area` + `/routing ospf interface-template`.
- Static routes: `/ip route add dst-address=... gateway=...`; the `distance`,
  `check-gateway`, and `scope`/`target-scope` fields still exist.
- For recursive next-hops set `gateway` + `scope`/`target-scope` appropriately.
- Do not paste v6 `/routing bgp peer` blocks into v7 — they will not parse.

## Bridge, VLAN filtering

- Group switch ports under a bridge: `/interface bridge add name=bridge`,
  then `/interface bridge port add bridge=bridge interface=etherN`.
- Hardware offload: keep `hw=yes` on ports where the switch chip supports it.
- VLAN filtering on the bridge:
  ```
  /interface bridge set bridge vlan-filtering=yes
  /interface bridge vlan add bridge=bridge tagged=bridge,ether1 untagged=ether2 vlan-ids=10
  ```
  Enable `vlan-filtering=yes` **after** the VLAN table is defined, or you can
  cut your own management access — do it in safe mode.

## DHCP, pools, DNS

- `/ip pool add name=dhcp ranges=<RANGE>`
- `/ip dhcp-server add interface=<LAN_BRIDGE> address-pool=dhcp name=dhcp1`
- `/ip dhcp-server network add address=<LAN_SUBNET> gateway=<LAN_GW> dns-server=<LAN_GW>`
- `/ip dhcp-client add interface=<WAN_IFACE> use-peer-dns=yes add-default-route=yes`
  for a DHCP WAN.

## PPPoE

- Server: `/interface pppoe-server server add service-name=<SVC> interface=<IF> \
  default-profile=<PROFILE> one-session-per-host=yes`.
- Client (WAN): `/interface pppoe-client add interface=<WAN_IFACE> \
  user=<PPP_USER> password=<PPP_PASS> add-default-route=yes use-peer-dns=yes`.
- RADIUS AAA: `/ppp aaa set use-radius=yes` + `/radius add service=ppp ...`.

## Interface naming

Read real names from `devices/`. Defaults worth remembering:
- Wireless: `wlan1` (2.4 GHz), `wlan2` (5 GHz) on dual-band; on the newer
  "ax" wifi-qcom driver the menu is `/interface wifi` with names like `wifi1`.
- SFP: `sfp1`, SFP+: `sfp-sfpplus1`, SFP28: `sfp28-1`, QSFP: `qsfpplus1-1`.
- The MikroTik factory default names the first Ethernet `ether1` and usually
  configures it as the WAN (DHCP client) with the rest bridged — but never
  assume; confirm against the model and the user's cabling.

## Things that bite people

- Enabling `vlan-filtering` or a default-drop firewall over a remote session
  without safe mode → lockout.
- `add-default-route=yes` on both a DHCP client and a PPPoE client → two default
  routes fighting; set `default-route-distance` to prioritise.
- Forgetting `/ip firewall nat` masquerade → LAN has addresses but no internet.
- IPv6 present but firewall absent → open box (see firewall.md).
- Reusing a v6 `/routing` or `/interface wireguard` (package) block on v7.
