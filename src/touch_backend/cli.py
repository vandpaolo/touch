"""Command-line entry point: ``touch_backend design "<prompt>"``.

A thin Typer shell over `agent.loop.Loop` — it loads `.env`, merges
flags into a `Config` (CLI > env > pyproject > defaults), derives a
`RunConfig`, constructs the Anthropic client + prompt bundle, runs the
loop, prints the run directory (F12), and exits with the run's F13 code.
No domain logic lives here.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import typer
from dotenv import load_dotenv

from touch_backend.agent.loop import Loop, RunConfig
from touch_backend.agent.planner import PromptsBundle
from touch_backend.config import Config

_PROMPTS_FILE = Path(__file__).resolve().parents[2] / "prompts" / "planner.system.md"

_EXIT_GENERIC = 1
_EXIT_BAD_ARGS = 2

app = typer.Typer(
    add_completion=False,
    help="Natural-language CAD: turn a prompt into a parametric solid + STEP.",
)


@app.callback()
def _main() -> None:
    """Maquette — natural-language CAD. Use the `design` command."""


@app.command()
def design(
    prompt: str = typer.Argument(
        ..., help="Natural-language description of the part to build."
    ),
    out: Path = typer.Option(
        None, "--out", help="Output root directory (default: output/)."
    ),
    max_iter: int = typer.Option(
        None, "--max-iter", help="Max refinement iterations (v0: 1)."
    ),
    exec_timeout: float = typer.Option(
        None, "--exec-timeout", help="Subprocess execution timeout in seconds."
    ),
    model: str = typer.Option(None, "--model", help="Anthropic model id."),
    quiet: bool = typer.Option(
        False, "-q", "--quiet", help="Print only the run directory path."
    ),
    verbose: bool = typer.Option(
        False, "-v", "--verbose", help="Print per-step detail to stderr."
    ),
) -> None:
    """Generate a parametric solid + STEP from a natural-language prompt."""
    load_dotenv()

    if not prompt.strip():
        typer.echo("error: prompt must not be empty.", err=True)
        raise typer.Exit(_EXIT_BAD_ARGS)

    if not os.environ.get("ANTHROPIC_API_KEY"):
        typer.echo(
            "error: ANTHROPIC_API_KEY is not set (put it in your environment "
            "or a .env file).",
            err=True,
        )
        raise typer.Exit(_EXIT_GENERIC)

    cfg = Config.load(
        cli_overrides=_overrides(out, max_iter, exec_timeout, model, quiet, verbose)
    )

    run_dir = _run(prompt, cfg)

    _report(run_dir, quiet=quiet, verbose=verbose)  # human detail -> stderr
    exit_code = _exit_code_from(run_dir)
    typer.echo(str(run_dir))  # F12: run dir -> stdout, on every exit.
    raise typer.Exit(exit_code)


def _overrides(
    out: Path | None,
    max_iter: int | None,
    exec_timeout: float | None,
    model: str | None,
    quiet: bool,
    verbose: bool,
) -> dict[str, object]:
    """Map CLI flags onto Config field names (omit unset options)."""
    overrides: dict[str, object] = {}
    if out is not None:
        overrides["out_root"] = out
    if max_iter is not None:
        overrides["max_iterations"] = max_iter
    if exec_timeout is not None:
        overrides["exec_timeout_s"] = exec_timeout
    if model is not None:
        overrides["model"] = model
    overrides["verbosity"] = 0 if quiet else (2 if verbose else 1)
    return overrides


def _run(prompt: str, cfg: Config) -> Path:
    """Construct the loop and run it. Unexpected errors -> exit 1."""
    from anthropic import Anthropic

    try:
        prompts = PromptsBundle(
            planner_system=_PROMPTS_FILE.read_text(encoding="utf-8")
        )
        loop = Loop(
            out_root=cfg.out_root,
            cfg=_runconfig_from(cfg),
            client=Anthropic(),
            prompts=prompts,
        )
        return loop.run(prompt)
    except typer.Exit:
        raise
    except Exception as e:  # backstop; the loop handles known failures itself.
        typer.echo(f"error: {e}", err=True)
        raise typer.Exit(_EXIT_GENERIC) from e


def _runconfig_from(cfg: Config) -> RunConfig:
    return RunConfig(
        model=cfg.model,
        max_iterations=cfg.max_iterations,
        exec_timeout_s=cfg.exec_timeout_s,
        sanity_enabled=cfg.sanity_enabled,
    )


def _report(run_dir: Path, *, quiet: bool, verbose: bool) -> None:
    """Human-readable detail to stderr. `-q` prints nothing here (stdout
    still gets the run dir); `-v` adds a per-step / per-LLM-call log."""
    if quiet:
        return
    status = _read_json(run_dir / "status.json")
    typer.echo(
        f"{status.get('status', '?')}  exit={status.get('exit_code', '?')}  "
        f"{float(status.get('duration_s', 0)):.1f}s  "
        f"${float(status.get('cost_usd_estimate', 0)):.4f}",
        err=True,
    )
    if not verbose:
        return
    for event in _read_trace(run_dir):
        line = f"  {event.get('step', '?')}  {float(event.get('duration_s', 0)):.3f}s"
        if event.get("step") == "PLANNING":
            line += (
                f"  in={event.get('tokens_in')} out={event.get('tokens_out')}"
                f" cache_read={event.get('cache_read_tokens')}"
                f" cache_creation={event.get('cache_creation_tokens')}"
            )
        typer.echo(line, err=True)


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_trace(run_dir: Path) -> list[dict]:
    trace = run_dir / "trace.jsonl"
    if not trace.exists():
        return []
    return [
        json.loads(line)
        for line in trace.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _exit_code_from(run_dir: Path) -> int:
    status = _read_json(run_dir / "status.json")
    return int(status.get("exit_code", _EXIT_GENERIC))


if __name__ == "__main__":
    app()
