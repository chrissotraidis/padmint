import io
import unittest
from unittest import mock

from padmint import cli, ui


class Page(io.BytesIO):
    def __init__(self, url, body=b""):
        super().__init__(body)
        self.url = url

    def geturl(self):
        return self.url


class LatestReleaseTests(unittest.TestCase):
    def test_uses_release_pages_not_the_api(self):
        sums = b"aa  Game-v1.2.3-ios-unsigned.ipa\nbb *Game-v1.2.3-padmint.json\n"
        pages = {
            "https://github.com/x/game/releases/latest": Page("https://github.com/x/game/releases/tag/v1.2.3"),
            "https://github.com/x/game/releases/download/v1.2.3/SHA256SUMS": Page("", sums),
        }
        with mock.patch.object(cli.tools, "open_url", side_effect=lambda url: pages[url]) as opened:
            tag, assets = cli.latest_release("https://github.com/x/game")
        self.assertEqual(tag, "v1.2.3")
        self.assertEqual(assets["Game-v1.2.3-ios-unsigned.ipa"],
                         "https://github.com/x/game/releases/download/v1.2.3/Game-v1.2.3-ios-unsigned.ipa")
        self.assertIn("Game-v1.2.3-padmint.json", assets)
        self.assertIn("SHA256SUMS", assets)
        self.assertFalse(any("api.github.com" in call.args[0] for call in opened.call_args_list))

    def test_a_latest_release_without_a_recipe_falls_back_to_the_newest_with_one(self):
        # BlueWake's latest release can be its ready-to-play Windows download, with no PadMint recipe.
        listing = (b'<a href="/x/game/releases/tag/v0.4.0">v0.4.0</a>'
                   b'<a href="/x/game/releases/tag/v0.4.0">again</a>'
                   b'<a href="/x/game/releases/tag/v0.1.0">v0.1.0</a>')
        pages = {
            "https://github.com/x/game/releases/latest": Page("https://github.com/x/game/releases/tag/v0.4.0"),
            "https://github.com/x/game/releases/download/v0.4.0/SHA256SUMS": Page("", b"aa  Game-v0.4.0-windows.zip\n"),
            "https://github.com/x/game/releases": Page("", listing),
            "https://github.com/x/game/releases/download/v0.1.0/SHA256SUMS":
                Page("", b"bb  Game-v0.1.0-ios-unsigned.ipa\ncc  Game-v0.1.0-padmint.json\n"),
        }
        with mock.patch.object(cli.tools, "open_url", side_effect=lambda url: pages[url]):
            tag, assets = cli.latest_release("https://github.com/x/game")
        self.assertEqual(tag, "v0.1.0")
        self.assertIn("Game-v0.1.0-ios-unsigned.ipa", assets)

    def test_without_a_readable_releases_page_the_latest_is_kept(self):
        pages = {
            "https://github.com/x/game/releases/latest": Page("https://github.com/x/game/releases/tag/v2"),
            "https://github.com/x/game/releases/download/v2/SHA256SUMS": Page("", b"aa  Game-v2-windows.zip\n"),
        }

        def opened(url):
            if url not in pages:
                raise RuntimeError("offline")
            return pages[url]
        with mock.patch.object(cli.tools, "open_url", side_effect=opened):
            tag, assets = cli.latest_release("https://github.com/x/game")
        self.assertEqual(tag, "v2")
        self.assertIn("Game-v2-windows.zip", assets)

    def test_no_release_yet_is_a_plain_error(self):
        page = Page("https://github.com/x/game/releases")
        with mock.patch.object(cli.tools, "open_url", return_value=page):
            with self.assertRaisesRegex(ValueError, "no published release"):
                cli.latest_release("https://github.com/x/game")


class DownloadReleaseTests(unittest.TestCase):
    def lookup(self, tags, releases):
        def opened(url):
            tag = url.rsplit("/", 1)[1]
            body = "".join(f'<a href="/x/game/releases/download/{tag}/{name}">asset</a>'
                           for name in releases[tag])
            return Page(url, body.encode())
        with mock.patch.object(cli, "release_tags", return_value=tags), \
                mock.patch.object(ui.tools, "open_url", side_effect=opened):
            return ui.release_tag("https://github.com/x/game.git", download=True)

    def test_preview_only_app_is_visible(self):
        self.assertEqual(self.lookup(["v1-preview.2"], {"v1-preview.2": {"Game.ipa": "url"}}),
                         "v1-preview.2")

    def test_newer_preview_is_visible_alongside_stable(self):
        self.assertEqual(self.lookup(["v2-preview.1", "v1"], {
            "v2-preview.1": {"Game.ipa": "url"}, "v1": {"Game.ipa": "url"}}), "v2-preview.1")

    def test_source_only_and_empty_releases_are_skipped(self):
        self.assertEqual(self.lookup(["v3", "v2", "v1"], {
            "v3": {"Source.zip": "url"}, "v2": {}, "v1": {"Game.ipa": "url"}}), "v1")

    def test_offline_or_no_ipa_has_no_update_news(self):
        self.assertIsNone(self.lookup([], {}))
        self.assertIsNone(self.lookup(["v1"], {"v1": {"Source.zip": "url"}}))

    def test_default_keeps_github_stable_selection(self):
        with mock.patch.object(ui.tools, "open_url", return_value=Page(
                "https://github.com/x/game/releases/tag/v1")), \
                mock.patch.object(cli, "release_tags") as listing:
            self.assertEqual(ui.release_tag("https://github.com/x/game"), "v1")
        listing.assert_not_called()

    def test_version_scan_uses_download_policy_only_for_download_entries(self):
        entries = {"app": {"repo_url": "https://github.com/x/app", "download": {"steps": ["Install"]}},
                   "held": {"repo_url": "https://github.com/x/held"}}
        with mock.patch.object(ui, "catalog", return_value=entries), \
                mock.patch.object(cli, "player_games", return_value=[]), \
                mock.patch.object(ui.update, "latest", return_value=None), \
                mock.patch.object(ui, "VERSIONS", {"games": {}}), \
                mock.patch.object(ui, "release_tag", return_value="v1") as lookup:
            ui.check_versions()
        lookup.assert_any_call("https://github.com/x/app", download=True)
        lookup.assert_any_call("https://github.com/x/held", download=False)


if __name__ == "__main__":
    unittest.main()
