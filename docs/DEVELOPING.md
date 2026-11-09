# Developing PadMint

This page is for people working on PadMint itself or on a game's PadMint recipe.
Players want the [README](../README.md) and the [player guide](GUIDE.md).

## Setup

Python 3.9 or newer; no packages. On Windows PadMint downloads Git itself; on a
Mac or Linux it uses the system's Git (`xcode-select --install`, or for example
`sudo apt install git`). Run everything from this repository.

## Commands

```sh
python3 -m padmint                           # the PadMint page in your browser (also: ui)
python3 -m padmint start                     # the guided path, in this terminal
python3 -m padmint list                      # supported games and platforms
python3 -m padmint make kartpad android --disc 'your disc.wbfs'   # one step: source, tools, build
python3 -m padmint doctor kartpad            # check this computer (installs nothing)
python3 -m padmint tools kartpad --target android --repo /path/to/kartpad   # pinned tools
python3 -m padmint get kartpad /path/to/kartpad   # download a game's source
python3 -m padmint check-manifest /path/to/game-repo
python3 -m padmint plan bluewake --repo /path/to/bluewake \
  --revision FULL_REVIEWED_COMMIT --disc '/path/to/your disc.iso'
python3 -m padmint build ...                 # same arguments as plan
python3 -m padmint history --repo /path/to/game-repo   # recorded builds
python3 -m padmint audit path/to/file-or-folder   # the release gate
```

`plan` validates paths, checkout state and platform support and prints the
backend command without building; change it to `build` to run it. Use
`--target` to choose a platform the game declares (default `ios`),
`--source-only`/`--no-mods` where the game supports them, and `--jobs 1-8`.
Builds run on the platforms a game marks *verified* or *experimental*; `list`
shows the rest as *planned*.

## How games plug in

Each game repository declares a `padmint.json` recipe (schema in
[padmint/manifest.py](../padmint/manifest.py)): accepted inputs, platforms and
their status, the backend command, stages, requirements and publication policy.
Each release attaches its recipe (`*-padmint.json`), and PadMint reads the
latest one on every build, so most game updates need no PadMint release.

The [catalog](../catalog/) lists every public game: the ones PadMint builds, the
ready-made apps (`download`) and the paused ones (`later`), with the
card text, requirements and install steps players see. Game-specific
translation, patches and packaging stay in the game's repository. See
[Adding a game](ADDING_A_GAME.md) for a complete example. New catalog entries
are only for Chris's own ports and need his go-ahead.

## What a build does

`plan` and `build` work on a checkout you provide; `make` and the PadMint
page do the downloading for you.

- Keep the game checkout clean at a commit you have reviewed. `plan` and
  `build` don't download repositories or install tools; use `doctor`,
  `tools` and `get`.
- Builds, logs and records stay under the game's ignored `build/padmint/`.
  One build runs per checkout; Ctrl-C cancels and keeps finished work.
- Every personal output is checked for structure and provenance, then run
  through the release gate. Its record says *personal build, not publishable*
  whatever the gate says.
- Nothing is installed on a device or uploaded.

## The release gate

`padmint audit` scans files, folders and ZIP-based packages for console keys,
address-named translated game functions, embedded original program sections and
provenance declaring translated game code. It fails closed on archives it can't
inspect. Keys are identified by a short prefix and a SHA-256 hash; this
repository contains no keys. A pass is a heuristic result, not copyright or
licensing clearance.

Game inputs, generated game code, saves, keys, personal builds and optimization
profiles never belong in this repository.

## Tests and checks

```sh
python3 -m unittest discover -s tests        # all tests
PADMINT_HOME=$(mktemp -d) python3 scripts/audit-catalog.py   # every game's published recipe
```

## Releasing a game that PadMint builds

1. Attach the recipe to the game's release (Windows routes also need the Windows
   recipe and the app without game code).
2. Run `scripts/player-check.sh` from PadMint's current `main`: with the
   game's clean checkout before tagging, and without it after publishing. It
   uses Apple's Python 3.9 and an empty PadMint folder, like players. A build
   with a newer Python and warm caches doesn't count, and a failure blocks the
   release.
3. Every public asset must pass `python3 -m padmint audit <asset>`.
4. If the release changes where or what the recipe builds (a host, a target),
   change `catalog/GAME.json` to match on the day it is published and release
   PadMint with it: the menu offers a game only where the catalog says. The
   player check lists what the catalog will need before tagging, and fails after
   publishing until the catalog matches (BlueWake 0.11.0 built on Windows for
   a day while PadMint still showed it as Mac only).

Players get the update the next time they build. PadMint itself only needs a
release when what the catalog describes changes: hosts, requirements, the game
file it asks for, install steps or card art.

