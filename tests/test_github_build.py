"""Hosted builds use one checked public recipe before any setup commands run."""
import contextlib
import copy
import importlib.util
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("github_build", ROOT / "scripts/github-build.py")
build = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build)


class GitHubBuildTests(unittest.TestCase):
    def setUp(self):
        self.entry = {"id": "game", "repo_url": "https://github.com/example/game",
                      "github_build": True, "player_targets": ["ios"], "player_game_file": "in-app",
                      "before_build": {"commands": ["prepare-fixture"]}}
        self.recipe = {"id": "game", "name": "Game", "inputs": [{"when": "in-app"}],
                       "targets": {"ios": {"hosts": {"macos-arm64": "experimental"},
                                           "command": ["build-fixture"]}}}
        self.release = ("v1.2.3", {"game-padmint.json": "https://example.invalid/recipe"})
        for patcher in (
            mock.patch.object(build, "catalog", return_value={"game": self.entry}),
            mock.patch.object(build.cli, "latest_release", return_value=self.release),
            mock.patch.object(build.cli, "published_recipe", return_value=(self.recipe, "game v1.2.3 release")),
            mock.patch.object(build.cli, "host_id", return_value="macos-arm64"),
            mock.patch.object(build.subprocess, "run"),
            mock.patch.dict(os.environ, {}, clear=False),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_release_needing_a_game_file_stops_before_setup(self):
        self.recipe["inputs"][0]["when"] = "build"
        with self.assertRaises(ValueError):
            build.prepare("game")
        build.subprocess.run.assert_not_called()

    def test_missing_or_invalid_published_recipe_cannot_use_catalog_fallback(self):
        build.cli.published_recipe.return_value = (self.recipe, "PadMint's built-in copy")
        with self.assertRaisesRegex(ValueError, "published recipe"):
            build.prepare("game")
        build.subprocess.run.assert_not_called()

    def test_wrong_host_stops_before_setup(self):
        build.cli.host_id.return_value = "windows-x86_64"
        with self.assertRaisesRegex(ValueError, "unsupported"):
            build.prepare("game")
        build.subprocess.run.assert_not_called()

    def test_new_cargo_install_is_available_to_current_and_later_steps(self):
        with tempfile.TemporaryDirectory(prefix="github home ") as folder:
            home = Path(folder)
            cargo = home / ".cargo/bin"
            cargo.mkdir(parents=True)
            github_path = home / "github-path"
            with mock.patch.object(build.Path, "home", return_value=home), \
                    mock.patch.dict(os.environ, {"PATH": "original-path", "GITHUB_PATH": str(github_path)}):
                self.assertEqual(build.prepare("game"), self.release)
                self.assertEqual(os.environ["PATH"], str(cargo) + os.pathsep + "original-path")
                self.assertEqual(github_path.read_text(), str(cargo) + "\n")

    def test_build_uses_checked_release_and_preserves_output_path(self):
        with tempfile.TemporaryDirectory(prefix="hosted build ") as folder, \
                mock.patch.object(build.cli, "make", return_value=23) as make:
            os.environ["CI"] = "true"
            os.environ["GITHUB_SHA"] = "padmint-commit"
            self.assertEqual(build.main(["game", "--out", folder]), 23)
            make.assert_called_once_with("game", "ios", None, Path(folder).resolve(), release=self.release)
        self.assertNotIn("CI", os.environ)
        self.assertNotIn("GITHUB_SHA", os.environ)
        build.cli.latest_release.assert_called_once()
        build.subprocess.run.assert_called_once()

    def test_private_dispatch_refuses_public_or_unknown_visibility_before_setup(self):
        self.entry["github_build_private"] = True
        for visibility in ("false", "", "TRUE"):
            with self.subTest(visibility=visibility), mock.patch.dict(os.environ, {
                    "GITHUB_EVENT_NAME": "workflow_dispatch", "PADMINT_REPOSITORY_PRIVATE": visibility}):
                with self.assertRaisesRegex(ValueError, "private repository"):
                    build.prepare("game")
        build.cli.latest_release.assert_not_called()
        build.subprocess.run.assert_not_called()

    def test_private_dispatch_and_non_uploading_ci_can_build(self):
        self.entry["github_build_private"] = True
        for event, visibility in (("workflow_dispatch", "true"), ("pull_request", "false"), ("schedule", "false")):
            with self.subTest(event=event), mock.patch.dict(os.environ, {
                    "GITHUB_EVENT_NAME": event, "PADMINT_REPOSITORY_PRIVATE": visibility}):
                self.assertEqual(build.prepare("game"), self.release)

    def test_matrix_uses_catalog_and_refuses_unlisted_selection(self):
        extra = copy.deepcopy(self.entry)
        extra["github_build"] = False
        build.catalog.return_value["local-only"] = extra
        self.assertEqual(build.matrix(), {"game": ["game"]})
        self.assertEqual(build.matrix("game"), {"game": ["game"]})
        with self.assertRaises(ValueError):
            build.matrix("local-only")
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(build.main(["--matrix", ""]), 0)
        self.assertEqual(output.getvalue().strip(), '{"game": ["game"]}')
        build.cli.latest_release.assert_not_called()
        build.subprocess.run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
