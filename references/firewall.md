# Canonical firewall structure (RouterOS v7)

A reusable, hardened firewall skeleton. Build interface lists first so rules key
off `in-interface-list`/`out-interface-list` instead of hard-wired interface
names — this survives adding VLANs or a second WAN.

## Interface lists

```
/interface list add name=WAN comment="uplinks / untrusted"
/interface list add name=LAN comment="trusted internal"
/interface list add name=MGMT comment="management sources"

/interface list member add list=WAN interface=<WAN_IFACE>
/interface list member add list=LAN interface=<LAN_BRIDGE>
;# MGMT can be a subnet handled in filter rules, or a dedicated iface here
```

`<WAN_IFACE>` and `<LAN_BRIDGE>` come from `devices/` (real port names) and the
topology. On most routers the LAN side is a bridge (`bridge` / `bridgeLocal`)
that groups the switch ports.

## IPv4 raw (drop early, before connection tracking)

```
/ip firewall raw
add chain=prerouting action=accept src-address-list=allowed comment="fast allow" ;# optional
add chain=prerouting action=drop in-interface-list=WAN src-address-list=bogons comment="drop bogons in"
add chain=prerouting action=drop in-interface-list=WAN src-address=<LAN_SUBNET> comment="anti-spoof: LAN src on WAN"
add chain=prerouting action=drop tcp-flags=fin,syn action=drop protocol=tcp comment="bad TCP: FIN+SYN"
add chain=prerouting action=drop tcp-flags=syn,rst protocol=tcp comment="bad TCP: SYN+RST"
add chain=prerouting action=drop protocol=tcp tcp-flags=fin,psh,urg,!syn,!rst,!ack comment="nmap xmas"
```

Bogon list (RFC1918 + reserved) — add the ones not used on your WAN:

```
/ip firewall address-list
add list=bogons address=0.0.0.0/8
add list=bogons address=10.0.0.0/8
add list=bogons address=100.64.0.0/10
add list=bogons address=127.0.0.0/8
add list=bogons address=169.254.0.0/16
add list=bogons address=172.16.0.0/12
add list=bogons address=192.168.0.0/16
add list=bogons address=192.0.2.0/24
add list=bogons address=198.18.0.0/15
add list=bogons address=198.51.100.0/24
add list=bogons address=203.0.113.0/24
add list=bogons address=224.0.0.0/4
add list=bogons address=240.0.0.0/4
```

> If the WAN itself is RFC1918 (CGNAT / behind another router), do **not** drop
> that range as a bogon. Flag this in the checklist.

## IPv4 filter

```
/ip firewall filter
;# --- INPUT: traffic TO the router ---
add chain=input action=accept connection-state=established,related,untracked comment="est/rel/untracked"
add chain=input action=drop   connection-state=invalid comment="drop invalid"
add chain=input action=accept protocol=icmp limit=50/5s,5:packet comment="icmp rate-limited"
add chain=input action=accept in-interface-list=LAN comment="LAN to router (tighten to MGMT if strict)"
add chain=input action=accept src-address=<MGMT_SUBNET> comment="management sources"
add chain=input action=drop   comment="DEFAULT DROP INPUT"

;# --- FORWARD: traffic THROUGH the router ---
add chain=forward action=fasttrack-connection connection-state=established,related hw-offload=yes comment="fasttrack"
add chain=forward action=accept connection-state=established,related,untracked comment="est/rel/untracked"
add chain=forward action=drop   connection-state=invalid comment="drop invalid"
add chain=forward action=drop   connection-state=new connection-nat-state=!dstnat in-interface-list=WAN comment="drop un-forwarded WAN-in"
add chain=forward action=accept in-interface-list=LAN out-interface-list=WAN comment="LAN to WAN"
add chain=forward action=drop   comment="DEFAULT DROP FORWARD"
```

Notes:
- The `input` rule accepting all of `LAN` is convenient; for a strict build,
  replace it with `src-address=<MGMT_SUBNET>` only and let DNS/DHCP be accepted
  by explicit service rules.
- The `forward` WAN-in drop lets inbound `dstnat` (port forwards) through while
  blocking unsolicited WAN-initiated sessions.
- Keep the two `DEFAULT DROP` rules **last** in their chains.

## IPv4 NAT

```
/ip firewall nat
add chain=srcnat action=masquerade out-interface-list=WAN comment="LAN masquerade"
;# port forward example (only if requested):
;# add chain=dstnat action=dst-nat in-interface-list=WAN protocol=tcp \
;#     dst-port=<PUB_PORT> to-addresses=<LAN_HOST> to-ports=<LAN_PORT> comment="fwd <svc>"
```

Prefer `action=src-nat to-addresses=<WAN_IP>` over `masquerade` when the WAN IP
is static — it is cheaper and survives interface flaps better.

## IPv6 firewall (required if any IPv6 is configured)

```
/ipv6 firewall address-list
add list=bad_ipv6 address=::1/128
add list=bad_ipv6 address=fe80::/10 comment="link-local (context dependent)"
add list=bad_ipv6 address=fc00::/7  comment="ULA"

/ipv6 firewall filter
add chain=input  action=accept connection-state=established,related,untracked
add chain=input  action=drop   connection-state=invalid
add chain=input  action=accept protocol=icmpv6 comment="ICMPv6 is mandatory for IPv6 to work"
add chain=input  action=accept in-interface-list=LAN
add chain=input  action=drop   comment="DEFAULT DROP INPUT v6"
add chain=forward action=accept connection-state=established,related,untracked
add chain=forward action=drop   connection-state=invalid
add chain=forward action=accept protocol=icmpv6
add chain=forward action=accept in-interface-list=LAN out-interface-list=WAN
add chain=forward action=drop   comment="DEFAULT DROP FORWARD v6"
```

**Do not** blanket-drop ICMPv6 — Neighbor Discovery and PMTUD rely on it, and
dropping it breaks IPv6 connectivity in subtle ways.

## Ordering rule of thumb

`raw` (drop garbage) → address-lists → `filter input` → `filter forward` →
`nat`. Default-drop rules always last in their chain. When editing an existing
config, use `place-before=` so a new rule lands above the default drop, not
after it.
