"""A game's README can ask Mac players to install programs once (Homebrew); the page shows
the same lines before the build, with what is already installed (catalog "before_build")."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from padmint import cli, manifest


class BeforeBuildTests(unittest.TestCase):
    def test_lines_and_installed_packages_on_a_mac(self):
        with tempfile.TemporaryDirectory() as folder:
            brew = Path(folder, "bin", "brew")
            brew.parent.mkdir()
            brew.touch()
            Path(folder, "opt", "cmake").mkdir(parents=True)
            with mock.patch.object(cli, "host_id", return_value="macos-arm64"), \
                    mock.patch.object(cli.shutil, "which", return_value=str(brew)):
                before = cli.before_build("ballpad")
        self.assertEqual(before["commands"], ["brew install cmake ninja ripgrep"])
        self.assertTrue(before["homebrew"])
        self.assertEqual(before["packages"], [{"name": "cmake", "ok": True}, {"name": "ninja", "ok": False},
                                              {"name": "ripgrep", "ok": False}])

    def test_no_homebrew_and_other_computers(self):
        with mock.patch.object(cli, "host_id", return_value="macos-arm64"), \
                mock.patch.object(cli.shutil, "which", return_value=None):
            before = cli.before_build("ballpad")
        self.assertFalse(before["homebrew"])
        self.assertFalse(any(package["ok"] for package in before["packages"]))
        with mock.patch.object(cli, "host_id", return_value="windows-x86_64"):
            self.assertIsNone(cli.before_build("ballpad"))
        self.assertIsNone(cli.before_build("kartpad"))

    def test_only_games_players_build_carry_a_list_of_lines(self):
        for name, change in (("ballpad", {"before_build": {"commands": []}}),
                             ("ballpad", {"before_build": {"commands": ["brew install x"], "extra": 1}}),
                             ("ballpad", {"before_build": ["brew install x"]}),
                             ("caesarpad", {"before_build": {"commands": ["brew install x"]}})):
            entry = json.loads((manifest.CATALOG / f"{name}.json").read_text())
            with self.subTest(name=name, change=change), tempfile.TemporaryDirectory() as folder:
                Path(folder, f"{name}.json").write_text(json.dumps(dict(entry, **change)))
                with mock.patch.object(manifest, "CATALOG", Path(folder)), self.assertRaises(ValueError):
                    manifest.catalog()


if __name__ == "__main__":
    unittest.main()
