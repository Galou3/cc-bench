"""ccbench doctor: static, evidence-cited audit of a Claude Code / Codex setup."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

CLAUDE_MD_SOFT_MAX = 200   # Anthropic guidance: keep CLAUDE.md under ~200 lines
CLAUDE_MD_HARD_MAX = 500   # well into context-rot territory
MEMORY_MAX_LINES = 200     # only first 200 lines / 25KB of MEMORY.md are loaded

# Embedded so --fix works from an installed package without bundling data files.
STARTER_CLAUDE_MD = """\
# <Project name>

## What this project is
<One or two sentences: what it does, the stack, the entry point.>

## How to run & test
- Install: `<command>`
- Run: `<command>`
- Test: `<command>`            # the single command that proves a change works

## Conventions that matter
- <formatting/lint command to run before committing>
- Make the smallest correct change; don't refactor unrelated code.

## Gotchas / non-obvious context
- <things NOT derivable from the code: a flaky service, an env var, a quirk>

## Out of scope / do not touch
- <generated files, vendored code, anything that must not be edited>

<!-- Keep this file under ~200 lines: long memory files reduce instruction
adherence (Anthropic guidance; lost-in-the-middle / context-rot). -->
"""


@dataclass(frozen=True, slots=True)
class Finding:
    rule: str
    severity: str  # "fail" | "warn" | "info" | "pass"
    message: str
    fix: str = ""
    citation: str = ""

    def to_dict(self) -> dict:
        return {"rule": self.rule, "severity": self.severity, "message": self.message,
                "fix": self.fix, "citation": self.citation}


def _nonblank_lines(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.strip())


def audit(root: str | Path) -> list[Finding]:
    """Run all checks against the setup rooted at ``root``. Pure read-only."""
    root = Path(root)
    out: list[Finding] = []
    claude_md = root / "CLAUDE.md"

    # --- CLAUDE.md ---------------------------------------------------------
    if not claude_md.is_file():
        out.append(Finding(
            "claude_md.present", "info",
            "No CLAUDE.md at the project root.",
            fix="Run `ccbench doctor --fix` to drop a concise starter, then adapt it.",
            citation="EVIDENCE.md > Claude Code usage (best practices)",
        ))
    else:
        text = claude_md.read_text(encoding="utf-8", errors="replace")
        n = len(text.splitlines())
        if _nonblank_lines(text) == 0:
            out.append(Finding("claude_md.empty", "warn", "CLAUDE.md is empty.",
                               fix="Add what to run/test and the conventions you actually follow.",
                               citation="EVIDENCE.md > Claude Code usage"))
        elif n > CLAUDE_MD_HARD_MAX:
            out.append(Finding(
                "claude_md.length", "fail",
                f"CLAUDE.md is {n} lines (> {CLAUDE_MD_HARD_MAX}). Long memory files "
                "burn context and measurably degrade instruction-following.",
                fix="Cut to the essentials (< 200 lines); move details to linked files, "
                    "import only what's needed with @path (max 4 hops).",
                citation="EVIDENCE.md > Claude Code usage [8]; Long-context behavior [10][11][13]",
            ))
        elif n > CLAUDE_MD_SOFT_MAX:
            out.append(Finding(
                "claude_md.length", "warn",
                f"CLAUDE.md is {n} lines (> {CLAUDE_MD_SOFT_MAX}). Anthropic recommends "
                "keeping it under ~200 lines.",
                fix="Trim or split; keep only high-signal, frequently-relevant instructions.",
                citation="EVIDENCE.md > Claude Code usage [8]",
            ))
        else:
            out.append(Finding("claude_md.length", "pass",
                               f"CLAUDE.md is {n} lines (concise).", citation="EVIDENCE.md [8]"))

        imports = [ln for ln in text.splitlines() if ln.strip().startswith("@")]
        if imports:
            out.append(Finding(
                "claude_md.imports", "info",
                f"CLAUDE.md uses {len(imports)} @import line(s).",
                fix="Fine - just remember imports recurse at most 4 hops.",
                citation="EVIDENCE.md > Claude Code usage [8]",
            ))

        markers = ("<Project name>", "<command>", "<One or two sentences",
                   "<formatting/lint", "<things NOT derivable", "<generated files")
        if any(m in text for m in markers):
            out.append(Finding(
                "claude_md.placeholders", "warn",
                "CLAUDE.md still contains starter placeholders (<...>).",
                fix="Replace them with your project's real run/test commands and conventions.",
                citation="EVIDENCE.md > Claude Code usage",
            ))

        low = text.lower()
        test_hints = ("pytest", "unittest", "npm test", "npm run", "yarn test", "pnpm",
                      "go test", "cargo test", "make test", "mvn test", "gradle", "jest",
                      "vitest", "tox", "rspec", "phpunit", "dotnet test", "ctest")
        if _nonblank_lines(text) > 0 and not any(h in low for h in test_hints):
            out.append(Finding(
                "claude_md.test_command", "info",
                "CLAUDE.md doesn't seem to state how to run the project's tests.",
                fix="Add the exact command (e.g. `pytest -q`, `npm test`). Telling the agent "
                    "how to verify its own work is one of the highest-leverage lines in a CLAUDE.md.",
                citation="EVIDENCE.md > Claude Code usage (best practices)",
            ))

    # --- AGENTS.md (the instruction file OpenAI Codex reads) ---------------
    agents_md = root / "AGENTS.md"
    if agents_md.is_file():
        n = len(agents_md.read_text(encoding="utf-8", errors="replace").splitlines())
        if n > CLAUDE_MD_HARD_MAX:
            out.append(Finding(
                "agents_md.length", "fail",
                f"AGENTS.md is {n} lines (> {CLAUDE_MD_HARD_MAX}); same long-context cost "
                "as an over-long CLAUDE.md.",
                fix="Trim to the essentials (< 200 lines).",
                citation="EVIDENCE.md > Long-context behavior [10][11][13]"))
        elif n > CLAUDE_MD_SOFT_MAX:
            out.append(Finding(
                "agents_md.length", "warn",
                f"AGENTS.md is {n} lines (> {CLAUDE_MD_SOFT_MAX}). Keep it concise.",
                citation="EVIDENCE.md > Long-context behavior"))
        else:
            out.append(Finding("agents_md.length", "pass", f"AGENTS.md is {n} lines (concise)."))
    else:
        out.append(Finding(
            "agents_md.present", "info",
            "No AGENTS.md (the instruction file OpenAI Codex reads).",
            fix="If you use Codex (`codex exec`), add a concise AGENTS.md alongside CLAUDE.md.",
            citation="Codex AGENTS.md convention"))

    # --- settings.json -----------------------------------------------------
    settings_path = root / ".claude" / "settings.json"
    if settings_path.is_file():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            out.append(Finding("settings.valid", "fail",
                               f".claude/settings.json is not valid JSON: {exc}",
                               fix="Fix the JSON syntax; a broken settings file is ignored."))
            settings = None
        if isinstance(settings, dict):
            allow = (settings.get("permissions", {}) or {}).get("allow")
            if allow:
                out.append(Finding("settings.permissions", "pass",
                                   f"Permissions allowlist present ({len(allow)} rule(s)).",
                                   citation="EVIDENCE.md > Claude Code usage [9]"))
            else:
                out.append(Finding("settings.permissions", "info",
                                   "No permissions allowlist.",
                                   fix="Allowlist safe commands (e.g. Edit, Bash(git commit *)) "
                                       "to cut approval prompts in unattended runs.",
                                   citation="EVIDENCE.md > Claude Code usage [9]"))
            if settings.get("hooks"):
                out.append(Finding("settings.hooks", "info", "Hooks are configured."))
    else:
        out.append(Finding("settings.present", "info",
                           "No .claude/settings.json (fine for many projects)."))

    # --- subagents ---------------------------------------------------------
    agents_dir = root / ".claude" / "agents"
    agent_files = sorted(agents_dir.glob("*.md")) if agents_dir.is_dir() else []
    if agent_files:
        out.append(Finding("agents.present", "pass",
                           f"{len(agent_files)} custom subagent(s) defined "
                           "(they isolate context in their own window).",
                           citation="EVIDENCE.md > Claude Code usage [9]"))
    else:
        out.append(Finding("agents.present", "info",
                           "No custom subagents (optional).",
                           fix="For big, separable jobs, a subagent keeps the main context clean.",
                           citation="EVIDENCE.md > Claude Code usage [9]"))

    # --- MEMORY.md ---------------------------------------------------------
    memory_path = root / ".claude" / "MEMORY.md"
    if memory_path.is_file():
        n = len(memory_path.read_text(encoding="utf-8", errors="replace").splitlines())
        if n > MEMORY_MAX_LINES:
            out.append(Finding("memory.length", "warn",
                               f"MEMORY.md is {n} lines; only the first {MEMORY_MAX_LINES} "
                               "lines (or 25KB) are loaded each session.",
                               fix="Keep the index short; the rest will be silently ignored.",
                               citation="EVIDENCE.md > Claude Code usage [8]"))

    return out


def apply_fixes(root: str | Path, findings: list[Finding]) -> list[str]:
    """Apply only safe, non-destructive auto-fixes. Returns actions taken.

    Currently: create a starter CLAUDE.md if one is missing. Never overwrites.
    """
    root = Path(root)
    actions: list[str] = []
    if any(f.rule == "claude_md.present" for f in findings):
        target = root / "CLAUDE.md"
        if not target.exists():
            target.write_text(STARTER_CLAUDE_MD, encoding="utf-8")
            actions.append("created CLAUDE.md (concise starter - adapt it)")
    return actions


def summary(findings: list[Finding]) -> dict[str, int]:
    counts = {"fail": 0, "warn": 0, "info": 0, "pass": 0}
    for f in findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1
    return counts


def overall(findings: list[Finding]) -> str:
    c = summary(findings)
    if c["fail"]:
        return "needs attention (failures)"
    if c["warn"]:
        return "ok with warnings"
    return "healthy"


def health_score(findings: list[Finding]) -> int:
    """0-100 audit-health score. Penalises fails and warnings, not optional infos."""
    score = 100 - sum({"fail": 30, "warn": 10}.get(f.severity, 0) for f in findings)
    return max(0, min(100, score))


_MARK = {"fail": "[FAIL]", "warn": "[warn]", "info": "[info]", "pass": "[ ok ]"}


def render(findings: list[Finding], root: str | Path) -> str:
    c = summary(findings)
    if c["fail"]:
        head = (f"-> {c['fail']} blocking issue(s)"
                + (f" + {c['warn']} warning(s)" if c["warn"] else "")
                + " likely costing you quality. Fix with `ccbench doctor --fix` or by hand below.")
    elif c["warn"]:
        head = f"-> {c['warn']} thing(s) likely costing you quality - see below (some auto-fixable: --fix)."
    elif c["info"]:
        head = "-> Setup is healthy; a few optional suggestions below."
    else:
        head = "-> Setup looks healthy."
    score = health_score(findings)
    lines = [f"cc-bench doctor - setup audit of {Path(root)}",
             f"Setup health: {score}/100 (audit health, not a success guarantee - run to confirm).",
             head, ""]
    order = {"fail": 0, "warn": 1, "info": 2, "pass": 3}
    for f in sorted(findings, key=lambda x: order.get(x.severity, 9)):
        lines.append(f"{_MARK.get(f.severity, '[?]')} {f.rule}: {f.message}")
        if f.fix and f.severity in ("fail", "warn", "info"):
            lines.append(f"        fix: {f.fix}")
        if f.citation:
            lines.append(f"        why: {f.citation}")
    c = summary(findings)
    lines += ["", f"Summary: {c['fail']} fail, {c['warn']} warn, {c['info']} info, "
                  f"{c['pass']} pass -> {overall(findings)}"]
    return "\n".join(lines)


__all__ = ["Finding", "audit", "apply_fixes", "render", "summary", "overall",
           "health_score", "STARTER_CLAUDE_MD"]
