# Authoring & maintaining the `mikrotik-config-gen` skill

Agent guide for working **inside this skill repository**. Read it before editing
`SKILL.md`, the references, the presets, the device tables, or any plugin
manifest.

> Naming (Russian): the adjective for "agent / agentic" is **«агентный»**, never
> «агентский».

## Repository layout

This skill is packaged for **Claude Code**, **Cursor**, and **OpenAI Codex**
(and installs as a plain skill folder for other agents). The layout is **flat** —
`SKILL.md` and its assets live at the repo root, and the plugin manifests point
their skill source at `./`.

```
mikrotik-config-gen/
├─ .claude-plugin/
│  ├─ plugin.json        # Claude Code plugin manifest
│  └─ marketplace.json   # single-plugin marketplace (plugin lives at "./")
├─ .cursor-plugin/plugin.json    # Cursor manifest
├─ .codex-plugin/plugin.json     # Codex manifest (interface block + skills: "./")
├─ SKILL.md              # CANONICAL skill: YAML frontmatter + instructions
├─ references/           # deep knowledge, loaded on demand from SKILL.md
├─ presets/              # four ready configs (adapt, don't paste verbatim)
├─ devices/              # per-model port/interface reference
├─ scripts/validate.py   # offline heuristic linter (stdlib only)
├─ README.md  AGENTS.md  LICENSE
```

There is no `skills/<name>/` subfolder — the root **is** the skill. If you
migrate to the nested layout, keep the root `SKILL.md` as a copy and update all
three manifests to match.

## Editing rules

- **Keep `SKILL.md` thin.** It holds the workflow and the hard rules. Depth goes
  in `references/`, `presets/`, `devices/`. If a section grows past a screen,
  move the detail into a reference and link it.
- **Every config is RouterOS v7.** If you add v6 notes, mark them clearly as
  out of scope. Do not mix v6 and v7 syntax in a preset.
- **Never bake in real secrets or IPs.** Presets and examples use
  `<PLACEHOLDER>` tokens and end with a "Fill these in" list. `validate.py`
  reports leftover placeholders as a warning — that is expected for a template.
- **Hardening is not optional.** Any change to a preset must preserve the
  input/forward default-drop and the service lockdown. Run `validate.py` on the
  preset's config block after editing. **Full** presets (isp-edge, pppoe, hotspot)
  must report **0 errors**. **Overlay** presets (wireguard-s2s) are applied on top
  of a hardened base and lint clean only when combined with it — that is expected.
- **Device tables:** naming conventions are the reliable part and must stay
  accurate. Exact PoE-out ports / combo behaviour vary by revision — hedge those
  with "check datasheet" rather than asserting a wrong specific.

## Keeping metadata in sync

When you change the description or bump the version, update it in **all** of:

- `SKILL.md` frontmatter (`version`, `description`)
- `.claude-plugin/plugin.json` **and** `.claude-plugin/marketplace.json`
- `.cursor-plugin/plugin.json`
- `.codex-plugin/plugin.json` (both top-level and the `interface` block)
- `README.md`

Keep the `name` identical everywhere: `mikrotik-config-gen`.

## Testing the linter

`scripts/validate.py` is pure stdlib (Python 3.8+). After changing it, sanity
check against a known-good config (0 errors) and a known-bad one (services open,
no default-drop → errors). The linter is a heuristic; keep false positives low —
it should not flag a config that is protected by an input default-drop.

## What this skill does NOT do

- It does not connect to or test on a device. Output is generated and statically
  validated only; say so.
- It does not target RouterOS v6, SwOS, or non-MikroTik gear.
- It does not store or echo back real credentials from a reviewed `/export`.
