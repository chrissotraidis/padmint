"""An iPhone app linked with the iOS 27 SDK that shows no UIKit scene startup may not open on
iOS 27; the finish screen says so instead of leaving it to the technical log."""
import unittest
from pathlib import Path
from unittest import mock

from padmint import cli


def checked(state, sdk):
    return {"apple_compatibility": {"scene_startup": state, "linked_slices": [{"sdk": sdk}]}}


class Ios27Tests(unittest.TestCase):
    def test_only_unverified_startup_with_the_ios_27_sdk_is_a_risk(self):
        for state, sdk, risk in (("unverified", "27.0", True), ("unverified", "28.1", True),
                                 ("unverified", "26.5", False), ("declared", "27.0", False),
                                 ("defined-configuration-callback", "27.0", False)):
            with self.subTest(state=state, sdk=sdk), \
                    mock.patch.object(cli, "validate_ipa", return_value=checked(state, sdk)):
                self.assertIs(cli.ios27_launch_risk(Path("Game.ipa")), risk)

    def test_an_unreadable_file_is_not_reported_as_a_risk(self):
        with mock.patch.object(cli, "validate_ipa", side_effect=ValueError("not an IPA")):
            self.assertFalse(cli.ios27_launch_risk(Path("Game.ipa")))


if __name__ == "__main__":
    unittest.main()
