# solveDaCube

```
  ____        _           ____        ____      _
 / ___|  ___ | |_   ___  |  _ \  __ |  __|   _| |__   ___
 \___ \ / _ \| \ \ / / _ \| | | |/ _` | |    |_   _| / _ \
  ___) | (_) | |\ V /  __/| |_| | (_| | |___   |_|  |  __/
 |____/ \___/|_| \_/ \___||____/ \__,_|_____|        \___|
```

> **Interactive ASCII terminal Rubik's Cube solver — powered by Kociemba's two-phase algorithm**

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey)
![Language](https://img.shields.io/badge/language-Python%20%E2%89%A53.10-yellow)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Quick Start

```bash
# Clone and install
git clone https://github.com/daneyand/solveDaCube.git
cd solveDaCube
pip install -e .

# Run
solveDaCube

# Or with python -m
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

Launch `solveDaCube` and you'll see an unfolded cube layout in your terminal:

```
               [U face 3×3]
  [L 3×3]  [F 3×3]  [R 3×3]  [B 3×3]
               [D face 3×3]
```

Navigate cells with **arrow keys** and press a color key to fill:

| Key | Color  |
|-----|--------|
| `W` | White  |
| `Y` | Yellow |
| `R` | Red    |
| `O` | Orange |
| `G` | Green  |
| `B` | Blue   |

Center cells are pre-filled and locked. Once all 54 stickers are filled, press **Enter** to solve.

### Solution Playback

- The solution is displayed as a move sequence, e.g.: `R U R' U' R' F R2 U' R' U' R U R' F'`
- The cube **auto-plays** each move (0.5s delay), re-rendering after every step
- Press `S` during playback to switch to **step mode** (Space/Enter advances)
- Press `A` to resume **auto-play** from step mode
- Press `R` at the end to restart with a new cube

---

## Project Layout

```
solveDaCube/
├── src/
│   └── solveDaCube/
│       ├── __init__.py      # version, tagline
│       ├── __main__.py      # python -m solveDaCube entry
│       ├── main.py          # CLI entry point, argparse, welcome banner
│       ├── cube.py          # CubeState model, validation, apply_move
│       ├── solver.py        # kociemba wrapper, InvalidCubeError
│       └── ui.py            # interactive input UI + solution animator
├── tests/
│   ├── __init__.py
│   ├── test_cube.py         # CubeState unit tests
│   └── test_solver.py       # Solver unit tests
├── pyproject.toml
├── README.md
└── LICENSE
```

---

## Dependencies

| Package     | Purpose                              |
|-------------|--------------------------------------|
| `kociemba`  | Two-phase Rubik's Cube solver (≤20 moves guaranteed) |
| `rich`      | Terminal colors, live rendering      |
| `readchar`  | Single-keypress input without Enter  |

---

## Algorithm

solveDaCube uses **Kociemba's two-phase algorithm**, the same approach used in competition-grade speedcubing software. It guarantees a solution in **God's Number (≤20 moves)** and typically solves in milliseconds.

---

## License

MIT — see [LICENSE](LICENSE).

---

<div align="center">
<sub><em>From the minds of IBM Bob & Daneyand</em></sub>
</div>
