# Security hardening baseline (RouterOS v7)

Apply this to **every** config, generate or review. Ordered roughly as it should
appear in the script. Values in `<ANGLE_BRACKETS>` are placeholders — never
invent them. Interface lists (`WAN`, `LAN`, `MGMT`) are defined in
[firewall.md](firewall.md); this file assumes they exist.

## 1. Identity, time, NTP

```
/system identity set name=<HOSTNAME>
/system clock set time-zone-name=<TIMEZONE>          ;# e.g. Europe/Moscow, UTC
/system ntp client set enabled=yes mode=unicast
/system ntp client servers add address=<NTP1>
/system ntp client servers add address=<NTP2>
```

Correct time is required for certificates, logs, and RADIUS. Do not skip it.

## 2. Users

```
/user add name=<ADMIN_USER> group=full password=<ADMIN_PASSWORD>
;# After you have confirmed login with the new user, disable the default:
;# /user set admin disabled=yes
/user aaa set interim-update=0s
```

- Never ship a config with an empty or default password.
- Prefer a **named** admin user over the built-in `admin`.
- If SSH keys are used, import with `/user ssh-keys import` and note the
  `<PUBKEY_FILE>` placeholder.

## 3. IP services — disable unused, pin the rest

```
/ip service disable telnet,ftp,www,api,api-ssl
/ip service set ssh   port=<SSH_PORT>   address=<MGMT_SUBNET>
/ip service set winbox                   address=<MGMT_SUBNET>
```

- `telnet`, `ftp`, `www`, `api`, `api-ssl` are off unless the user explicitly
  needs them (e.g. `www`/`api` for a controller). If needed, still pin `address=`.
- `<MGMT_SUBNET>` is the trusted management source, e.g. `10.0.0.0/24` or a
  jump host `/32`. Leaving `address=` empty means reachable from anywhere.
- Harden SSH: `/ip ssh set strong-crypto=yes host-key-size=4096`.

## 4. Neighbor discovery and MAC access

```
/ip neighbor discovery-settings set discover-interface-list=LAN
/tool mac-server set allowed-interface-list=LAN
/tool mac-server mac-winbox set allowed-interface-list=LAN
/tool mac-server ping set enabled=no
```

Keep MNDP/CDP, MAC-Telnet and MAC-Winbox off the WAN. MAC-Winbox on a public
interface bypasses IP firewalling.

## 5. Turn off unused daemons

```
/tool bandwidth-server set enabled=no
/tool romon set enabled=no                 ;# unless RoMON is deliberately used
/ip proxy set enabled=no
/ip socks set enabled=no
/ip upnp set enabled=no
/ip cloud set ddns-enabled=no update-time=no   ;# enable only if DDNS is wanted
```

## 6. DNS

```
/ip dns set servers=<DNS1>,<DNS2> allow-remote-requests=yes cache-size=2048KiB
```

`allow-remote-requests=yes` turns the router into a resolver for the LAN — it
**must** be paired with a firewall rule that drops `udp/tcp dst-port 53` on
`in-interface-list=WAN` (see firewall.md), or the box becomes a DNS
amplification reflector.

## 7. Firewall

The firewall is the core of hardening — see [firewall.md](firewall.md) for the
full `raw` + `filter` + `nat` structure. Non-negotiables:

- `chain=input`: accept `established,related`, accept ICMP (rate-limited),
  accept from `MGMT`/`LAN` to router services, **drop everything else**.
- `chain=forward`: accept `established,related`, `drop invalid`, use fasttrack
  for established if desired, allow `LAN→WAN`, **drop everything else**.
- `/ip firewall raw`: drop bogons and obvious spoofing on WAN ingress.
- Mirror all of this under `/ipv6 firewall` if any IPv6 is configured.

## 8. IPv6

If IPv6 is not used, disable it so it cannot be an unfiltered back door:

```
/ipv6 settings set disable-ipv6=yes forward=no
```

If IPv6 **is** used, it needs its own full firewall (see firewall.md). An
addressed-but-unfiltered IPv6 stack is a common real-world hole.

## 9. Logging

```
/system logging add topics=info,!debug action=memory
/system logging add topics=critical,error,warning action=memory
;# optional remote syslog:
;# /system logging action add name=remote target=remote remote=<SYSLOG_IP>
;# /system logging add topics=info action=remote
```

## Review-mode checklist

When auditing an existing `/export`, flag each of these as a finding
(ERROR / WARN) with the exact fix:

- [ ] Any IP service enabled with no `address=` restriction → ERROR
- [ ] `telnet`/`ftp`/`www`/`api` enabled at all → WARN (ERROR if open to WAN)
- [ ] No default-drop on `input` → ERROR
- [ ] No default-drop on `forward` → ERROR
- [ ] `discover-interface-list` / mac-server allowed on WAN or `all` → WARN
- [ ] `bandwidth-server` / `romon` / `upnp` enabled unintentionally → WARN
- [ ] DNS `allow-remote-requests=yes` without WAN drop of port 53 → ERROR
- [ ] IPv6 addressed but no `/ipv6 firewall` rules → ERROR
- [ ] Default/blank admin password, default `admin` user still active → WARN
- [ ] No NTP / wrong timezone → WARN
