#!/usr/bin/env python3
"""Heuristic offline linter for MikroTik RouterOS v7 scripts (.rsc).

This is NOT an official validator. RouterOS has no offline validator; a clean
report here is not proof of correctness. The only real test is applying the
script on the device under /system safe-mode.

It flags the security holes and mistakes this skill cares about:
  - missing default-drop on chain=input / chain=forward
  - IP services enabled without an address restriction (winbox/ssh/telnet/...)
  - risky services (telnet/ftp/www/api) left enabled
  - DNS allow-remote-requests without an input default-drop or a port-53 drop
  - IPv6 addressed but no /ipv6 firewall rules
  - leftover <PLACEHOLDER> tokens
  - basic syntax: unbalanced quotes / braces

Usage:
    python3 validate.py config.rsc
    python3 validate.py --json config.rsc
Exit code is non-zero when any ERROR is found.
"""
from __future__ import annotations

import argparse
import json
import re
import sys

ACTIONS = {
    "add", "set", "remove", "enable", "disable", "print", "export",
    "unset", "move", "comment", "find",
}
RISKY_SERVICES = {"telnet", "ftp", "www", "www-ssl", "api", "api-ssl"}
MGMT_SERVICES = {"ssh", "winbox"}
PLACEHOLDER_RE = re.compile(r"<[A-Z0-9_]+>")
ATTR_RE = re.compile(r'(\S+?)=("[^"]*"|\S+)')


class Finding:
    def __init__(self, severity, area, message, line=None):
        self.severity = severity
        self.area = area
        self.message = message
        self.line = line

    def as_dict(self):
        return {
            "severity": self.severity,
            "area": self.area,
            "message": self.message,
            "line": self.line,
        }


def strip_trailing_comment(s):
    """Remove a trailing ';#' comment, but not inside a quoted string."""
    in_q = False
    for i, ch in enumerate(s):
        if ch == '"':
            in_q = not in_q
        elif ch == ";" and not in_q and s[i:i + 2] == ";#":
            return s[:i]
    return s


def logical_lines(text):
    """Join RouterOS backslash line-continuations. Yields (lineno, text)."""
    raw = text.splitlines()
    buf, start = "", None
    for n, line in enumerate(raw, 1):
        if start is None:
            start = n
        stripped = line.rstrip()
        if stripped.endswith("\\"):
            buf += stripped[:-1] + " "
        else:
            buf += stripped
            yield start, buf
            buf, start = "", None
    if buf:
        yield start, buf


def parse_attrs(rest):
    out = {}
    for k, v in ATTR_RE.findall(rest):
        if v.startswith('"') and v.endswith('"'):
            v = v[1:-1]
        out[k] = v
    return out


def parse_commands(text):
    """Return list of dicts: {line, path, action, rest, attrs}. Tracks context."""
    cmds = []
    context = None
    for lineno, line in logical_lines(text):
        s = strip_trailing_comment(line).strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("/"):
            tokens = s.split()
            idx = next((i for i, t in enumerate(tokens) if t in ACTIONS), None)
            if idx is None:
                context = s  # pure context path, e.g. "/ip firewall filter"
                continue
            path = " ".join(tokens[:idx])
            context = path
            action = tokens[idx]
            rest = " ".join(tokens[idx + 1:])
        else:
            tokens = s.split()
            if not tokens or tokens[0] not in ACTIONS or context is None:
                continue  # scripting line or stray text
            path = context
            action = tokens[0]
            rest = " ".join(tokens[1:])
        cmds.append({
            "line": lineno,
            "path": path,
            "action": action,
            "rest": rest,
            "attrs": parse_attrs(rest),
        })
    return cmds


def collect_services(cmds):
    """service name -> {'disabled': bool|None, 'address': str|None, 'line': int}"""
    svc = {}
    for c in cmds:
        if not c["path"].endswith("/ip service"):
            continue
        if c["action"] in ("disable", "enable"):
            names = [t for t in re.split(r"[,\s]+", c["rest"]) if t and "=" not in t]
            for name in names:
                svc.setdefault(name, {"disabled": None, "address": None, "line": c["line"]})
                svc[name]["disabled"] = (c["action"] == "disable")
                svc[name]["line"] = c["line"]
        elif c["action"] == "set":
            toks = c["rest"].split()
            if not toks:
                continue
            name = toks[0] if "=" not in toks[0] else None
            if name is None:
                continue
            entry = svc.setdefault(name, {"disabled": None, "address": None, "line": c["line"]})
            a = c["attrs"]
            if "disabled" in a:
                entry["disabled"] = a["disabled"] in ("yes", "true")
            if "address" in a:
                entry["address"] = a["address"]
            entry["line"] = c["line"]
    return svc


BENIGN_ATTRS = {"chain", "action", "comment", "log", "log-prefix", "place-before", "disabled"}


def is_catchall_drop(attrs):
    if attrs.get("action") != "drop":
        return False
    if attrs.get("chain") not in ("input", "forward"):
        return False
    match_keys = [k for k in attrs if k not in BENIGN_ATTRS]
    return len(match_keys) == 0


def check(text):
    findings = []
    cmds = parse_commands(text)

    def add(sev, area, msg, line=None):
        findings.append(Finding(sev, area, msg, line))

    # --- services ---
    svc = collect_services(cmds)
    for name in RISKY_SERVICES:
        e = svc.get(name)
        if e and e["disabled"] is False:
            add("WARN", "services", f"risky service '{name}' is enabled; disable it unless required", e["line"])
    for name in MGMT_SERVICES:
        e = svc.get(name)
        if e and e["disabled"] is not True and not e["address"]:
            add("WARN", "services", f"'{name}' not pinned to a management subnet (set address=)", e["line"])

    # --- firewall filter default-drops ---
    filter_rules = [c for c in cmds if c["path"].endswith("/ip firewall filter") and c["action"] == "add"]
    if not filter_rules:
        add("ERROR", "firewall", "no /ip firewall filter rules — the router input/forward is open")
        has_input_catchall = has_forward_catchall = False
    else:
        has_input_catchall = any(is_catchall_drop(c["attrs"]) and c["attrs"].get("chain") == "input" for c in filter_rules)
        has_forward_catchall = any(is_catchall_drop(c["attrs"]) and c["attrs"].get("chain") == "forward" for c in filter_rules)
        if not has_input_catchall:
            add("ERROR", "firewall", "no default-drop on chain=input (add a trailing 'chain=input action=drop')")
        if not has_forward_catchall:
            add("ERROR", "firewall", "no default-drop on chain=forward (add a trailing 'chain=forward action=drop')")

    # --- DNS open resolver ---
    if "allow-remote-requests=yes" in text.replace(" ", ""):
        explicit_53 = any(
            c["attrs"].get("action") == "drop"
            and ("53" in (c["attrs"].get("dst-port", "") + c["attrs"].get("port", "")))
            for c in cmds if "firewall" in c["path"]
        )
        if not has_input_catchall and not explicit_53:
            add("WARN", "dns", "allow-remote-requests=yes without an input default-drop or a port-53 WAN drop (open resolver risk)")

    # --- IPv6 addressed but unfiltered ---
    ipv6_addr = any(c["path"].endswith("/ipv6 address") and c["action"] == "add" for c in cmds) \
        or any(c["path"].endswith("/ipv6 dhcp-client") and c["action"] == "add" for c in cmds)
    ipv6_fw = any(c["path"].endswith("/ipv6 firewall filter") and c["action"] == "add" for c in cmds)
    if ipv6_addr and not ipv6_fw:
        add("ERROR", "ipv6", "IPv6 is addressed but there are no /ipv6 firewall filter rules")

    # --- NAT presence (informational) ---
    has_nat = any(c["attrs"].get("action") in ("masquerade", "src-nat") for c in cmds if c["path"].endswith("/ip firewall nat"))
    if not has_nat:
        add("INFO", "nat", "no srcnat masquerade/src-nat rule found (fine only if the LAN uses routed public IPs)")

    # --- placeholders ---
    ph = sorted(set(PLACEHOLDER_RE.findall(text)))
    if ph:
        add("WARN", "placeholders", f"{len(ph)} placeholder(s) still to fill: {', '.join(ph)}")

    # --- syntax: quotes per logical line ---
    for lineno, line in logical_lines(text):
        s = line.strip()
        if s.startswith("#"):
            continue
        if s.count('"') % 2 != 0:
            add("WARN", "syntax", "unbalanced double-quote on this line", lineno)

    # --- syntax: braces across file ---
    body = "\n".join(l for _, l in logical_lines(text) if not l.strip().startswith("#"))
    if body.count("{") != body.count("}"):
        add("WARN", "syntax", f"unbalanced braces: {body.count('{')} '{{' vs {body.count('}')} '}}'")

    return findings


def main(argv=None):
    ap = argparse.ArgumentParser(description="Heuristic offline linter for RouterOS v7 .rsc scripts.")
    ap.add_argument("path", help="path to the .rsc file")
    ap.add_argument("--json", action="store_true", help="emit findings as JSON")
    args = ap.parse_args(argv)

    try:
        with open(args.path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError as e:
        print(f"cannot read {args.path}: {e}", file=sys.stderr)
        return 2

    findings = check(text)
    errors = sum(1 for f in findings if f.severity == "ERROR")
    warns = sum(1 for f in findings if f.severity == "WARN")
    infos = sum(1 for f in findings if f.severity == "INFO")

    if args.json:
        print(json.dumps({
            "path": args.path,
            "summary": {"errors": errors, "warnings": warns, "info": infos},
            "findings": [f.as_dict() for f in findings],
        }, indent=2))
    else:
        print(f"MikroTik config lint: {args.path}")
        print(f"  {errors} error(s), {warns} warning(s), {infos} info")
        print()
        order = {"ERROR": 0, "WARN": 1, "INFO": 2}
        for f in sorted(findings, key=lambda x: order[x.severity]):
            loc = f" (line {f.line})" if f.line else ""
            print(f"  {f.severity:<5} [{f.area}] {f.message}{loc}")
        if not findings:
            print("  no issues found by the heuristic checks")
        print()
        print("Heuristic linter — a clean report is not proof of correctness.")
        print("Apply on-device under /system safe-mode to actually verify.")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
