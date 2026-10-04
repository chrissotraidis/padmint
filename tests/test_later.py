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


if __name__ == "__main__":
    unittest.main()
