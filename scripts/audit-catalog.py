#!/usr/bin/env python3
"""Check every game PadMint offers against the recipe its latest release publishes.

Usage: PADMINT_HOME=$(mktemp -d) python3 scripts/audit-catalog.py [--json]

Reads each recipe the way a player's PadMint does, then reports what would confuse or stop
a player: a target the recipe lacks, a target the recipe builds that PadMint silently hides,
a ready-to-play download the release doesn't publish, a menu showing a raw target name, a copy
with no finishing steps, an Xcode iPhone build that does not check Xcode's iOS platform, a game
file asked for at the wrong time, a player tool without install steps, a step run with {python}
that needs a newer Python than PadMint's own, a help link to a missing README heading, a
missing base app, a Windows/Linux host no longer allowed by the recipe, an unsafe GitHub
build, or a game-code recipe that allows public binaries. It also prints where each
target builds; --json records the release, architecture and target matrix without claiming
build or device acceptance. Needs the network; changes nothing. Exit status 1 on a problem.
The catalog-check workflow runs it every day, so a game release that changes what it publishes
fails here instead of confusing players.
"""
import argparse
from datetime import datetime, timezone
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from padmint import cli  # noqa: E402
from padmint.manifest import catalog, ios_build_hosts, needs_build_input, player_input_mode, validate_github_build  # noqa: E402

SHORT = {"macos-arm64": "Mac", "macos-x86_64": "Intel Mac", "windows-x86_64": "Windows",
         "windows-arm64": "Windows ARM", "linux-x86_64": "Linux", "linux-arm64": "Linux ARM"}
OFF_MAC_HOSTS = ("windows-x86_64", "windows-arm64", "linux-x86_64", "linux-arm64")


def route_problems(entry, recipe):
    """Check the catalog's route promises against the selected release, not its fallback."""
    problems = []
    if recipe.get("id") != entry["id"]:
        problems.append(f"the published recipe declares {recipe.get('id')}, not {entry['id']}")
    if entry.get("player_game_file", "build") != player_input_mode(recipe):
        problems.append(f"catalog player_game_file is {entry.get('player_game_file', 'build')}, "
                        f"but the recipe needs {player_input_mode(recipe)} input")
    ios_hosts = recipe.get("targets", {}).get("ios", {}).get("hosts", {})
    if "ios" in entry.get("player_targets", []):
        for host in ios_build_hosts(entry):
            if ios_hosts.get(host) not in cli.RUNNABLE_STATES:
                problems.append(f"catalog offers iPhone on {host}, but the published recipe does not")
        for host in OFF_MAC_HOSTS:
            if ios_hosts.get(host) in cli.RUNNABLE_STATES and host not in ios_build_hosts(entry):
                problems.append(f"the published recipe builds iPhone on {host}, but the catalog hides it "
                                "(add it to ios_hosts)")
    if entry.get("github_build"):
        try:
            validate_github_build(entry, recipe)
        except ValueError as error:
            problems.append(f"GitHub build unavailable: {error}")
    return problems


def release_version(repo_url, tag):
    """The same version.json choice make() uses, read from the selected source tag."""
    path = urllib.parse.urlsplit(repo_url).path.strip("/").removesuffix(".git")
    url = f"https://raw.githubusercontent.com/{path}/{urllib.parse.quote(tag, safe='')}/version.json"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.load(response)
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
        data = {}
    except ValueError:
        data = {}
    if not isinstance(data, dict):
        raise ValueError("version.json must contain an object")
    version, build = data.get("version"), data.get("build")
    if isinstance(version, str) and version and isinstance(build, int) and build > 0:
        return version
    return tag.lstrip("v")


def published_app_problems(entry, recipe, release):
    """Required base apps must be in this release's checksummed asset list."""
    apps = {name: target["published_app"] for name, target in recipe.get("targets", {}).items()
            if target.get("published_app") and any(
                state in cli.RUNNABLE_STATES for state in target.get("hosts", {}).values())}
    if not apps:
        return []
    tag, assets = release
    problems = []
    if "SHA256SUMS" not in assets:
        problems.append(f"{tag} has required base apps but no SHA256SUMS")
    try:
        version = release_version(entry["repo_url"], tag)
        for target, template in apps.items():
            name = template.format(version=version)
            if name not in assets:
                problems.append(f"{target} needs base app {name}, but {tag} does not list it in SHA256SUMS")
    except (OSError, ValueError, KeyError) as error:
        problems.append(f"cannot check {tag}'s required base apps ({error})")
    return problems


def ready_asset(platform, names):
    """A release file a player installs directly on this platform, if the release has one.
    An IPA made for PadMint (no game code in it) is not a ready-to-play iPhone app."""
    def match(name):
        lower = name.lower()
        if platform == "android":
            return lower.endswith(".apk")
        if platform == "ios":
            return lower.endswith(".ipa") and "for-padmint" not in lower
        if platform == "macos":
            return "mac" in lower and lower.endswith((".zip", ".dmg"))
        if platform == "windows":
            return "windows" in lower and lower.endswith(".zip")
        return False
    return next((name for name in names if match(name)), None)


def readme(repo_url, tag):
    path = urllib.parse.urlsplit(repo_url).path.strip("/")
    for name in ("README.md", "readme.md"):  # GitHub shows either; OpenRCT2 Touch uses readme.md
        try:
            with urllib.request.urlopen(f"https://raw.githubusercontent.com/{path}/{tag}/{name}", timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except OSError:
            pass
    return ""


def anchor(heading):
    return re.sub(r"[^\w\- ]", "", heading.strip().lower()).replace(" ", "-")


def audit(json_output=False):
    problems = []
    rows = []
    for game, entry in sorted(catalog().items()):
        targets = entry.get("player_targets") or []
        row = {"game": game, "repo_url": entry["repo_url"], "player_targets": targets,
               "route": "build" if targets else "download" if entry.get("download") else "paused",
               "ios_hosts": ios_build_hosts(entry) if "ios" in targets else [],
               "github_mac_ios": bool(entry.get("github_build")),
               "other_route": (entry.get("off_mac") or {}).get("url"), "targets": {}}
        rows.append(row)
        if not targets:
            continue
        found = lambda message: problems.append(f"{game}: {message}")  # noqa: E731
        try:
            release = cli.latest_release(entry["repo_url"])
            recipe, source = cli.published_recipe(game, release=release)
        except Exception as error:  # an unreadable recipe is itself the finding
            found(f"recipe unreadable ({error})")
            row["error"] = str(error)
            continue
        row.update(release=release[0], recipe_source=source, kind=recipe.get("kind"),
                   build_input=needs_build_input(recipe), input_mode=player_input_mode(recipe))
        row["targets"] = {name: {"hosts": target.get("hosts", {}),
                                 "published_app": target.get("published_app"),
                                 "offered": name in targets}
                          for name, target in recipe.get("targets", {}).items()}
        if "built-in" in source:
            found(f"recipe not read from a release ({source})")
        for problem in route_problems(entry, recipe):
            found(problem)
        for problem in published_app_problems(entry, recipe, release):
            found(problem)
        tag = source.split()[1] if source.endswith(" release") else "HEAD"
        ready = entry.get("ready_to_play")
        if ready:
            for name in ready.get("platforms", targets):
                if not ready_asset(name, release[1]):
                    found(f"catalog says {name} has a ready-to-play download, but {release[0]} publishes "
                          "none (fix ready_to_play.platforms and its text)")
        held = entry.get("unoffered_targets") or {}
        for name, target in (recipe.get("targets") or {}).items():
            runnable = any(s in cli.RUNNABLE_STATES for s in target.get("hosts", {}).values())
            if runnable and name not in targets and name not in held:
                found(f"the recipe builds {name} but PadMint doesn't offer it; add it to player_targets, "
                      "or to unoffered_targets with the reason")
            if name in held and name in targets:
                found(f"{name} is both offered and listed in unoffered_targets")
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
        for tool in cli.player_requirements(recipe):
            if not tool.get("note"):
                found(f"player tool {tool['name']} has no install note")
        # A Mac card says "Needs Xcode" when the catalog has no Homebrew line (before_build) and
        # no ready-to-play app; then Xcode must really be all the player installs.
        if {"ios", "macos"} & set(targets) and not entry.get("before_build") and not entry.get("ready_to_play"):
            with mock.patch.object(cli, "host_id", return_value="macos-arm64"):
                extra = sorted({tool["name"] for name in set(targets) & {"ios", "macos"}
                                for tool in cli.player_requirements(recipe, name)} - {"xcodebuild", "xcrun", "git"})
            if extra:
                found(f"its card says Needs Xcode, but the recipe also asks for {', '.join(extra)}; "
                      "add their install line to before_build")
        # {python} is the Python running PadMint: Apple's 3.9 when PadMint.command starts it.
        # Only a Mac runs that Python, so count Mac steps and Mac-side requirements only.
        on_mac = lambda hosts: not hosts or any(host.startswith("macos") for host in hosts)
        newer = [tool["min_version"] for tool in recipe.get("requirements", {}).get("tools", [])
                 if tool["name"] in ("python", "python3") and on_mac(tool.get("hosts"))
                 and cli.version_tuple(str(tool.get("min_version", "0"))) > (3, 9)]
        steps = [step for target in (recipe.get("targets") or {}).values()
                 for step in ([target] if "command" in target else target.get("steps", []))
                 if "macos" in step.get("on", ["macos"])]
        if newer and any(step["command"][:1] == ["{python}"] for step in steps):
            found(f"a step runs {{python}} (PadMint's Python, 3.9 on a Mac) but the recipe checks for "
                  f"Python {newer[0]}+; run python3, the program that check finds")
        help_url = entry.get("player_help") or ""
        if "#" in help_url:
            text = readme(entry["repo_url"], tag) or readme(entry["repo_url"], "HEAD")
            if help_url.split("#", 1)[1] not in {anchor(h) for h in re.findall(r"^#+\s+(.+)$", text, re.M)}:
                found(f"help link {help_url} has no matching README heading")
        if recipe.get("kind") in ("decomp-patches", "disc-translation") \
                and recipe.get("publication", {}).get("public_binaries") is not False:
            found("a game-code recipe allows public binaries")
        if entry.get("github_build"):
            where.append("iOS remote: GitHub Cloud Build (no build-time game file)")
        if not json_output:
            print(f"{game:13} {tag:9} {recipe.get('kind', '?'):16} {'; '.join(where)}", flush=True)
    if json_output:
        print(json.dumps({"checked_at": datetime.now(timezone.utc).isoformat(),
                          "evidence": "Release recipe declarations only; builds and device runtime not tested by this audit.",
                          "games": rows, "problems": problems}, indent=2))
        print(f"{len(rows)} catalog entries; {len(problems)} problem(s)", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
    else:
        print(f"\n{len(problems)} problem(s)")
        for problem in problems:
            print(f"  {problem}")
    return 1 if problems else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit the release/host/target matrix and findings as JSON")
    sys.exit(audit(json_output=parser.parse_args().json))
