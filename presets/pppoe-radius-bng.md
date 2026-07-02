# Preset: PPPoE server + RADIUS (BNG)

Subscriber termination: the router runs a PPPoE server, authenticates each
session against a RADIUS server, and hands out addresses from a pool (or from
RADIUS Framed-IP). This is a Broadband Network Gateway edge. RouterOS v7.

## Gap questions
- Subscriber-facing interface(s) or VLAN(s) (`<SUB_IFACE>`).
- PPPoE `service-name` (`<PPPOE_SVC>`).
- RADIUS server IP `<RADIUS_IP>` + shared secret `<RADIUS_SECRET>`.
- Subscriber address source: local pool `<PPP_POOL_RANGE>` or RADIUS Framed-IP.
- Gateway/local address for PPP `<PPP_LOCAL_IP>`; DNS for subscribers.
- Default rate-limit / profile? Accounting needed?

## Template

```rsc
# --- <HOSTNAME> — PPPoE BNG + RADIUS — RouterOS v7 — validate in safe mode ---

# --- SYSTEM + HARDENING (see hardening.md; abbreviated here) ---
/system identity set name=<HOSTNAME>
/ip service disable telnet,ftp,www,api,api-ssl
/ip service set ssh port=<SSH_PORT> address=<MGMT_SUBNET>
/ip service set winbox address=<MGMT_SUBNET>

# --- INTERFACE LISTS ---
/interface list add name=WAN
/interface list add name=LAN
/interface list add name=SUBS comment="subscriber-facing"
/interface list member add list=WAN interface=<UPLINK_IFACE>
/interface list member add list=SUBS interface=<SUB_IFACE>

# --- IP POOL FOR SUBSCRIBERS (skip if RADIUS assigns Framed-IP) ---
/ip pool add name=pppoe-pool ranges=<PPP_POOL_RANGE>

# --- PPP PROFILE ---
/ppp profile add name=bng-default local-address=<PPP_LOCAL_IP> \
    remote-address=pppoe-pool dns-server=<DNS1>,<DNS2> \
    rate-limit=<UP>/<DOWN> only-one=yes comment="default subscriber profile"

# --- RADIUS ---
/radius add service=ppp address=<RADIUS_IP> secret=<RADIUS_SECRET> \
    timeout=3s src-address=<RADIUS_SRC_IP>
/ppp aaa set use-radius=yes accounting=yes interim-update=5m
/radius incoming set accept=yes port=3799   ;# CoA / disconnect (optional)

# --- PPPoE SERVER ---
/interface pppoe-server server add service-name=<PPPOE_SVC> \
    interface=<SUB_IFACE> default-profile=bng-default \
    authentication=pap,chap,mschap2 one-session-per-host=yes \
    max-sessions=<MAX_SESSIONS> disabled=no

# --- FIREWALL ---
/ip firewall filter
add chain=input action=accept connection-state=established,related,untracked
add chain=input action=drop connection-state=invalid
add chain=input action=accept protocol=icmp limit=50/5s,5:packet
add chain=input action=accept src-address=<MGMT_SUBNET> comment="mgmt"
add chain=input action=accept protocol=udp port=1812,1813 src-address=<RADIUS_IP> comment="radius"
add chain=input action=drop comment="DEFAULT DROP INPUT"
add chain=forward action=accept connection-state=established,related,untracked
add chain=forward action=drop connection-state=invalid
add chain=forward action=accept in-interface=all-ppp out-interface-list=WAN comment="subs to upstream"
add chain=forward action=accept in-interface-list=WAN out-interface=all-ppp comment="upstream to subs"
add chain=forward action=drop comment="DEFAULT DROP FORWARD"

# --- NAT (only if subscribers use private IPs) ---
/ip firewall nat
add chain=srcnat action=masquerade out-interface-list=WAN comment="CGNAT/masq (omit if public IPs routed)"
```

## Notes
- `remote-address=pppoe-pool` gives addresses from the local pool; if RADIUS
  returns `Framed-IP-Address`, that overrides the pool per subscriber.
- `in-interface=all-ppp` matches every dynamic PPP session in the firewall.
- For per-subscriber rate limits, return `Mikrotik-Rate-Limit` from RADIUS
  instead of hard-coding `rate-limit` in the profile.
- MTU/MRU: PPPoE overhead means 1480; set `max-mtu=1480 max-mru=1480` on the
  server if you see fragmentation, and consider `change-tcp-mss=yes`.
- Large BNG: prefer a dedicated subscriber VLAN trunk and terminate PPPoE per
  VLAN; watch the switch-chip vs CPU forwarding path on the model (`devices/`).

## Fill these in
`<HOSTNAME> <SSH_PORT> <MGMT_SUBNET> <UPLINK_IFACE> <SUB_IFACE> <PPP_POOL_RANGE>
<PPP_LOCAL_IP> <DNS1> <DNS2> <UP> <DOWN> <RADIUS_IP> <RADIUS_SECRET>
<RADIUS_SRC_IP> <PPPOE_SVC> <MAX_SESSIONS>`.
