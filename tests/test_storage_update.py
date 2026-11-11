"""Storage lists what PadMint keeps and removes only what it may; updates are checked and switched to."""
import hashlib
import io
import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from padmint import storage, tools, update


class FolderTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name)
        patcher = mock.patch.dict(os.environ, {"PADMINT_HOME": str(self.home)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def make(self, relative, data=b"x" * 5000):
        path = self.home / relative / "file.bin"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


class StorageTests(FolderTests):
    def test_latest_release_and_current_tools_are_kept_everything_else_may_go(self):
        for folder in ("games/kartpad-v0.7.9", "games/kartpad-v0.8.3", "games/kartpad-v0.8.4.partial",
                       "games/sunpad-v0.2.0", "tools/cmake-0.0.1", "cache/kartpad", "apps/kartpad"):
            self.make(folder)
        current_tool = "tools/cmake-" + tools.version(tools.lock()["cmake"], "macos-arm64")
        self.make(current_tool)
        with mock.patch.object(storage, "_host", return_value="macos-arm64"):
            found = {item["id"]: item for item in storage.items({"kartpad": "v0.8.3"})}
            kept = {key for key, item in found.items() if not item["removable"]}
            self.assertEqual(kept, {"games/kartpad-v0.8.3", "games/sunpad-v0.2.0", current_tool})
            self.assertEqual(found["games/kartpad-v0.8.4.partial"]["reason"], "partial")
            self.assertEqual(found["cache/kartpad"]["reason"], "cache")
            with self.assertRaisesRegex(ValueError, "keeps"):
                storage.remove(["games/kartpad-v0.8.3"], {"kartpad": "v0.8.3"})
            with self.assertRaisesRegex(ValueError, "keeps"):
                storage.remove(["../outside"], {"kartpad": "v0.8.3"})
            freed = storage.remove(["games/kartpad-v0.7.9", "tools/cmake-0.0.1"], {"kartpad": "v0.8.3"})
        self.assertGreater(freed, 0)
        self.assertFalse((self.home / "games/kartpad-v0.7.9").exists())
        self.assertTrue((self.home / "games/kartpad-v0.8.3").exists())

    def test_an_old_download_is_removed_with_gits_read_only_files(self):
        # Git marks its object files read-only, and Windows refuses to delete those until
        # they are made writable: Remove stopped there, with the folder half gone.
        self.make("games/kartpad-v0.7.9/.git/objects/ab")
        (self.home / "games/kartpad-v0.7.9/.git/objects/ab/file.bin").chmod(0o444)
        self.make("games/kartpad-v0.8.3")
        with mock.patch.object(storage, "_host", return_value="macos-arm64"):
            storage.remove(["games/kartpad-v0.7.9"], {"kartpad": "v0.8.3"})
        self.assertFalse((self.home / "games/kartpad-v0.7.9").exists())


class UpdateTests(FolderTests):
    def release(self, version, payload_version=None):
        data = io.BytesIO()
        with zipfile.ZipFile(data, "w") as bundle:
            top = f"PadMint-v{version}/app/"
            bundle.writestr(top + "padmint/__init__.py", f'__version__ = "{payload_version or version}"\n')
            bundle.writestr(top + "python/python.exe", b"not for macOS")
            bundle.writestr(f"PadMint-v{version}/PadMint.command", b"#!/bin/bash")
        return data.getvalue()

    def serve(self, files):
        def fake(url):
            name = url.rsplit("/", 1)[1]
            response = io.BytesIO(files[name])
            response.headers = {"Content-Length": str(len(files[name]))}
            response.__enter__ = lambda *a: response
            response.__exit__ = lambda *a: None
            return response
        return mock.patch.object(tools, "open_url", side_effect=fake)

    def test_a_checked_release_is_installed_and_becomes_current(self):
        archive = self.release("9.9.9")
        sums = f"{hashlib.sha256(archive).hexdigest()}  PadMint-macos.zip\n".encode()
        with mock.patch.object(update, "platform", return_value="macos"), \
                self.serve({"SHA256SUMS": sums, "PadMint-macos.zip": archive}):
            update.install("9.9.9")
        self.assertEqual(update.installed()[0], "9.9.9")
        self.assertTrue((self.home / "padmint/9.9.9/padmint/__init__.py").is_file())
        self.assertFalse((self.home / "padmint/9.9.9/python").exists())

    def test_a_download_that_does_not_match_its_checksum_changes_nothing(self):
        archive = self.release("9.9.9")
        with mock.patch.object(update, "platform", return_value="macos"), \
                self.serve({"SHA256SUMS": b"0" * 64 + b"  PadMint-macos.zip\n", "PadMint-macos.zip": archive}):
            with self.assertRaisesRegex(ValueError, "checksum"):
                update.install("9.9.9")
        self.assertIsNone(update.installed())

    def test_only_a_newer_installed_copy_is_run(self):
        (self.home / "padmint/0.0.1/padmint").mkdir(parents=True)
        (self.home / "padmint/0.0.1/padmint/__init__.py").write_text("")
        (self.home / "padmint/current").write_text("0.0.1")
        with mock.patch.object(os, "execv") as execv, mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PADMINT_FROM_UPDATE", None)
            update.switch([])
            execv.assert_not_called()
            (self.home / "padmint/99.0.0/padmint").mkdir(parents=True)
            (self.home / "padmint/99.0.0/padmint/__init__.py").write_text("")
            (self.home / "padmint/current").write_text("99.0.0")
            cwd = os.getcwd()
            try:
                update.switch(["ui"])
            finally:
                os.chdir(cwd)
            self.assertEqual(execv.call_args[0][1][-2:], ["padmint", "ui"])


if __name__ == "__main__":
    unittest.main()

