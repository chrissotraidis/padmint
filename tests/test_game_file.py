import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from padmint import game_file
from padmint.manifest import validate_manifest

MANIFEST = {"name": "KartPad", "game": "Mario Kart Wii (Wii, RMCP01)",
            "inputs": [{"type": "wii-disc", "game_ids": ["RMCP01"], "revisions": [0]}]}


def header(game_id="RMCP01", revision=0, title="MarioKartWii"):
    """The top of `nodtool info` output (2.0.0-alpha.9)."""
    return (f"Format: RVZ\nLossless: true\n\nTitle: {title}\nGame ID: {game_id}\n"
            f"Disc 1, Revision {revision}\n\nPartition 0\n\tGame ID: {game_id} (00010004)\n")


class GameFileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.disc = Path(self.temp.name) / "My Disc.rvz"
        self.disc.write_bytes(b"synthetic input, not game data")

    def run_check(self, stdout, returncode=0, stderr="", manifest=MANIFEST):
        result = subprocess.CompletedProcess([], returncode, stdout, stderr)
        with mock.patch.object(game_file.subprocess, "run", return_value=result) as run:
            outcome = game_file.check(manifest, self.disc, "nodtool")
        self.assertEqual(run.call_args.args[0], ["nodtool", "info", str(self.disc)])
        return outcome

    def test_supported_disc_is_described(self):
        self.assertEqual(self.run_check(header()), "MarioKartWii (RMCP01, Europe, revision 0)")

    def test_other_region_says_which_version_is_needed(self):
        with self.assertRaisesRegex(ValueError, r"USA version \(RMCE01\).*Europe \(RMCP01\)"):
            self.run_check(header("RMCE01"))

    def test_other_game_is_named(self):
        with self.assertRaisesRegex(ValueError, r"Your file is ZELDA \(GZLE01\), not the game KartPad"):
            self.run_check(header("GZLE01", title="ZELDA"))

    def test_other_revision(self):
        with self.assertRaisesRegex(ValueError, "revision 1 of RMCP01.*revision 0"):
            self.run_check(header(revision=1))

    def test_unreadable_file_explains_likely_causes(self):
        with self.assertRaisesRegex(ValueError, "could not read My Disc.rvz.*unexpected end of file.*incomplete"):
            self.run_check("", returncode=1, stderr="Error: unexpected end of file")

    def test_games_without_disc_ids_are_not_checked(self):
        manifest = {"name": "Game", "inputs": [{"type": "wii-disc"}]}
        with mock.patch.object(game_file.subprocess, "run") as run:
            self.assertIsNone(game_file.check(manifest, self.disc, "nodtool"))
            self.assertIsNone(game_file.check(MANIFEST, None, "nodtool"))
        run.assert_not_called()

    def test_only_nodtool_is_installed_before_the_check(self):
        target = {"tools": ["dotnet", "android-ndk", "nodtool"]}
        with mock.patch.object(game_file.tools, "install") as install, \
                mock.patch.object(game_file.tools, "executable", return_value="nodtool"), \
                mock.patch.object(game_file.subprocess, "run",
                                  return_value=subprocess.CompletedProcess([], 0, header("RMCE01"), "")):
            with self.assertRaises(ValueError):
                game_file.check_before_tools(MANIFEST, target, self.disc, "linux-x86_64")
        install.assert_called_once_with(["nodtool"], "linux-x86_64")

    def test_manifest_validates_disc_ids(self):
        base = {"schema_version": 1, "id": "game", "name": "Game", "game": "Game", "kind": "disc-translation",
                "status": "experimental", "publication": {"public_binaries": False},
                "targets": {"android": {"hosts": {"linux-x86_64": "planned"}}}}
        validate_manifest(dict(base, inputs=[{"type": "wii-disc", "game_ids": ["RMCP01"], "revisions": [0]}]))
        for bad in ({"game_ids": ["rmcp01"]}, {"game_ids": "RMCP01"}, {"revisions": ["0"]}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate_manifest(dict(base, inputs=[dict({"type": "wii-disc"}, **bad)]))


class AcceptedInputTests(unittest.TestCase):
    def setUp(self):
        import hashlib
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.file = Path(self.temp.name) / 'Original.exe'
        self.file.write_bytes(b'synthetic original')
        self.accepted = hashlib.sha256(self.file.read_bytes()).hexdigest()
        self.input = {'type': 'pc-game-installer', 'formats': ['exe'],
                      'accepted_sha256': [self.accepted],
                      'description': 'Choose Original.exe, not the update patch.'}
        self.manifest = {'name': 'ExamplePad', 'inputs': [self.input]}

    def test_accepts_original_independent_of_filename(self):
        renamed = self.file.with_name('renamed.EXE')
        self.file.rename(renamed)
        self.assertIn('SHA-256 verified', game_file.check_file_hash(self.manifest, renamed))

    def test_patch_is_rejected_before_tools_with_recipe_guidance(self):
        self.file.write_bytes(b'synthetic update patch')
        with mock.patch.object(game_file.tools, 'install') as install:
            with self.assertRaisesRegex(ValueError, 'not the update patch.*Renaming'):
                game_file.check_before_tools(self.manifest, {'tools': ['nodtool']}, self.file, 'macos-arm64')
        install.assert_not_called()

    def test_renaming_wrong_input_to_an_undeclared_extension_cannot_bypass_preflight(self):
        renamed = self.file.with_suffix('.zip')
        renamed.write_bytes(b'synthetic patch')
        with mock.patch.object(game_file.tools, 'install') as install:
            with self.assertRaisesRegex(ValueError, 'Choose Original.exe'):
                game_file.check_before_tools(self.manifest, {'tools': ['nodtool']}, renamed, 'macos-arm64')
        install.assert_not_called()

    def test_folders_and_unrestricted_alternatives_remain_backend_inputs(self):
        self.assertIsNone(game_file.check_file_hash(self.manifest, self.file.parent))
        self.manifest['inputs'].append({'type': 'other-installer', 'formats': ['exe']})
        self.file.write_bytes(b'another supported installer')
        self.assertIsNone(game_file.check_file_hash(self.manifest, self.file))
        self.manifest['inputs'].append({'type': 'archive', 'formats': ['zip']})
        archive = self.file.with_suffix('.zip')
        archive.write_bytes(b'an unrestricted archive')
        self.assertIsNone(game_file.check_file_hash(self.manifest, archive))

    def test_other_formats_and_in_app_alternatives_do_not_bypass_hash(self):
        self.manifest['inputs'] += [{'type': 'archive', 'formats': ['zip']},
                                    {'type': 'rom', 'formats': ['exe'], 'when': 'in-app'}]
        self.file.write_bytes(b'synthetic update patch')
        with self.assertRaises(ValueError):
            game_file.check_file_hash(self.manifest, self.file)

    def test_verified_hashes_stay_informational_and_cloud_files_are_not_read(self):
        self.input['verified_sha256'] = self.input.pop('accepted_sha256')
        self.file.write_bytes(b'another supported original')
        self.assertIsNone(game_file.check_file_hash(self.manifest, self.file))
        self.input['accepted_sha256'] = [self.accepted]
        with mock.patch.object(game_file, 'cloud_only', return_value=True):
            with self.assertRaisesRegex(ValueError, 'Download Now'):
                game_file.check_file_hash(self.manifest, self.file)

    def test_manifest_accepts_only_nonempty_digest_lists(self):
        base = {'schema_version': 1, 'id': 'examplepad', 'name': 'ExamplePad', 'game': 'Example',
                'kind': 'disc-translation', 'status': 'experimental', 'publication': {'public_binaries': False},
                'targets': {'ios': {'hosts': {'macos-arm64': 'planned'}}}, 'inputs': [self.input]}
        validate_manifest(base)
        for bad in ([], self.accepted, [None], ['A' * 64], ['short']):
            with self.subTest(bad=bad):
                self.input['accepted_sha256'] = bad
                with self.assertRaisesRegex(ValueError, 'accepted_sha256'):
                    validate_manifest(base)


if __name__ == "__main__":
    unittest.main()
