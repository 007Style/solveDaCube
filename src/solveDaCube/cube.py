"""
cube.py
=======
Cube state model, validation, and move application.

Responsibilities:
- Define face constants (U, R, F, D, L, B) and color constants (W, Y, R, O, G, B)
- Define sticker index layout (54 stickers, 9 per face)
- CubeState class:
    - Initialize from a 54-char string or dict of face arrays
    - to_kociemba_string() → 54-char string in kociemba order (U R F D L B)
    - validate() → check color count integrity
    - apply_move(move: str) → transform state for a standard move token
        (e.g. "R", "U'", "F2")
"""
