"""PadMint lists only Chris's own game ports (AGENTS.md: "Only Chris's own games")."""
import unittest
import json
import tempfile
from pathlib import Path
from unittest import mock

from padmint import manifest

OWNER = "https://github.com/chrissotraidis/"
# Recipe-only wrappers around other people's projects were removed and must not return.
NOT_OURS = {"melee-pc", "melee-pc-padmint"}


class OwnershipTests(unittest.TestCase):
    def test_every_entry_is_a_chrissotraidis_game_repository(self):
        for game, entry in manifest.catalog().items():
            with self.subTest(game=game):
                self.assertTrue(entry["repo_url"].startswith(OWNER), entry["repo_url"])
                self.assertNotIn(game, NOT_OURS)
                self.assertNotIn(entry["repo_url"].rstrip("/").rsplit("/", 1)[-1], NOT_OURS)

    def test_other_ports_only_name_our_own_catalog_games(self):
        games = manifest.catalog()
        for game, entry in games.items():
            for port in entry.get("other_ports", []):
                with self.subTest(game=game, port=port):
                    self.assertIn(port, games)
                    self.assertTrue(games[port]["repo_url"].startswith(OWNER))

    def test_the_build_workflow_offers_no_removed_project(self):
        workflow = (manifest.CATALOG.parent / ".github/workflows/build-for-iphone.yml").read_text()
        for name in NOT_OURS:
            self.assertNotIn(name, workflow)


class LocalRecipeOwnershipTests(unittest.TestCase):
    def test_removed_games_are_rejected_before_reading_a_local_recipe(self):
        for game in NOT_OURS:
            with self.subTest(game=game), \
                    mock.patch.object(manifest, "repository_manifest") as read:
                with self.assertRaisesRegex(ValueError, "was removed"):
                    manifest.manifest_for(game, Path("synthetic-checkout"))
                read.assert_not_called()

    def test_removed_games_are_rejected_without_a_checkout_too(self):
        for game in NOT_OURS:
            with self.subTest(game=game), self.assertRaisesRegex(ValueError, "was removed"):
                manifest.manifest_for(game)

    def test_new_local_recipe_development_still_works_in_both_formats(self):
        recipe = dict(manifest.catalog()["kartpad"]["manifest"], id="synthetic-own-port")
        for filename in ("padmint.json", "padforge.json"):
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as folder:
                Path(folder, filename).write_text(json.dumps(recipe))
                found, source = manifest.manifest_for("synthetic-own-port", folder)
                self.assertEqual(found["id"], "synthetic-own-port")
                self.assertEqual(source, "repository")


if __name__ == "__main__":
    unittest.main()
