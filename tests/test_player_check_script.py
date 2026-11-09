"""Exercise the release-check wrapper without downloading or building games."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(sys.platform == "darwin", "player-check.sh uses Apple's Python on macOS")
class PlayerCheckScriptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="player check ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "scripts").mkdir()
        shutil.copy2(ROOT / "scripts/player-check.sh", self.root / "scripts/player-check.sh")
        (self.root / "padmint").mkdir()
        (self.root / "padmint/__init__.py").touch()
        (self.root / "padmint/__main__.py").write_text('''import json, os, pathlib, sys
home = pathlib.Path(os.environ['PADMINT_HOME'])
with open(os.environ['TEST_LOG'], 'a') as f:
    f.write(json.dumps({'args': sys.argv[1:], 'home': str(home), 'fresh': not home.exists()}) + '\\n')
if sys.argv[1] == 'tools':
    home.mkdir(parents=True)
    sys.exit(int(os.environ.get('FAIL_TOOLS', '0')))
''')
        # The catalog audit: logged apart from PadMint's calls, failing or naming hidden hosts on request.
        (self.root / "scripts/audit-catalog.py").write_text('''import json, os, sys
with open(os.environ['AUDIT_LOG'], 'a') as f:
    f.write(json.dumps(sys.argv[1:]) + '\\n')
if '--recipe' in sys.argv:
    print(os.environ.get('HIDDEN', ''), end='')
sys.exit(int(os.environ.get('FAIL_AUDIT', '0')))
''')
        self.checkout = self.root / "game source"
        self.checkout.mkdir()
        subprocess.run(["git", "init", "-q", str(self.checkout)], check=True)
        subprocess.run(["git", "-C", str(self.checkout), "-c", "user.name=Fixture",
                        "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture",
                        "--allow-empty"], check=True)
        self.log = self.root / "calls.jsonl"
        self.audit_log = self.root / "audit.jsonl"

    def run_check(self, checkout=True, app=None, fail=0, game_file="disc with spaces.iso", **extra):
        args = ["/bin/bash", str(self.root / "scripts/player-check.sh"), "fixture", "ios", game_file]
        if checkout:
            args.append(str(self.checkout))
        if app:
            args.append(app)
        env = dict(os.environ, TEST_LOG=str(self.log), TMPDIR=str(self.root), FAIL_TOOLS=str(fail),
                   AUDIT_LOG=str(self.audit_log), **extra)
        result = subprocess.run(args, cwd=self.root, env=env, capture_output=True, text=True)
        calls = [json.loads(row) for row in self.log.read_text().splitlines()] if self.log.exists() else []
        return result, calls

    def test_checkout_prepares_tools_then_passes_exact_app_path(self):
        result, calls = self.run_check(app="/tmp/base app $(no-shell).ipa")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([c['args'][0] for c in calls], ['tools', 'build'])
        self.assertTrue(calls[0]['fresh'])
        self.assertEqual(calls[0]['home'], calls[1]['home'])
        self.assertEqual(calls[1]['args'][-2:], ['--app', '/tmp/base app $(no-shell).ipa'])
        for call in calls:
            self.assertEqual(call['args'][call['args'].index('--target') + 1], 'ios')

    def test_relative_app_path_is_resolved_before_changing_directory(self):
        result, calls = self.run_check(app="base app.ipa")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(Path(calls[-1]['args'][-1]).resolve(),
                         (self.root / 'base app.ipa').resolve())

    def test_tool_failure_prevents_build_and_success_message(self):
        result, calls = self.run_check(fail=23)
        self.assertEqual(result.returncode, 23)
        self.assertEqual(len(calls), 1)
        self.assertNotIn('Player check passed', result.stdout)

    def test_checkout_without_base_app_still_works(self):
        result, calls = self.run_check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('--app', calls[-1]['args'])

    def test_game_chosen_in_the_app_passes_no_game_file(self):
        for checkout in (True, False):
            with self.subTest(checkout=checkout):
                self.log.unlink(missing_ok=True)
                result, calls = self.run_check(checkout=checkout, game_file="-")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn('--disc', calls[-1]['args'])
                self.assertNotIn('-', calls[-1]['args'])

    def test_game_file_is_passed_when_given(self):
        result, calls = self.run_check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls[-1]['args'][calls[-1]['args'].index('--disc') + 1], 'disc with spaces.iso')

    def test_published_release_uses_make_with_empty_home(self):
        result, calls = self.run_check(checkout=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]['args'][:3], ['make', 'fixture', 'ios'])
        self.assertTrue(calls[0]['fresh'])
        self.assertEqual(json.loads(self.audit_log.read_text()), ['--game', 'fixture'])

    def test_published_release_whose_catalog_differs_fails_before_building(self):
        result, calls = self.run_check(checkout=False, FAIL_AUDIT="1")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(calls, [])
        self.assertIn("catalog doesn't match", result.stdout)
        self.assertNotIn('Player check passed', result.stdout)

    def test_checkout_names_the_hosts_the_catalog_will_need_and_still_builds(self):
        (self.checkout / "padmint.json").write_text("{}")
        result, calls = self.run_check(HIDDEN="fixture: the published recipe builds iPhone on windows-x86_64, "
                                              "but the catalog hides it")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("windows-x86_64", result.stdout)
        self.assertIn("release PadMint with it", result.stdout)
        self.assertEqual([c['args'][0] for c in calls], ['tools', 'build'])


if __name__ == '__main__':
    unittest.main()
