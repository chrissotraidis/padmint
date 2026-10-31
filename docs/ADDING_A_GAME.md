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
- **`{python}`** is the Python running PadMint: Apple's Python 3.9 on a Mac and
  PadMint's bundled Python on Windows. Scripts it runs must work on 3.9. A
  script that needs a newer Python should run as `python3` and list `python3`
  with that `min_version` in `requirements.tools`, so the check and the build use
  the same program.
- **Windows Python imports:** bundled Python isolates its module search path.
  Invoke a repository backend by its script path, such as
  `"{repo}/scripts/build-module.py"`. Use `-m` only for a package installed in that
  interpreter. A script importing sibling helpers must explicitly add its own
  directory to `sys.path`; test that path with `python -I` as well as bundled
  Windows Python. Pass `-B` to Python children that import from verified source
  or tool folders, so imports do not create `__pycache__` files there. Isolated
  Python ignores the `PYTHONDONTWRITEBYTECODE` environment variable.
- **Job cap:** every step runs with `CMAKE_BUILD_PARALLEL_LEVEL` set to
  `--jobs`, which `cmake --build` honors. Scripts that call `ninja`, `make`
  or `xcodebuild` directly should pass `{jobs}` themselves. Check the actual
  backend commands; setting the environment alone does not cap those tools.
- **Inputs:** use `"when": "build"` when a script reads the player's disc or ROM
  (then `--disc` is required and passed as `{disc}`), or `"in-app"` when the
  player chooses it after installing (then `--disc` is refused).
  For private files discovered by the backend in a local game installation, use
  `"schema_version": 2` with `"when": "build", "selection": "installed"`. PadMint then shows installed-game
  guidance without a file chooser or `--disc`; the backend must find and validate
  the installation. Omitted `selection` means `"file"`, preserving existing recipes.
  The catalog's `player_game_file` is `"installed"` when all build inputs use this
  mode (`"build"` if any input still needs a selected file). These are private local
  builds and are never eligible for the GitHub build route.
  Existing recipes can remain on schema 1; schema 2 makes older PadMint refuse
  installed-input recipes instead of incorrectly demanding `--disc`.

  Release order matters: ship PadMint with schema 2 support, then the corrected
  game recipe, then change its catalog input mode. AgePad's current v0.1.0 recipe
  still declares `in-app`, although its injector reads the local Mac game and Steam
  installation. Keep `catalog/agepad.json` unchanged until a released schema 2
  recipe declares installed selection; then change only `player_game_file` to
  `installed` and require a clean catalog audit. This does not enable Windows hosts
  or a GitHub build route.
- **Input guidance:** describe the required original file in `inputs[].description`.
  The window uses the latest release recipe for guidance and extension checks,
  falling back to the catalog when that recipe is unavailable.
- **Exact input files:** an optional `inputs[].accepted_sha256` lists the accepted
  full-file SHA-256 digests. PadMint checks the selected file before downloading
  build tools and repeats the check when making the copy. Include every supported
  file variant; do not use a trimmed-disc hash for a full-disc input. A matching
  alternative input without this field remains unrestricted. Folder inputs stay
  with the game's backend. `verified_sha256` remains a record of tested inputs,
  not a restriction. Backends must still validate their own inputs.
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
    {"stage": "compile", "command": ["{python}", "-B", "{repo}/scripts/build-module.py", "--toolchain", "{ios_toolchain}",
                                     "--out", "{work}/module/libexample_game.dylib"]}
  ]
}
```

Before the steps, PadMint assembles an iPhone SDK from Apple's open-source headers and
LLVM's libc++ (`{ios_sdk}`) and a CMake toolchain file for its LLVM (`{ios_toolchain}`),
with stubs for the published app's thread-local exports. Your steps compile only the game
library. Afterwards PadMint checks imports against the app's exports, an explicit list
of known C/runtime symbols and standard C++ namespaces, strips it, names it `@rpath/<file>` and puts it at
`into` inside a copy of the published app. `scripts/ios-module-probe.py` runs the whole
pipeline with a small probe library and no game code.

The module must be a thin arm64 dynamic library for a physical iOS device. PadMint
checks its complete load-command table and minimum iOS version before and after
stripping, before replacing any previous personal IPA. Its minimum must not be
newer than the app's `MinimumOSVersion` (or the linked executable's minimum when
the plist omits it). A plist claiming support below the executable's minimum is
rejected too. The shared toolchain keeps its iOS 16 default for newer apps and
uses the app's lower minimum for older apps; the real compiler probe covers iOS
15 and 16. These metadata checks do not establish runtime symbol availability or
device acceptance.

To keep an existing full-app builder on some systems, schema 2 accepts an optional
`"on": ["windows", "linux"]` inside `ios_module` (with either `file`/`into` or
`result`). Omit it to keep module packaging on every host. The list must be
non-empty, unique, and contain only `macos`, `windows`, or `linux`. On other
systems, PadMint runs the normal recipe command and its modes/options, without
preparing the portable SDK or inserting a module. Use a small game-owned command
dispatcher to select the backend and preserve existing Mac build options such as
training; `steps` targets still do not support modes/options. The tool download
plan and both tool-install commands use this same selection.

Ship this selection together with PadMint's initial schema 2 support, before any
game recipe uses it. Older schema 1 PadMint refuses the recipe safely; an earlier
schema 2 implementation could ignore `on` in the `file`/`into` form. If schema 2
ships without this feature, use a newer schema before publishing such recipes.

Unknown C imports fail the build; a missing game callback must be exported by the
app, never added to the runtime list. The list's pinned public source references
are beside `_RUNTIME_IMPORTS` in `padmint/ios_module.py`. Verify new runtime names
before extending it. The C++ namespace classification is a heuristic: it does not
verify every symbol's availability on the target iOS version. Passing the import
check still requires device install, launch and gameplay acceptance.

Some games choose a different library name for each supported disc revision and
need an identity file beside it. Use schema 2 and
`"ios_module": {"result": "{work}/module-result.json"}` instead of `file`/`into`.
After a successful build, write this result (the hashes below are placeholders):

```json
{
  "file": "module/selected.dylib",
  "into": "game-r2.dylib",
  "sha256": "<SHA-256 of the compiled module>",
  "companions": [
    {"file": "module/identity.txt", "into": "game-r2.dylib.dol-sha256",
     "sha256": "<SHA-256 of the identity file>"}
  ]
}
```

Source paths use forward slashes, relative to the result file, and must resolve
inside this build's `{work}` folder. Write the result last, after checking the
selected input and completing all outputs. PadMint verifies every hash before
the import check and insertion. Companion files are data, not extra libraries;
destinations must be distinct and cannot replace any file in the published app.
The module is installed executable (`0755`) and companions as data (`0644`);
the base app's bytes and ZIP metadata are preserved.

Result hashes identify the backend's files **before** PadMint strips local symbols
and sets the library's install name. Companion contents are unchanged. For example,
MeleePad's companion identifies its original game executable, not the final dylib.
Schema 1 and the existing fixed `file`/`into` form continue to work unchanged.

### Checking Windows support across releases

Keep local Windows builds separate from builds started in a browser that run on
GitHub Cloud Build. Set `github_build: true` in the catalog only for an iOS build whose
game input is selected in the app. The hosted helper checks the selected release's
recipe before setup and uses that same release for the build. The workflow's test
matrix comes from the catalog; its player-facing choice menu must also include the
game. Catalog, runner and tool changes rerun the hosted builds.

For personal output that must remain private, also set `github_build_private: true`
and supply an `off_mac` guide describing private repository import and Actions
usage. Public or unknown-visibility manual runs stop before setup. PR and scheduled
checks compile without uploading the app. Record a successful clean hosted build
before describing the route as validated.

A game's separate GitHub workflow can be listed in the cloud category with
`off_mac.github_workflow: true`. Its `off_mac.url` and localized text must explain
which repository and workflow to use. This is a link to the game's own route;
it does not add it to PadMint's shared build menu or claim its normal recipe can
build without inputs. Do not combine it with `github_build`.

For local iOS builds, prefer an exact catalog `ios_hosts` list, for example
`["macos-arm64", "windows-arm64"]` when only those computers have the required
evidence. It is a nonempty list of unique host IDs and requires an `ios` player
target. The list overrides both `ios_off_mac` and `ios_intel_mac`; include every
host you intend to offer, including Apple Silicon. A Windows ARM64 entry does not
enable Windows x64 or Linux. Android phones remain excluded from iOS builds.
The UI names the permitted computers when a route is unavailable here.

Without `ios_hosts`, existing entries keep their behavior: Apple Silicon by
default, Intel Mac with `ios_intel_mac: true`, and Windows/Linux on both x64 and
ARM64 with `ios_off_mac: true`. Every offered host must be runnable in the selected
release recipe. A runnable recipe is not a device acceptance result.

```sh
python3 scripts/audit-catalog.py --json > catalog-audit.json
python3 scripts/player-flow-probe.py "/tmp/PadMint player probe"
```

The daily catalog audit records every game's selected release and declared host
states. It rejects missing base-app assets, mismatched game IDs and advertised
routes the published recipe cannot use. Its report explicitly leaves runtime
testing unverified.

The player-flow probe uses a tiny synthetic repository with no network downloads.
It exercises real cloning, stages, package checks, failure/retry, source recovery
and paths with spaces. On Windows, run it with the ZIP's included
`app/python/python.exe` and `--app` pointing at that extracted `app` directory;
Git must be on PATH. CI runs this on Windows x64 and ARM64 hosts and Linux. The
Windows ZIP currently bundles x64 Python, including when run under ARM64 emulation.
These checks complement each game's complete private-input build and device
install/launch test; the synthetic IPA is deliberately not runnable.

When a source download needs recovery, PadMint keeps previous files beside it in
a `.recovered-<id>` folder. Failed replacements leave the original in place.
These folders can contain private game files; inspect them before removing them.

### One recipe for Windows, Linux and Mac

`windows-*` in a target's `hosts` means **this Windows computer can run the
build**. It does not create a Windows desktop game. The target still names its
player device (`ios`, `macos`, `android` or `windows`); an iPhone target built
with Windows tools produces an iPhone/iPad `.ipa`. Label that copy **Build
here** in the app or release notes, never “Windows version”. A separate **GitHub
Mac** route means GitHub's macOS runner performs the build after PadMint starts
the workflow.

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

Before publishing a recipe, run the pinned PadMint manifest check from that game's
CI, then build from a clean release checkout on every host the recipe advertises.
An invalid host key such as `windows-x64` must fail before a release goes out;
the valid host names are `windows-x86_64` and `windows-arm64`. Update
[WINDOWS.md](WINDOWS.md) and [COMPATIBILITY.md](COMPATIBILITY.md) with the new
route only after the matching app or shell, recipe and physical-device check are
all recorded.

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
headroom. If targets need different amounts, add an optional
`free_space_gb_by_target` map, for example `{"macos": 12}`; unlisted targets use
`free_space_gb`. Only targets in `player_targets` may have overrides. The same
estimate appears in the window, player `doctor`, the initial source download
check and disk-full guidance. Cached source keeps the existing resume behavior;
the initial budget is not required again after downloading it. The recipe's
`requirements.disk_gb` applies to checkout `doctor` and may allow more room for
development builds.

For tools the player must install, set `player: true` and an actionable `note`
on the recipe requirement. Probe the tool or SDK the backend actually uses;
finding an unrelated Python executable or Xcode's command-line tools is not
enough. PadMint-supplied tools belong in the target's `tools` list instead.

An `ios` target whose recipe requires `xcodebuild` gets one check for free: PadMint
also checks Xcode's iOS platform (`xcrun --sdk iphoneos`), which Xcode installs
separately, unless the recipe already probes `iphoneos` itself. Mac copies don't
get this check. PadMint checks every program the player installs right after
reading the release recipe, before it downloads the game's source.

A prerequisite may specify `"input_formats": ["exe"]` when only those selected input
formats need it. PadMint refreshes the prerequisite list after file selection and checks
it again before downloading source or running the build. Without a selected file, or
when selecting a folder, all host prerequisites are shown. Omit this field for tools
needed by every input. The game backend must still check its own tools; this metadata
does not validate file contents or replace input hashes.

## 3. Promote it

1. From PadMint's current `main` on an Apple Silicon Mac, run
   `scripts/player-check.sh GAME PLATFORM GAME_FILE CHECKOUT`
   before tagging, and `scripts/player-check.sh GAME PLATFORM GAME_FILE` after publishing
   and before announcing. It builds the way a player's PadMint does: Apple's Python 3.9
   (what `PadMint.command` runs), an empty PadMint folder and a fresh copy of the source.
   `python3 -m padmint build` from your own checkout usually runs a newer Python with
   warm caches, so its success does not show that players can build. The record shows
   each stage, the output check and the release gate result.
   For changes to Mac startup, targets, recipes or completion instructions, also
   test the newly extracted candidate Mac ZIP through `PadMint.command` and its
   page. Check native Apple Silicon, an actual Rosetta parent restarting natively,
   and real Intel showing an explicit reason for unsupported targets while
   retaining supported choices. `scripts/check-macos-launch.py` covers these
   startup checks; it does not build or play a game.
   Complete **Make my copy** with an isolated empty PadMint folder, then repeat
   with the same folder, unchanged game checkout and inputs. Verify cache reuse,
   a new output, and preservation of the first output and existing player data.
2. After a complete build, set `status` to `experimental`; after a build is
   accepted on a device, mark the host `verified` and pin `reviewed_revision`.
   Match acceptance to the change: follow affected completion instructions from
   missing game data through import, check changed controls or gameplay in the
   relevant profiles, and check clean quit/relaunch when persistence is affected.
   A focused installer, target-selection or controls fix does not require finishing
   a full race. Record CI, build/package, import/relaunch, gameplay, audio and
   performance results separately, including checks not performed. A fault in an
   affected flow blocks its acceptance; a successful build alone does not establish
   gameplay support or justify promoting an untested host.
3. Before anything is published, every public file must pass
   `python3 -m padmint audit`. Personal builds are never published.
4. Run `PADMINT_HOME=$(mktemp -d) python3 scripts/audit-catalog.py` after changing a
   catalog entry, a recipe or PadMint itself. It reads every game's latest release
   recipe the way a player's PadMint does and lists what would confuse or stop a
   player, plus where each target builds.

## Intel Mac iPhone builds

Set catalog `ios_intel_mac: true` only for a game whose published iOS
recipe declares `macos-x86_64` as experimental or verified. This is separate
from `ios_off_mac` (Windows/Linux) and does not enable a native Mac app.
The Intel route uses Xcode and its iOS platform. Publish the matching game
recipe before releasing the catalog change; the release recipe still decides
whether a build can start.

## 4. When a game's release changes what it publishes

PadMint describes each game from two places: the game's latest release (its recipe
and its files) and the catalog entry here. When a release adds or drops a
ready-to-play download, or a target or build computer, update the catalog in the
same change:

- `player_targets`: every target the recipe builds for players. A target the
  recipe builds but PadMint should not offer yet goes in `unoffered_targets`
  with the reason, for example `{"macos": "needs Homebrew tools until 0.8.0"}`.
- `ready_to_play`: only for platforms whose release has a file players install
  directly, listed in `platforms`. An IPA made for PadMint (`…-for-padmint.ipa`)
  has no game in it and does not count.
- `off_mac`: a message and link for Windows, Linux and Intel Mac players when
  the game has its own route without an Apple Silicon Mac (HaloPad's Xbox edition
  builds with GitHub Cloud Build).
- `before_build`: the Homebrew line from the game's README. On a Mac the card then
  says **Needs Xcode + Homebrew**, and the page offers one line with only the missing
  packages. Without it the card says **Needs Xcode**, and the catalog check fails if the
  recipe asks players for anything besides Xcode.
- `player_next`: the steps after a build, per target. For `ios`, `"sideload": true`
  puts PadMint's Sideloadly steps first and the game's own steps after them; without
  `player_next.ios` a game gets only the Sideloadly steps.
- README and STATUS.md say the same thing as the catalog.

The **Catalog check** workflow runs `scripts/audit-catalog.py` every day and on
every catalog change. It fails when the catalog promises a download the latest
release doesn't publish, offers a target or computer the recipe lacks, or hides a
target the recipe builds. A failing run means a game's release and PadMint
disagree: fix the catalog (or the game's release) before players notice.
