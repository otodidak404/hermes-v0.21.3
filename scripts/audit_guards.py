#!/usr/bin/env python3
"""Guard checklist audit — verifies the 23 guard keys baked into
hermes_cli/config_defaults.py match the setup-hermes.sh checklist.

Run from anywhere inside a repo checkout:
    python3 scripts/audit_guards.py
Exit 0 = all baked defaults match, exit 1 = mismatch/missing.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from hermes_cli import config_defaults  # noqa: E402

try:
    from agent import agent_init  # noqa: E402
    CLAMP_SRC = str(agent_init.__file__)
except Exception:
    CLAMP_SRC = str(REPO / "agent" / "agent_init.py")

# (section_tuple_or_key, expected_value)  — mirrors setup-hermes.sh _GUARD_SETS
CHECKS = [
    (("approvals", "mode"), "off"),
    (("approvals", "destructive_slash_confirm"), False),
    (("security", "tirith_enabled"), False),
    (("security", "tirith_fail_open"), True),
    (("security", "redact_secrets"), False),
    (("security", "allow_private_urls"), True),
    (("security", "protected_instruction_files"), False),
    (("browser", "allow_private_urls"), True),
    (("tool_loop_guardrails", "warnings_enabled"), False),
    (("tool_loop_guardrails", "hard_stop_enabled"), False),
    (("tool_loop_guardrails", "non_interactive_hard_stop_enabled"), False),
    (("tool_loop_guardrails", "loop_caps", "max_web_searches"), 0),
    (("tool_loop_guardrails", "loop_caps", "max_subagents"), 0),
    (("gateway", "loop_watchdog"), False),
    (("gateway", "startup_watchdog"), False),
    (("gateway", "bot_loop_guard", "enabled"), False),
    (("loops", "max_ticks"), 0),
    (("agent", "max_turns"), 9999),
    (("goals", "max_turns"), 9999),
    (("delegation", "max_iterations"), 9999),
    (("code_execution", "max_tool_calls"), 9999),
    (("compression", "max_attempts"), 99),
    ("hooks_auto_accept", True),
]

DEFAULTS = config_defaults.DEFAULT_CONFIG
raw = Path(CLAMP_SRC).read_text(encoding="utf-8")
passed = failed = 0

for path, want in CHECKS:
    node = DEFAULTS
    if isinstance(path, tuple):
        missing = False
        for part in path:
            if not isinstance(node, dict) or part not in node:
                missing = True
                break
            node = node[part]
        label = ".".join(path)
        if missing:
            print(f"MISSING {label} (want {want})")
            failed += 1
            continue
        ok = node == want
        print(f"{'PASS' if ok else 'FAIL'} {label} = {node!r}"
              + ("" if ok else f" want {want!r}"))
    else:
        label = path
        if path not in config_defaults.DEFAULT_CONFIG:
            print(f"MISSING {label} (want {want})")
            failed += 1
            continue
        node = config_defaults.DEFAULT_CONFIG[path]
        ok = node == want
        print(f"{'PASS' if ok else 'FAIL'} {label} = {node!r}"
              + ("" if ok else f" want {want!r}"))
    passed += ok
    failed += not ok

# runtime clamp must not silently re-cap compression.max_attempts at 10
if "min(max_attempts, 99)" in raw:
    print("PASS agent_init compression clamp = min(max_attempts, 99)")
    passed += 1
else:
    print("FAIL agent_init compression clamp is not min(max_attempts, 99)")
    failed += 1

total = passed + failed
print(f"\n{passed}/{total} PASS, {failed} FAIL")
sys.exit(0 if failed == 0 else 1)
