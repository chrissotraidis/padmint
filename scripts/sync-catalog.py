#!/usr/bin/env python3
"""Write library.json and the app's Info.plist from PadMint's catalog.

Usage: scripts/sync-catalog.py [PADMINT_CHECKOUT]   (default: ../padmint)

The library lists only games in PadMint's catalog (Chris's own ports). PadMint-built
iPhone/iPad apps answer to padmint-<game>:// (padmint#242). The app may only ask iOS
whether a link is installed for links its Info.plist declares, and iOS 27 answers for
the first 25 of those only (measured in the simulator, 7 November 2026). Opening a link
needs no declaration, so games past the first 25 are found when the player opens them.
"""
import json
import plistlib
import re
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = "https://raw.githubusercontent.com/chrissotraidis/padmint/main/art/{id}.png"
BOX_ART = "https://thumbnails.libretro.com/{system}/Named_Boxarts/{name}.png"
CHECKED_LINKS = 25


def box_art(cover):
    """The download link for a covers.json entry; libretro replaces &*/:`<>?\\|" with _."""
    if not cover:
        return None
    name = re.sub(r'[&*/:`<>?\\|"]', "_", cover["name"])
    return BOX_ART.format(system=urllib.parse.quote(cover["system"], safe=""),
                          name=urllib.parse.quote(name, safe=""))


def games(padmint, covers):
    found = []
    for path in sorted((padmint / "catalog").glob("*.json")):
        entry = json.loads(path.read_text(encoding="utf-8"))
        built = "ios" in (entry.get("player_targets") or [])
        ready_made = bool(entry.get("download"))
        if entry.get("later") or not (built or ready_made):
            continue  # paused, or not an iPhone/iPad app
        found.append({
            "id": entry["id"],
            "name": (entry.get("manifest") or {}).get("name") or entry.get("name") or entry["id"],
            "game": entry["game"],
            "repo": entry["repo_url"],
            "art": ART.format(id=entry["id"]),
            # Downloaded by the app only after the player agrees; never stored here.
            "box_art": box_art(covers.get(entry["id"])),
            # Ready-made apps aren't built by PadMint, so they answer to no link yet.
            "link": f"padmint-{entry['id']}" if built else None,
        })
    return found


def main():
    padmint = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT.parent / "padmint").resolve()
    covers = json.loads((ROOT / "covers.json").read_text(encoding="utf-8"))["covers"]
    listed = games(padmint, covers)
    links = [game["link"] for game in listed if game["link"]][:CHECKED_LINKS]
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
