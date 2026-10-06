#!/usr/bin/env python3
"""Check every game PadMint offers against the recipe its latest release publishes.

Usage: PADMINT_HOME=$(mktemp -d) python3 scripts/audit-catalog.py

Reads each recipe the way a player's PadMint does, then reports what would confuse or stop
a player: a target the recipe lacks, a menu showing a raw target name, a copy with no
finishing steps, an Xcode iPhone build that does not check Xcode's iOS platform, a game file
asked for at the wrong time, a player tool without install steps, a help link to a missing
README heading, or a game-code recipe that allows public binaries. It also prints where each
target builds. Needs the network; changes nothing. Exit status 1 when it finds a problem.
"""
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from padmint import cli  # noqa: E402
from padmint.manifest import catalog, needs_build_input  # noqa: E402

SHORT = {"macos-arm64": "Mac", "macos-x86_64": "Intel Mac", "windows-x86_64": "Windows",
         "windows-arm64": "Windows ARM", "linux-x86_64": "Linux", "linux-arm64": "Linux ARM"}


def readme(repo_url, tag):
    path = urllib.parse.urlsplit(repo_url).path.strip("/")
    try:
        with urllib.request.urlopen(f"https://raw.githubusercontent.com/{path}/{tag}/README.md", timeout=30) as r:
            return r.read().decode("utf-8", "replace")
    except OSError:
        return ""


def anchor(heading):
    return re.sub(r"[^\w\- ]", "", heading.strip().lower()).replace(" ", "-")


def audit():
    problems = []
    for game, entry in sorted(catalog().items()):
        targets = entry.get("player_targets") or []
        if not targets:
            continue
        found = lambda message: problems.append(f"{game}: {message}")  # noqa: E731
        try:
            recipe, source = cli.published_recipe(game)
        except Exception as error:  # an unreadable recipe is itself the finding
            found(f"recipe unreadable ({error})")
            continue
        if "built-in" in source:
            found(f"recipe not read from a release ({source})")
        tag = source.split()[1] if source.endswith(" release") else "HEAD"
        where = []
        for name in targets:
            target = (recipe.get("targets") or {}).get(name)
            if target is None:
                found(f"catalog offers {name}, the recipe has no {name} target")
                continue
            hosts = [SHORT.get(h, h) for h, s in target.get("hosts", {}).items() if s in cli.RUNNABLE_STATES]
            where.append(f"{name}: {', '.join(hosts) or 'nowhere'}")
            if not hosts:
                found(f"{name} has no host it can build on")
            if cli.platform_label(name, "en") == name:
                found(f"the menu would show the raw target name {name}")
            if name != "ios" and not (entry.get("player_next") or {}).get(name):
                found(f"no finishing steps (catalog player_next) for {name}")
            with mock.patch.object(cli, "host_id", return_value="macos-arm64"):
                checks = cli.player_requirements(recipe, name)
                xcode = any(tool["name"] == "xcodebuild" for tool in cli.host_requirements(recipe))
            if name == "ios" and xcode and not any("iphoneos" in tool.get("version_args", []) for tool in checks):
                found("an Xcode iPhone build without an iOS platform check")
            for host, state in target.get("hosts", {}).items():
                if state not in cli.RUNNABLE_STATES or host.startswith("macos"):
                    continue
                with mock.patch.object(cli, "host_id", return_value=host):
                    asks = [cli.label(tool) for tool in cli.player_requirements(recipe, name)
                            if tool["name"] in ("xcodebuild", "xcrun")]
                if asks:
                    found(f"{name} on {SHORT.get(host, host)} asks for {', '.join(asks)}")
        if (entry.get("player_game_file", "build") == "in-app") == needs_build_input(recipe):
            when = "reads" if needs_build_input(recipe) else "does not read"
            found(f"catalog player_game_file is {entry.get('player_game_file', 'build')}, "
                  f"but the build {when} the game file")
        for tool in cli.player_requirements(recipe):
            if not tool.get("note"):
                found(f"player tool {tool['name']} has no install note")
        help_url = entry.get("player_help") or ""
        if "#" in help_url:
            text = readme(entry["repo_url"], tag) or readme(entry["repo_url"], "HEAD")
            if help_url.split("#", 1)[1] not in {anchor(h) for h in re.findall(r"^#+\s+(.+)$", text, re.M)}:
                found(f"help link {help_url} has no matching README heading")
        if recipe.get("kind") in ("decomp-patches", "disc-translation") \
                and recipe.get("publication", {}).get("public_binaries") is not False:
            found("a game-code recipe allows public binaries")
        print(f"{game:13} {tag:9} {recipe.get('kind', '?'):16} {'; '.join(where)}")
    print(f"\n{len(problems)} problem(s)")
    for problem in problems:
        print(f"  {problem}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(audit())
