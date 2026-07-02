# Workflow: modes, questions, build order, delivery

## Generate mode

Input: a plain-language description. Output: a full `.rsc` from scratch.

1. Identify the device model → `devices/` for interface names.
2. Ask the gap questions for the matching scenario (below). Ask them in one
   batch, not one-by-one, and mark anything the user leaves blank as a
   placeholder.
3. Pick a preset from `presets/` if one fits; otherwise assemble from the
   references.
4. Emit the script in canonical order (below) with the hardening baseline.
5. Validate, then deliver with the fill-in checklist and anti-lockout note.

## Review mode

Input: a pasted `/export` (starts with `# <date> by RouterOS <ver>` and lines
like `/ip firewall filter`). Output: findings + a corrected `.rsc`.

1. Read the `# model =` / `# software id =` header for the device and version.
   If it says RouterOS 6.x, stop and tell the user this skill targets v7.
2. Walk the export against the **review checklist** in
   [hardening.md](hardening.md#review-mode-checklist).
3. Produce a findings table: `severity | area | issue | fix`.
4. Produce a corrected `.rsc` containing only the **changes** (use
   `set`/`add place-before=`/`remove`), or a full rebuilt config if the user
   asked for one. Keep existing addressing/passwords as placeholders — do not
   echo real secrets back.
5. Validate the corrected script and deliver.

## Canonical build order

Always emit sections in this order so dependencies resolve and you never lock
yourself out mid-script:

1. `/system identity`, `/system clock`, `/system ntp client`
2. `/user` (create named admin; note to disable default after login)
3. `/ip service`, discovery, mac-server, unused daemons off (hardening.md §3–5)
4. `/interface list` + members (WAN/LAN/MGMT)
5. Bridges, VLANs, bonding (`/interface bridge`, `/interface vlan`)
6. Addressing: `/ip address`, `/ipv6 address`, `/ip pool`, `/ip dhcp-server`,
   `/ip dhcp-client` (WAN) or PPPoE client
7. `/ip dns`
8. Firewall: `/ip firewall raw` → address-lists → `filter` → `nat`; IPv6 mirror
9. Routing: `/ip route`, `/routing` (OSPF/BGP) as needed
10. Target feature: PPPoE server + RADIUS / WireGuard / hotspot / etc.
11. SNMP, logging, scheduler, extras

## Gap questions per scenario

Ask what you actually need; everything unanswered becomes a placeholder.

**Common to all**
- Device model? Management source subnet/host (`<MGMT_SUBNET>`)? SSH port?
- WAN type: DHCP client / static / PPPoE? WAN interface (from `devices/`)?
- LAN subnet + gateway (`<LAN_SUBNET>`, `<LAN_GW>`)? DHCP range? VLANs?
- IPv6 in use? If yes, prefix/delegation source.

**ISP edge** — number of uplinks; static WAN IP or DHCP/PPPoE; any port
forwards; failover needed?

**PPPoE + RADIUS (BNG)** — RADIUS server IP + secret (`<RADIUS_IP>`,
`<RADIUS_SECRET>`); PPPoE service name; local vs remote IP pool for subscribers;
default profile (rate-limit, DNS); interface(s) facing subscribers.

**Site-to-site WireGuard** — this router's role; peer public endpoint
(`<PEER_ENDPOINT>`) + port; each side's tunnel address (`<WG_LOCAL_IP>`); the
LAN subnets to route across (`<LOCAL_LAN>`, `<REMOTE_LAN>`); peer public key
(`<WG_PEER_PUBKEY>`) — generate the local keypair on-device.

**Hotspot** — interface/bridge for guests; hotspot subnet + pool; auth method
(HTML login, PIN, RADIUS); walled-garden hosts; session/rate limits.

## Delivery format

Deliver in this shape:

````
```rsc
# --- <hostname> — RouterOS v7 — generated, validate on-device in safe mode ---
# --- SYSTEM ---
...
```
````

Then:

**Fill these in**
- `<WAN_IP>` — public address from the ISP
- `<LAN_SUBNET>` — internal network, e.g. 192.168.88.0/24
- `<ADMIN_PASSWORD>` — strong password
- … (list every placeholder that appears)

**Apply safely (anti-lockout)**
1. Enter safe mode: terminal `F4`, or the Safe Mode button in Winbox. If the
   session drops, the router auto-reverts.
2. Paste the script (or apply section by section: system → interfaces →
   addressing → **firewall last**).
3. Confirm you still have access, then exit safe mode to commit.
4. If applying remotely, add the firewall rules with a scheduled
   `:delay 300; /ip firewall filter remove [find comment~"DEFAULT DROP"]`
   rollback until you have verified access, then cancel it.

Never state the config was tested on hardware — it was generated and
statically validated only.
