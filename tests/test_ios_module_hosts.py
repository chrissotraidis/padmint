"""A portable module route must preserve the game's existing full-app builder."""
import argparse
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

from padmint import cli, ios_module, manifest, ui
from padmint.package import add_launch_link
from fixtures import entries, write_ipa


def recipe():
    return {"schema_version": 2, "id": "hostpad", "name": "HostPad", "game": "Synthetic",
            "kind": "disc-translation", "status": "experimental", "inputs": [{"type": "disc"}],
            "targets": {"ios": {"hosts": {host: "experimental" for host in manifest.HOSTS},
                "tools": ["libcxx"], "output": "ipa", "check": "ipa",
                "published_app": "HostPad-v{version}.ipa",
                "ios_module": {"result": "{work}/module-result.json", "on": ["windows", "linux"]},
                "command": ["{python}", "{repo}/builder.py", "{app}", "{output}", "{work}"],
                "modes": {"full": ["--train-pgo"], "source-only": ["--source-only"]},
                "options": {"no-mods": ["--no-mods"]}}},
            "publication": {"public_binaries": False}}


class ModuleHostTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="PadMint module hosts ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.recipe = manifest.validate_manifest(recipe())
        self.target = self.recipe["targets"]["ios"]

    def test_selection_and_omitted_selection_on_every_supported_host(self):
        for host in manifest.HOSTS:
            with self.subTest(host=host):
                self.assertEqual(bool(manifest.module_here(self.target, host)), not host.startswith("macos-"))
                with mock.patch.object(manifest, "host_id", return_value=host):
                    self.assertEqual(manifest.module_here(self.target), manifest.module_here(self.target, host))
        self.target["ios_module"].pop("on")
        for host in manifest.HOSTS:
            self.assertIs(manifest.module_here(self.target, host), self.target["ios_module"])
            self.assertIsNone(manifest.module_here({}, host))

    def test_selection_requires_schema_two_unique_systems_and_known_fields(self):
        for module in ({"result": "{work}/result.json"}, {"file": "{work}/game.dylib", "into": "game.dylib"}):
            for on in (None, [], "windows", ["windows", "windows"], ["windows-arm64"], [True], [{}]):
                self.target["ios_module"] = dict(module, on=on)
                with self.subTest(module=module, on=on), self.assertRaisesRegex(ValueError, "ios_module.on"):
                    manifest.validate_manifest(self.recipe)
            self.target["ios_module"] = dict(module, on=["windows"])
            manifest.validate_manifest(self.recipe)
            self.recipe["schema_version"] = 1
            with self.assertRaisesRegex(ValueError, "on requires schema_version 2"):
                manifest.validate_manifest(self.recipe)
            self.recipe["schema_version"] = 2
            self.target["ios_module"]["onn"] = ["macos"]
            with self.assertRaises(ValueError):
                manifest.validate_manifest(self.recipe)

    def test_tools_command_uses_only_the_selected_hosts_portable_tools(self):
        for host, portable in (("macos-arm64", False), ("windows-arm64", True), ("linux-x86_64", True)):
            with self.subTest(host=host), mock.patch.object(cli, "host_id", return_value=host), \
                    mock.patch.object(cli, "manifest_for", return_value=(self.recipe, "repository")), \
                    mock.patch.object(cli, "homebrew_on_path"), \
                    mock.patch.object(cli.tools, "install") as install, redirect_stdout(io.StringIO()):
                self.assertEqual(cli.main(["tools", "hostpad", "--target", "ios", "--repo", str(self.root)]), 0)
                install.assert_called_once_with(["libcxx"], host, any_host=portable)

    def test_player_make_uses_the_same_tool_selection(self):
        entry = {"name": "HostPad", "repo_url": "https://example.invalid/hostpad"}
        disc = self.root / "synthetic.disc"
        disc.write_bytes(b"synthetic")
        for host, portable in (("macos-arm64", False), ("windows-arm64", True), ("linux-x86_64", True)):
            with self.subTest(host=host), mock.patch.object(cli, "host_id", return_value=host), \
                    mock.patch.object(cli, "catalog", return_value={"hostpad": entry}), \
                    mock.patch.object(cli, "release_source", return_value=(self.root, "test-ref", {})), \
                    mock.patch.object(cli, "manifest_for", return_value=(self.recipe, "repository")), \
                    mock.patch.object(cli.tools, "tools_root", return_value=self.root / "tools"), \
                    mock.patch.object(cli.tools, "install") as install, \
                    mock.patch.object(cli, "finish_submodules"), \
                    mock.patch.object(cli, "git", return_value="0" * 40), \
                    mock.patch.object(cli, "execute", return_value=23), redirect_stdout(io.StringIO()):
                self.assertEqual(cli._make("hostpad", "ios", disc, self.root / "out", ref="test-ref",
                                           app=self.root / "base.ipa"), 23)
                self.assertEqual(install.call_args.kwargs["any_host"], portable)

    def test_page_download_plan_uses_the_same_tool_selection(self):
        entry = {"name": "HostPad", "repo_url": "https://example.invalid/hostpad", "free_space_gb": 1}
        for host, portable in (("macos-arm64", False), ("windows-arm64", True), ("linux-x86_64", True)):
            with self.subTest(host=host), mock.patch.object(cli, "host_id", return_value=host), \
                    mock.patch.object(ui, "catalog", return_value={"hostpad": entry}), \
                    mock.patch.object(ui, "release_recipe", return_value=self.recipe), \
                    mock.patch.object(cli, "before_build", return_value=None), \
                    mock.patch.object(cli, "player_folder", return_value=self.root), \
                    mock.patch.object(ui.tools, "installed", return_value=False), \
                    mock.patch.object(ui.tools, "_with_companions", wraps=ui.tools._with_companions) as companions:
                plan = ui.plan("hostpad", "ios", "en")
                self.assertEqual(companions.call_args.args[3], portable)
                self.assertEqual("libcxx" in [item["name"] for item in plan["tools"]], portable)

    def test_full_mac_command_and_source_only_mode_skip_module_packaging(self):
        repo = self.root / "backend"
        repo.mkdir()
        (repo / ".gitignore").write_text("build/\n")
        (repo / "padmint.json").write_text(json.dumps(self.recipe))
        (repo / "builder.py").write_text('''from pathlib import Path
import json, shutil, sys
app, output, work = map(Path, sys.argv[1:4])
work.mkdir(parents=True, exist_ok=True)
(work / 'arguments.json').write_text(json.dumps(sys.argv[4:]))
if '--source-only' not in sys.argv:
    shutil.copyfile(app, output)
''')
        for args in (["init", "-q"], ["config", "user.email", "test@example.invalid"],
                     ["config", "user.name", "Test"], ["add", "."], ["commit", "-qm", "synthetic"]):
            subprocess.run(["git", "-C", str(repo), *args], check=True)
        revision = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
        app = self.root / "base.ipa"
        members = entries()
        members.pop("KartPadBuilderProvenance.json")
        write_ipa(app, members)
        disc = self.root / "synthetic.disc"
        disc.write_bytes(b"synthetic")
        for host, source_only in (("macos-arm64", False), ("windows-arm64", True), ("linux-x86_64", True)):
            args = argparse.Namespace(game="hostpad", repo=repo, disc=disc, revision=revision,
                                      target="ios", source_only=source_only, no_mods=True, jobs=1, app=app)
            with self.subTest(host=host), mock.patch.object(cli, "host_id", return_value=host), \
                    mock.patch.object(ios_module, "prepare") as prepare, \
                    mock.patch.object(ios_module, "check_imports") as check, \
                    mock.patch.object(ios_module, "insert") as insert, \
                    mock.patch.object(cli, "backend_env", return_value=dict(os.environ)) as env, \
                    redirect_stdout(io.StringIO()):
                selected_repo, checked_disc = cli.validate(args)
                self.assertEqual(cli.execute(args, selected_repo, checked_disc), 0)
                prepare.assert_not_called()
                check.assert_not_called()
                insert.assert_not_called()
                self.assertFalse(env.call_args.args[3])
            actual_args = next((repo / "build/padmint").glob("*/backend/arguments.json"))
            self.assertEqual(json.loads(actual_args.read_text()),
                             ["--source-only" if source_only else "--train-pgo", "--no-mods"])
            if not source_only:
                # The published app unchanged apart from its padmint-hostpad:// launch link.
                expected = self.root / "expected.ipa"
                shutil.copyfile(app, expected)
                add_launch_link(expected, "hostpad")
                self.assertEqual(args.output_path.read_bytes(), expected.read_bytes())
        records = [json.loads(path.read_text()) for path in (repo / "build/padmint").glob("*/runs/*/record.json")]
        self.assertEqual(len(records), 3)
        self.assertTrue(all(record["status"] == "completed" and "module_result_sha256" not in record
                            for record in records))


if __name__ == "__main__":
    unittest.main()
