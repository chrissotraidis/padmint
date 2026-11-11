"""A folder rename straight after writing it can meet Windows antivirus still reading the
new files (padmint#255: "Access is denied" 24 s into a first BlueWake build). PadMint
waits and tries again there instead of failing the build or downloading a tool twice."""
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from padmint import tools


class ReplaceFolderTests(unittest.TestCase):
    def rename(self, system, failures):
        with tempfile.TemporaryDirectory() as folder:
            source, target = Path(folder) / "tool.partial", Path(folder) / "tool"
            source.mkdir()
            real, calls = tools.os.replace, []

            def busy_at_first(*args):
                calls.append(args)
                if len(calls) <= failures:
                    raise PermissionError(13, "Access is denied")
                return real(*args)

            with mock.patch.object(tools.os, "name", system), mock.patch.object(tools.time, "sleep"), \
                    mock.patch.object(tools.os, "replace", side_effect=busy_at_first):
                tools.replace_folder(source, target)
            return target.is_dir()

    def test_windows_tries_again_until_the_scan_lets_go(self):
        self.assertTrue(self.rename("nt", failures=3))

    def test_windows_gives_up_when_the_folder_stays_in_use(self):
        with self.assertRaises(PermissionError):
            self.rename("nt", failures=50)

    def test_other_systems_fail_at_once(self):
        with self.assertRaises(PermissionError):
            self.rename("posix", failures=1)


if __name__ == "__main__":
    unittest.main()
