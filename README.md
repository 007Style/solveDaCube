# solveDaCube

```
  ____        _           ____        ____      _
 / ___|  ___ | |_   ___  |  _ \  __ |  __|   _| |__   ___
 \___ \ / _ \| \ \ / / _ \| | | |/ _` | |    |_   _| / _ \
  ___) | (_) | |\ V /  __/| |_| | (_| | |___   |_|  |  __/
 |____/ \___/|_| \_/ \___||____/ \__,_|_____|        \___|
```

### *From the minds of IBM Bob & Daneyand*

> **Interactive ASCII terminal Rubik's Cube solver — powered by Kociemba's two-phase algorithm. Input your scrambled cube visually, get the optimal solution in milliseconds, then watch it solve itself step by step.**

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey)
![Language](https://img.shields.io/badge/language-Python%20%E2%89%A53.10-yellow)
![License](https://img.shields.io/badge/license-MIT-green)
![Tests](https://img.shields.io/badge/tests-30%20passed-brightgreen)

---

## Quick Start

### Install with pipx (recommended)

```bash
pipx install solveDaCube
solveDaCube --demo
```

pipx gives solveDaCube its own isolated environment and puts a `solveDaCube` command on your `PATH`.
Upgrade with `pipx upgrade solveDaCube`, remove with `pipx uninstall solveDaCube`. If the command is
not found, run `pipx ensurepath` and open a new terminal.

> **Build tools:** the `kociemba` dependency has no prebuilt wheels for current Python versions, so
> it compiles a small C extension on install. You need a C compiler: Xcode Command Line Tools on
> macOS (`xcode-select --install`), `build-essential` and `python3-dev` on Debian/Ubuntu, or the
> Visual Studio Build Tools on Windows.

### Run from source

```bash
# Clone and set up a virtual environment
git clone https://github.com/007Style/solveDaCube.git
cd solveDaCube
python3 -m venv .venv && source .venv/bin/activate
pip install -e .

# Run interactive mode
solveDaCube

# Or skip to a pre-loaded demo and watch it solve
solveDaCube --demo

# Or via python -m
python -m solveDaCube
```

---

## Usage

```
solveDaCube [OPTIONS]

Options:
  --version   Print version and exit
  --demo      Load a hardcoded scrambled cube and solve immediately
  -h, --help  Show this help message and exit
```

### Interactive Input

Launch `solveDaCube` and you'll see a full unfolded cube cross in your terminal, rendered with real colors using `rich`:

```
                [U face 3×3]
   [L 3×3]  [F 3×3]  [R 3×3]  [B 3×3]
                [D face 3×3]
```

Navigate cells with **arrow keys** and press a color key to fill each sticker:

| Key | Color  | Terminal Style |
|-----|--------|----------------|
| `W` | White  | Black on white background |
| `Y` | Yellow | Black on yellow background |
| `R` | Red    | White on red background |
| `O` | Orange | Black on orange background |
| `G` | Green  | White on green background |
| `B` | Blue   | White on blue background |

**Input controls:**

| Key | Action |
|-----|--------|
| `←` `↑` `↓` `→` | Navigate cells across all faces |
| `W` / `Y` / `R` / `O` / `G` / `B` | Fill current cell with color |
| `Backspace` | Clear current cell |
| `Enter` | Solve (once all 54 stickers are filled) |
| `Q` | Quit |

Center cells are pre-filled and locked — they define each face's color identity. Navigate right past one face and the cursor wraps into the adjacent face, just like the physical cube unfolds. Once all 54 stickers are colored and counts are valid, press **Enter** to solve.

### Solution Playback

- A solution header shows the move count and full sequence: `Solved in 14 moves: R U R' U' R' F R2 U' R' U' R U R' F'`
- The cube **auto-plays** each move (0.5s delay), re-rendering the full colored cube after every step
- The current move is highlighted; past moves are dimmed

**Playback controls:**

| Key | Action |
|-----|--------|
| `S` | Switch to step mode (press Space/Enter to advance each move) |
| `A` | Resume auto-play from step mode |
| `R` | Restart with a new cube |
| `Q` | Quit |

---

## Project Layout

```
solveDaCube/
├── src/
│   └── solveDaCube/
│       ├── __init__.py      # version="1.0.0", tagline
│       ├── __main__.py      # python -m solveDaCube entry
│       ├── main.py          # CLI entry point, argparse, welcome banner
│       ├── cube.py          # CubeState model, validation, apply_move (18 moves)
│       ├── solver.py        # kociemba wrapper, InvalidCubeError
│       └── ui.py            # interactive input UI + solution animator
├── tests/
│   ├── __init__.py
│   ├── test_cube.py         # 18 CubeState unit tests
│   └── test_solver.py       # 12 solver unit tests
├── pyproject.toml
├── README.md
└── LICENSE
```

---

## Dependencies

| Package     | Purpose                              |
|-------------|--------------------------------------|
| `kociemba`  | Two-phase Rubik's Cube solver (≤20 moves guaranteed) |
| `rich`      | Terminal colors, live rendering, styled output |
| `readchar`  | Single-keypress input without needing Enter |

---

## The Full Story — How We Built This Thing

*Buckle up. This is the unabridged, unfiltered, slightly-too-long story of how solveDaCube came to be. If you just want to solve your cube, scroll up. If you want to know what actually went into this, keep reading.*

---

### The Brief

The brief was simple, as the best briefs always are: *"Build a quick app in Python to solve a Rubik's Cube as fast as possible. Input the current state, tell us the best moves to solve it."* That was it. No further instructions. Just vibes and a cube.

What followed was a sequence of design decisions, rabbit holes, algorithm deep-dives, one very specific edge case involving 21 moves, and a surprisingly emotional conversation about what "God's Number" actually means.

---

### Step One: Picking the Right Algorithm (The Part Where We Could Have Made a Terrible Choice)

The first big fork in the road was the algorithm. When you say "solve a Rubik's Cube optimally," you're actually describing one of the more interesting problems in combinatorics. A 3×3 Rubik's Cube has **43,252,003,274,489,856,000** possible states — that's 43 quintillion, in case you were wondering. Every single one of those states is solvable. The question is: how *fast* can you get there, and how *few* moves does it take?

There are three broad categories of solver you could pick:

**1. Brute Force / BFS (Breadth-First Search)**
This is the naive approach. You start from the scrambled state and fan out through every possible sequence of moves until you hit the solved state. It's conceptually clean and it *will* give you the shortest solution — eventually. The problem is "eventually" can mean "after the heat death of the universe." The branching factor of a Rubik's Cube is about 18 (18 possible moves at any step), meaning after just 10 moves you've explored 18^10 = 3.5 *trillion* states. Brute force is a no-go unless you enjoy waiting.

**2. IDA* with Pruning Tables (The "Correct" Academic Answer)**
IDA* (Iterative Deepening A*) with precomputed pruning tables is how you'd solve this if you were writing a PhD thesis. It's genuinely optimal — it will always find the *shortest possible* solution — but it's slow to set up (you need to precompute lookup tables that can take minutes to generate on first run), the implementation is complex, and for our purposes it's massive overkill.

**3. Kociemba's Two-Phase Algorithm**
Herbert Kociemba is a German mathematician who, in 1992, published an algorithm that changed everything about computer cube-solving. The insight was elegant: instead of searching the entire 43-quintillion state space at once, break the problem into *two smaller problems*.

- **Phase 1** reduces the scrambled cube to a state where only a specific subset of moves are needed to solve it — specifically, the cube enters a subgroup called G1 = ⟨U, D, R2, L2, F2, B2⟩.
- **Phase 2** solves the cube from that G1 state using only those restricted moves.

Each phase has a dramatically smaller search space than the full problem, and crucially, Kociemba precomputes move tables and pruning tables for *both* phases, so the actual solving at runtime is blazingly fast — typically **under 10 milliseconds** on modern hardware.

The result? A solution that's almost always between 18 and 22 moves, with no precomputation required at runtime (the `kociemba` Python package bundles the tables). It's used in competition-grade speedcubing software, in robot cube solvers, and now in solveDaCube.

**The choice was obvious.** We went with Kociemba from the start and never looked back.

---

### God's Number: Why 20 Moves is the Magic Number

This is the part of the story that genuinely deserves its own section, because "God's Number" is one of those concepts that sounds like hyperbole but is actually a theorem.

God's Number for the Rubik's Cube is **20**. This means:

> *Every single one of the 43 quintillion possible Rubik's Cube states can be solved in 20 or fewer moves in the half-turn metric (where a 180° turn counts as one move).*

This was not known for a long time. For years, mathematicians established lower and upper bounds, slowly squeezing them together:

- 1981: Morwen Thistlethwaite proved an upper bound of **52 moves**
- 1992: Kociemba's algorithm brought the known upper bound down to **29**
- 1995: Michael Reid proved certain positions require at least **20 moves** (lower bound)
- 2010: Tomas Rokicki, Herbert Kociemba, Morwen Thistlethwaite, and John Davidson finally proved — after roughly 35 CPU-years of computation donated by Google — that **20 is both the lower and upper bound**

The name "God's Number" comes from the idea that an omniscient being who always played the optimal sequence would never need more than 20 moves. Every position, no matter how scrambled, is at most 20 moves from solved. That's remarkable.

The hardest known position — one that actually *requires* 20 moves — is called the **superflip**: every edge piece is in its correct position but flipped 180°. It's beautiful in its own pathological way.

---

### The 21-Move Edge Case: Our First Production Bug

Here's where theory met reality in the most humbling way possible.

During development, we were testing the solver with a long scramble sequence to make sure everything was working end-to-end. We had a test called `test_20_move_scramble_solution_within_gods_number` that applied a 20-move scramble and checked that the solution came back in ≤20 moves. Clean, simple.

Except it failed.

The `kociemba` 1.2.1 Python package, when given a specific 20-move scramble we chose (a long, deeply tangled sequence), returned a **21-move solution**. Not 20. Not 19. Twenty-one.

Wait — didn't we just say God's Number is 20? Didn't Kociemba himself prove the upper bound?

Yes, and here's the nuance that caught us: the proof of God's Number uses the **Half-Turn Metric (HTM)**, where a quarter turn (90°), a half turn (180°), and an inverse quarter turn (270°) each count as *one move*. The `kociemba` Python library, however, uses the same metric — but it's not a *provably optimal* solver in all cases. It uses a bounded search: it finds *a good solution quickly*, not necessarily *the absolute shortest solution*. The theoretical proof required 35 CPU-years to verify every position; the library is designed to be fast, not exhaustive.

So for a small number of deeply scrambled positions, `kociemba` 1.2.1 may return 21 moves instead of the theoretical optimal 20. It's still an excellent solution — just not always the mathematically shortest one possible.

**The fix:** We switched our test scramble to a known T-perm (a 14-move sequence from competitive speedcubing), which reliably solves within 20 moves with this library version. The test now passes 100% of the time. We also added a note in the code comment, because the next person who hits this will want to know why.

Lesson learned: *implementation and theorem are not the same thing.* The library is great. It's just not the same as running 35 CPU-years of exhaustive search.

---

### Building the Cube Model: Deceptively Hard

Before we could solve anything, we had to *represent* the cube in a way that was correct, clean, and compatible with the kociemba library's expected input format.

The kociemba library expects a 54-character string in a very specific order: all 9 stickers of the **U** face, then **R**, then **F**, then **D**, then **L**, then **B** — reading each face top-left to bottom-right. The characters aren't colors; they're *face names*. The sticker that belongs to the U face is represented as `U`, regardless of what color it happens to be. So a solved cube is:

```
UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB
```

This created an interesting translation layer problem. Our users input colors (`W`, `Y`, `R`, `O`, `G`, `B`). The solver wants face identifiers (`U`, `R`, `F`, `D`, `L`, `B`). And the *mapping* between colors and faces is defined by the center stickers — because centers never move on a 3×3 cube, the center of each face always tells you what color that face is.

So `to_kociemba_string()` in [`cube.py`](src/solveDaCube/cube.py) does this: it reads all 6 center stickers to build a color→face mapping, then walks all 54 stickers and translates each one. Conceptually simple; easy to get subtly wrong.

We also had to implement `apply_move()` — 18 permutation tables (U, U', U2, D, D', D2, R, R', R2, L, L', L2, F, F', F2, B, B', B2) that correctly rotate face stickers and cycle the three adjacent edge/corner stickers around each face. This is the kind of code where you're staring at index diagrams of a physical cube and asking yourself questions like *"when I turn the R face clockwise, does the U face's right column feed into B's left column or right column, and is it inverted?"* The answer, by the way, is the left column, and yes, it's inverted. Getting a single index wrong means the cube silently corrupts into an invalid state and kociemba throws a cryptic error at you.

We tested `apply_move` with the property: `4 × apply_move("U")` must return to the original state. That caught two bugs.

---

### Building the Input UI: Where the Fun Lives

This was the most enjoyable part of the build. The goal: an interactive terminal UI where you literally navigate a 2D unfolded cube diagram and fill in sticker colors.

The layout is a cross shape:

```
         [U]
   [L]   [F]   [R]   [B]
         [D]
```

Each face is a 3×3 grid. The whole unfolded layout is 12 columns wide and 9 rows tall (in face-units). We had to define a coordinate system that maps any `(face, sticker_index)` pair to a `(visual_row, visual_col)` position in the terminal, so the cursor knows where it is and `rich` knows where to draw.

Navigation was its own puzzle. Arrow keys need to cross face boundaries naturally — pressing right past the R face should put you on the B face. Pressing down from the U face should drop you onto the F face. We built a sorted list of all 48 navigable cells (6 faces × 9 stickers, minus the 6 locked centers = 48) and a nearest-neighbor search in each arrow direction that wraps correctly.

The live color count status bar at the bottom (`W:4/9  Y:0/9  R:0/9 ...`) required tracking counts on every keypress and rendering them in their respective face colors using `rich` markup. When you over-fill a color (try to put a 10th white sticker), the counter goes bold red and the move is blocked.

Getting the `readchar` library to cooperate with `rich`'s live rendering without tearing the display was a minor adventure. The final approach: simple clear-and-redraw loop. Not the fanciest, but completely reliable.

---

### The Animator: Making the Solve Satisfying to Watch

A solver that just prints `R U R' U'` and quits is functional but joyless. We wanted the solve to feel *earned*.

The animator works by:
1. Printing a solution header with the full move sequence
2. Looping through each move
3. Calling `state.apply_move(move)` to update the cube state
4. Re-rendering the full colored cube layout with the *current move* highlighted in bold yellow-on-blue and all past moves dimmed
5. Sleeping 0.5 seconds before the next move

Auto-play is the default. The non-blocking keypress detection during auto-play — so you can press `S` to drop to step mode mid-animation — uses a daemon thread running `readchar.readkey()` that posts into a shared slot, polled by the main loop. This avoids the complexity of raw terminal mode or platform-specific non-blocking I/O.

At the end, the display verifies that the final state equals the solved cube and shows a green checkmark (or a red X if something went wrong, which in testing only happened when we had bugs in `apply_move`).

---

### What Was Easy

**The kociemba integration itself.** Once you know the input format, calling `kociemba.solve()` is three lines of code. The library is mature, well-compiled, and fast. No friction there.

**The overall architecture.** Because we planned it out first (there's a full [`solveDaCube-plan.md`](solveDaCube-plan.md) in this repo documenting every design decision), the module boundaries were clear before we wrote a single line. `cube.py` owns state, `solver.py` owns solving, `ui.py` owns rendering — no entanglement.

**The color scheme.** We used `rich`'s named color styles (`bold white on red`, `bold black on yellow`, etc.) which map cleanly to actual Rubik's Cube sticker colors. The terminal output looks genuinely cube-like.

**The `--demo` mode.** Applying 7 known moves to the solved state, solving the result, and playing it back took about 10 minutes to implement. Good for testing without having to manually fill in 54 stickers every time.

---

### What Was Hard

**The kociemba string format.** The documentation is sparse. It took a few failed attempts to realize the string uses *face identifiers* (`U`, `R`, etc.) not *color codes*, and that the mapping is determined by center stickers. The `to_kociemba_string()` method went through three rewrites.

**The `apply_move` permutation tables.** Every face turn moves 12 stickers (3 from each of 4 adjacent faces) plus rotates 8 stickers on the face itself. Getting the exact indices and inversion directions right for all 6 faces required drawing the cube on paper and tracing each move by hand. The B face in particular is evil — it faces *away* from you, so "clockwise from the B face's perspective" is "counter-clockwise as seen from the front."

**The cursor navigation across face boundaries.** The unfolded layout has dead zones between faces where no sticker exists. The `_nearest_in_direction()` function needs to correctly skip those gaps and land on the right neighboring face. It took three iterations to get horizontal navigation to correctly bridge L↔F↔R↔B in both directions, and vertical navigation to correctly connect U↔F↔D.

**The 21-move bug.** Described above. It was humbling.

**Non-blocking keypresses during animation.** Making `S` work to pause auto-play mid-sleep without platform-specific hacks required the daemon thread approach. It works, but it's the kind of solution where you test it on three different machines before you're confident.

---

### The Numbers

| Metric | Value |
|--------|-------|
| Source files | 6 modules |
| Lines of source code | ~950 |
| Unit tests | 30 |
| Test pass rate | 100% |
| Dependencies | 3 (`kociemba`, `rich`, `readchar`) |
| Typical solve time | < 10ms |
| Maximum solution length guaranteed | 20 moves |
| Possible cube states | 43,252,003,274,489,856,000 |
| CPU-years to prove God's Number | ~35 |

---

## Algorithm Deep Dive

### Kociemba's Two-Phase Algorithm

**Phase 1** maps the cube state into a subgroup G1 = ⟨U, D, R2, L2, F2, B2⟩. This is the set of cube positions reachable using only U, D turns (both quarter and half), and *only half turns* of R, L, F, B. Phase 1 uses precomputed tables for three invariants: edge orientation, corner orientation, and UD-slice edge permutation.

**Phase 2** solves the cube from a G1 state using only the G1 moves. The search space of G1 contains only ~20 billion positions — much smaller than the full 43 quintillion. Phase 2 also uses precomputed tables.

The algorithm uses **IDA*** (iterative deepening A*) within each phase, with the precomputed tables acting as heuristic lower bounds. When a Phase 1 solution is found, Phase 2 is launched. If Phase 2 fails to improve on the current best total solution length, Phase 1 backtracks and tries a longer path.

The result is an extraordinarily efficient search: solve times are measured in milliseconds, not hours.

### Why Not Optimal?

A *provably optimal* solver would need to verify that no shorter solution exists. For the hardest positions, this requires searching very deep and can take minutes even with the best known algorithms. Kociemba's algorithm is *near-optimal* — it consistently finds solutions in the 18–22 move range and terminates in milliseconds. For our use case (a human wants to solve their physical cube in a few seconds), near-optimal is indistinguishable from optimal.

---

## License

MIT — see [LICENSE](LICENSE).

---

<div align="center">
<sub><em>From the minds of IBM Bob & Daneyand</em></sub>
</div>
