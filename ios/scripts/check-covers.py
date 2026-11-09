#!/usr/bin/env python3
"""Check that every box-art link in covers.json loads as an image, and print its shape.
libretro links are checked on GitHub too: the app falls back to that copy (Covers.swift).

Usage: scripts/check-covers.py   (exits 1 when a link fails)
"""
import json
import struct
import sys
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def size(data):
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", data[16:24])
    i = 2
    while i + 9 < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker, length = data[i + 1], struct.unpack(">H", data[i + 2:i + 4])[0]
        if marker in (0xC0, 0xC1, 0xC2):
            height, width = struct.unpack(">HH", data[i + 5:i + 9])
            return width, height
        i += 2 + length
    raise ValueError("not a PNG or JPEG")


def mirror(url):
    """The GitHub copy of a libretro thumbnail, as CoverStore.libretroMirror builds it."""
    parts = urllib.parse.urlsplit(url)
    if parts.netloc != "thumbnails.libretro.com":
        return None
    system, folder, name = parts.path.strip("/").split("/")
    system = urllib.parse.quote(urllib.parse.unquote(system).replace(" ", "_"))
    return f"https://raw.githubusercontent.com/libretro-thumbnails/{system}/master/{folder}/{name}"


def load(url):
    request = urllib.request.Request(url, headers={"User-Agent": "PadMintLibrary"})
    return size(urllib.request.urlopen(request, timeout=30).read())


def check(item):
    game, entry = item
    lines, ok = [], True
    for label, url in (("", entry["box_art"]), (" (GitHub copy)", mirror(entry["box_art"])),
                       (" back", entry.get("box_back")), (" spine", entry.get("box_spine"))):
        if url is None:
            continue
        try:
            width, height = load(url)
            lines.append(f"{game + label:28} {width}x{height} {width / height:.2f}")
        except Exception as error:  # noqa: BLE001 - report every failure
            lines.append(f"{game + label:28} FAILED {error}")
            ok = False
    return "\n".join(lines), ok


def main():
    games = json.loads((ROOT / "covers.json").read_text(encoding="utf-8"))["games"]
    for entry in list(games.values()):
        games.update({extra["id"]: extra for extra in entry.get("also", [])})
    with ThreadPoolExecutor(8) as pool:
        results = list(pool.map(check, sorted(games.items())))
    for line, _ok in results:
        print(line)
    sys.exit(0 if all(ok for _line, ok in results) else 1)


if __name__ == "__main__":
    main()
