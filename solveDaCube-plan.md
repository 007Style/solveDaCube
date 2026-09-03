# solveDaCube — Plan

## Overview

Build a Python CLI app that solves a Rubik's Cube as fast as possible using **Kociemba's two-phase algorithm** (industry standard, always ≤20 moves). The user interacts via an **interactive ASCII terminal UI** where they visually fill in the 54 sticker colors on an unfolded cube layout. After input, the app solves the cube and displays the move sequence (e.g. `R U R' U'`), the move count, and an **animated step-by-step ASCII walkthrough** of each move applied to the cube state.

**Project name:** `solveDaCube`
**Version:** `1.0.0`
**Tagline:** *From the minds of IBM Bob & Daneyand*
**Language:** Python ≥ 3.10
**Key dependencies:** `kociemba` (solver), `rich` (terminal UI/animation), `readchar` (single-keypress input)
**Layout:** `src/` package layout, `pyproject.toml`, `pytest` tests, MIT license

### Color & Key Mapping

| Key | Color | Rich Style | Face |
|-----|-------|------------|------|
| `W` | White  | `bold white on white` | Up (U) |
| `Y` | Yellow | `bold black on yellow` | Down (D) |
| `R` | Red    | `bold white on red` | Right (R) |
| `O` | Orange | `bold black on orange1` | Left (L) |
| `G` | Green  | `bold white on green` | Front (F) |
| `B` | Blue   | `bold white on blue` | Back (B) |

> `B` is unambiguous in context: during color input it means **Blue**; face labels always use full names (Up, Down, Front, Back, Left, Right).

### Playback Defaults
- Solution animator **auto-plays by default** (0.5s delay between moves)
- User can press `S` at any time to switch to **step mode** (Space/Enter to advance)
- User can press `A` to resume auto-play from step mode

---

## Architecture

```
Entry Point (main.py)
      │
      ▼
 InputUI (ui.py)
 Interactive ASCII unfolded cube
 User fills 54 sticker cells
      │
      ▼
 Validator (cube.py)
 Validates color counts and
 cube state legality
      │
      ▼
 Solver (solver.py)
 kociemba.solve() → move sequence string
      │
      ▼
 Animator (ui.py)
 Step-by-step ASCII cube
 walkthrough of each move
```

---

## Sub-Tasks

---

### Sub-Task 1 — Project Scaffold

**Intent:**  
Create the full project skeleton: directory structure, `pyproject.toml`, `README.md`, `LICENSE`, `.gitignore`, and empty module stubs. This gives every subsequent sub-task a stable base to build on.

**Expected Outcomes:**
- `solveDaCube/` directory exists with `src/solveDaCube/` package
- `pyproject.toml` declares metadata, Python ≥3.10, dependencies (`kociemba`, `rich`), CLI entry point
- `README.md` with ASCII art header, badges, quick-start, usage, project layout, and footer: *"From the minds of IBM Bob & Daneyand"*
- `MIT LICENSE`
- `.gitignore` for Python projects
- Empty module stubs: `main.py`, `cube.py`, `solver.py`, `ui.py`, `__init__.py`, `__main__.py`
- `tests/` directory with `__init__.py` and empty test files
- `git init` run, initial commit ready

**Todo List:**
- [ ] Create directory tree (`src/solveDaCube/`, `tests/`)
- [ ] Write `pyproject.toml` with `name = "solveDaCube"`, `version = "1.0.0"`, description, Python floor, deps, entry point
- [ ] Write `README.md` with ASCII art, badges, quick start, usage, project layout, and footer *"From the minds of IBM Bob & Daneyand"*
- [ ] Write `LICENSE` (MIT)
- [ ] Write `.gitignore`
- [ ] Create empty module stubs with docstring headers
- [ ] Create `tests/__init__.py` and empty test stubs
- [ ] Run `git init` and make initial commit

**Relevant Context:**
- Follow `pyproject.toml` pattern from `procThumper` — `[project.scripts]` maps `solveDaCube → solveDaCube.main:main`
- `__init__.py` must set `__version__ = "1.0.0"` and `__tagline__ = "From the minds of IBM Bob & Daneyand"`
- `src/` layout: `[tool.setuptools.packages.find] where = ["src"]`
- README follows workspace convention: ASCII art, emoji, attribution footer "From the minds of IBM Bob & Daneyand..."

**Status:** [ ] pending

---

### Sub-Task 2 — Cube State Model (`cube.py`)

**Intent:**  
Define the cube's internal data model and validation logic. This is the foundation that the input UI, solver, and animator all depend on.

**Expected Outcomes:**
- A `CubeState` class (or dataclass) that holds the 54-sticker state as a dict/list keyed by face
- Standard face order and sticker indexing documented (matches kociemba's expected string format: `UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB` — 54 chars, order U, R, F, D, L, B)
- A `validate()` method that checks: exactly 9 of each color, center stickers are unique, and the state is a physically reachable cube (delegated to kociemba's own error on bad input)
- Color constants (`W Y R O G B`) and face constants (`U R F D L B`) defined — no black
- `to_kociemba_string()` method to serialize state for the solver
- `apply_move(move: str)` method to transform the state given a standard move notation (R, U, F, D, L, B, with `'` for inverse, `2` for double) — needed by the animator

**Todo List:**
- [ ] Define face constants (U, R, F, D, L, B) and color constants (W, Y, R, O, G, B)
- [ ] Define sticker index layout for each face (3×3 = 9 stickers per face, 54 total)
- [ ] Implement `CubeState` with initialization from a 54-char string or a dict of face arrays
- [ ] Implement `to_kociemba_string()` returning the 54-char face string in kociemba order
- [ ] Implement `validate()` checking color count integrity
- [ ] Implement `apply_move(move)` for all 18 standard moves (6 faces × quarter/half/inverse)
- [ ] Write unit tests in `tests/test_cube.py` for: valid solved state, valid scrambled state, invalid color count, `to_kociemba_string()` round-trip, `apply_move()` for at least R, U, F moves

**Relevant Context:**
- kociemba string format: 54 chars, faces in order U R F D L B, each face read top-left to bottom-right
- Standard color-to-face mapping (solved state): U=white, R=red, F=green, D=yellow, L=orange, B=blue (or any consistent assignment; user will define their own per input)
- `apply_move` rotation tables are well-known permutation arrays for each face turn — can use a hardcoded lookup table

**Status:** [ ] pending

---

### Sub-Task 3 — Interactive Input UI (`ui.py` — input phase)

**Intent:**  
Build the interactive terminal UI that displays an unfolded ASCII cube layout and lets the user navigate cells and enter colors interactively. This is the primary UX of the app.

**Expected Outcomes:**
- Renders a clean unfolded cube layout in the terminal using `rich`:
  ```
         [U face 3x3]
  [L 3x3][F 3x3][R 3x3][B 3x3]
         [D face 3x3]
  ```
- Each cell shows the current color rendered in its **rich color style** (see Color & Key Mapping table), or a dim `?` placeholder
- User navigates cells with arrow keys; pressing a color key (`W`, `Y`, `R`, `O`, `G`, `B`) fills the current cell — `B` = Blue (not Back)
- Center cells are pre-filled and locked (centers define the face color)
- Live validation feedback: shows a warning if color counts are exceeded
- A "Solve!" prompt appears once all 54 cells are filled and valid
- Returns a completed `CubeState` to the caller

**Todo List:**
- [ ] Design the ASCII unfolded layout coordinate system (map terminal row/col to face/sticker index)
- [ ] Implement `render_cube(state, cursor_pos)` using `rich.console` — draw the full cube, highlight the active cell
- [ ] Implement key input loop using `readchar` (arrow keys + color keys W/Y/R/O/G/B + Enter/Q)
- [ ] Lock center cells on render; pre-fill them with face colors
- [ ] Show a live color count status bar (e.g. `W:4/9 Y:0/9 ...`) at the bottom
- [ ] Implement "Solve!" confirmation step when all cells filled
- [ ] Return completed `CubeState` from `run_input_ui()`
- [ ] Manual test: verify layout renders correctly, navigation works, invalid fills are blocked

**Relevant Context:**
- Use `rich.live` or a simple redraw loop with `console.clear()` for interactive feel
- `readchar` is already a declared dependency — use it for all single-keypress input
- Center sticker indices per face: index 4 of each face's 9-sticker array (0-indexed)
- This function is called from `main.py` and returns a `CubeState`

**Status:** [ ] pending

---

### Sub-Task 4 — Solver Integration (`solver.py`)

**Intent:**  
Wrap the `kociemba` library to take a validated `CubeState` and return the optimal move sequence as a list of move strings.

**Expected Outcomes:**
- `solve(state: CubeState) -> list[str]` function that calls `kociemba.solve(cube_string)` and parses the result into a list of individual move tokens (e.g. `["R", "U", "R'", "U'"]`)
- Handles kociemba errors (invalid state) by raising a clean `InvalidCubeError` with a user-friendly message
- Returns move count alongside the move list
- Fast: kociemba solves in milliseconds; no threading needed

**Todo List:**
- [ ] Implement `solve(state: CubeState) -> tuple[list[str], int]` — returns (moves, count)
- [ ] Parse kociemba's space-separated move string into individual tokens
- [ ] Wrap kociemba exceptions in `InvalidCubeError` with a readable message
- [ ] Write unit tests in `tests/test_solver.py` for: solved cube returns 0 moves, known scramble returns correct/valid solution, invalid state raises `InvalidCubeError`

**Relevant Context:**
- `kociemba.solve(cube_string)` returns a string like `"R U R' U' R' F R2 U' R' U' R U R' F'"` or raises an exception
- The solved cube kociemba string: `"UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"`
- kociemba guarantees ≤20 moves (God's Number)

**Status:** [ ] pending

---

### Sub-Task 5 — Solution Display & Animated Walkthrough (`ui.py` — output phase)

**Intent:**  
After solving, display the move sequence with move count, then animate each move step-by-step showing the cube state after every move using ASCII art. This is the payoff of the app.

**Expected Outcomes:**
- A solution header showing move count and the full move sequence: `Solved in 14 moves: R U R' U' R' F R2 U' R' U' R U R' F'`
- Each move is highlighted as it's applied (bold/colored current move in the sequence)
- The ASCII cube re-renders after each move to show the updated state using **rich face colors**
- **Auto-play is the default** (0.5s delay); user presses `S` to switch to step mode (Space/Enter to advance), `A` to resume auto-play
- At the end, the cube shows the fully solved state (all faces solid color)
- Option to press `R` to restart with a new cube

**Todo List:**
- [ ] Implement `display_solution(moves: list[str], initial_state: CubeState)` in `ui.py`
- [ ] Print solution header with move count and full move string
- [ ] Loop through moves: call `state.apply_move(move)`, re-render the cube, highlight the current move
- [ ] Auto-play is the default — loop through moves with `time.sleep(0.5)` between each
- [ ] Allow `S` keypress during auto-play to drop into step mode; `A` to resume auto-play
- [ ] Add `[R]estart` option at the end
- [ ] Verify that the final state after all moves equals a solved cube

**Relevant Context:**
- Reuses `render_cube()` from Sub-Task 3
- Uses `state.apply_move()` from Sub-Task 2
- `rich.live` or `time.sleep` + clear/redraw works well for animation
- Move highlighting: use `rich` markup to bold/color the current move in the printed sequence

**Status:** [ ] pending

---

### Sub-Task 6 — Main Entry Point & Integration (`main.py`)

**Intent:**  
Wire all components together into a cohesive CLI application. Handle startup, argument parsing, and the full user flow.

**Expected Outcomes:**
- `main()` function orchestrates: show welcome screen → run input UI → solve → display solution → offer restart
- `--version` flag prints `solveDaCube v1.0.0 — From the minds of IBM Bob & Daneyand` and exits
- `--demo` flag loads a hardcoded scrambled cube and solves it immediately (useful for testing/demoing without manual input)
- Graceful `Ctrl+C` handling (exits cleanly with a goodbye message)
- Welcome screen with ASCII art logo and tagline: *From the minds of IBM Bob & Daneyand*

**Todo List:**
- [ ] Implement `main()` with `argparse` for `--version` and `--demo`
- [ ] Display ASCII art welcome banner on startup
- [ ] Call `run_input_ui()` → `solve()` → `display_solution()` in sequence
- [ ] Implement restart loop (after solution, offer to solve another)
- [ ] Handle `KeyboardInterrupt` gracefully
- [ ] Verify end-to-end flow: from launch to solved cube display

**Relevant Context:**
- Entry point registered in `pyproject.toml`: `solveDaCube = "solveDaCube.main:main"`
- `__main__.py` should call `main()` so `python -m solveDaCube` also works
- Welcome banner should match workspace README ASCII art style

**Status:** [ ] pending

---

### Sub-Task 7 — Tests, Polish & README Finalization

**Intent:**  
Complete the test suite, do a final pass on polish (colors, spacing, edge cases), and finalize the README with real usage examples and screenshots.

**Expected Outcomes:**
- All unit tests pass (`pytest`)
- `pip install -e .` works cleanly
- `solveDaCube --demo` runs end-to-end without errors
- README has accurate quick-start, usage, demo GIF placeholder, project layout, and attribution footer

**Todo List:**
- [ ] Fill in any missing unit tests (cube model, solver, edge cases)
- [ ] Test on a solved cube (0 moves), a 1-move scramble, and a 20-move scramble
- [ ] Fix any rendering edge cases discovered during testing
- [ ] Finalize README: update quick-start with real install command, add usage examples, add project layout tree
- [ ] Ensure `solveDaCube --version` and `solveDaCube --demo` work
- [ ] Run `pytest` — all tests green

**Status:** [ ] pending
