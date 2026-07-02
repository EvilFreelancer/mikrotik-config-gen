# Preset: hotspot captive portal

Guest network with a captive login page. Users hit any URL, get redirected to
the hotspot login, authenticate (local user, voucher/PIN, or RADIUS), then get
internet. RouterOS v7.

## Gap questions
- Guest interface/bridge (`<GUEST_IFACE>`) and subnet (`<HS_SUBNET>`, `<HS_GW>`).
- DHCP range for guests (`<HS_RANGE>`).
- Auth: local users / RADIUS (`<RADIUS_IP>` + `<RADIUS_SECRET>`)?
- Walled garden hosts (payment page, auth domain) to allow pre-login.
- Session timeout, shared-users, rate-limit per user.

## Template

```rsc
# --- <HOSTNAME> — Hotspot captive portal — RouterOS v7 — validate in safe mode ---

# --- SYSTEM + HARDENING (see hardening.md) ---
/system identity set name=<HOSTNAME>
/ip service disable telnet,ftp,www,api,api-ssl
/ip service set ssh port=<SSH_PORT> address=<MGMT_SUBNET>
/ip service set winbox address=<MGMT_SUBNET>
/tool bandwidth-server set enabled=no
/ip proxy set enabled=no

# --- GUEST BRIDGE + ADDRESS ---
/interface bridge add name=bridgeGuest
/interface bridge port add bridge=bridgeGuest interface=<GUEST_IFACE>
/interface list add name=LAN
/interface list member add list=LAN interface=bridgeGuest
/ip address add address=<HS_GW>/24 interface=bridgeGuest comment="hotspot gw"

# --- DHCP FOR GUESTS ---
/ip pool add name=hs-pool ranges=<HS_RANGE>
/ip dhcp-server add name=hs-dhcp interface=bridgeGuest address-pool=hs-pool
/ip dhcp-server network add address=<HS_SUBNET> gateway=<HS_GW> dns-server=<HS_GW>

# --- DNS (hotspot needs the router to resolve for redirect) ---
/ip dns set servers=<DNS1>,<DNS2> allow-remote-requests=yes

# --- HOTSPOT PROFILE + SERVER ---
/ip hotspot profile add name=hsprof hotspot-address=<HS_GW> \
    dns-name=<HS_DNS_NAME> html-directory=hotspot login-by=http-chap,http-pap
/ip hotspot add name=guest interface=bridgeGuest address-pool=hs-pool \
    profile=hsprof addresses-per-mac=2 idle-timeout=5m keepalive-timeout=2m

# --- LOCAL USERS (skip if RADIUS) ---
/ip hotspot user profile add name=guest-limited rate-limit=<UP>/<DOWN> shared-users=1 session-timeout=1h
/ip hotspot user add name=<GUEST_USER> password=<GUEST_PASS> profile=guest-limited

# --- RADIUS variant (instead of local users) ---
;# /radius add service=hotspot address=<RADIUS_IP> secret=<RADIUS_SECRET>
;# /ip hotspot profile set hsprof use-radius=yes

# --- WALLED GARDEN (pre-login allow) ---
/ip hotspot walled-garden add dst-host=<ALLOWED_HOST> comment="e.g. payment/auth"
/ip hotspot walled-garden ip add dst-address=<ALLOWED_IP> action=accept comment="raw IP allow"

# --- FIREWALL (hotspot inserts its own rules; keep the border hardened) ---
/interface list add name=WAN
/interface list member add list=WAN interface=<WAN_IFACE>
/ip firewall filter
add chain=input action=accept connection-state=established,related,untracked
add chain=input action=drop connection-state=invalid
add chain=input action=accept src-address=<MGMT_SUBNET> comment="mgmt"
add chain=input action=accept in-interface=bridgeGuest protocol=udp port=53,67 comment="guest dns/dhcp"
add chain=input action=accept in-interface=bridgeGuest protocol=tcp port=64872,64873,80,443 comment="hotspot login"
add chain=input action=drop comment="DEFAULT DROP INPUT"
add chain=forward action=accept connection-state=established,related,untracked
add chain=forward action=drop connection-state=invalid
add chain=forward action=accept in-interface=bridgeGuest out-interface-list=WAN comment="guests to internet (post-login)"
add chain=forward action=drop comment="DEFAULT DROP FORWARD"

# --- NAT ---
/ip firewall nat
add chain=srcnat action=masquerade out-interface-list=WAN
```

## Notes
- The hotspot service auto-inserts NAT/filter/mangle rules in the `hotspot`
  chains when you create it; the rules above are the surrounding border policy.
- `login-by=http-chap,http-pap` for the standard login page; add `mac` for
  MAC-based auto-login (weak), `https` with a cert for encrypted login.
- Isolate guests from the trusted LAN: do **not** put `bridgeGuest` in the same
  bridge/interface-list as the internal LAN, and add no `forward` rule from
  guest to LAN.
- Customise the portal by editing files in the `hotspot/` directory on the
  router's filesystem (`html-directory`).

## Fill these in
`<HOSTNAME> <GUEST_IFACE> <HS_SUBNET> <HS_GW> <HS_RANGE> <HS_DNS_NAME>
<DNS1> <DNS2> <UP> <DOWN> <GUEST_USER> <GUEST_PASS> <ALLOWED_HOST>
<ALLOWED_IP> <WAN_IFACE> <MGMT_SUBNET>` (+ RADIUS values if used).
