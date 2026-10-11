"""Games listed so players can find them, with nothing to build or download yet."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from padmint import manifest, ui


class LaterTests(unittest.TestCase):
    def test_listed_games_reach_the_page_in_the_players_language(self):
        later = {game["id"]: game for game in ui.player_data("es")["later"]}
        self.assertIn("galaxypad", later)
        self.assertIn("snappad", later)
        self.assertEqual(later["galaxypad"]["about"], "Super Mario Galaxy (Wii)")
        self.assertIn("no están publicadas", later["galaxypad"]["text"])
        self.assertTrue(later["ratouch"]["link"].startswith("https://github.com/chrissotraidis/ratouch"))

    def test_a_listed_game_cannot_also_be_built_or_downloaded(self):
        entry = json.loads((manifest.CATALOG / "galaxypad.json").read_text())
        for change in ({"player_targets": ["ios"], "free_space_gb": 10},
                       {"download": {"steps": ["x"]}}, {"later": {}}):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as folder:
                Path(folder, "galaxypad.json").write_text(json.dumps(dict(entry, **change)))
                with mock.patch.object(manifest, "CATALOG", Path(folder)), self.assertRaises(ValueError):
                    manifest.catalog()

    def test_games_this_computer_cannot_make_are_listed_with_the_reason(self):
        from padmint import cli
        with mock.patch.object(cli, "host_id", return_value="windows-x86_64"), \
                mock.patch.object(cli, "on_android", return_value=False):
            data = ui.player_data("en")
        built = {game["id"] for game in data["games"]}
        waiting = {game["id"]: game for game in data["later"]}
        self.assertIn("kartpad", built)
        self.assertNotIn("bellpad", built)
        self.assertIn("Apple Silicon", waiting["bellpad"]["text"])
        self.assertEqual(waiting["bellpad"]["tag"], "Needs an M1+ Mac")
        self.assertEqual(waiting["bellpad"]["about"], "Animal Crossing (GameCube)")
        everything = built | set(waiting) | {app["id"] for app in data["downloads"]}
        self.assertEqual(everything, set(manifest.catalog()))

    def test_a_device_held_back_is_shown_on_the_computer_that_would_make_it(self):
        # KartPad's Mac copy isn't offered yet: an Apple Silicon Mac says so in step 3,
        # instead of only showing Android and iPhone/iPad (Discord, 12 Oct 2026).
        from padmint import cli
        for host, held in (("macos-arm64", ["macos"]), ("macos-x86_64", []), ("windows-x86_64", [])):
            with self.subTest(host=host), mock.patch.object(cli, "host_id", return_value=host), \
                    mock.patch.object(cli, "on_android", return_value=False):
                kartpad = {game["id"]: game for game in ui.player_data("en")["games"]}["kartpad"]
            self.assertEqual([item["id"] for item in kartpad["held"]], held)
        self.assertEqual(kartpad["held"], [])
        with mock.patch.object(cli, "host_id", return_value="macos-arm64"), \
                mock.patch.object(cli, "on_android", return_value=False):
            kartpad = {game["id"]: game for game in ui.player_data("es")["games"]}["kartpad"]
        self.assertEqual(kartpad["held"][0]["label"], "Este Mac")
        self.assertEqual(kartpad["held"][0]["text"],
                         "PadMint todavía no crea KartPad para Mac. Para jugar ahora, elige Android o iPhone/iPad.")


if __name__ == "__main__":
    unittest.main()
