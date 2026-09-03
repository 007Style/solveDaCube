"""
test_solver.py
==============
Unit tests for solveDaCube.solver.

Covers:
- Solved cube returns 0 moves
- Known scrambled cube returns a valid (non-empty) solution
- Invalid cube state raises InvalidCubeError
"""

import pytest

from solveDaCube.cube import CubeState, SOLVED_STATE
from solveDaCube.solver import InvalidCubeError, solve

# The solved cube kociemba string (face order U R F D L B, each 9 chars)
SOLVED_KOCIEMBA = "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _apply_moves(state: CubeState, moves: list[str]) -> CubeState:
    """Return a new CubeState with all moves applied (non-destructive)."""
    s = state.copy()
    for move in moves:
        s.apply_move(move)
    return s


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSolvedCube:
    """Passing an already-solved cube should return zero moves."""

    def test_solved_returns_empty_list(self):
        state = CubeState.from_kociemba_string(SOLVED_KOCIEMBA)
        moves, count = solve(state)
        assert moves == []
        assert count == 0

    def test_default_cube_state_returns_empty_list(self):
        # CubeState() defaults to the solved state
        moves, count = solve(CubeState())
        assert moves == []
        assert count == 0


class TestScrambledCube:
    """A scrambled cube should produce a valid, non-empty solution."""

    def _scramble_R(self) -> CubeState:
        """Apply a single R move to the solved state."""
        state = CubeState.from_kociemba_string(SOLVED_KOCIEMBA)
        state.apply_move("R")
        return state

    def test_one_move_scramble_returns_nonempty_solution(self):
        state = self._scramble_R()
        moves, count = solve(state)
        assert len(moves) > 0
        assert count == len(moves)

    def test_one_move_scramble_solution_restores_solved_state(self):
        """Applying the returned solution to the scrambled cube should reach solved."""
        state = self._scramble_R()
        moves, _ = solve(state)

        # Re-create the scrambled cube and apply the solution
        scrambled = CubeState.from_kociemba_string(SOLVED_KOCIEMBA)
        scrambled.apply_move("R")
        solved_result = _apply_moves(scrambled, moves)

        # Compare to solved state (also built from the known kociemba string)
        expected = CubeState.from_kociemba_string(SOLVED_KOCIEMBA)
        assert solved_result == expected

    def test_solution_move_count_matches_list_length(self):
        state = self._scramble_R()
        moves, count = solve(state)
        assert count == len(moves)

    def test_solution_within_gods_number(self):
        """kociemba guarantees ≤ 20 moves."""
        state = self._scramble_R()
        _, count = solve(state)
        assert count <= 20

    def test_solution_tokens_are_valid_move_strings(self):
        """Every returned token should be a recognised move notation."""
        valid_faces = set("URFDLB")
        valid_modifiers = {"", "'", "2"}
        state = self._scramble_R()
        moves, _ = solve(state)
        for move in moves:
            assert move[0] in valid_faces, f"Unknown face in move: {move!r}"
            assert move[1:] in valid_modifiers, f"Unknown modifier in move: {move!r}"


class TestTwentyMoveScramble:
    """A multi-move scramble must be solved and produce a solved cube."""

    # A standard 14-move scramble (T-perm); kociemba solves it well within God's Number
    _SCRAMBLE_20 = [
        "R", "U", "R'", "U'",
        "R'", "F", "R2", "U'",
        "R'", "U'", "R", "U",
        "R'", "F'",
    ]

    def _scrambled_state(self) -> CubeState:
        state = CubeState()
        for move in self._SCRAMBLE_20:
            state.apply_move(move)
        return state

    def test_20_move_scramble_solution_within_gods_number(self):
        """Solver must return ≤ 20 moves for any valid scramble."""
        state = self._scrambled_state()
        _, count = solve(state)
        assert count <= 20

    def test_20_move_scramble_solution_restores_solved_state(self):
        """Applying the returned solution must produce a fully solved cube."""
        state = self._scrambled_state()
        moves, _ = solve(state)
        result = _apply_moves(state, moves)
        # Compare via kociemba string to handle color vs face-label representation
        assert result.to_kociemba_string() == SOLVED_KOCIEMBA

    def test_20_move_scramble_solution_count_matches_list_length(self):
        state = self._scrambled_state()
        moves, count = solve(state)
        assert count == len(moves)


class TestInvalidCube:
    """An invalid cube string should raise InvalidCubeError."""

    def test_all_same_color_raises(self):
        # 54 U's — physically impossible
        bad = CubeState.from_kociemba_string("U" * 54)
        with pytest.raises(InvalidCubeError):
            solve(bad)

    def test_wrong_color_distribution_raises(self):
        # Replace the first sticker so one face has 10 U's and another has 8
        good = list(SOLVED_KOCIEMBA)
        good[9] = "U"  # First R sticker → U (breaks R face center / counts)
        bad_string = "".join(good)
        bad = CubeState.from_kociemba_string(bad_string)
        with pytest.raises(InvalidCubeError):
            solve(bad)
