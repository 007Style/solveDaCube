"""
cube.py
=======
Cube state model, validation, and move application.

Responsibilities:
- Define face constants (U, R, F, D, L, B) and color constants (W, Y, R, O, G, B)
- Define sticker index layout (54 stickers, 9 per face)
- CubeState class:
    - Initialize from a 54-char string or dict of face arrays
    - to_kociemba_string() -> 54-char string in kociemba order (U R F D L B)
    - from_kociemba_string(s: str) -> CubeState
    - validate() -> check color count integrity and center uniqueness
    - apply_move(move: str) -> transform state for a standard move token
        (e.g. "R", "U'", "F2")
- SOLVED_STATE constant
"""

from __future__ import annotations
import copy
from typing import Dict, List, Optional, Union

# Face constants (standard kociemba ordering: U, R, F, D, L, B)
U = "U"
R = "R"
F = "F"
D = "D"
L = "L"
B = "B"

FACES: tuple[str, ...] = (U, R, F, D, L, B)

# Color constants: White, Yellow, Red, Orange, Green, Blue (no black)
W = "W"
Y = "Y"
COLOR_R = "R"  # Red
O = "O"
G = "G"
COLOR_B = "B"  # Blue

COLORS: tuple[str, ...] = (W, Y, COLOR_R, O, G, COLOR_B)

# Standard face to color mapping for a solved cube:
# U=W (White), R=R (Red), F=G (Green), D=Y (Yellow), L=O (Orange), B=B (Blue)
DEFAULT_FACE_COLORS: dict[str, str] = {
    U: W,
    R: COLOR_R,
    F: G,
    D: Y,
    L: O,
    B: COLOR_B,
}

# Color to standard kociemba face name mapping
DEFAULT_COLOR_TO_FACE: dict[str, str] = {
    W: U,
    COLOR_R: R,
    G: F,
    Y: D,
    O: L,
    COLOR_B: B,
}

# 9 stickers per face (indices 0..8):
# 0 1 2
# 3 4 5
# 6 7 8
#
# Index 4 is the center sticker.

# Clockwise rotation of a 3x3 face indices:
# 0 1 2       6 3 0
# 3 4 5  -->  7 4 1
# 6 7 8       8 5 2
_FACE_ROT_CW = [6, 3, 0, 7, 4, 1, 8, 5, 2]


def _rotate_face_cw(face_stickers: list[str]) -> list[str]:
    return [face_stickers[i] for i in _FACE_ROT_CW]


def _rotate_face_ccw(face_stickers: list[str]) -> list[str]:
    # Apply CW 3 times
    res = face_stickers
    for _ in range(3):
        res = _rotate_face_cw(res)
    return res


def _rotate_face_180(face_stickers: list[str]) -> list[str]:
    res = face_stickers
    for _ in range(2):
        res = _rotate_face_cw(res)
    return res


class CubeState:
    """Represents the 54-sticker state of a 3x3 Rubik's cube."""

    def __init__(
        self,
        faces: Optional[Union[Dict[str, List[str]], str]] = None,
    ) -> None:
        """
        Initialize cube state.
        faces can be:
          - None: initializes to solved state
          - dict mapping face string (U, R, F, D, L, B) to list of 9 color strings
          - 54-character string in kociemba face order (U, R, F, D, L, B)
        """
        if faces is None:
            self.faces: dict[str, list[str]] = {
                face: [DEFAULT_FACE_COLORS[face]] * 9 for face in FACES
            }
        elif isinstance(faces, str):
            if len(faces) != 54:
                raise ValueError(
                    f"Expected 54 characters for cube string, got {len(faces)}"
                )
            self.faces = {}
            for i, face in enumerate(FACES):
                self.faces[face] = list(faces[i * 9 : (i + 1) * 9])
        elif isinstance(faces, dict):
            for face in FACES:
                if face not in faces or len(faces[face]) != 9:
                    raise ValueError(
                        f"Face {face} must be present and contain exactly 9 stickers"
                    )
            self.faces = {face: list(faces[face]) for face in FACES}
        else:
            raise TypeError(
                f"Unsupported type for faces: {type(faces).__name__}"
            )

    @classmethod
    def from_kociemba_string(cls, s: str) -> CubeState:
        """Parse a 54-char string back into a CubeState."""
        return cls(faces=s)

    def to_kociemba_string(self) -> str:
        """
        Returns 54-character string in order U, R, F, D, L, B matching kociemba's format.
        If stickers are stored as face names (U, R, F, D, L, B), they are returned directly.
        If stickers are stored as color codes (W, Y, R, O, G, B), they are mapped to face names
        based on the center sticker of each face.
        """
        # Determine mapping from sticker representation to face name
        # Centers are at index 4 of each face
        centers = {self.faces[face][4]: face for face in FACES}

        chars: list[str] = []
        for face in FACES:
            for sticker in self.faces[face]:
                if sticker in centers:
                    chars.append(centers[sticker])
                elif sticker in DEFAULT_COLOR_TO_FACE:
                    chars.append(DEFAULT_COLOR_TO_FACE[sticker])
                elif sticker in FACES:
                    chars.append(sticker)
                else:
                    chars.append(sticker)
        return "".join(chars)

    def validate(self) -> None:
        """
        Validates:
        - Exactly 9 of each of the 6 colors/stickers
        - 6 unique center stickers
        Raises ValueError if invalid.
        """
        all_stickers: list[str] = []
        for face in FACES:
            stickers = self.faces.get(face)
            if stickers is None or len(stickers) != 9:
                raise ValueError(
                    f"Face {face} must have exactly 9 stickers, got {len(stickers) if stickers else 0}"
                )
            all_stickers.extend(stickers)

        if len(all_stickers) != 54:
            raise ValueError(
                f"Total stickers must be 54, got {len(all_stickers)}"
            )

        # Check centers
        centers = [self.faces[face][4] for face in FACES]
        if len(set(centers)) != 6:
            raise ValueError(
                f"Face centers must all be unique, got: {centers}"
            )

        # Check count of each unique sticker / color
        counts: dict[str, int] = {}
        for sticker in all_stickers:
            counts[sticker] = counts.get(sticker, 0) + 1

        if len(counts) != 6:
            raise ValueError(
                f"Cube must have exactly 6 distinct colors/faces, got {len(counts)}: {counts}"
            )

        for color, count in counts.items():
            if count != 9:
                raise ValueError(
                    f"Color/Face '{color}' has count {count}, expected exactly 9"
                )

    def copy(self) -> CubeState:
        """Return a deep copy of this CubeState."""
        return CubeState(faces=copy.deepcopy(self.faces))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CubeState):
            return False
        return self.faces == other.faces

    def __repr__(self) -> str:
        return f"CubeState({self.faces})"

    def apply_move(self, move: str) -> CubeState:
        """
        Transforms state for any of the 18 standard moves:
        U, U', U2, D, D', D2, L, L', L2, R, R', R2, F, F', F2, B, B', B2.
        Mutates self and returns self.
        """
        move = move.strip()
        if not move:
            return self

        face = move[0].upper()
        if face not in FACES:
            raise ValueError(f"Invalid move face: {move}")

        modifier = move[1:] if len(move) > 1 else ""
        if modifier not in ("", "'", "2"):
            raise ValueError(f"Invalid move modifier: {move}")

        # Execute 1, 2, or 3 clockwise turns
        # Normal (e.g. "R"): 1 CW turn
        # Double (e.g. "R2"): 2 CW turns
        # Prime (e.g. "R'"): 3 CW turns (or 1 CCW turn)
        num_cw = 1 if modifier == "" else (2 if modifier == "2" else 3)

        for _ in range(num_cw):
            self._apply_quarter_turn(face)

        return self

    def _apply_quarter_turn(self, face: str) -> None:
        """Apply a single clockwise quarter turn for the specified face."""
        # 1. Rotate the face itself clockwise
        self.faces[face] = _rotate_face_cw(self.faces[face])

        # 2. Cycle adjacent edge/corner stickers
        # We define the 4 groups of 3 stickers that cycle around the given face.
        if face == U:
            # Adjacent faces around U: B -> R -> F -> L (top rows: 0,1,2)
            # When looking at U from top:
            # F(0,1,2) <- R(0,1,2) <- B(0,1,2) <- L(0,1,2) <- F(0,1,2)
            # So CW cycle: F(0,1,2) moves to L(0,1,2), L(0,1,2) moves to B(0,1,2),
            # B(0,1,2) moves to R(0,1,2), R(0,1,2) moves to F(0,1,2).
            f_top = [self.faces[F][i] for i in (0, 1, 2)]
            r_top = [self.faces[R][i] for i in (0, 1, 2)]
            b_top = [self.faces[B][i] for i in (0, 1, 2)]
            l_top = [self.faces[L][i] for i in (0, 1, 2)]

            for i, idx in enumerate((0, 1, 2)):
                self.faces[F][idx] = r_top[i]
                self.faces[L][idx] = f_top[i]
                self.faces[B][idx] = l_top[i]
                self.faces[R][idx] = b_top[i]

        elif face == D:
            # Looking at D from bottom:
            # Adjacent faces around D: F(6,7,8), R(6,7,8), B(6,7,8), L(6,7,8)
            # Clockwise turn of D moves:
            # F(6,7,8) -> R(6,7,8) -> B(6,7,8) -> L(6,7,8) -> F(6,7,8)
            f_bot = [self.faces[F][i] for i in (6, 7, 8)]
            r_bot = [self.faces[R][i] for i in (6, 7, 8)]
            b_bot = [self.faces[B][i] for i in (6, 7, 8)]
            l_bot = [self.faces[L][i] for i in (6, 7, 8)]

            for i, idx in enumerate((6, 7, 8)):
                self.faces[R][idx] = f_bot[i]
                self.faces[B][idx] = r_bot[i]
                self.faces[L][idx] = b_bot[i]
                self.faces[F][idx] = l_bot[i]

        elif face == R:
            # Adjacent around R: U right col (2,5,8), B left col (0,3,6), D right col (2,5,8), F right col (2,5,8)
            # Looking at R face:
            # Top is U (2,5,8), Right is B (0,3,6 upside down relative to R), Bottom is D (2,5,8), Left is F (2,5,8)
            # Clockwise turn:
            # U(2,5,8) -> B(6,3,0) [inverted]
            # B(6,3,0) -> D(2,5,8) [so B(0,3,6) -> D(8,5,2)]
            # D(2,5,8) -> F(2,5,8)
            # F(2,5,8) -> U(2,5,8)
            u_col = [self.faces[U][i] for i in (2, 5, 8)]
            b_col = [self.faces[B][i] for i in (0, 3, 6)]
            d_col = [self.faces[D][i] for i in (2, 5, 8)]
            f_col = [self.faces[F][i] for i in (2, 5, 8)]

            # U(2,5,8) receives F(2,5,8)
            self.faces[U][2] = f_col[0]
            self.faces[U][5] = f_col[1]
            self.faces[U][8] = f_col[2]

            # B(0,3,6) receives U(8,5,2) (inverted)
            self.faces[B][0] = u_col[2]
            self.faces[B][3] = u_col[1]
            self.faces[B][6] = u_col[0]

            # D(2,5,8) receives B(6,3,0) (inverted)
            self.faces[D][2] = b_col[2]
            self.faces[D][5] = b_col[1]
            self.faces[D][8] = b_col[0]

            # F(2,5,8) receives D(2,5,8)
            self.faces[F][2] = d_col[0]
            self.faces[F][5] = d_col[1]
            self.faces[F][8] = d_col[2]

        elif face == L:
            # Adjacent around L: U left col (0,3,6), F left col (0,3,6), D left col (0,3,6), B right col (2,5,8)
            # Looking at L face:
            # Top is U(0,3,6), Right is F(0,3,6), Bottom is D(0,3,6), Left is B(8,5,2)
            # Clockwise turn:
            # U(0,3,6) -> F(0,3,6)
            # F(0,3,6) -> D(0,3,6)
            # D(0,3,6) -> B(8,5,2) [so B(2,5,8) receives D(6,3,0)]
            # B(8,5,2) -> U(0,3,6) [so U(0,3,6) receives B(8,5,2)]
            u_col = [self.faces[U][i] for i in (0, 3, 6)]
            f_col = [self.faces[F][i] for i in (0, 3, 6)]
            d_col = [self.faces[D][i] for i in (0, 3, 6)]
            b_col = [self.faces[B][i] for i in (2, 5, 8)]

            # F(0,3,6) receives U(0,3,6)
            self.faces[F][0] = u_col[0]
            self.faces[F][3] = u_col[1]
            self.faces[F][6] = u_col[2]

            # D(0,3,6) receives F(0,3,6)
            self.faces[D][0] = f_col[0]
            self.faces[D][3] = f_col[1]
            self.faces[D][6] = f_col[2]

            # B(2,5,8) receives D(6,3,0) (inverted)
            self.faces[B][2] = d_col[2]
            self.faces[B][5] = d_col[1]
            self.faces[B][8] = d_col[0]

            # U(0,3,6) receives B(8,5,2) (inverted)
            self.faces[U][0] = b_col[2]
            self.faces[U][3] = b_col[1]
            self.faces[U][6] = b_col[0]

        elif face == F:
            # Adjacent around F: U bottom row (6,7,8), R left col (0,3,6), D top row (0,1,2), L right col (2,5,8)
            # Looking at F face:
            # Top is U(6,7,8), Right is R(0,3,6), Bottom is D(0,1,2), Left is L(2,5,8)
            # Clockwise turn:
            # U(6,7,8) -> R(0,3,6)
            # R(0,3,6) -> D(2,1,0) (inverted from D top row) -> D(0,1,2) gets R(6,3,0)
            # D(0,1,2) -> L(6,3,0) -> L(2,5,8) gets D(0,1,2)
            # L(2,5,8) -> U(8,7,6) -> U(6,7,8) gets L(8,5,2)
            u_row = [self.faces[U][i] for i in (6, 7, 8)]
            r_col = [self.faces[R][i] for i in (0, 3, 6)]
            d_row = [self.faces[D][i] for i in (0, 1, 2)]
            l_col = [self.faces[L][i] for i in (2, 5, 8)]

            # R(0,3,6) receives U(6,7,8)
            self.faces[R][0] = u_row[0]
            self.faces[R][3] = u_row[1]
            self.faces[R][6] = u_row[2]

            # D(0,1,2) receives R(6,3,0) (inverted)
            self.faces[D][0] = r_col[2]
            self.faces[D][1] = r_col[1]
            self.faces[D][2] = r_col[0]

            # L(2,5,8) receives D(0,1,2)
            self.faces[L][2] = d_row[0]
            self.faces[L][5] = d_row[1]
            self.faces[L][8] = d_row[2]

            # U(6,7,8) receives L(8,5,2) (inverted)
            self.faces[U][6] = l_col[2]
            self.faces[U][7] = l_col[1]
            self.faces[U][8] = l_col[0]

        elif face == B:
            # Adjacent around B: U top row (0,1,2), L left col (0,3,6), D bottom row (6,7,8), R right col (2,5,8)
            # Looking at B face:
            # Top is U(2,1,0), Right is L(0,3,6), Bottom is D(8,7,6), Left is R(2,5,8)
            # Clockwise turn:
            # U(0,1,2) -> L(6,3,0) [so L(0,3,6) receives U(2,1,0)]
            # L(0,3,6) -> D(6,7,8)
            # D(6,7,8) -> R(8,5,2) [so R(2,5,8) receives D(8,7,6)]
            # R(2,5,8) -> U(0,1,2)
            u_row = [self.faces[U][i] for i in (0, 1, 2)]
            l_col = [self.faces[L][i] for i in (0, 3, 6)]
            d_row = [self.faces[D][i] for i in (6, 7, 8)]
            r_col = [self.faces[R][i] for i in (2, 5, 8)]

            # L(0,3,6) receives U(2,1,0) (inverted)
            self.faces[L][0] = u_row[2]
            self.faces[L][3] = u_row[1]
            self.faces[L][6] = u_row[0]

            # D(6,7,8) receives L(0,3,6)
            self.faces[D][6] = l_col[0]
            self.faces[D][7] = l_col[1]
            self.faces[D][8] = l_col[2]

            # R(2,5,8) receives D(8,7,6) (inverted)
            self.faces[R][2] = d_row[2]
            self.faces[R][5] = d_row[1]
            self.faces[R][8] = d_row[0]

            # U(0,1,2) receives R(2,5,8)
            self.faces[U][0] = r_col[0]
            self.faces[U][1] = r_col[1]
            self.faces[U][2] = r_col[2]


# Solved state constant
SOLVED_STATE = CubeState()
