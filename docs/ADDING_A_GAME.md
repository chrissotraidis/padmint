# Adding a game to PadMint

A game joins PadMint with two small files and no PadMint code changes.

## 1. Add `padmint.json` to the game repository

List the scripts the repository already uses, in order. PadMint runs each one
as a stage, shows progress, stops at the first failure and audits the result.

```json
{
  "schema_version": 1,
  "id": "examplepad",
  "name": "ExamplePad",
  "game": "Example Game (N64)",
  "kind": "decomp-patches",
  "status": "draft-untested",
  "inputs": [{"type": "n64-rom", "formats": ["z64"], "when": "in-app",
              "description": "Your own ROM, chosen in the app."}],
  "targets": {
    "ios": {
      "hosts": {"macos-arm64": "experimental"},
      "output": "ipa",
      "check": "ipa",
      "steps": [
        {"stage": "preflight", "command": ["{repo}/scripts/check-repo-safety.sh"]},
        {"stage": "compile", "command": ["{repo}/scripts/build-ios.sh", "--device"]},
        {"stage": "package", "command": ["{repo}/scripts/package-ios.sh",
                                         "{repo}/build-ios/Release-iphoneos/ExamplePad.app", "{output}"]}
      ]
    }
  },
  "requirements": {"disk_gb": 10, "tools": [{"name": "xcodebuild", "version_args": ["-version"]}]},
  "publication": {"public_binaries": false, "reason": "Personal builds contain game code."}
}
```

- **Placeholders** fill whole arguments only: `{repo}`, `{disc}`, `{work}`,
  `{output}`, `{jobs}`. Values never become shell text. A step may also set
  `"env": {"NAME": "{output}"}` when a script reads its output path from the
  environment.
- **Job cap:** every step runs with `CMAKE_BUILD_PARALLEL_LEVEL` set to
  `--jobs`, which `cmake --build` honors. Scripts that call `ninja`, `make`
  or `xcodebuild` directly should pass `{jobs}` themselves. Check the actual
  backend commands; setting the environment alone does not cap those tools.
- **Inputs:** use `"when": "build"` when a script reads the player's disc or ROM
  (then `--disc` is required and passed as `{disc}`), or `"in-app"` when the
  player chooses it after installing (then `--disc` is refused).
- **Kinds:** `disc-translation`, `emulator-shell`, `decomp-patches`,
  `upstream-engine`, `clean-engine`.
- **Hosts and states:** `verified` (a recorded complete build from that host,
  accepted on the target device), `experimental` (runnable, not yet accepted),
  `planned`, `unsupported`. Only verified and experimental hosts run.
- A game with its own one-command builder can use a single `command` with
  `modes` (`full`, `source-only`) and `options` instead of `steps`.
- **A program folder** (a Windows game: the .exe with its DLLs and data): set
  `"output": "folder"` and name where the backend leaves the finished folder,
  `"folder": "{work}/ExamplePad"`. PadMint checks it, moves it into the build
  record and gives the player the whole folder. A `windows` player target is
  offered only on Windows PCs: the copy runs on the PC that makes it.
- **Programs the player installs** that are not on PATH can be named by path with
  `%VARIABLES%`. Visual Studio, for example, through its `vswhere.exe`:
  `{"name": "%ProgramFiles(x86)%/Microsoft Visual Studio/Installer/vswhere.exe",
  "version_args": ["-latest", "-products", "*", "-requires", "<component>",
  "-property", "catalog_productDisplayVersion"], "min_version": "17",
  "player": true, "hosts": ["windows-x86_64", "windows-arm64"], "note": "..."}`.
  An empty answer counts as not installed.
- Run executable scripts directly so their own `#!/usr/bin/env bash` shebang
  applies. On macOS `/bin/bash` is bash 3.2, which some scripts do not support.
- If a step needs submodules, add a first step
  `["git", "-C", "{repo}", "submodule", "update", "--init", "--recursive"]`: fresh
  worktrees start with empty submodule folders.
- Make sure the repository ignores `build/`: PadMint writes its private
  workspace to `build/padmint/`.

Check it:

```sh
python3 -m padmint check-manifest /path/to/examplepad
python3 -m padmint plan examplepad --repo /path/to/examplepad --revision FULL_COMMIT
```

### iPhone modules on any computer

If the game publishes an iPhone app with no game code and loads its game code from a
library inside the app, let PadMint build that library's surroundings on Windows,
Linux and Macs alike, with no Xcode:

```json
"ios": {
  "hosts": {"macos-arm64": "experimental", "windows-x86_64": "experimental", "linux-x86_64": "experimental"},
  "output": "ipa", "check": "ipa",
  "tools": ["libcxx", "cmake", "ninja"],
  "published_app": "ExamplePad-v{version}-ios-unsigned.ipa",
  "ios_module": {"file": "{work}/module/libexample_game.dylib", "into": "Frameworks/libexample_game.dylib"},
  "steps": [
    {"stage": "compile", "command": ["{python}", "-m", "example_builder", "--toolchain", "{ios_toolchain}",
                                     "--out", "{work}/module/libexample_game.dylib"]}
  ]
}
```

Before the steps, PadMint assembles an iPhone SDK from Apple's open-source headers and
LLVM's libc++ (`{ios_sdk}`) and a CMake toolchain file for its LLVM (`{ios_toolchain}`),
with stubs for the published app's thread-local exports. Your steps compile only the game
library. Afterwards PadMint checks that every name the library imports comes from the
app or the device's C and C++ libraries, strips it, names it `@rpath/<file>` and puts it at
`into` inside a copy of the published app. `scripts/ios-module-probe.py` runs the whole
pipeline with a small probe library and no game code.

### One recipe for Windows, Linux and Mac

A step with `"on"` runs only on the systems it lists (`macos`, `linux`, `windows`);
a step without it runs everywhere. Keep the game's shell script for Macs and Linux, add
a Python step for Windows (Windows has no bash), and share everything else. Two steps
may use the same stage name when they run on different systems, so the player sees
the same stages on every computer:

```json
"steps": [
  {"stage": "translate", "on": ["macos", "linux"],
   "command": ["/bin/bash", "{repo}/scripts/build.sh", "{disc}", "--out", "{work}", "--source-only"]},
  {"stage": "translate", "on": ["windows"],
   "command": ["{python}", "{repo}/scripts/windows/build.py", "{disc}", "--out", "{work}", "--source-only"]},
  {"stage": "configure", "command": ["cmake", "-S", "{repo}/module", "-B", "{work}/module", "-G", "Ninja",
                                     "-DCMAKE_TOOLCHAIN_FILE={ios_toolchain}"]},
  {"stage": "compile", "command": ["cmake", "--build", "{work}/module", "-j", "{jobs}"]}
]
```

Every host the target lists as runnable must have at least one step. Give the
per-system variants of a step the same stage name: PadMint 0.3.9 and older refuse such
a recipe instead of running every system's steps.

**Making a game buildable off a Mac** takes the same four things for every game:

1. **A published app with no game code** that loads the game from a library inside
   the app (BlueWake: `Frameworks/gGZLE01_recomp.dylib`). It must pass
   `padmint audit`. Publishing it is the owner's decision.
2. **Source steps that run on each host**: shell on Macs and Linux, Python (or another
   program PadMint supplies) on Windows, selected with `"on"`. They turn the player's
   game file into the library's C/C++ sources.
3. **A library build with `{ios_toolchain}`**, PadMint's open-source iPhone SDK, the
   same on every host. Add `libcxx` to `tools`.
4. **`ios_module`** naming the library and where it goes in the app. PadMint checks its
   imports against the published app and inserts it.

Until a host has a recorded end-to-end build and a device check, mark it
`experimental`. Games without step 1 stay Mac only, and PadMint lists them on other
computers with the reason.

## 2. Add a catalog entry to PadMint

`catalog/examplepad.json`:

```json
{"schema_version": 1, "id": "examplepad",
 "repo_url": "https://github.com/chrissotraidis/examplepad",
 "reviewed_revision": null, "notes": "Manifest owned by the game repository.",
 "manifest": null}
```

To offer the game in guided setup, add `player_targets` and a positive whole
number for `free_space_gb`. Measure the first player build, including downloaded
tools, fetched sources, temporary build files and the exported output; allow
headroom. The catalog estimate is used by player `doctor` and the initial source
download check. The recipe's `requirements.disk_gb` applies to checkout `doctor`
and may allow more room for development builds.

For tools the player must install, set `player: true` and an actionable `note`
on the recipe requirement. Probe the tool or SDK the backend actually uses;
finding an unrelated Python executable or Xcode's command-line tools is not
enough. PadMint-supplied tools belong in the target's `tools` list instead.

## 3. Promote it

1. Run `python3 -m padmint build` from a clean checkout. The record shows each
   stage, the output check and the release gate result.
2. After a complete build, set `status` to `experimental`; after a build is
   accepted on a device, mark the host `verified` and pin `reviewed_revision`.
3. Before anything is published, every public file must pass
   `python3 -m padmint audit`. Personal builds are never published.
