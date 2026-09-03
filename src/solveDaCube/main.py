"""
main.py
=======
CLI entry point for solveDaCube.

Responsibilities:
- Parse CLI arguments (--version, --demo)
- Display the ASCII art welcome banner
- Orchestrate the full user flow:
    run_input_ui() → solve() → display_solution()
- Handle restart loop
- Handle KeyboardInterrupt gracefully
"""

from __future__ import annotations

import argparse
import sys

from rich.console import Console

from solveDaCube import __version__, __tagline__
from solveDaCube.cube import CubeState, SOLVED_STATE
from solveDaCube.ui import run_input_ui, display_solution
from solveDaCube.solver import solve, InvalidCubeError

console = Console()

_BANNER = r"""
  ____        _           ____        ____      _
 / ___|  ___ | |_   ___  |  _ \  __ |  __|   _| |__   ___
 \___ \ / _ \| \ \ / / _ \| | | |/ _` | |    |_   _| / _ \
  ___) | (_) | |\ V /  __/| |_| | (_| | |___   |_|  |  __/
 |____/ \___/|_| \_/ \___||____/ \__,_|_____|        \___|
"""

# A known scramble applied to SOLVED_STATE to produce the demo cube.
# Sequence: R U R' U' F' U F
_DEMO_MOVES = ["R", "U", "R'", "U'", "F'", "U", "F"]


def _build_demo_state() -> CubeState:
    """Return a scrambled CubeState produced by applying _DEMO_MOVES to the solved state."""
    state = SOLVED_STATE.copy()
    for move in _DEMO_MOVES:
        state.apply_move(move)
    return state


def _print_welcome() -> None:
    """Print the ASCII art banner and tagline."""
    console.print(_BANNER, style="bold cyan")
    console.print(
        f"  [dim italic]{__tagline__}[/dim italic]\n"
    )


def main() -> None:
    """Entry point registered in pyproject.toml."""
    parser = argparse.ArgumentParser(
        prog="solveDaCube",
        description="Interactive ASCII terminal Rubik's Cube solver.",
        add_help=True,
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print version and exit.",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run a demo solve on a pre-scrambled cube (no manual input).",
    )
    args = parser.parse_args()

    if args.version:
        print(f"solveDaCube v{__version__} \u2014 {__tagline__}")
        sys.exit(0)

    try:
        _print_welcome()

        while True:
            # ── Obtain cube state ──────────────────────────────────────────────
            if args.demo:
                console.print(
                    "  [bold yellow][DEMO][/bold yellow] Loading pre-scrambled cube "
                    f"([cyan]{' '.join(_DEMO_MOVES)}[/cyan] applied to solved state)...\n"
                )
                state = _build_demo_state()
            else:
                state = run_input_ui()

            # ── Solve ──────────────────────────────────────────────────────────
            try:
                moves, move_count = solve(state)
            except InvalidCubeError as exc:
                console.print(f"\n  [bold red]Error:[/bold red] {exc}\n")
                if args.demo:
                    sys.exit(1)
                # In interactive mode let the user try again
                continue

            # ── Display ────────────────────────────────────────────────────────
            restart = display_solution(moves, state)
            if not restart:
                break

    except KeyboardInterrupt:
        console.print("\n\n  [dim]Goodbye! Thanks for solving with solveDaCube.[/dim]\n")
        sys.exit(0)
