---
name: mikrotik-config-gen
version: 0.1.0
description: >
  Generate secure MikroTik RouterOS v7 configurations from a plain-language
  description, or review and harden an existing /export. Use when the user asks
  to write, generate, build, audit, or harden a MikroTik / RouterOS config,
  firewall, NAT, PPPoE + RADIUS BNG, site-to-site WireGuard, hotspot captive
  portal, or ISP edge router. Always applies a security-hardening baseline,
  takes per-model port and interface names from devices/, and never invents IPs
  or secrets — it emits clearly marked placeholders plus a fill-in checklist.
metadata:
  author: Pavel Rykov <paul@drteam.rocks>
  homepage: https://github.com/EvilFreelancer/mikrotik-config-gen
  triggers: >
    mikrotik, routeros, routeros v7, mikrotik config, harden mikrotik, /export
    review, pppoe bng, wireguard site-to-site, hotspot captive portal, isp edge
---

# MikroTik config generator

Turn a plain-language network description into a deployable **RouterOS v7**
script, or review an existing `/export` and harden it. This skill encodes the
security baseline, the canonical firewall structure, four ready presets, and a
per-model hardware reference so you assemble a correct config instead of
guessing interface names or leaving management ports open.

Scope: **RouterOS v7 only** (native WireGuard, the new `/routing` stack, `/ip`
menu layout). If the user is on v6, say so and stop — the syntax differs.

## When to use

- "Generate a MikroTik config for …", "set up an ISP edge router", "PPPoE BNG
  with RADIUS", "site-to-site WireGuard between two routers", "hotspot with a
  captive portal".
- "Review / audit / harden this config" + a pasted `/export`.
- Any request that ends in a `.rsc` script the user will paste into Winbox
  terminal or SSH.

## Two modes

| Mode | Trigger | What you produce |
|------|---------|------------------|
| **Generate** | a description of the network | a full `.rsc` from scratch, hardened |
| **Review** | a pasted `/export` (or `.rsc`) | findings list + a corrected/hardened `.rsc` |

## Workflow

Follow this order every time. Details live in `references/`.

1. **Detect the mode** — is there an existing `/export` to review, or a
   description to build from? If both, review then extend.
2. **Identify the device.** Ask for the model (or read it from the export's
   `# model =` header). Look it up in `devices/` to get real interface names
   (`ether1..N`, `sfp-sfpplus1`, `wlan1/wlan2`, PoE-out ports, switch grouping).
   If the model is unknown, say so and use generic `etherN` names, and flag it
   in the fill-in checklist.
3. **Gather requirements → build a gap checklist.** Ask only the questions you
   need (WAN type, LAN subnet, VLANs, DHCP range, remote-management sources,
   VPN peers, etc.). See `references/workflow.md` for the question set per
   preset. **Never invent** IPs, passwords, PSKs, ASNs, or ISP details — use
   explicit placeholders (`<WAN_IP>`, `<LAN_SUBNET>`, `<ADMIN_PASSWORD>`,
   `<WG_PEER_PUBKEY>`) and collect every one into a "Fill these in" list at the
   end. This is the site's "Review Gaps" step.
4. **Pick a preset** if the task matches one in `presets/`, and adapt it. Presets
   already include the hardening baseline.
5. **Assemble in canonical order** (see `references/workflow.md`):
   identity → users & service hardening → interface lists → bridges/VLANs →
   addressing → DHCP/DNS → firewall (raw → filter → NAT) → routing → the target
   feature (PPPoE/WireGuard/hotspot/…) → SNMP/logging/NTP.
6. **Always apply the hardening baseline** from `references/hardening.md`, even
   in Generate mode with a terse prompt. It is not optional.
7. **Validate** the script offline: `python3 scripts/validate.py out.rsc`.
   Fix every `ERROR`, review every `WARN`. The validator is a heuristic linter,
   not a substitute for a device — see its caveats below.
8. **Deliver** the `.rsc` in a fenced block, followed by:
   - the **Fill these in** checklist (every placeholder),
   - an **anti-lockout** warning and the recommended apply order,
   - a one-line reminder to apply under `/system safe-mode` (press `F4` in
     terminal / the toggle in Winbox) so a bad rule auto-reverts.

## Hardening baseline (summary)

Full list and rationale in `references/hardening.md`. Every config must:

- Put a **default-drop** at the end of `chain=input` and `chain=forward`, with
  `accept established,related` and `drop invalid` first.
- **Disable unused IP services** (telnet, ftp, www, api, api-ssl) and pin the
  rest (`winbox`, `ssh`) to a management subnet via `/ip service set address=`.
- Drop management on WAN: no Winbox/SSH/DNS/`allow-remote-requests` reachable
  from the internet; disable MAC-server, MAC-winbox and neighbor discovery on
  the WAN interface list.
- Filter bogons/RFC1918 and drop `invalid`/`bad TCP` in `/ip firewall raw`.
- Mirror the firewall for **IPv6** whenever any IPv6 address is configured.
- Strong `admin` password (placeholder), disable or rename the default user,
  set `/system clock` timezone and NTP, and set `/system note`/identity.

## Presets

Adapt these; do not paste verbatim without filling placeholders. See `presets/`.

| Preset | File | Use when |
|--------|------|----------|
| ISP edge router | `presets/isp-edge.md` | single WAN uplink + NAT'd LAN, hardened border |
| PPPoE + RADIUS (BNG) | `presets/pppoe-radius-bng.md` | subscriber termination with RADIUS AAA |
| Site-to-site WireGuard | `presets/wireguard-s2s.md` | two routers, encrypted tunnel between LANs |
| Hotspot captive portal | `presets/hotspot.md` | guest Wi-Fi / captive login |

## Device reference

`devices/` holds per-model port and interface data (Ethernet count, SFP/SFP+,
wireless bands, PoE-in/out, USB, switch-chip grouping, default WAN port). Read
the relevant file to get **real interface names** before writing the config.
Start at `devices/README.md`. If a model is not listed, use generic names and
note it in the checklist — do not guess PoE-out or SFP+ port numbers.

## Output rules

- **RouterOS v7 syntax only.** Prefer full-path commands (`/ip/address/add …`)
  or the classic `/ip address add …` form consistently; comment every section.
- One deployable `.rsc` in a single fenced block, ordered as in step 5.
- Every secret/site-specific value is a `<PLACEHOLDER>`; list them all.
- Comment each block (`# --- WAN ---`) so the user can read and trust it.
- Never claim it was tested on hardware. It was not. Say "generated, validate
  on-device in safe mode".

## Validation

```bash
python3 scripts/validate.py path/to/config.rsc      # human report
python3 scripts/validate.py --json path/to/config.rsc
```

It flags: missing input/forward default-drop, services open to `0.0.0.0/0`,
unpinned winbox/ssh, DNS `allow-remote-requests` without a WAN drop, missing
IPv6 firewall when IPv6 is present, leftover `<PLACEHOLDER>` tokens, and basic
syntax problems (unbalanced quotes/braces). Exit code is non-zero if any
`ERROR` is found.

**Caveat:** RouterOS has no official offline validator. This is a static
heuristic; a clean report is not proof of correctness. The only real test is
applying the script on the device under `/system safe-mode`.

## Common mistakes

- Leaving `winbox`/`api`/`www` reachable from WAN — the #1 way boxes get owned.
- Forgetting the `chain=forward` default-drop (only dropping `input`).
- Using v6-only or deprecated syntax on v7 (bridge VLAN filtering, `/routing`).
- Guessing interface names instead of reading `devices/`.
- Inventing IPs/passwords instead of emitting placeholders.
- Applying without safe-mode and locking yourself out.
