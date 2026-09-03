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
