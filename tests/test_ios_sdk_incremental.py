"""SDK retries preserve build dependencies, while changed inputs still take effect."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from padmint import ios_module
from fixtures import entries, write_ipa
from test_ios_module import AVAILABILITY


class IncrementalSdkTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="padmint SDK with spaces ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.roots = {name: self.root / "sources" / name for name in ios_module.SOURCES}
        self.own = self.root / "own headers"
        files = {
            self.roots["libc"] / "include/stdio.h": "/* stdio */\n",
            self.roots["xnu"] / "bsd/sys/cdefs.h": "#ifdef XNU_PLATFORM_iPhoneOS\n#endif\n",
            self.roots["xnu"] / "bsd/types/old.h": "/* old type */\n",
            self.roots["availability"] / "availability": AVAILABILITY,
            self.roots["availability"] / "templates/Availability.h": "/* template */\n",
            self.roots["libcxx"] / "include/vector": "// vector\n",
            self.roots["libcxx"] / "include/__config_site.in": "#cmakedefine01 _LIBCPP_HAS_THREADS\n",
            self.roots["libcxx"] / "vendor/llvm/default_assertion_handler.in": "// handler\n",
            self.own / "math.h": "/* math */\n",
        }
        for path, text in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        self.llvm = self.root / "llvm"
        (self.llvm / "bin").mkdir(parents=True)
        for name in ("clang", "clang++", "ld64.lld", "llvm-ar", "llvm-ranlib", "llvm-install-name-tool"):
            (self.llvm / "bin" / (name + (".exe" if os.name == "nt" else ""))).touch()
        self.app = self.root / "published.ipa"
        write_ipa(self.app, entries())
        self.folder = self.root / "prepared"
        self.sdk = self.folder / ios_module.FOLDER
        for name, value in (
            ("HEADERS", (("libc", "include", "", "stdio.h"),
                         ("xnu", "bsd/sys", "sys", "cdefs.h"),
                         ("xnu", "bsd/types", "types", "*"))),
            ("HEADERS_DIR", self.own), ("AVAILABILITY_HEADERS", ("Availability.h",)),
        ):
            patch = mock.patch.object(ios_module, name, value)
            patch.start(); self.addCleanup(patch.stop)
        for name, value in (("source_roots", self.roots), ("llvm_root", self.llvm),
                            ("app_thread_locals", ["_synthetic_tls"])):
            patch = mock.patch.object(ios_module, name, return_value=value)
            mocked = patch.start(); self.addCleanup(patch.stop)
            if name == "app_thread_locals":
                self.thread_locals = mocked

    def prepare(self):
        return ios_module.prepare(self.folder, self.app)

    def snapshot(self, mark=False):
        result = {}
        for path in self.folder.rglob("*"):
            if path.is_file():
                if mark:
                    # No sleeps or dependence on the host filesystem's clock precision.
                    os.utime(path, ns=(1_600_000_000_000_000_000,) * 2)
                result[path.relative_to(self.folder).as_posix()] = (path.read_bytes(), path.stat().st_mtime_ns)
        return result

    def test_complete_prepare_preserves_identical_files_including_final_tls_stubs(self):
        first = self.prepare()
        before = self.snapshot(mark=True)
        self.assertEqual(first, self.prepare())
        self.assertEqual(before, self.snapshot())
        self.assertIn(b"_synthetic_tls", (self.sdk / "usr/lib/libSystem.tbd").read_bytes())
        self.assertFalse(list(self.folder.glob(".padmint-sdk-*")))

    def test_changed_added_removed_and_corrupt_headers_are_reconciled(self):
        self.prepare()
        before = self.snapshot(mark=True)
        (self.roots["libc"] / "include/stdio.h").write_text("/* changed stdio */\n")
        (self.roots["xnu"] / "bsd/types/old.h").unlink()
        (self.roots["xnu"] / "bsd/types/new.h").write_text("/* new type */\n")
        (self.sdk / "usr/include/math.h").write_text("corrupt cached header")
        (self.sdk / "stale/subfolder").mkdir(parents=True)
        (self.sdk / "stale/subfolder/header.h").write_text("removed generated header")
        self.prepare()
        after = self.snapshot()
        prefix = ios_module.FOLDER + "/"
        self.assertNotIn(prefix + "usr/include/types/old.h", after)
        self.assertFalse((self.sdk / "stale").exists())
        self.assertEqual(after[prefix + "usr/include/types/new.h"][0],
                         (self.roots["xnu"] / "bsd/types/new.h").read_bytes())
        self.assertEqual(after[prefix + "usr/include/math.h"][0], before[prefix + "usr/include/math.h"][0])
        changed = {prefix + path for path in ("usr/include/stdio.h", "usr/include/math.h", "SOURCES.json")}
        for name in before.keys() & after.keys():
            if name not in changed:
                self.assertEqual(before[name], after[name], name)
        sources = json.loads((self.sdk / "SOURCES.json").read_text())["files"]
        self.assertIn("usr/include/types/new.h", {item["file"] for item in sources})

    def test_install_options_and_libcxx_configuration_changes_take_effect(self):
        self.prepare()
        before = self.snapshot(mark=True)
        with mock.patch.dict(ios_module.INSTALL_DEFINES, {"xnu": ("OTHER_PLATFORM",)}), \
                mock.patch.dict(ios_module.LIBCXX_SITE, {"_LIBCPP_HAS_THREADS": "0"}):
            self.prepare()
        self.assertIn("#ifdef XNU_PLATFORM_iPhoneOS", (self.sdk / "usr/include/sys/cdefs.h").read_text())
        self.assertIn("#define _LIBCPP_HAS_THREADS 0", (self.sdk / "usr/include/c++/v1/__config_site").read_text())
        after = self.snapshot()
        self.assertEqual(before[ios_module.FOLDER + "/usr/include/stdio.h"],
                         after[ios_module.FOLDER + "/usr/include/stdio.h"])

    def test_generation_failure_preserves_previous_sdk_and_cleans_scratch(self):
        self.prepare()
        before = self.snapshot(mark=True)
        (self.roots["libc"] / "include/stdio.h").write_text("/* newer header */\n")
        with mock.patch.object(ios_module, "_run_availability", side_effect=RuntimeError("generator failed")):
            with self.assertRaisesRegex(RuntimeError, "generator failed"):
                self.prepare()
        self.assertEqual(before, self.snapshot())
        self.assertFalse(list(self.folder.glob(".padmint-sdk-*")))

    def test_tls_changes_and_removal_update_only_the_system_stubs(self):
        self.prepare()
        for names in (["_different_tls"], []):
            before = self.snapshot(mark=True)
            self.thread_locals.return_value = names
            self.prepare()
            after = self.snapshot()
            changed = {name for name in before if before[name] != after[name]}
            self.assertEqual(changed, {ios_module.FOLDER + "/usr/lib/" + name + ".tbd"
                                      for name in ("libSystem", "libm", "libc", "libpthread", "libdl")})
            system = (self.sdk / "usr/lib/libSystem.tbd").read_text()
            self.assertEqual("thread-local-symbols:" in system, bool(names))

    def test_toolchain_changes_and_app_executable_updates_are_content_aware(self):
        self.prepare()
        before = self.snapshot(mark=True)
        ios_module.toolchain(self.sdk, self.llvm, "15.0")
        self.assertIn("arm64-apple-ios15.0", (self.sdk / "toolchain.cmake").read_text())
        self.assertNotEqual(before[ios_module.FOLDER + "/toolchain.cmake"],
                            self.snapshot()[ios_module.FOLDER + "/toolchain.cmake"])
        same = self.snapshot(mark=True)
        ios_module.toolchain(self.sdk, self.llvm, "15.0")
        self.assertEqual(same, self.snapshot())
        members = entries()
        executable = next(name for name in members if name.endswith(".app/Synthetic"))
        members[executable] += b"changed executable bytes"
        write_ipa(self.app, members)
        ios_module.published_executable(self.app, self.folder / "app-executable")
        self.assertEqual((self.folder / "app-executable").read_bytes(), members[executable])

    def test_generated_file_directory_transitions_remove_obsolete_paths(self):
        self.prepare()
        header = self.sdk / "usr/include/math.h"
        header.unlink(); header.mkdir(); (header / "stale.h").touch()
        types = self.sdk / "usr/include/types"
        (types / "old.h").unlink(); types.rmdir(); types.write_text("old generated file")
        self.prepare()
        self.assertEqual(header.read_text(), "/* math */\n")
        self.assertTrue((types / "old.h").is_file())


if __name__ == "__main__":
    unittest.main()
