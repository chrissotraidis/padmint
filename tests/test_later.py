"""Games listed so players can find them, with nothing to build or download yet."""
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest import mock

from padmint import manifest, ui


class LaterTests(unittest.TestCase):
    LISTED = {"schema_version": 1, "id": "somepad", "name": "SomePad", "game": "Some Game (N64)",
              "repo_url": "https://github.com/chrissotraidis/somepad", "plays_on": ["ipad"],
              "later": {"status": "paused", "text": "Downloads are paused.",
                        "translations": {"es": {"text": "Las descargas están en pausa."}}},
              "manifest": None}

    def test_listed_games_reach_the_page_in_the_players_language(self):
        with tempfile.TemporaryDirectory() as folder:
            for name in ("somepad", "ratouch"):
                entry = self.LISTED if name == "somepad" else json.loads((manifest.CATALOG / "ratouch.json").read_text())
                Path(folder, f"{name}.json").write_text(json.dumps(entry))
            with mock.patch.object(manifest, "CATALOG", Path(folder)):
                data = ui.player_data("es")
        later = {game["id"]: game for game in data["later"]}
        self.assertEqual(later["somepad"]["about"], "Some Game (N64)")
        self.assertEqual(later["somepad"]["status"], "paused")
        self.assertIn("están en pausa", later["somepad"]["text"])
        self.assertTrue(later["somepad"]["link"].startswith("https://github.com/chrissotraidis/somepad"))
        downloads = {app["id"]: app for app in ui.player_data("es")["downloads"]}
        self.assertIn("RAtouch-v0.1.0-unsigned.ipa", downloads["ratouch"]["steps"][0])

    def test_a_listed_game_cannot_also_be_built_or_downloaded(self):
        entry = self.LISTED
        for change in ({"player_targets": ["ios"], "free_space_gb": 10},
                       {"download": {"steps": ["x"]}}, {"later": {}}):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as folder:
                Path(folder, "somepad.json").write_text(json.dumps(dict(entry, **change)))
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
        self.assertNotIn("sunpad", built)
        self.assertIn("Apple Silicon", waiting["sunpad"]["text"])
        self.assertEqual(waiting["sunpad"]["tag"], "Needs Apple Silicon Mac")
        self.assertEqual(waiting["sunpad"]["about"], "Super Mario Sunshine (GameCube)")
        # A game that takes its game file in the app points to GitHub Cloud Build instead.
        self.assertNotIn("bellpad", built)
        self.assertEqual(waiting["bellpad"]["tag"], "GitHub Cloud Build")
        self.assertIn("pick bellpad", waiting["bellpad"]["text"])
        self.assertEqual(waiting["bellpad"]["link"], ui.GITHUB_BUILD_HELP)
        self.assertTrue(waiting["bellpad"]["github"])
        self.assertEqual(len(waiting["bellpad"]["steps"]), 5)
        self.assertIn("pick bellpad", waiting["bellpad"]["steps"][2])
        self.assertFalse(waiting["sunpad"]["github"])
        self.assertEqual(waiting["melee-pc"]["tag"], "GitHub Cloud Build")
        self.assertIn("private", waiting["melee-pc"]["text"])
        self.assertTrue(waiting["melee-pc"]["github"])
        self.assertTrue(waiting["melee-pc"]["cloud"]["private"])
        self.assertEqual(waiting["melee-pc"]["steps"], [])  # No public-fork instructions.
        self.assertIn("#build-on-github-without-a-mac", waiting["melee-pc"]["link"])
        everything = built | set(waiting) | {app["id"] for app in data["downloads"]}
        self.assertEqual(everything, set(manifest.catalog()))
        self.assertEqual(data["host_name"], "Windows x64")
        self.assertEqual(data["text"]["tab_build"], "Build here")
        self.assertEqual(data["text"]["tab_github"], "GitHub Cloud Build")
        self.assertEqual(data["text"]["other_routes_head"], "Other routes")
        self.assertEqual(data["text"]["github_build_tag"], "GitHub Cloud Build")
        self.assertEqual(data["text"]["needs_mac_head"], "Apple Silicon Mac")
        self.assertEqual(sum(item.get("github", False) for item in data["later"]), 16)
        self.assertIn("not a local Windows build", waiting["bellpad"]["text"])
        self.assertIn("not Windows desktop games", data["text"]["here_other_hosts"])
        self.assertIn("this computer only starts the workflow", data["text"]["github_note"])
        self.assertIn("None of these is a Windows desktop build", data["text"]["needs_mac_note"])
        self.assertEqual(waiting["bluewake"]["tag"], "Windows app available")
        self.assertIn("BlueWake.exe", waiting["bluewake"]["text"])

    def test_melee_normal_build_routes_preserve_recipe_identity_on_each_host(self):
        from padmint import cli
        for host in ("macos-arm64", "macos-x86_64", "windows-x86_64", "linux-x86_64"):
            with self.subTest(host=host), mock.patch.object(cli, "host_id", return_value=host), \
                    mock.patch.object(cli, "on_android", return_value=False):
                data = ui.player_data("en")
                games = {x["id"]: x for x in data["games"] + data["later"]}
                self.assertEqual(games["meleepad"]["other_ports"], [{"id": "melee-pc", "name": "Melee PC", "github": True}])
                self.assertEqual(games["melee-pc"]["other_ports"], [{"id": "meleepad", "name": "MeleePad", "github": False}])
                self.assertIsNone(games["meleepad"]["cloud"])  # Never label Melee PC as a MeleePad build.
                cloud = games["melee-pc"]["cloud"]
                self.assertTrue(cloud["private"])
                self.assertEqual(cloud["url"], "https://github.com/chrissotraidis/melee-pc-padmint#build-on-github-without-a-mac")
                self.assertIn("private", cloud["text"])
                self.assertIn("Melee", games["melee-pc"]["about"])
                self.assertNotIn("save-fix", json.dumps(games))
                self.assertNotIn("notice", games["meleepad"])
                self.assertFalse(games["bellpad"]["cloud"]["private"])
                self.assertEqual(games["bellpad"]["other_ports"], [])

    def test_github_builds_match_the_workflow_and_need_no_game_file_while_building(self):
        # The workflow's game menu is the catalog's github_build list; a game that reads
        # the player's game file while building must never be offered there.
        import re
        workflow = (manifest.CATALOG.parent / ".github/workflows/build-for-iphone.yml").read_text()
        menu = re.search(r"options:\n((?:\s+- \S+\n)+)", workflow).group(1).split()
        menu = [item for item in menu if item != "-"]
        marked = sorted(game for game, entry in manifest.catalog().items() if entry.get("github_build"))
        self.assertEqual(menu, marked)
        for game in marked:
            entry = manifest.catalog()[game]
            self.assertIn("ios", entry["player_targets"], game)
            self.assertEqual(entry["player_game_file"], "in-app", game)
            self.assertEqual(bool(entry.get("off_mac")), bool(entry.get("github_build_private")), game)

    def test_a_device_held_back_is_shown_on_the_computer_that_would_make_it(self):
        # A Mac copy PadMint holds back (KartPad's, before 0.8.0) is shown dimmed in step 3 on
        # an Apple Silicon Mac, instead of only Android and iPhone/iPad (Discord, 12 Oct 2026).
        from padmint import cli
        entry = json.loads((manifest.CATALOG / "kartpad.json").read_text())
        entry["player_targets"] = [target for target in entry["player_targets"] if target != "macos"]
        entry["unoffered_targets"] = {"macos": "held back for this test"}
        entry["player_next"].pop("macos", None)
        entry.pop("free_space_gb_by_target", None)
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, "kartpad.json").write_text(json.dumps(entry))
            with mock.patch.object(manifest, "CATALOG", Path(folder)), \
                    mock.patch.object(cli, "on_android", return_value=False):
                for host, held in (("macos-arm64", ["macos"]), ("macos-x86_64", ["macos"]), ("windows-x86_64", [])):
                    with self.subTest(host=host), mock.patch.object(cli, "host_id", return_value=host):
                        kartpad = ui.player_data("en")["games"][0]
                        self.assertEqual([item["id"] for item in kartpad["held"]], held)
                with mock.patch.object(cli, "host_id", return_value="macos-arm64"):
                    kartpad = ui.player_data("es")["games"][0]
        self.assertEqual(kartpad["held"][0]["label"], "Este Mac")
        self.assertEqual(kartpad["held"][0]["text"],
                         "PadMint todavía no crea KartPad para Mac. Para jugar ahora, elige Android o iPhone/iPad.")

    def test_kartpad_offers_this_mac_on_apple_silicon_only(self):
        from padmint import cli
        for host, has_mac in (("macos-arm64", True), ("macos-x86_64", False), ("windows-x86_64", False)):
            with self.subTest(host=host), mock.patch.object(cli, "host_id", return_value=host), \
                    mock.patch.object(cli, "on_android", return_value=False):
                kartpad = {game["id"]: game for game in ui.player_data("en")["games"]}["kartpad"]
            self.assertEqual("macos" in [p["id"] for p in kartpad["platforms"]], has_mac)
            if host == "macos-x86_64":
                self.assertEqual([p["id"] for p in kartpad["held"]], ["macos"])
                self.assertEqual(kartpad["held"][0]["tag"], "Requires Apple Silicon")
                self.assertIn("cannot run on an Intel Mac", kartpad["held"][0]["text"])
                self.assertEqual([p["id"] for p in kartpad["platforms"]], ["android", "ios"])
            else:
                self.assertEqual(kartpad["held"], [])

    def test_every_advertised_mac_copy_is_available_or_explained_on_a_mac(self):
        # Use the shipped catalog, not a fixture with only mobile targets. This protects
        # every game from disappearing choices when host policy or the catalog changes.
        from padmint import cli
        advertised = {game for game, entry in manifest.catalog().items()
                      if "macos" in entry.get("player_targets", [])}
        self.assertIn("kartpad", advertised)
        for host in ("macos-arm64", "macos-x86_64"):
            with self.subTest(host=host), mock.patch.object(cli, "host_id", return_value=host), \
                    mock.patch.object(cli, "on_android", return_value=False):
                data = ui.player_data("en")
            available = {game["id"]: game for game in data["games"]}
            elsewhere = {game["id"]: game for game in data["later"]}
            for game in advertised:
                with self.subTest(host=host, game=game):
                    if game in available:
                        choices = available[game]["platforms"] + available[game]["held"]
                        self.assertEqual(sum(p["id"] == "macos" for p in choices), 1)
                        for choice in available[game]["held"]:
                            self.assertTrue(choice["text"])
                            self.assertTrue(choice["tag"])
                    else:
                        self.assertIn("Apple Silicon", elsewhere[game]["text"])

    def test_intel_explanation_is_translated(self):
        from padmint import cli
        for lang in ("en", "es", "pt"):
            with self.subTest(lang=lang), mock.patch.object(cli, "host_id", return_value="macos-x86_64"), \
                    mock.patch.object(cli, "on_android", return_value=False):
                kartpad = next(g for g in ui.player_data(lang)["games"] if g["id"] == "kartpad")
            self.assertIn("Intel", kartpad["held"][0]["text"])
            self.assertIn("Apple Silicon", kartpad["held"][0]["tag"])

    def test_intel_mac_choice_cannot_start_a_build_even_with_a_direct_request(self):
        from padmint import cli
        server = ThreadingHTTPServer(("127.0.0.1", 0), ui.make_handler("test-token", ui.Builds()))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        base = f"http://127.0.0.1:{server.server_address[1]}"
        with mock.patch.object(cli, "host_id", return_value="macos-x86_64"), \
                mock.patch.object(cli, "on_android", return_value=False), \
                mock.patch.object(ui.Builds, "start") as build:
            for route, body in (("/api/plan?game=kartpad&platform=macos", None),
                                ("/api/make", json.dumps({"game": "kartpad", "platform": "macos"}).encode())):
                request = urllib.request.Request(base + route, data=body,
                                                 headers={"X-PadMint-Token": "test-token"})
                with self.subTest(route=route), self.assertRaises(urllib.error.HTTPError) as error:
                    urllib.request.urlopen(request, timeout=5)
                self.assertEqual(error.exception.code, 400)
                error.exception.close()
        build.assert_not_called()


if __name__ == "__main__":
    unittest.main()
