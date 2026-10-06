"""Release-owned input guidance and validation without network or game data."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from padmint import cli, ui


class RecipeInputTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.file = Path(self.temp.name) / 'Original.exe'
        self.file.write_bytes(b'synthetic original')
        self.recipe = {'name': 'ExamplePad', 'inputs': [
            {'type': 'pc-game-installer', 'formats': ['exe'], 'when': 'build',
             'description': 'Choose Original.exe, not the patch.',
             'accepted_sha256': [hashlib.sha256(self.file.read_bytes()).hexdigest()]},
            {'type': 'rom', 'formats': ['iso'], 'when': 'in-app', 'description': 'For later import.'}],
            'targets': {'ios': {'hosts': {'macos-arm64': 'experimental'}}}}
        self.entry = {'repo_url': 'https://example.invalid/examplepad', 'manifest': None}
        for obj, name, value in ((ui, 'catalog', {'examplepad': self.entry}),
                                 (ui, 'release_recipe', self.recipe),
                                 (cli, 'before_build', None),
                                 (cli, 'player_requirements', [])):
            patcher = mock.patch.object(obj, name, return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)
        no_network = mock.patch('urllib.request.urlopen', side_effect=AssertionError('network'))
        no_network.start()
        self.addCleanup(no_network.stop)

    def test_plan_exposes_only_build_input_descriptions_from_release(self):
        plan = ui.plan('examplepad', 'ios', 'en')
        self.assertEqual(plan['inputs'], self.recipe['inputs'][:1])

    def test_release_recipe_refuses_wrong_extension_even_without_catalog_manifest(self):
        app = self.file.with_suffix('.ipa')
        app.write_bytes(b'synthetic app')
        with mock.patch.object(cli, 'game_from_file') as probe:
            problem = ui.check_file('examplepad', str(app), 'en')
        self.assertIn('EXE', problem)
        self.assertIn('ExamplePad', problem)
        probe.assert_not_called()

    def test_source_recipe_unrestricted_format_alternative_remains_selectable(self):
        self.recipe['inputs'].append({'type': 'game-file', 'description': 'Another original game file.'})
        alternative = self.file.with_suffix('.data')
        alternative.write_bytes(b'synthetic alternative')
        with mock.patch.object(cli, 'game_from_file') as probe:
            self.assertIsNone(ui.check_file('examplepad', str(alternative), 'en'))
        probe.assert_not_called()

    def test_patch_and_renamed_patch_fail_but_original_never_downloads_disc_tools(self):
        with mock.patch.object(cli, 'game_from_file') as probe, \
                mock.patch.object(cli.tools, 'install', side_effect=AssertionError('tool download')):
            self.assertIsNone(ui.check_file('examplepad', str(self.file), 'en'))
            self.file.write_bytes(b'synthetic patch')
            problem = ui.check_file('examplepad', str(self.file), 'en')
        self.assertIn('Choose Original.exe, not the patch.', problem)
        probe.assert_not_called()

    def test_format_hint_does_not_claim_unrestricted_alternatives_are_exhaustive(self):
        self.assertEqual(ui.input_formats(self.recipe['inputs'][:1]), ['exe'])
        self.assertEqual(ui.input_formats(self.recipe['inputs'][:1] + [{'type': 'game-file'}]), [])
        self.assertEqual(ui.input_formats(self.recipe['inputs'][:1] + [{'type': 'game-file', 'formats': []}]), [])

    def test_catalog_recipe_is_used_offline(self):
        self.entry['manifest'] = self.recipe
        self.file.write_bytes(b'synthetic patch')
        with mock.patch.object(ui, 'release_recipe', return_value=None):
            problem = ui.check_file('examplepad', str(self.file), 'en')
            plan = ui.plan('examplepad', 'ios', 'en')
        self.assertIn('Choose Original.exe', problem)
        self.assertEqual(plan['inputs'], self.recipe['inputs'][:1])

    def test_make_rechecks_actual_recipe_and_stops_before_tools_or_backend(self):
        self.recipe['targets']['ios']['command'] = ['synthetic-builder']
        self.file.write_bytes(b'synthetic patch')
        with mock.patch.object(cli, 'catalog', return_value={'examplepad': self.entry}), \
                mock.patch.object(cli, 'host_id', return_value='macos-arm64'), \
                mock.patch.object(cli, 'latest_release', return_value=('v1', {})), \
                mock.patch.object(cli, 'published_recipe', return_value=(self.recipe, 'release')), \
                mock.patch.object(cli, 'release_source', return_value=(self.file.parent, 'v1', {})), \
                mock.patch.object(cli, 'manifest_for', return_value=(self.recipe, 'source')), \
                mock.patch.object(cli.tools, 'missing_system_library', return_value=None), \
                mock.patch.object(cli.tools, 'install') as install, \
                mock.patch.object(cli, 'execute') as execute:
            with self.assertRaisesRegex(ValueError, 'Choose Original.exe'):
                cli._make('examplepad', 'ios', self.file, self.file.parent)
        install.assert_not_called()
        execute.assert_not_called()

    def test_report_uses_actual_build_host_and_selection_does_not_claim_validation(self):
        with mock.patch.object(cli, 'player_games', return_value=[]), \
                mock.patch.object(cli, 'downloads', return_value=[]), \
                mock.patch.object(cli, 'later', return_value=[]), \
                mock.patch.object(cli, 'elsewhere', return_value=[]), \
                mock.patch.object(cli, 'host_id', return_value='macos-arm64'):
            data = ui.player_data('en')
        self.assertEqual(data['host'], 'macos-arm64')
        self.assertNotIn('navigator.platform', ui.PAGE)
        self.assertEqual(data['text']['file_ok'], 'Selected: {file}')


if __name__ == '__main__':
    unittest.main()
