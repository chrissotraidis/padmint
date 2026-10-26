#!/usr/bin/env python3
"""Run the universal iPhone module pipeline end to end on this computer, with no game code.

Downloads PadMint's pinned open-source iPhone parts, assembles the SDK for a published
app without game code (KartPad's public IPA by default), compiles a small C++ library
that uses the app's exports and the device's C and C++ libraries, checks its imports and
puts it in a copy of the app. Used by CI on Windows, Linux and macOS.

Usage: scripts/ios-module-probe.py WORK_FOLDER [PUBLISHED_IPA]
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from padmint import ios_module, tools  # noqa: E402
from padmint.manifest import host_id  # noqa: E402
from padmint.package import validate_ipa  # noqa: E402

APP_URL = "https://github.com/chrissotraidis/kartpad/releases/download/v0.7.4/KartPad-v0.7.4-ios-unsigned.ipa"
APP_SHA256 = "74f0c7e82e1df2d3f32eb0893cb6f5040e50b6e7839272372425057e2b35714a"


def incremental_probe(work, app, env, prepared, cmake, build, module):
    """An identical retry is idle; changed thread-local stubs relink only."""
    def stamps(paths):
        return {path: path.stat().st_mtime_ns for path in paths}

    sdk_files = [path for path in prepared["sdk"].rglob("*") if path.is_file()]
    sdk_files.append(prepared["executable"])
    before_sdk = stamps(sdk_files)
    objects = list(build.rglob("*.o"))
    if not objects:
        raise SystemExit("the incremental probe found no compiled objects")
    before_objects, before_module = stamps(objects), module.stat().st_mtime_ns
    ios_module.prepare(work / "sdk", app, env)
    if stamps(sdk_files) != before_sdk:
        raise SystemExit("preparing the same SDK changed generated file timestamps")
    subprocess.run([cmake, "--build", str(build)], check=True, env=env)
    if stamps(objects) != before_objects or module.stat().st_mtime_ns != before_module:
        raise SystemExit("an unchanged SDK rebuilt the module")
    llvm = ios_module.llvm_root(env)
    original = ios_module.app_thread_locals(llvm, prepared["executable"])
    try:
        for names in (original + ["_padmint_incremental_probe_tls"], original):
            previous = module.stat().st_mtime_ns
            ios_module.write_stubs(prepared["sdk"], names)
            subprocess.run([cmake, "--build", str(build)], check=True, env=env)
            if stamps(objects) != before_objects or module.stat().st_mtime_ns == previous:
                raise SystemExit("changed SDK thread-local stubs did not relink only the module")
    finally:
        ios_module.write_stubs(prepared["sdk"], original)
    print(f"SDK incremental probe passed: {len(sdk_files)} files unchanged; TLS changes relink only")


def main():
    if len(sys.argv) not in (2, 3):
        raise SystemExit(__doc__)
    work = Path(sys.argv[1]).resolve()
    work.mkdir(parents=True, exist_ok=True)
    host = host_id()
    if len(sys.argv) == 3:
        app = Path(sys.argv[2]).resolve()
    else:
        import hashlib
        app = work / "published.ipa"
        data = urllib.request.urlopen(APP_URL).read()
        if hashlib.sha256(data).hexdigest() != APP_SHA256:
            raise SystemExit("published app checksum mismatch")
        app.write_bytes(data)
    tools.install(["libcxx", "cmake", "ninja"], host, any_host=True)
    env = tools.environment(["libcxx", "cmake", "ninja"], host, any_host=True)
    # Exercise a fresh default build, then a deployment change in the same cache.
    probe(work, app, env)
    if ios_module._os_version(ios_module.app_minimum(app)) >= (15, 0, 0):
        probe(work, app, env, target="15.0", fresh=False)


def probe(work, app, env, target=None, fresh=True):
    host = host_id()
    prepared = ios_module.prepare(work / "sdk", app, env)
    llvm = ios_module.llvm_root(env)
    if target is not None:
        prepared["toolchain"] = ios_module.toolchain(prepared["sdk"], llvm, target)
    build = work / "build"
    cmake = tools.executable("cmake", host)
    subprocess.run([cmake, *(["--fresh"] if fresh else []),
                    "-S", str(ROOT / "tests/ios-module-probe"), "-B", str(build), "-G", "Ninja",
                    f"-DCMAKE_TOOLCHAIN_FILE={prepared['toolchain']}", "-DCMAKE_BUILD_TYPE=Release"],
                   check=True, env=env)
    subprocess.run([cmake, "--build", str(build)], check=True, env=env)
    llvm = ios_module.llvm_root(env)
    module = build / "libgame.dylib"
    if target is None:
        incremental_probe(work, app, env, prepared, cmake, build, module)
    imports = set(subprocess.check_output([str(ios_module.llvm_tool(llvm, "llvm-nm")), "-u", "-j", str(module)],
                                          text=True).splitlines())
    required = {"___assert_rtn", "_mmap", "_munmap", "_atexit", "_strtol", "_pthread_create",
                "_pthread_join", "_pthread_once", "_pthread_mutex_lock", "_pthread_mutex_unlock",
                "_pthread_cond_broadcast", "_pthread_cond_signal", "_pthread_cond_wait"}
    if not required <= imports:
        raise SystemExit(f"the module did not exercise every required runtime header: {sorted(required - imports)}")
    ios_module.check_imports(llvm, module, prepared["executable"])
    output = ios_module.insert(app, module, "Frameworks/libpadmint_probe.dylib",
                               work / ("probe.ipa" if target is None else "probe-ios15.ipa"), llvm,
                               work / "insert")
    report = validate_ipa(output, None, None, None)
    slices = report["apple_compatibility"]["linked_slices"]
    module_report = ios_module.linked(module)
    print(json.dumps({"host": host, "module": module_report, "app": slices}, indent=1))
    expected = ios_module._os_version(target) if target is not None else min(
        ios_module._os_version(ios_module.app_minimum(app)), ios_module._os_version(ios_module.DEPLOYMENT_TARGET))
    cached = next(line.split("=", 1)[1] for line in (build / "CMakeCache.txt").read_text().splitlines()
                  if line.startswith("CMAKE_OSX_DEPLOYMENT_TARGET:STRING="))
    if ios_module._os_version(cached) != expected:
        raise SystemExit("the CMake cache retained a different iOS deployment target")
    if module_report["platform"] != "ios" or ios_module._os_version(module_report["minimum_os"]) != expected:
        raise SystemExit("the module does not have the requested iOS deployment target")
    print(f"Universal iPhone module pipeline passed on {host}: {output}")


if __name__ == "__main__":
    main()
