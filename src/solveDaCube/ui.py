"""
ui.py
=====
Terminal UI — interactive cube input and solution animator.

Responsibilities:

Input phase:
- run_input_ui() → CubeState
    Renders the unfolded ASCII cube layout, handles arrow-key navigation,
    color-key input (W/Y/R/O/G/B), locks center cells, shows live color
    count status bar, and returns a completed CubeState once all 54
    stickers are filled and valid.

Output phase:
- display_solution(moves: list[str], initial_state: CubeState)
    Prints the solution header (move count + full move sequence), then
    animates each move step-by-step:
      - Auto-play by default (0.5 s delay)
      - S key → step mode (Space/Enter to advance)
      - A key → resume auto-play
      - R key at end → restart

Color key mapping (input phase only):
    W = White  | Y = Yellow | R = Red
    O = Orange | G = Green  | B = Blue

Unfolded layout (each face is 3×3 stickers):
         [ U ]
    [L]  [F]  [R]  [B]
         [ D ]
"""

from __future__ import annotations

import os
import sys
import time
import threading
from typing import Optional

import readchar
from rich.console import Console
from rich.text import Text

from solveDaCube.cube import (
    FACES, COLORS,
    U, R, F, D, L, B,
    W, Y, COLOR_R, O, G, COLOR_B,
    CubeState,
    DEFAULT_FACE_COLORS,
    SOLVED_STATE,
)

# ---------------------------------------------------------------------------
# Rich style table: color code → rich style string
# ---------------------------------------------------------------------------
COLOR_STYLE: dict[str, str] = {
    W:       "bold black on white",
    Y:       "bold black on yellow",
    COLOR_R: "bold white on red",
    O:       "bold black on orange1",
    G:       "bold white on green",
    COLOR_B: "bold white on blue",
}

# Label shown inside each sticker cell (3 chars wide including padding)
COLOR_LABEL: dict[str, str] = {
    W:       " W ",
    Y:       " Y ",
    COLOR_R: " R ",
    O:       " O ",
    G:       " G ",
    COLOR_B: " B ",
}

# Mapping from key char (upper) to color code
KEY_TO_COLOR: dict[str, str] = {
    "W": W,
    "Y": Y,
    "R": COLOR_R,
    "O": O,
    "G": G,
    "B": COLOR_B,
}

# Center sticker index per face
CENTER_IDX = 4

# ---------------------------------------------------------------------------
# Unfolded cube layout
# ---------------------------------------------------------------------------
# Faces in the visual grid.  Each face occupies a (grid_row, grid_col) cell
# where each grid cell is 3 sticker-rows × 3 sticker-cols.
#
#  grid_row 0: U at grid_col 1
#  grid_row 1: L at grid_col 0, F at grid_col 1, R at grid_col 2, B at grid_col 3
#  grid_row 2: D at grid_col 1

FACE_GRID_POS: dict[str, tuple[int, int]] = {
    U: (0, 1),
    L: (1, 0),
    F: (1, 1),
    R: (1, 2),
    B: (1, 3),
    D: (2, 1),
}

# Pre-compute: for every (face, sticker_index) the "visual grid" position
# as (grid_row * 3 + sticker_row, grid_col * 3 + sticker_col)
def _sticker_visual_pos(face: str, idx: int) -> tuple[int, int]:
    gr, gc = FACE_GRID_POS[face]
    sr, sc = divmod(idx, 3)
    return (gr * 3 + sr, gc * 3 + sc)


# Build a list of all navigable (face, idx) positions in reading order
# (top-to-bottom, left-to-right by visual position) excluding centers.
def _build_nav_order() -> list[tuple[str, int]]:
    cells: list[tuple[tuple[int, int], str, int]] = []
    for face in FACES:
        for idx in range(9):
            if idx == CENTER_IDX:
                continue
            vpos = _sticker_visual_pos(face, idx)
            cells.append((vpos, face, idx))
    cells.sort(key=lambda x: x[0])
    return [(face, idx) for _, face, idx in cells]


NAV_ORDER: list[tuple[str, int]] = _build_nav_order()

# Build reverse lookup: (face, idx) -> position in NAV_ORDER
NAV_INDEX: dict[tuple[str, int], int] = {
    cell: i for i, cell in enumerate(NAV_ORDER)
}

# Build a 2D map: visual_pos -> (face, idx) for all navigable cells
_VPOS_TO_CELL: dict[tuple[int, int], tuple[str, int]] = {
    _sticker_visual_pos(face, idx): (face, idx)
    for face, idx in NAV_ORDER
}


def _nearest_in_direction(
    current: tuple[str, int],
    direction: str,  # "up" | "down" | "left" | "right"
) -> tuple[str, int]:
    """Return the nearest navigable cell in the given direction from current."""
    cr, cc = _sticker_visual_pos(*current)

    if direction == "up":
        candidates = [(face, idx) for (face, idx) in NAV_ORDER
                      if _sticker_visual_pos(face, idx)[0] < cr
                      and _sticker_visual_pos(face, idx)[1] == cc]
        if candidates:
            return max(candidates, key=lambda c: _sticker_visual_pos(*c)[0])
        # wrap: find same column, highest visual row
        candidates = [(face, idx) for (face, idx) in NAV_ORDER
                      if _sticker_visual_pos(face, idx)[1] == cc]
        return max(candidates, key=lambda c: _sticker_visual_pos(*c)[0]) if candidates else current

    elif direction == "down":
        candidates = [(face, idx) for (face, idx) in NAV_ORDER
                      if _sticker_visual_pos(face, idx)[0] > cr
                      and _sticker_visual_pos(face, idx)[1] == cc]
        if candidates:
            return min(candidates, key=lambda c: _sticker_visual_pos(*c)[0])
        candidates = [(face, idx) for (face, idx) in NAV_ORDER
                      if _sticker_visual_pos(face, idx)[1] == cc]
        return min(candidates, key=lambda c: _sticker_visual_pos(*c)[0]) if candidates else current

    elif direction == "left":
        candidates = [(face, idx) for (face, idx) in NAV_ORDER
                      if _sticker_visual_pos(face, idx)[1] < cc
                      and _sticker_visual_pos(face, idx)[0] == cr]
        if candidates:
            return max(candidates, key=lambda c: _sticker_visual_pos(*c)[1])
        candidates = [(face, idx) for (face, idx) in NAV_ORDER
                      if _sticker_visual_pos(face, idx)[0] == cr]
        return max(candidates, key=lambda c: _sticker_visual_pos(*c)[1]) if candidates else current

    elif direction == "right":
        candidates = [(face, idx) for (face, idx) in NAV_ORDER
                      if _sticker_visual_pos(face, idx)[1] > cc
                      and _sticker_visual_pos(face, idx)[0] == cr]
        if candidates:
            return min(candidates, key=lambda c: _sticker_visual_pos(*c)[1])
        candidates = [(face, idx) for (face, idx) in NAV_ORDER
                      if _sticker_visual_pos(face, idx)[0] == cr]
        return min(candidates, key=lambda c: _sticker_visual_pos(*c)[1]) if candidates else current

    return current


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------

console = Console()


def _render_sticker(color: Optional[str], is_cursor: bool, is_center: bool) -> Text:
    """Return a 3-char Rich Text for a single sticker cell."""
    if is_cursor:
        if color:
            style = COLOR_STYLE[color]
            label = f"[{color}]" if len(color) == 1 else f"[{color[0]}]"
            # Cursor: show label in brackets, same bg
            return Text(f"[{color}]", style=style)
        else:
            return Text("[?]", style="bold black on bright_cyan")
    elif color:
        return Text(COLOR_LABEL[color], style=COLOR_STYLE[color])
    else:
        dim_style = "dim white" if not is_center else "bold white"
        return Text(" ? ", style="dim white")


def _count_colors(faces_data: dict[str, list[Optional[str]]]) -> dict[str, int]:
    counts: dict[str, int] = {c: 0 for c in COLORS}
    for face in FACES:
        for sticker in faces_data[face]:
            if sticker is not None and sticker in counts:
                counts[sticker] += 1
    return counts


def _all_filled(faces_data: dict[str, list[Optional[str]]]) -> bool:
    for face in FACES:
        if any(s is None for s in faces_data[face]):
            return False
    return True


def _render_frame(
    faces_data: dict[str, list[Optional[str]]],
    cursor: tuple[str, int],
    warning: str = "",
) -> str:
    """
    Build the full unfolded cube as a list of Rich-markup lines, returned
    as a single string for printing via Console.print.

    Layout:
      row0: 3 lines for U face (indented 9 chars = 1 face width)
      row1: 3 lines for L/F/R/B faces side by side
      row2: 3 lines for D face (indented 9 chars)
    """
    lines: list[Text] = []

    # Face label row (just a small header)
    indent = Text("         ")  # 9 spaces = 3 stickers × 3 chars each
    header = Text("     ── solveDaCube ──     ", style="bold cyan")
    lines.append(header)

    # Helper: render one horizontal row of a face (sticker_row 0,1,2)
    def face_row_text(face: str, sticker_row: int) -> Text:
        t = Text()
        for sc in range(3):
            idx = sticker_row * 3 + sc
            color = faces_data[face][idx]
            is_cur = (cursor == (face, idx))
            is_cen = (idx == CENTER_IDX)
            t.append_text(_render_sticker(color, is_cur, is_cen))
        return t

    # Top face (U), indented by one face width (9 chars)
    for sr in range(3):
        t = Text("         ")  # 9-char indent
        t.append_text(face_row_text(U, sr))
        lines.append(t)

    # Separator
    lines.append(Text(""))

    # Belt: L F R B
    for sr in range(3):
        t = Text()
        for face in (L, F, R, B):
            t.append_text(face_row_text(face, sr))
        lines.append(t)

    # Separator
    lines.append(Text(""))

    # Bottom face (D), indented
    for sr in range(3):
        t = Text("         ")
        t.append_text(face_row_text(D, sr))
        lines.append(t)

    # Color count status bar
    lines.append(Text(""))
    counts = _count_colors(faces_data)
    status = Text()
    for color in COLORS:
        cnt = counts[color]
        over = cnt > 9
        style = COLOR_STYLE[color]
        label = COLOR_LABEL[color].strip()
        badge = Text(f" {label}:{cnt}/9 ", style=("bold red on white" if over else style))
        status.append_text(badge)
        status.append(" ")
    lines.append(status)

    if warning:
        lines.append(Text(f"  ⚠  {warning}", style="bold red"))

    # Help bar
    lines.append(Text(""))
    lines.append(Text(
        "  [W/Y/R/O/G/B] fill  [←↑↓→] move  [⌫] clear  [Q] quit",
        style="dim"
    ))

    # Check if all filled and valid for Solve prompt
    if _all_filled(faces_data):
        counts_ok = all(v == 9 for v in counts.values())
        if counts_ok:
            lines.append(Text(""))
            lines.append(Text("  ✓ All stickers filled!  Press [ENTER] to Solve!", style="bold green"))

    result_lines = []
    for t in lines:
        result_lines.append(t)
    return result_lines


def _clear() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def _print_frame(
    faces_data: dict[str, list[Optional[str]]],
    cursor: tuple[str, int],
    warning: str = "",
) -> None:
    _clear()
    frame_lines = _render_frame(faces_data, cursor, warning)
    for line in frame_lines:
        console.print(line)


# ---------------------------------------------------------------------------
# Public API: run_input_ui
# ---------------------------------------------------------------------------

def run_input_ui() -> CubeState:
    """
    Interactive unfolded cube input UI.

    Displays the unfolded ASCII cube, lets the user navigate with arrow keys,
    fill stickers with color keys (W/Y/R/O/G/B), backspace to clear, and
    press Enter to solve once all 54 stickers are filled and valid.

    Returns a completed CubeState.
    """
    # Initialize faces_data: centers pre-filled, rest None
    faces_data: dict[str, list[Optional[str]]] = {}
    for face in FACES:
        row: list[Optional[str]] = [None] * 9
        row[CENTER_IDX] = DEFAULT_FACE_COLORS[face]
        faces_data[face] = row

    cursor: tuple[str, int] = NAV_ORDER[0]  # start at first navigable cell
    warning = ""

    while True:
        _print_frame(faces_data, cursor, warning)
        warning = ""

        key = readchar.readkey()

        # Quit
        if key.lower() == "q":
            console.print("\n[dim]Bye![/dim]")
            sys.exit(0)

        # Arrow key navigation
        if key == readchar.key.UP:
            cursor = _nearest_in_direction(cursor, "up")
        elif key == readchar.key.DOWN:
            cursor = _nearest_in_direction(cursor, "down")
        elif key == readchar.key.LEFT:
            cursor = _nearest_in_direction(cursor, "left")
        elif key == readchar.key.RIGHT:
            cursor = _nearest_in_direction(cursor, "right")

        # Color key input
        elif key.upper() in KEY_TO_COLOR:
            color = KEY_TO_COLOR[key.upper()]
            counts = _count_colors(faces_data)
            if counts[color] >= 9:
                warning = f"Color {color} already has 9 stickers — cannot add more."
            else:
                face, idx = cursor
                faces_data[face][idx] = color
                # Advance cursor to next unfilled navigable cell (or just next)
                nav_pos = NAV_INDEX[cursor]
                # Find next unfilled
                next_pos = None
                for delta in range(1, len(NAV_ORDER)):
                    candidate = NAV_ORDER[(nav_pos + delta) % len(NAV_ORDER)]
                    cf, ci = candidate
                    if faces_data[cf][ci] is None:
                        next_pos = candidate
                        break
                if next_pos is not None:
                    cursor = next_pos

        # Backspace / Delete to clear
        elif key in (readchar.key.BACKSPACE, readchar.key.DELETE):
            face, idx = cursor
            if faces_data[face][idx] is not None:
                faces_data[face][idx] = None
            else:
                # Move to previous cell and clear it
                nav_pos = NAV_INDEX[cursor]
                if nav_pos > 0:
                    cursor = NAV_ORDER[nav_pos - 1]
                    face, idx = cursor
                    faces_data[face][idx] = None

        # Enter: attempt to solve
        elif key in (readchar.key.ENTER, "\r", "\n"):
            if _all_filled(faces_data):
                counts = _count_colors(faces_data)
                counts_ok = all(v == 9 for v in counts.values())
                if counts_ok:
                    # Build and return CubeState
                    face_dict = {face: [s for s in faces_data[face]] for face in FACES}
                    return CubeState(faces=face_dict)  # type: ignore[arg-type]
                else:
                    over = [f"{c}:{counts[c]}" for c in COLORS if counts[c] != 9]
                    warning = "Color counts invalid: " + "  ".join(over)
            else:
                filled = sum(
                    1 for face in FACES for s in faces_data[face] if s is not None
                )
                warning = f"Not all stickers filled yet ({filled}/54)."


# ---------------------------------------------------------------------------
# Public API: display_solution
# ---------------------------------------------------------------------------

def display_solution(moves: list[str], initial_state: CubeState) -> bool:
    """
    Animate the solution step-by-step.

    Args:
        moves: list of move strings (e.g. ["R", "U", "R'", "U'"])
        initial_state: the CubeState before any moves are applied

    Returns:
        True if the user wants to restart, False otherwise.
    """
    state = initial_state.copy()
    move_count = len(moves)
    # Mutable container so the closure and outer function share one reference
    mode = {"auto_play": True}
    step_delay = 0.5

    def _render_solution(current_move_idx: int) -> None:
        """Clear screen and redraw: header, highlighted move sequence, cube, mode hint."""
        _clear()
        # ── Solution header ──────────────────────────────────────────────────
        move_str = " ".join(moves)
        console.print(
            f"\n  Solved in [bold green]{move_count}[/bold green] moves: "
            f"[cyan]{move_str}[/cyan]\n"
        )

        # ── Move sequence with highlighting ──────────────────────────────────
        if move_count > 0:
            seq = Text("  ")
            for i, m in enumerate(moves):
                if i == current_move_idx:
                    seq.append(f" {m} ", style="bold yellow on blue")
                elif i < current_move_idx:
                    seq.append(f"{m}", style="dim")
                else:
                    seq.append(f"{m}")
                if i < move_count - 1:
                    seq.append(" ")
            console.print(seq)
            console.print()

        # ── Cube render ───────────────────────────────────────────────────────
        faces_data: dict[str, list[Optional[str]]] = {
            face: list(state.faces[face]) for face in FACES  # type: ignore[misc]
        }
        # Pass a center cell as cursor so no cell is highlighted during playback
        frame_lines = _render_frame(faces_data, (U, CENTER_IDX))
        for line in frame_lines:
            console.print(line)

        # ── Mode hint ─────────────────────────────────────────────────────────
        if mode["auto_play"]:
            hint = "[dim][S] step mode  [Q] quit[/dim]"
        else:
            hint = "[dim][A] auto-play  [Space/Enter] next  [Q] quit[/dim]"
        console.print(f"\n  {hint}")

    # ── Non-blocking keypress reader used during auto-play ───────────────────
    # We spin up a daemon thread that blocks on readchar.readkey() and posts
    # the character into a shared slot.  The main thread polls it during the
    # inter-move delay so it never blocks.
    _key_slot: list[Optional[str]] = [None]
    _key_lock = threading.Lock()

    def _key_listener() -> None:
        while True:
            try:
                ch = readchar.readkey()
            except Exception:
                return
            with _key_lock:
                _key_slot[0] = ch

    _listener = threading.Thread(target=_key_listener, daemon=True)
    _listener.start()

    def _poll_key() -> Optional[str]:
        """Consume and return the latest key from the listener, or None."""
        with _key_lock:
            ch = _key_slot[0]
            _key_slot[0] = None
        return ch

    # ── Main animation loop ──────────────────────────────────────────────────
    # Invariant: render FIRST (state before this move), THEN apply, THEN wait.
    i = 0
    while i < move_count:
        _render_solution(i)

        if mode["auto_play"]:
            # Sleep in small increments, checking for 'S' / 'Q' keypresses
            start = time.monotonic()
            while time.monotonic() - start < step_delay:
                ch = _poll_key()
                if ch is not None:
                    if ch.lower() == "s":
                        mode["auto_play"] = False
                        break
                    elif ch.lower() == "q":
                        console.print("\n[dim]Bye![/dim]")
                        sys.exit(0)
                time.sleep(0.02)

            # If we just switched to step mode, re-render with updated hint
            # then fall through to step-mode wait below without advancing
            if not mode["auto_play"]:
                _render_solution(i)
                # fall into step-mode wait
            else:
                # Auto-play: advance state and move to next move
                state.apply_move(moves[i])
                i += 1
                continue

        # Step mode: wait for Space / Enter (advance) or 'A' (resume auto)
        while True:
            # Drain anything the listener already captured
            ch = _poll_key()
            if ch is None:
                ch = readchar.readkey()
            if ch in (" ", readchar.key.ENTER, "\r", "\n"):
                state.apply_move(moves[i])
                i += 1
                break
            elif ch.lower() == "a":
                mode["auto_play"] = True
                state.apply_move(moves[i])
                i += 1
                break
            elif ch.lower() == "q":
                console.print("\n[dim]Bye![/dim]")
                sys.exit(0)

    # ── Final frame: fully solved cube ───────────────────────────────────────
    _render_solution(move_count)

    # Verify the final state equals the solved cube
    is_solved = (state == SOLVED_STATE)
    if is_solved:
        console.print("\n  [bold green]✓ Cube solved![/bold green]")
    else:
        console.print("\n  [bold red]✗ Final state does not match solved cube.[/bold red]")

    console.print(
        "\n  Press [bold][R][/bold] to restart or [bold][Q][/bold] to quit: ",
        end="",
    )

    while True:
        ch = _poll_key() or readchar.readkey()
        if ch.lower() == "r":
            return True
        elif ch.lower() == "q":
            console.print("\n[dim]Bye![/dim]")
            sys.exit(0)
