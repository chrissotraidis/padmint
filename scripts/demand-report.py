#!/usr/bin/env python3
"""Demand per game, from GitHub: stars, recent visitors and player downloads.

Usage: scripts/demand-report.py            (needs the gh CLI, signed in)

Player downloads add up every release asset a player installs (APK, IPA, Mac,
Windows and Linux builds). Recipes and checksums are left out: PadMint's own
catalog audit downloads them on every run. IPA counts include the code-free
apps PadMint downloads while it builds, so they are an upper bound for players.
Visitors are GitHub's 14-day unique visitors, which needs push access to the repo.
"""
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
OWNER = "chrissotraidis"


def gh(*args):
    run = subprocess.run(["gh", *args], capture_output=True, text=True)
    return run.stdout.strip() if run.returncode == 0 else ""


def kind(name):
    name = name.lower()
    if name.endswith("padmint.json") or name == "sha256sums":
        return None
    if name.endswith(".apk"):
        return "android"
    if name.endswith(".ipa"):
        return "ios"
    if "windows" in name or "win64" in name or name.endswith(".exe"):
        return "windows"
    if "linux" in name or name.endswith(".appimage"):
        return "linux"
    if "mac" in name or name.endswith(".dmg"):
        return "mac"
    return None


def main():
    repos = {}
    for path in sorted((ROOT / "catalog").glob("*.json")):
        repos[path.stem] = json.loads(path.read_text())["repo_url"].rstrip("/").split("/")[-1]
    repos["padmint"] = "padmint"
    rows = []
    for game, repo in repos.items():
        info = json.loads(gh("api", f"repos/{OWNER}/{repo}") or "{}")
        counts = {"ios": 0, "android": 0, "mac": 0, "windows": 0, "linux": 0}
        pages = gh("api", f"repos/{OWNER}/{repo}/releases?per_page=100", "--paginate", "-q", ".[].assets[] | [.name, .download_count]")
        for line in pages.splitlines():
            name, count = json.loads(line)
            if kind(name):
                counts[kind(name)] += count
        visitors = gh("api", f"repos/{OWNER}/{repo}/traffic/views", "-q", ".uniques") or "?"
        rows.append((info.get("stargazers_count", 0), game, visitors, counts))
    print("| Game | Stars | Visitors, 14 days | iPhone/iPad | Android | Mac | Windows | Linux |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|")
    for stars, game, visitors, c in sorted(rows, key=lambda row: -row[0]):
        print(f"| {game} | {stars} | {visitors} | {c['ios']} | {c['android']} | {c['mac']} | {c['windows']} | {c['linux']} |")


if __name__ == "__main__":
    main()

