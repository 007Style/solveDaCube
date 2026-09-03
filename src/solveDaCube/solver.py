"""
solver.py
=========
Kociemba solver wrapper.

Responsibilities:
- solve(state: CubeState) -> tuple[list[str], int]
    Calls kociemba.solve() and parses the result into a list of move tokens
    and a move count.
- InvalidCubeError: raised when kociemba rejects the cube state, wrapping
    the underlying exception with a user-friendly message.
"""

from __future__ import annotations

import kociemba

from solveDaCube.cube import CubeState

# kociemba's canonical solved-state string
_SOLVED_KOCIEMBA = "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"


class InvalidCubeError(Exception):
    """Raised when kociemba rejects the cube state as unsolvable or invalid."""


def solve(state: CubeState) -> tuple[list[str], int]:
    """
    Solve the cube using Kociemba's two-phase algorithm.

    Parameters
    ----------
    state : CubeState
        A validated cube state.

    Returns
    -------
    tuple[list[str], int]
        A tuple of (moves, move_count) where moves is a list of individual
        move tokens such as ["R", "U", "R'", "U'"] and move_count is their
        length.  Returns ([], 0) if the cube is already solved.

    Raises
    ------
    InvalidCubeError
        If kociemba rejects the cube string as invalid or unsolvable.
    """
    cube_string = state.to_kociemba_string()

    # Short-circuit: kociemba returns a non-empty string even for a solved
    # cube, so we detect the solved state ourselves before calling it.
    if cube_string == _SOLVED_KOCIEMBA:
        return [], 0

    try:
        result = kociemba.solve(cube_string)
    except Exception as exc:
        raise InvalidCubeError(
            f"The cube state is invalid or unsolvable: {exc}"
        ) from exc

    moves = result.strip().split()
    return moves, len(moves)
