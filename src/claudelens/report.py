"""Rich-based reporters for lint findings."""
from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console
from rich.table import Table

from claudelens.checks.base import Finding, Severity
from claudelens.skill import Skill


_SEVERITY_STYLE = {
    Severity.ERROR: "bold red",
    Severity.WARNING: "yellow",
    Severity.INFO: "cyan",
}


def render_text(
    console: Console,
    skills: list[Skill],
    findings: list[Finding],
    parse_errors: list[tuple[Path, str]],
) -> None:
    console.print(
        f"[dim]Scanned {len(skills)} skill(s); "
        f"{len(parse_errors)} parse error(s); "
        f"{len(findings)} finding(s).[/]"
    )

    if parse_errors:
        console.print()
        console.rule("[bold]Parse errors")
        for path, msg in parse_errors:
            console.print(f"[red]✗[/] {path}: {msg}")

    if not findings:
        console.print()
        console.print("[bold green]No collisions detected.[/]")
        return

    console.print()
    table = Table(title="Skill collisions", show_lines=False)
    table.add_column("Severity")
    table.add_column("Check")
    table.add_column("Skills")
    table.add_column("Message", overflow="fold")
    table.add_column("Score", justify="right")

    for f in sorted(findings, key=Finding.sort_key):
        table.add_row(
            f"[{_SEVERITY_STYLE[f.severity]}]{f.severity.value}[/]",
            f.check,
            ", ".join(f.skills),
            f.message,
            f"{f.score:.2f}" if f.score is not None else "-",
        )
    console.print(table)


def render_json(
    skills: list[Skill],
    findings: list[Finding],
    parse_errors: list[tuple[Path, str]],
) -> str:
    return json.dumps(
        {
            "scanned": len(skills),
            "skills": [s.name for s in skills],
            "parse_errors": [{"path": str(p), "message": m} for p, m in parse_errors],
            "findings": [
                {
                    "check": f.check,
                    "severity": f.severity.value,
                    "skills": list(f.skills),
                    "message": f.message,
                    "score": f.score,
                }
                for f in sorted(findings, key=Finding.sort_key)
            ],
        },
        indent=2,
    )
