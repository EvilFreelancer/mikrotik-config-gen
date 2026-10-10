# mikrotik-config-gen

An agent skill that generates secure **MikroTik RouterOS v7** configurations from
a plain-language description, or reviews and hardens an existing `/export`. It is
a portable skill — install it in Claude Code, Cursor, or OpenAI Codex, or just
drop the folder into any agent that reads `SKILL.md`, and generate configs
anywhere.

Inspired by the web tool at
[zille-skill-mikrotik.lovable.app](https://zille-skill-mikrotik.lovable.app/):
same idea (plain English → hardened RouterOS v7 script), packaged as a skill so
it runs inside your own agent instead of a website.

## What it does

- **Generate** — describe the network ("ISP edge with PPPoE WAN and a /24 LAN")
  and get a deployable `.rsc`, hardened by default.
- **Review** — paste an existing `/export` and get a findings list plus a
  corrected, hardened config.
- **Harden** — a non-optional security baseline: default-drop firewall, disabled
  unused services, management pinned to a trusted subnet, bogon/anti-spoof
  filtering, IPv6 firewall parity.
- **Presets** — ISP edge, PPPoE + RADIUS (BNG), site-to-site WireGuard, hotspot
  captive portal.
- **Device reference** — per-model port/interface data so the agent uses real
  names (`ether1`, `sfp-sfpplus1`, `wlan1`/`wifi1`) instead of guessing.
- **Validate** — an offline heuristic linter for the generated script.

Scope: **RouterOS v7 only**. Nothing here is tested on hardware — configs are
generated and statically validated; apply them on-device under `/system
safe-mode`.

## Layout

```
mikrotik-config-gen/
├─ SKILL.md                 # the skill: workflow + rules the agent follows
├─ references/
│  ├─ workflow.md           # modes, gap questions, build order, delivery
│  ├─ hardening.md          # the security baseline (with commands)
│  ├─ firewall.md           # canonical raw/filter/nat + IPv6 structure
│  └─ routeros7-notes.md    # v7 syntax and v6→v7 gotchas
├─ presets/
│  ├─ isp-edge.md
│  ├─ pppoe-radius-bng.md
│  ├─ wireguard-s2s.md
│  └─ hotspot.md
├─ devices/                 # per-model ports, SFP, Wi-Fi, PoE, interface names
│  ├─ README.md
│  ├─ soho-hex-hap.md
│  ├─ rb-series.md
│  ├─ ccr-series.md
│  └─ crs-series.md
├─ scripts/
│  └─ validate.py           # offline heuristic linter (stdlib only)
├─ .claude-plugin/ .cursor-plugin/ .codex-plugin/   # agent manifests
├─ AGENTS.md  README.md  LICENSE
```

## Install

The skill is distributed through the [rpa-skills](https://github.com/EvilFreelancer/rpa-skills) catalog
and also installs as a plain skill folder.

**As a plugin (Claude Code)**: add the catalog once, then install this skill from it:

```text
/plugin marketplace add EvilFreelancer/rpa-skills
/plugin install mikrotik-config-gen@rpa-skills
```

**Codex**: `codex plugin marketplace add EvilFreelancer/rpa-skills`, then install `mikrotik-config-gen` from `/plugins`.

**In Coddy**: the rpa-skills catalog is built into [Coddy](https://coddy.dev) as a system source,
so there is nothing to connect. One sync installs this skill together with the rest of the collection
into `~/.coddy/skills/mikrotik-config-gen/` and keeps it up to date (or press **Sync all** in Settings → Skills):

```bash
coddy skills sync
```

**As a plain skill folder**: copy or symlink this repository into a skill root (its `SKILL.md` lives at
the repo root):

| Tool          | Path |
|---------------|------|
| Claude Code   | `~/.claude/skills/mikrotik-config-gen/` |
| Cursor        | `~/.cursor/skills/mikrotik-config-gen/` |
| OpenAI Codex  | `~/.codex/skills/mikrotik-config-gen/` |
| Kimi Code CLI | `~/.kimi/skills/mikrotik-config-gen/` |
| Coddy         | `~/.coddy/skills/mikrotik-config-gen/` |

The directory name must match the `name` field in `SKILL.md`.

## Usage

Ask your agent, for example:

- "Generate a MikroTik RB5009 config: PPPoE WAN on ether1 (2.5G), LAN
  192.168.10.0/24, management from 10.0.0.0/24 only."
- "Set up site-to-site WireGuard between two hAP ax³ routers."
- "Review and harden this export:" *(paste `/export`)*

Then validate the result:

```bash
python3 scripts/validate.py my-config.rsc
python3 scripts/validate.py --json my-config.rsc
```

## Safety

- Secrets and site-specific values are emitted as `<PLACEHOLDERS>` with a
  fill-in checklist — the skill never invents IPs or passwords.
- Every config comes with an anti-lockout note; apply under `/system safe-mode`.
- The validator is a heuristic, not a guarantee. A clean report is not proof of
  correctness — the device is the only real test.

## License

MIT © Pavel Rykov. Not affiliated with MikroTik. "MikroTik" and "RouterOS" are
trademarks of Mikrotīkls SIA.
