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
"""
