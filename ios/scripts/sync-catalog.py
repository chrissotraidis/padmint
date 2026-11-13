#!/usr/bin/env python3
"""Write library.json and the app's Info.plist from PadMint's catalog.

Usage: ios/scripts/sync-catalog.py   (reads the catalog of the PadMint checkout it is in)

The library lists only games in PadMint's catalog (Chris's own ports). PadMint-built
iPhone/iPad apps answer to padmint-<game>:// (padmint#242). The app may only ask iOS
whether a link is installed for links its Info.plist declares, and iOS 27 answers for
the first 25 of those only (measured in the simulator, 7 November 2026). Opening a link
needs no declaration, so games past the first 25 are found when the player opens them.
"""
import json
import plistlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = "https://raw.githubusercontent.com/chrissotraidis/padmint/main/art/{id}.png"
CHECKED_LINKS = 25


def games(padmint, covers):
    found = []
    missing = []
    for path in sorted((padmint / "catalog").glob("*.json")):
        entry = json.loads(path.read_text(encoding="utf-8"))
        built = "ios" in (entry.get("player_targets") or [])
        ready_made = bool(entry.get("download"))
        if entry.get("later") or not (built or ready_made):
            continue  # paused, or not an iPhone/iPad app
        cover = covers.get(entry["id"])
        if not cover:
            missing.append(entry["id"])
            continue
        game = {
            "id": entry["id"],
            "name": (entry.get("manifest") or {}).get("name") or entry.get("name") or entry["id"],
            "title": cover["title"],
            "platform": cover["platform"],
            "game": entry["game"],
            "repo": entry["repo_url"],
            "art": ART.format(id=entry["id"]),
            # Downloaded by the app only after the player agrees; never stored here.
            "box_art": cover["box_art"],
            "box_back": cover.get("box_back"),
            "box_spine": cover.get("box_spine"),
            # Ready-made apps aren't built by PadMint, so they answer to no link yet.
            "link": f"padmint-{entry['id']}" if built else None,
        }
        found.append(game)
        # One app holding several games (TribesPad: Starsiege: Tribes, Tribes 2 and
        # Tribes: Vengeance) lists each game; they share the app, its link and its art.
        for extra in cover.get("also", []):
            found.append({**game, **{key: extra.get(key) for key in ("id", "title", "box_art", "box_back", "box_spine")}})
    if missing:
        raise SystemExit("add these games to covers.json (title, platform, box_art): " + ", ".join(missing))
    return found


def main():
    padmint = ROOT.parent
    covers = json.loads((ROOT / "covers.json").read_text(encoding="utf-8"))["games"]
    listed = games(padmint, covers)
    links = list(dict.fromkeys(game["link"] for game in listed if game["link"]))[:CHECKED_LINKS]
    for game in listed:
        game["checked"] = game["link"] in links
    (ROOT / "library.json").write_text(json.dumps({"schema_version": 1, "games": listed},
                                                  indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    info = {
        "CFBundleDevelopmentRegion": "en",
        "CFBundleDisplayName": "PadMint",
        "CFBundleExecutable": "$(EXECUTABLE_NAME)",
        "CFBundleIdentifier": "$(PRODUCT_BUNDLE_IDENTIFIER)",
        "CFBundleInfoDictionaryVersion": "6.0",
        "CFBundleName": "$(PRODUCT_NAME)",
        "CFBundlePackageType": "APPL",
        "CFBundleShortVersionString": "$(MARKETING_VERSION)",
        "CFBundleVersion": "$(CURRENT_PROJECT_VERSION)",
        "LSApplicationQueriesSchemes": links,
        # The library can be used with a game controller (ios/Sources/Controller.swift).
        "GCSupportsControllerUserInteraction": True,
        "GCSupportedGameControllers": [{"ProfileName": "ExtendedGamepad"}],
        "LSRequiresIPhoneOS": True,
        "UIApplicationSceneManifest": {"UIApplicationSupportsMultipleScenes": False},
        "UILaunchScreen": {},
        "UISupportedInterfaceOrientations": ["UIInterfaceOrientationPortrait",
                                             "UIInterfaceOrientationLandscapeLeft",
                                             "UIInterfaceOrientationLandscapeRight"],
        "UISupportedInterfaceOrientations~ipad": ["UIInterfaceOrientationPortrait",
                                                  "UIInterfaceOrientationPortraitUpsideDown",
                                                  "UIInterfaceOrientationLandscapeLeft",
                                                  "UIInterfaceOrientationLandscapeRight"],
    }
    with (ROOT / "Sources/Info.plist").open("wb") as stream:
        plistlib.dump(info, stream, sort_keys=True)
    print(f"{len(listed)} games, {len(links)} checked links, from {padmint}")


if __name__ == "__main__":
    main()
