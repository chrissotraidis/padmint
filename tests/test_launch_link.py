"""PadMint-built iPhone/iPad apps answer to padmint-<game>:// for the PadMint Library app."""
import plistlib
import tempfile
import unittest
import zipfile
from pathlib import Path

from padmint.package import add_launch_link

PLIST = "Payload/Game.app/Info.plist"


def info(path):
    with zipfile.ZipFile(path) as archive:
        return archive.read(PLIST), plistlib.loads(archive.read(PLIST))


class LaunchLinkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.ipa = Path(self.temp.name) / "game.ipa"

    def write(self, plist, fmt=plistlib.FMT_XML):
        with zipfile.ZipFile(self.ipa, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(PLIST, plistlib.dumps(plist, fmt=fmt))
            binary = zipfile.ZipInfo("Payload/Game.app/Game", (2026, 1, 2, 3, 4, 6))
            binary.external_attr = 0o100755 << 16
            archive.writestr(binary, b"\xcf\xfa\xed\xfe" + bytes(range(256)) * 64)
            link = zipfile.ZipInfo("Payload/Game.app/Frameworks/libgame.dylib", (2026, 1, 2, 3, 4, 6))
            link.external_attr = 0o120777 << 16
            archive.writestr(link, b"libgame.1.dylib")

    def entries(self):
        with zipfile.ZipFile(self.ipa) as archive:
            return {item.filename: (archive.read(item), item.external_attr, item.date_time)
                    for item in archive.infolist() if item.filename != PLIST}

    def test_adds_the_link_and_keeps_every_other_entry(self):
        self.write({"CFBundleIdentifier": "com.example.game", "CFBundleExecutable": "Game"})
        before = self.entries()
        self.assertEqual(add_launch_link(self.ipa, "SunPad"), "padmint-sunpad")
        _raw, plist = info(self.ipa)
        self.assertEqual(plist["CFBundleURLTypes"],
                         [{"CFBundleURLName": "padmint-sunpad", "CFBundleURLSchemes": ["padmint-sunpad"]}])
        self.assertEqual(plist["CFBundleIdentifier"], "com.example.game")
        self.assertEqual(self.entries(), before)  # contents, permissions and symlinks unchanged

    def test_keeps_the_apps_own_links_and_runs_once(self):
        own = {"CFBundleURLName": "darkpad", "CFBundleURLSchemes": ["darkpad"]}
        self.write({"CFBundleExecutable": "Game", "CFBundleURLTypes": [own]}, plistlib.FMT_BINARY)
        add_launch_link(self.ipa, "darkpad")
        raw, first = info(self.ipa)
        self.assertTrue(raw.startswith(b"bplist"))  # the app's plist format stays
        add_launch_link(self.ipa, "darkpad")
        self.assertEqual(info(self.ipa)[1], first)
        self.assertEqual([item["CFBundleURLSchemes"] for item in first["CFBundleURLTypes"]],
                         [["darkpad"], ["padmint-darkpad"]])
