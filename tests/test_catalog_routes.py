"""Hosted builds and Windows promises follow the selected release's recipe."""
import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import urllib.error
from unittest import mock

from padmint import manifest

SPEC = importlib.util.spec_from_file_location(
    "audit_catalog", Path(__file__).resolve().parents[1] / "scripts/audit-catalog.py")
audit_catalog = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit_catalog)


def entry():
    return {"id": "testpad", "repo_url": "https://github.com/example/testpad",
            "player_targets": ["ios"], "player_game_file": "in-app", "free_space_gb": 1,
            "github_build": True}


def recipe():
    return {"id": "testpad", "inputs": [{"when": "in-app"}], "kind": "clean-engine",
            "targets": {"ios": {"hosts": {"macos-arm64": "experimental"},
                                "command": ["build"]}}}


class CatalogRouteTests(unittest.TestCase):
    def read_entry(self, data):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, "testpad.json").write_text(json.dumps(data))
            with mock.patch.object(manifest, "CATALOG", Path(folder)):
                return manifest.catalog()["testpad"]

    def test_github_flag_is_a_boolean_and_requires_in_app_ios(self):
        self.assertTrue(self.read_entry(entry())["github_build"])
        for change in ({"github_build": "false"}, {"github_build": 1},
                       {"player_game_file": "build"}, {"player_targets": ["macos"]}):
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, "github_build"):
                self.read_entry(dict(entry(), **change))
        self.assertFalse(self.read_entry(dict(entry(), github_build=False, player_game_file="build"))["github_build"])

    def test_private_cloud_build_requires_boolean_and_its_own_setup_guide(self):
        declared = dict(entry(), github_build_private=True,
                        off_mac={"text": "Use a private copy", "url": "https://example.com/private-build"})
        self.assertTrue(self.read_entry(declared)["github_build_private"])
        for change in ({"github_build_private": "true"}, {"github_build": False}, {"off_mac": None}):
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, "github_build_private"):
                self.read_entry(dict(declared, **change))

    def test_selected_recipe_inputs_block_hosted_build_even_when_catalog_is_stale(self):
        released = recipe()
        released["inputs"][0]["when"] = "build"
        with self.assertRaisesRegex(ValueError, "keep this build local"):
            manifest.validate_github_build(entry(), released)
        findings = audit_catalog.route_problems(entry(), released)
        self.assertTrue(any("GitHub build unavailable" in finding for finding in findings))

    def test_unspecified_input_timing_is_private_build_input(self):
        released = recipe()
        released["inputs"] = [{}]
        with self.assertRaisesRegex(ValueError, "game file"):
            manifest.validate_github_build(entry(), released)

    def test_catalog_and_release_must_agree_about_installed_inputs(self):
        released = recipe()
        released["inputs"] = [{"when": "build", "selection": "installed"}]
        declared = dict(entry(), github_build=False, player_game_file="installed")
        self.assertEqual(audit_catalog.route_problems(declared, released), [])
        problems = audit_catalog.route_problems(dict(declared, player_game_file="in-app"), released)
        self.assertEqual(len(problems), 1)
        self.assertIn("recipe needs installed input", problems[0])

    def test_hosted_build_requires_the_matching_game_and_runnable_mac_target(self):
        self.assertIsNotNone(manifest.validate_github_build(entry(), recipe()))
        for change in ({"id": "otherpad"}, {"targets": {}},
                       {"targets": {"ios": {"hosts": {"macos-arm64": "planned"}}}},
                       {"targets": {"ios": {"hosts": {"windows-x86_64": "experimental"}}}}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                manifest.validate_github_build(entry(), dict(recipe(), **change))

    def test_a_local_only_game_is_not_accepted_for_hosting(self):
        with self.assertRaisesRegex(ValueError, "not offered"):
            manifest.validate_github_build(dict(entry(), github_build=False), recipe())

    def test_off_mac_flag_requires_both_architectures_on_windows_and_linux(self):
        data = dict(entry(), github_build=False, ios_off_mac=True)
        released = recipe()
        hosts = released["targets"]["ios"]["hosts"]
        for host in audit_catalog.OFF_MAC_HOSTS:
            hosts[host] = "experimental"
        self.assertEqual(audit_catalog.route_problems(data, released), [])
        for host in audit_catalog.OFF_MAC_HOSTS:
            broken = copy.deepcopy(released)
            broken["targets"]["ios"]["hosts"].pop(host)
            with self.subTest(host=host):
                self.assertEqual(len(audit_catalog.route_problems(data, broken)), 1)
                self.assertIn(host, audit_catalog.route_problems(data, broken)[0])

    def test_exact_advertised_hosts_override_flags_without_requiring_linux(self):
        data = dict(entry(), github_build=False, ios_hosts=["windows-arm64"],
                    ios_off_mac=True, ios_intel_mac=True)
        released = recipe()
        released["targets"]["ios"]["hosts"] = {"windows-arm64": "experimental"}
        self.assertEqual(audit_catalog.route_problems(data, released), [])
        released["targets"]["ios"]["hosts"] = {"windows-x86_64": "experimental"}
        problems = audit_catalog.route_problems(data, released)
        self.assertEqual(len(problems), 1)
        self.assertIn("windows-arm64", problems[0])

    def test_audit_rejects_a_release_recipe_for_a_different_game(self):
        findings = audit_catalog.route_problems(dict(entry(), github_build=False), dict(recipe(), id="otherpad"))
        self.assertEqual(findings, ["the published recipe declares otherpad, not testpad"])

    def test_json_report_preserves_architecture_status_and_marks_evidence_limits(self):
        data = entry()
        released = recipe()
        released["targets"]["ios"]["hosts"]["windows-x86_64"] = "planned"
        with mock.patch.object(audit_catalog, "catalog", return_value={"testpad": data}), \
                mock.patch.object(audit_catalog.cli, "latest_release", return_value=("v1.2.3", {})), \
                mock.patch.object(audit_catalog.cli, "published_recipe", return_value=(released, "testpad v1.2.3 release")), \
                mock.patch("sys.stdout", new_callable=io.StringIO) as output:
            self.assertEqual(audit_catalog.audit(json_output=True), 0)
        report = json.loads(output.getvalue())
        self.assertIn("runtime not tested", report["evidence"])
        self.assertEqual(report["games"][0]["release"], "v1.2.3")
        self.assertEqual(report["games"][0]["targets"]["ios"]["hosts"]["windows-x86_64"], "planned")
        self.assertTrue(report["games"][0]["github_mac_ios"])

    def test_base_app_uses_tagged_source_version_instead_of_release_tag_spelling(self):
        released = recipe()
        released["targets"]["ios"]["published_app"] = "Game-v{version}-ios.ipa"
        release = ("release-build-123", {"Game-v1.2.3-ios.ipa": "app-url", "SHA256SUMS": "sums-url"})
        with mock.patch.object(audit_catalog.urllib.request, "urlopen",
                               return_value=io.BytesIO(b'{"version":"1.2.3","build":123}')) as fetch:
            self.assertEqual(audit_catalog.published_app_problems(entry(), released, release), [])
        self.assertEqual(fetch.call_args.args[0],
                         "https://raw.githubusercontent.com/example/testpad/release-build-123/version.json")

    def test_missing_version_file_uses_the_same_tag_fallback_as_make(self):
        with mock.patch.object(audit_catalog.urllib.request, "urlopen",
                               side_effect=urllib.error.HTTPError("url", 404, "Not found", {}, None)):
            self.assertEqual(audit_catalog.release_version(entry()["repo_url"], "v1.2.3"), "1.2.3")
        for data in (b"not JSON", b'{"version":"2.0.0"}', b'{"version":"2.0.0","build":0}'):
            with self.subTest(data=data), mock.patch.object(audit_catalog.urllib.request, "urlopen",
                                                           return_value=io.BytesIO(data)):
                self.assertEqual(audit_catalog.release_version(entry()["repo_url"], "v1.2.3"), "1.2.3")

    def test_base_app_cannot_come_from_a_different_release_or_lack_checksums(self):
        released = recipe()
        released["targets"]["ios"]["published_app"] = "Game-v{version}-ios.ipa"
        with mock.patch.object(audit_catalog, "release_version", return_value="1.2.3"):
            problems = audit_catalog.published_app_problems(
                entry(), released, ("v1.2.3", {"Game-v1.2.2-ios.ipa": "older-url", "SHA256SUMS": "sums-url"}))
            self.assertEqual(len(problems), 1)
            self.assertIn("Game-v1.2.3-ios.ipa", problems[0])
            problems = audit_catalog.published_app_problems(
                entry(), released, ("v1.2.3", {"Game-v1.2.3-ios.ipa": "app-url"}))
            self.assertEqual(len(problems), 1)
            self.assertIn("no SHA256SUMS", problems[0])

    def test_network_failure_cannot_silently_change_the_base_app_version(self):
        released = recipe()
        released["targets"]["ios"]["published_app"] = "Game-v{version}-ios.ipa"
        with mock.patch.object(audit_catalog.urllib.request, "urlopen", side_effect=OSError("offline")):
            problems = audit_catalog.published_app_problems(
                entry(), released, ("v1.2.3", {"Game-v1.2.3-ios.ipa": "app-url", "SHA256SUMS": "sums-url"}))
        self.assertEqual(len(problems), 1)
        self.assertIn("cannot check", problems[0])

    def test_games_without_base_apps_need_no_version_metadata_request(self):
        with mock.patch.object(audit_catalog.urllib.request, "urlopen") as fetch:
            self.assertEqual(audit_catalog.published_app_problems(entry(), recipe(), ("v1.2.3", {})), [])
        fetch.assert_not_called()

    def test_a_planned_target_does_not_need_a_published_base_app_yet(self):
        released = recipe()
        released["targets"]["ios"].update(published_app="Game-v{version}-ios.ipa",
                                          hosts={"macos-arm64": "planned"})
        with mock.patch.object(audit_catalog.urllib.request, "urlopen") as fetch:
            self.assertEqual(audit_catalog.published_app_problems(entry(), released, ("v1.2.3", {})), [])
        fetch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
