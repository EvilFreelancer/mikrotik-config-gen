# Preset: ISP edge router

Single WAN uplink, NAT'd/routed LAN, hardened border. WAN is shown as a DHCP
client; swap the WAN block for the static or PPPoE variant as noted. Fill every
`<PLACEHOLDER>` and validate before applying.

## Gap questions
- Model + WAN/LAN port names (see `devices/`).
- WAN: DHCP / static (`<WAN_IP>/<WAN_CIDR>`, `<WAN_GW>`) / PPPoE?
- LAN subnet, gateway, DHCP range.
- Management source (`<MGMT_SUBNET>`), SSH port.
- Any inbound port forwards? IPv6?

## Template

```rsc
# --- <HOSTNAME> — ISP edge — RouterOS v7 — generate & validate in safe mode ---

# --- SYSTEM ---
/system identity set name=<HOSTNAME>
/system clock set time-zone-name=<TIMEZONE>
/system ntp client set enabled=yes mode=unicast
/system ntp client servers add address=<NTP1>
/system ntp client servers add address=<NTP2>

# --- USERS ---
/user add name=<ADMIN_USER> group=full password=<ADMIN_PASSWORD>
;# after confirming login: /user set admin disabled=yes

# --- SERVICES (harden) ---
/ip service disable telnet,ftp,www,api,api-ssl
/ip service set ssh port=<SSH_PORT> address=<MGMT_SUBNET>
/ip service set winbox address=<MGMT_SUBNET>
/ip ssh set strong-crypto=yes host-key-size=4096
/tool bandwidth-server set enabled=no
/tool romon set enabled=no
/ip proxy set enabled=no
/ip socks set enabled=no
/ip upnp set enabled=no
/ip cloud set ddns-enabled=no

# --- INTERFACE LISTS ---
/interface list add name=WAN
/interface list add name=LAN
/interface list member add list=WAN interface=<WAN_IFACE>
/interface list member add list=LAN interface=bridgeLocal

# --- LAN BRIDGE (add the switch ports you want in the LAN) ---
/interface bridge add name=bridgeLocal
/interface bridge port add bridge=bridgeLocal interface=<LAN_IFACE_1>
/interface bridge port add bridge=bridgeLocal interface=<LAN_IFACE_2>

# --- DISCOVERY / MAC (LAN only) ---
/ip neighbor discovery-settings set discover-interface-list=LAN
/tool mac-server set allowed-interface-list=LAN
/tool mac-server mac-winbox set allowed-interface-list=LAN
/tool mac-server ping set enabled=no

# --- ADDRESSING ---
/ip address add address=<LAN_GW>/24 interface=bridgeLocal comment="LAN gw"
# WAN (DHCP client) — replace with static or PPPoE variant below if needed
/ip dhcp-client add interface=<WAN_IFACE> use-peer-dns=no add-default-route=yes

# --- DHCP SERVER (LAN) ---
/ip pool add name=lan-pool ranges=<DHCP_RANGE>
/ip dhcp-server add name=lan-dhcp interface=bridgeLocal address-pool=lan-pool
/ip dhcp-server network add address=<LAN_SUBNET> gateway=<LAN_GW> dns-server=<LAN_GW>

# --- DNS ---
/ip dns set servers=<DNS1>,<DNS2> allow-remote-requests=yes cache-size=2048KiB

# --- FIREWALL: RAW (anti-spoof / bogons) ---
/ip firewall address-list
add list=bogons address=0.0.0.0/8
add list=bogons address=10.0.0.0/8
add list=bogons address=100.64.0.0/10
add list=bogons address=127.0.0.0/8
add list=bogons address=169.254.0.0/16
add list=bogons address=172.16.0.0/12
add list=bogons address=192.168.0.0/16
add list=bogons address=224.0.0.0/4
add list=bogons address=240.0.0.0/4
/ip firewall raw
add chain=prerouting action=drop in-interface-list=WAN src-address-list=bogons comment="drop bogons in"
add chain=prerouting action=drop in-interface-list=WAN src-address=<LAN_SUBNET> comment="anti-spoof"

# --- FIREWALL: FILTER ---
/ip firewall filter
add chain=input action=accept connection-state=established,related,untracked
add chain=input action=drop connection-state=invalid
add chain=input action=accept protocol=icmp limit=50/5s,5:packet comment="icmp"
add chain=input action=accept src-address=<MGMT_SUBNET> comment="mgmt"
add chain=input action=accept in-interface-list=LAN comment="LAN to router (DNS/DHCP)"
add chain=input action=drop comment="DEFAULT DROP INPUT"
add chain=forward action=fasttrack-connection connection-state=established,related hw-offload=yes
add chain=forward action=accept connection-state=established,related,untracked
add chain=forward action=drop connection-state=invalid
add chain=forward action=drop connection-state=new connection-nat-state=!dstnat in-interface-list=WAN comment="block unsolicited WAN-in"
add chain=forward action=accept in-interface-list=LAN out-interface-list=WAN comment="LAN to WAN"
add chain=forward action=drop comment="DEFAULT DROP FORWARD"

# --- NAT ---
/ip firewall nat
add chain=srcnat action=masquerade out-interface-list=WAN comment="LAN masquerade"
;# port forward (optional):
;# add chain=dstnat action=dst-nat in-interface-list=WAN protocol=tcp dst-port=<PUB_PORT> to-addresses=<LAN_HOST> to-ports=<LAN_PORT>

# --- LOGGING ---
/system logging add topics=critical,error,warning action=memory
```

## Static WAN variant
Replace the DHCP-client line with:
```rsc
/ip address add address=<WAN_IP>/<WAN_CIDR> interface=<WAN_IFACE> comment="WAN"
/ip route add dst-address=0.0.0.0/0 gateway=<WAN_GW> comment="default"
/ip dns set servers=<DNS1>,<DNS2>
```

## PPPoE WAN variant
Replace the DHCP-client line with:
```rsc
/interface pppoe-client add name=pppoe-out1 interface=<WAN_IFACE> \
    user=<PPP_USER> password=<PPP_PASS> add-default-route=yes use-peer-dns=yes disabled=no
```
and add `pppoe-out1` to the `WAN` interface list instead of (or with) the
physical port.

## Fill these in
`<HOSTNAME> <TIMEZONE> <NTP1> <NTP2> <ADMIN_USER> <ADMIN_PASSWORD> <SSH_PORT>
<MGMT_SUBNET> <WAN_IFACE> <LAN_IFACE_1> <LAN_IFACE_2> <LAN_GW> <LAN_SUBNET>
<DHCP_RANGE> <DNS1> <DNS2>` (+ WAN variant values / port-forward values).
