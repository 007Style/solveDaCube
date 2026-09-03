"""
test_cube.py
============
Unit tests for solveDaCube.cube.

Covers:
- Valid solved state
- Valid scrambled state
- Invalid color count raises expected error
- Invalid center stickers raises error
- to_kociemba_string() round-trip
- apply_move() for R, U, F moves (and all 6 faces, double, prime)
- apply_move("R") then apply_move("R'") returns to original state
- 4x apply_move("U") returns to original state
"""

import pytest
from solveDaCube.cube import (
    CubeState,
    SOLVED_STATE,
    U,
    R,
    F,
    D,
    L,
    B,
    W,
    Y,
    COLOR_R,
    O,
    G,
    COLOR_B,
    FACES,
    COLORS,
)


def test_solved_state_initialization():
    state = CubeState()
    assert state == SOLVED_STATE
    assert len(state.faces) == 6
    for face in FACES:
        assert len(state.faces[face]) == 9


def test_solved_state_kociemba_string():
    state = CubeState()
    expected = "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"
    assert state.to_kociemba_string() == expected


def test_from_kociemba_string_round_trip():
    original_str = "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"
    state = CubeState.from_kociemba_string(original_str)
    assert state.to_kociemba_string() == original_str

    # Test round trip with a scrambled kociemba string
    scrambled_str = "DUUBULDBFRBFRRULLLBRDFFFBLURDBFDFDRFRULBLUFDURRBLBDUDL"
    scrambled_state = CubeState.from_kociemba_string(scrambled_str)
    assert scrambled_state.to_kociemba_string() == scrambled_str


def test_validate_solved_state():
    state = CubeState()
    state.validate()  # Should not raise


def test_validate_scrambled_state():
    scrambled_str = "DUUBULDBFRBFRRULLLBRDFFFBLURDBFDFDRFRULBLUFDURRBLBDUDL"
    state = CubeState.from_kociemba_string(scrambled_str)
    state.validate()  # Should not raise


def test_validate_invalid_color_counts():
    state = CubeState()
    # Change one sticker to make count unbalanced
    state.faces[U][0] = Y  # 8 W, 10 Y
    with pytest.raises(ValueError, match="Color/Face"):
        state.validate()


def test_validate_invalid_centers():
    state = CubeState()
    # Duplicate a center
    state.faces[U][4] = state.faces[D][4]
    with pytest.raises(ValueError, match="Face centers must all be unique"):
        state.validate()


def test_apply_move_inverse():
    # R followed by R' returns to original state
    state = CubeState()
    original = state.copy()
    state.apply_move("R")
    assert state != original
    state.apply_move("R'")
    assert state == original


def test_apply_move_four_quarter_turns():
    # 4x U returns to original state
    state = CubeState()
    original = state.copy()
    for _ in range(4):
        state.apply_move("U")
    assert state == original


def test_apply_move_double_turn():
    # R2 equals 2x R and is self-inverse
    state1 = CubeState()
    state2 = CubeState()
    state1.apply_move("R2")
    state2.apply_move("R").apply_move("R")
    assert state1 == state2

    state1.apply_move("R2")
    assert state1 == SOLVED_STATE


def test_all_faces_four_turns():
    for face in FACES:
        state = CubeState()
        original = state.copy()
        for _ in range(4):
            state.apply_move(face)
        assert state == original, f"4x {face} did not return to original state"

        # Also test 4x prime
        for _ in range(4):
            state.apply_move(f"{face}'")
        assert state == original, f"4x {face}' did not return to original state"


def test_superflip_or_standard_scramble():
    # Sexy move 6 times returns to solved: (R U R' U') * 6
    state = CubeState()
    for _ in range(6):
        state.apply_move("R").apply_move("U").apply_move("R'").apply_move("U'")
    assert state == SOLVED_STATE


def test_invalid_moves():
    state = CubeState()
    with pytest.raises(ValueError, match="Invalid move face"):
        state.apply_move("X")
    with pytest.raises(ValueError, match="Invalid move modifier"):
        state.apply_move("R3")


def test_apply_move_R():
    """R move changes state; R' undoes it; R and R' are distinct."""
    state = CubeState()
    original = state.copy()
    state.apply_move("R")
    assert state != original
    state.apply_move("R'")
    assert state == original


def test_apply_move_U():
    """U move changes state; U' undoes it."""
    state = CubeState()
    original = state.copy()
    state.apply_move("U")
    assert state != original
    state.apply_move("U'")
    assert state == original


def test_apply_move_F():
    """F move changes state; F' undoes it."""
    state = CubeState()
    original = state.copy()
    state.apply_move("F")
    assert state != original
    state.apply_move("F'")
    assert state == original


def test_validate_swapped_centers():
    """Two identical center stickers must fail validate()."""
    state = CubeState()
    # Overwrite D center with U's color — U and D now share the same center color.
    # This represents a physically impossible cube (two faces with the same center).
    state.faces[D][4] = state.faces[U][4]  # both centers become W
    with pytest.raises(ValueError):
        state.validate()


def test_20_move_scramble_consistency():
    """Apply a 20-move sequence; state must differ from solved and be self-consistent."""
    scramble = [
        "R", "U", "R'", "U'",
        "F", "D", "F'", "D'",
        "L", "U'", "L'", "U",
        "B", "D'", "B'", "D",
        "R", "F", "R'", "F'",
    ]
    state = CubeState()
    original = state.copy()
    for move in scramble:
        state.apply_move(move)
    # State must differ after scrambling
    assert state != original
    # Applying the inverse sequence must restore original
    inverse = []
    for move in reversed(scramble):
        if move.endswith("'"):
            inverse.append(move[:-1])
        elif move.endswith("2"):
            inverse.append(move)  # R2 is its own inverse
        else:
            inverse.append(move + "'")
    for move in inverse:
        state.apply_move(move)
    assert state == original
