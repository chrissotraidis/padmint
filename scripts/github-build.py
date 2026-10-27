#!/usr/bin/env python3
"""Prepare GitHub Cloud Build for one game, the way a player prepares their own Mac.

Checks the release recipe before running setup, then optionally builds that same
release. The hosted route must never require a player's private game input.

Usage: scripts/github-build.py GAME [--out OUTPUT_FOLDER]
       scripts/github-build.py --matrix [GAME]
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from padmint import cli  # noqa: E402
from padmint.manifest import catalog, validate_github_build  # noqa: E402

# Rustup puts cargo in ~/.cargo/bin and asks the shell to read ~/.cargo/env.
SHELL_SETUP = 'set -e; if [ -f "$HOME/.cargo/env" ]; then . "$HOME/.cargo/env"; fi; '


def matrix(game=None):
    games = sorted(name for name, entry in catalog().items() if entry.get("github_build"))
    if game and game not in games:
        raise ValueError(f"{game} is not offered with GitHub Cloud Build")
    return {"game": [game] if game else games}


def prepare(game):
    entry = catalog().get(game)
    if not entry or not entry.get("github_build"):
        raise ValueError(f"{game} is not offered with GitHub Cloud Build")
    # Dispatch uploads an IPA; PR/scheduled checks only compile and discard it.
    if (entry.get("github_build_private") and os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
            and os.environ.get("PADMINT_REPOSITORY_PRIVATE") != "true"):
        raise ValueError("This personal build needs a private repository. Import PadMint into a private "
                         "repository and run its workflow there; a public fork exposes the IPA.")
    release = cli.latest_release(entry["repo_url"])
    recipe, source = cli.published_recipe(game, release=release)
    if source != f"{game} {release[0]} release":
        raise ValueError(f"Cannot check {game}'s published recipe: {source}")
    validate_github_build(entry, recipe)
    cli.player_target(recipe, "ios")
    print(f"Building {game} from {release[0]} (published recipe checked)", flush=True)
    for command in (entry.get("before_build") or {}).get("commands", []):
        print(f"+ {command}", flush=True)
        subprocess.run(["/bin/bash", "-c", SHELL_SETUP + command], check=True)
    cargo = Path.home() / ".cargo/bin"
    if cargo.is_dir():
        os.environ["PATH"] = str(cargo) + os.pathsep + os.environ.get("PATH", "")
        if os.environ.get("GITHUB_PATH"):
            with open(os.environ["GITHUB_PATH"], "a", encoding="utf-8") as stream:
                stream.write(f"{cargo}\n")
    return release


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game", nargs="?")
    parser.add_argument("--matrix", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.matrix:
            print(json.dumps(matrix(args.game)))
            return 0
        if not args.game:
            parser.error("a game is required")
        release = prepare(args.game)
        if args.out:
            # Some backends read these as if this were their own repository's CI.
            for name in ("CI", "GITHUB_ACTIONS", "GITHUB_REF", "GITHUB_REF_NAME", "GITHUB_HEAD_REF",
                         "GITHUB_BASE_REF", "GITHUB_EVENT_NAME", "GITHUB_SHA"):
                os.environ.pop(name, None)
            return cli.make(args.game, "ios", None, args.out.resolve(), release=release)
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"PadMint: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
