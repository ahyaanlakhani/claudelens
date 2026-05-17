"""Typer CLI entry point."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from claudelens import __version__
from claudelens.checks import (
    Severity,
    check_descriptions,
    check_naming,
    check_triggers,
)
from claudelens.config import load_config
from claudelens.report import render_json, render_text
from claudelens.scanner import scan

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="ClaudeLens — skill-collision linter for Claude Code.",
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"claudelens {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(  # noqa: UP007 (Typer needs Optional)
        None,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Print version and exit.",
    ),
) -> None:
    """ClaudeLens — skill-collision linter for Claude Code."""


@app.command()
def lint(
    path: Path = typer.Argument(
        ...,
        help="Path to the .claude/skills/ directory to lint.",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
    ),
    strict: bool = typer.Option(
        False, "--strict", help="Exit non-zero on warnings as well as errors."
    ),
    output_json: bool = typer.Option(
        False, "--json", help="Emit findings as JSON instead of a table."
    ),
    show_all: bool = typer.Option(
        False, "--show-all", help="Reserved for future use; currently has no effect.",
    ),
) -> None:
    """Scan PATH for skill collisions and print findings."""
    console = Console()
    config = load_config(path)

    result = scan(path)
    findings = []
    findings.extend(check_naming(result.skills, config))
    findings.extend(check_descriptions(result.skills, config))
    findings.extend(check_triggers(result.skills, config))

    if output_json:
        typer.echo(render_json(result.skills, findings, result.errors))
    else:
        render_text(console, result.skills, findings, result.errors)

    exit_code = _compute_exit_code(findings, result.errors, strict=strict)
    raise typer.Exit(code=exit_code)


@app.command()
def list_skills(
    path: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="Path to the skills directory to enumerate.",
    ),
) -> None:
    """Print a flat list of skills discovered under PATH."""
    console = Console()
    result = scan(path)
    for s in result.skills:
        console.print(f"[bold]{s.name}[/] [dim]({s.path})[/]")
        console.print(f"  {s.description}")
    if result.errors:
        console.print()
        for path_, msg in result.errors:
            console.print(f"[red]parse error:[/] {path_}: {msg}")


def _compute_exit_code(findings, parse_errors, *, strict: bool) -> int:
    if parse_errors:
        return 2
    has_error = any(f.severity == Severity.ERROR for f in findings)
    has_warning = any(f.severity == Severity.WARNING for f in findings)
    if has_error:
        return 1
    if strict and has_warning:
        return 1
    return 0
