#!/usr/bin/env python3
"""Check that every box-art link in covers.json loads as an image, and print its shape.

Usage: scripts/check-covers.py   (exits 1 when a link fails)
"""
import json
import struct
import sys
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


def check(item):
    game, entry = item
    try:
        request = urllib.request.Request(entry["box_art"], headers={"User-Agent": "PadMintLibrary"})
        width, height = size(urllib.request.urlopen(request, timeout=30).read())
        return f"{game:14} {width}x{height} {width / height:.2f}", True
    except Exception as error:  # noqa: BLE001 - report every failure
        return f"{game:14} FAILED {error}", False


def main():
    games = json.loads((ROOT / "covers.json").read_text(encoding="utf-8"))["games"]
    with ThreadPoolExecutor(8) as pool:
        results = list(pool.map(check, sorted(games.items())))
    for line, _ok in results:
        print(line)
    sys.exit(0 if all(ok for _line, ok in results) else 1)


if __name__ == "__main__":
    main()
