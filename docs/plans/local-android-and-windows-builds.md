# Plan: KartPad for Android and BlueWake for Windows, built on the player's computer

Status: proposal for Chris, 19 October 2026. Nothing here is implemented yet. It
carries out the rule in [ROADMAP.md](../ROADMAP.md#the-rule): every copy is made on
the player's computer from the player's own game files, and public releases hold
no game code.

Code references are to these commits: PadMint `b32105a`, KartPad `c30f758e`,
BlueWake `095f7014`. Points marked *(inference)* were not checked directly.

## The problem

Two public downloads hold game code today:

| Download | What's inside | Downloads |
|---|---|---|
| KartPad Android APK, v0.7.9 to v0.8.3 (11 releases) | `lib/arm64-v8a/libkartpad_game.so` (about 134 MB): the translated game, plus Mario Kart Wii's original PowerPC code (`kData__text`), data and `StaticR.rel` copied byte for byte | about 22,900 |
| BlueWake Windows zip, v0.4.0 to v0.8.0 | `BlueWake/gGZLE01_recomp.dll` (371 to 481 MB): Wind Waker's code, recompiled, with the game's own source-file and function names | about 13,000 |

KartPad's iOS and Mac downloads from v0.7.9 to v0.7.13 had the same game code
(about 400 downloads). Those are already off the release route, but the files
are still attached to their releases.

These are the files most like the ones Nintendo has targeted before: built
executables of its games. Both projects already have most of what's needed to
stop publishing them.

## Goals

- Android and Windows players can still play, with one PadMint run on their own
  computer.
- No public file holds game code, and CI enforces that.
- Android updates keep installing over the old app and keep saves.
- Nothing from the player's disc, and no personal build, is uploaded anywhere.

## Non-goals

- Cloud builds or hosted personal builds. They would put game code back on a
  server and break "nothing is uploaded" (D15 already rejects this).
- New Android or Windows ports of other games.
- Deleting old releases. They're switched to draft, which can be undone.

## Current state

### KartPad for Android already has an engine-only route

KartPad shipped engine-only APKs from v0.6.0 to v0.7.8 (each about 31 MB; the
release notes call them "the Android app without game code"). The game code came
from the player:

1. PadMint built `KartPad-v…-android-personal.so` (the game pack) on the player's
   Windows, Mac or Linux computer from their disc, with the Android NDK, CMake and
   Ninja (D6).
2. The player copied that file to the phone, tapped the Mario Kart Wii card and
   chose it with **Choose file**.
3. The app copied it into its own storage and loaded it at startup.

That code is still in KartPad's main branch:

- `android/app/src/main/java/dev/kartpad/android/KartPadGamePack.kt`
  - line 35–37: the pack lives at `filesDir/gamepack/libkartpad_game.so` (or in
    `nativeLibraryDir` when it's built in);
  - line 68 on: `import()` copies the chosen file, checks the ELF header and the
    `kartpad_game_pack_info` symbol (line 76), checks the 64-hex pack fingerprint
    against `BuildConfig.PACK_FINGERPRINT` (line 81) and renames it into place
    (line 86).
- `android/app/build.gradle.kts` lines 13–24: `kartpadGamePackApp=true` builds the
  engine-only app; adding `kartpadBundledGamePack` puts the pack inside the APK, which
  is the ready-to-play build. Lines 187–203 add the pack as a native library.
- `scripts/audit-android-package.sh` line 108 and `scripts/audit-android-bundle.sh`
  line 104: the APK audits allow `libkartpad_game.so` only when
  `KARTPAD_ANDROID_ALLOW_GAME_PACK=1`.
- The pack fingerprint (pack ABI 3, kartpad#347) means a pack keeps working
  across app updates until the interface changes.

PadMint's side also exists. `catalog/kartpad.json` line 266 on: the `android` target
runs `kartpad_builder.cli build-pack android` against the published APK (line 283,
`published_app`) and outputs a `.so` plus the game data folder, on macOS, Windows
and Linux (all marked experimental). `padmint/tools.lock.json` pins NDK r29
(0.78 to 1.05 GB download, depending on the computer).

**Why it changed.** KartPad 0.7.9 (kartpad#403, owner decision 4 October 2026)
went back to the bundled APK because "building a game pack has been too hard for
many players, especially on Android". Issues kartpad#366, #386 and #380 show the
friction: PadMint closing in a terminal, not knowing which file to pick, and the
pack and game-data import steps. KartPad's `RIGHTS_AND_LICENSES.md` lines 111–121
record the exception and say it is not a rights clearance.

**What Android allows.** DECISIONS.md S3 verified that an app targeting API 36
can copy a native library into `files/` and load it with `System.load`, with JNI
working in both directions; KartPad 0.6.0 to 0.7.8 shipped that route to
players. Android's documentation:

- Android 10: apps targeting API 29+ can't `execve` files from their writable
  data directory; `dlopen` of a library there is allowed, and Google recommends
  packaging native code in the APK
  ([Android 10 changes](https://developer.android.com/about/versions/10/behavior-changes-10)).
- Android 14: dynamically loaded DEX, JAR and APK files must be read-only; this
  doesn't cover native libraries
  ([Android 14 changes](https://developer.android.com/about/versions/14/behavior-changes-14)).
- Android 17: for apps targeting API 37+, `System.load` throws
  `UnsatisfiedLinkError` if the file isn't read-only
  ([Android 17 changes](https://developer.android.com/about/versions/17/behavior-changes-17)).
  KartPad's importer doesn't mark the pack read-only yet.
- Google Play forbids loading executable code from outside Play
  ([Device and Network Abuse](https://support.google.com/googleplay/android-developer/answer/16559646)).
  KartPad is distributed through GitHub, not Play *(inference: no Play listing
  was found)*, so this doesn't apply today.

### BlueWake for Windows is already split into app and game

The v0.8.0 zip holds `BlueWake.exe` (6 MB) and the game in
`gGZLE01_recomp.dll` (454 MB). The exe's import table doesn't list the game DLL;
the app loads it at runtime and accepts `--module FILE` ("the translated game
module (default gGZLE01_recomp.dll)"). The rest of the zip is Dawn, SDL3, the
DirectX shader compiler, the Visual C++ runtime, licenses and
`dsp/dsp_rom.bin`, `dsp_coef.bin`. The two DSP files match Dolphin's free
replacements in `Data/Sys/GC` exactly (same git blob hashes), so they aren't
Nintendo's ROMs. The exe holds one game name, `d_a_kamoH1`; everything else that
names the game is in the DLL.

BlueWake already has a builder: `scripts/windows/build.py` ([docs/WINDOWS.md](https://github.com/chrissotraidis/bluewake/blob/main/docs/WINDOWS.md)).
It needs Visual Studio 2026 (or 2022) with its clang, Python, Git, CMake and
Ninja, about 15 GB free, and 15 to 40 minutes on a fast PC. It trains a local
optimization profile by playing the game with the app. Draft bluewake#46
("[Parked] Build BlueWake for Windows through PadMint") adds a `windows` target
to `padmint.json`, checks for Visual Studio with `vswhere` before downloading
anything, supports Windows on ARM through x64 emulation, and writes progress
events. It also found that the training module can go over the 2 GB DLL limit.
BlueWake's proposal
([PROPOSAL_SOURCE_ONLY_WINDOWS](https://github.com/chrissotraidis/bluewake/blob/main/docs/status/PROPOSAL_SOURCE_ONLY_WINDOWS_2026-10-04.md))
compares two ways to skip Visual Studio: xwin with LLVM (Microsoft's CRT and SDK
downloaded on the player's PC after they accept Microsoft's license), and
llvm-mingw (redistributable, but a different C runtime). Elliott Tate
co-maintains BlueWake and builds and tests the Windows releases.

PadMint's own state: STATUS.md says BlueWake's Windows route is parked and
Windows players use the ready-made download; `catalog/bluewake.json` offers only
`ios`.

## Options

### KartPad for Android

| Option | How the game code gets in | Signing and updates | Player work | Verdict |
|---|---|---|---|---|
| A. Keep the bundled APK | Chris's release | Chris's key, updates in place | Install one APK | Ships game code. Rejected. |
| B. Engine-only APK, player imports the pack (0.6.0 to 0.7.8) | PadMint builds the pack; the app copies it into its own storage and loads it | Chris's key, updates in place, saves kept, pack survives updates | Run PadMint once per pack interface, move one file to the phone | **Recommended.** Already built and shipped. |
| C. PadMint builds and signs a personal APK | PadMint puts the pack into `lib/arm64-v8a/` and signs with a key made on the player's computer | Different signer: Android refuses to update over Chris's APK, so the first switch means uninstalling (saves must be exported first). Every app update needs a new PadMint run. Needs apksigner, so the Android SDK build tools and a Java runtime | More | Fallback only, if a future Android blocks B |
| D. Build on the phone (Termux) | PadMint in Termux builds the pack on the phone | Same as B | No computer, but about 25 GB free, 8 GB of memory, and an unmeasured, likely long build | Later, after measuring |
| E. Cloud build | A server builds it | — | — | Rejected: uploads the disc and hosts game code |

The roadmap's current wording for this item ("have PadMint put the game part into
it and save the finished APK") is option C. This plan recommends B, because it
keeps Chris's signing key and in-place updates, and it is the route players
already used.

### BlueWake for Windows

| Option | Compiler | Player work | Verdict |
|---|---|---|---|
| A. Keep the full zip | — | Unzip | Ships game code. Rejected. |
| B. Engine zip plus PadMint-built DLL, Visual Studio Build Tools | clang from Visual Studio | Install VS Build Tools once (several GB), then 15 to 40 minutes | **Phase 1.** bluewake#46 is most of it |
| C. Same, with xwin and PadMint's pinned LLVM | LLVM 21.1.8 (already pinned) plus Microsoft's CRT and SDK, fetched on the player's PC | No Visual Studio; PadMint shows Microsoft's license | **Phase 2**, once Microsoft's terms are read and it builds the same DLL |
| D. Same, with llvm-mingw | MinGW C runtime | No Visual Studio | Not recommended: the app and the prebuilt Dawn use the Visual C++ runtime, so mixing them is real porting work |
| E. Full local build of app and DLL (BlueWake's builder as it is) | Visual Studio | Same as B, plus building the app | Works today, but the app needn't be rebuilt; B reuses the published, signed-off exe |

## Recommended design

### KartPad for Android (option B, made easier)

**Release.** Each KartPad release publishes `KartPad-v…-android.apk` built with
`kartpadGamePackApp=true` and no `kartpadBundledGamePack`, signed with the same
key as today, so it installs over 0.8.3. The ready-to-play builds stop. Because
0.8.3 deletes the imported pack folder on first launch (`removeImportedPack`),
players coming from 0.7.9 to 0.8.3 need a new pack once.

**PadMint.** The `android` target stays as it is (it already builds the pack
against the published APK). The finish step gets easier:

1. If a phone is connected over USB with USB debugging on, PadMint installs the
   APK and sends the pack with `adb` *(new: adb comes from Google's platform-tools,
   about 15 MB, which PadMint would pin like its other tools)*. It then opens
   KartPad's import screen with an intent. Without adb it falls back to step 2.
2. Otherwise PadMint shows the pack file and one plain instruction: copy this
   file to the phone (USB, cloud drive or Quick Share), open KartPad, tap the
   Mario Kart Wii card, choose the file.
3. The game data folder goes the same way, or PadMint makes one archive holding
   pack and game data so the player moves one file *(to decide; the app would
   need to accept it)*.

**KartPad app.**

- Accept the pack from **Open with** and **Share** (an intent filter), so a
  player can tap the file in Files or Quick Share instead of finding it in a
  picker.
- After the rename on line 86 of `KartPadGamePack.kt`, call
  `destination.setReadOnly()` so the route keeps working when targetSdk moves to
  37.
- The first screen without a pack names the step plainly and links to PadMint's
  KartPad page.
- Keep the fingerprint check, so a pack from an older interface is refused with
  a clear message.

**Phone without a computer.** Keep the Termux route experimental and measure
building the pack on an 8 GB phone before offering it.

### BlueWake for Windows (option B, then C)

**Release.** Publish `BlueWake-v…-windows-x64-app.zip`: the current zip without
`gGZLE01_recomp.dll`. Remove or move the `d_a_kamoH1` string from the exe, or
allow it explicitly in the release check.

**PadMint.** Finish bluewake#46 against that zip: a `windows` target with
`published_app` set to the app zip; BlueWake's builder compiles only the game DLL
(a new `--module-only` mode, *to build*) and PadMint puts it beside the app in
the player's folder. The app and the DLL must agree on the module interface; the
exe already checks versioned handshakes for its optional paths *(inference: a
whole-module version check also exists or is easy to add)*. Players need a
module built for the same release; PadMint rebuilds it when the interface
changes and reuses it otherwise, like KartPad's pack fingerprint.

**Training.** Local training plays the game with the app on the player's PC and
takes most of the build time. Shipping a reviewed profile would save that time
*(open question: whether a profile counts as game-derived data; it holds counts
for game functions, no code)*.

**Phase 2.** Replace Visual Studio with PadMint's pinned LLVM plus xwin, after
reading Microsoft's terms and checking that the DLL works with the published exe.

### Release check (both repositories, and PadMint's package step)

A script, run in CI on every release job and before `gh release upload`, that
unpacks every asset (APK, AAB, IPA, zip, tar.gz) and fails if any file:

- is named `libkartpad_game.so`, `*_recomp.dll`, `*_recomp.dylib` or a
  known game library name;
- exports `kData__text`, `kData__data`, `kData__rodata`, `kData_StaticR` or
  `kModuleImage`;
- contains more than a small threshold of big-endian PowerPC `mflr r0` prologues
  (`7C 08 02 A6`; the audit found 5,768 in the APK's game code), or the
  `9421ffe0 7c0802a6` pair;
- contains the strings `/Boot/Strap/eu/`, `d_a_obj_`, `fopAcM_`, `d_a_` or a
  game ID's module names, except for a reviewed allow list kept in the
  repository;
- is a disc image, `.dol`, `.rel`, `.wbfs`, `.rvz` or a console key.

It also fails if a recipe declares `public_binaries` as anything but `false`, and
if `KARTPAD_ANDROID_ALLOW_GAME_PACK=1` is set in a release job. KartPad's audits
(`scripts/audit-android-package.sh`, `scripts/audit-android-bundle.sh`) are the
starting point; PadMint's `scripts/package-release.py` and
`scripts/audit-catalog.py` run the same check on what PadMint links to. The
check is a backstop: it catches known patterns, not every possible leak.

## Milestones

Each one is done only when its check passes on real hardware, as the roadmap
requires.

1. **Release check in CI** (KartPad, BlueWake, PadMint). Done when it fails on
   the backed-up v0.8.3 APK and v0.8.0 Windows zip, and passes on v0.7.8's APK and
   the planned app zip.
2. **KartPad engine-only APK again.** Read-only pack, Open with/Share intake,
   clear first screen. Done when, on a physical Android phone: a fresh install
   imports a PadMint pack and game data and reaches a race; an update over 0.8.3
   keeps saves and asks for a pack once; an update over that keeps the pack.
3. **PadMint Android finish step.** adb install and pack transfer, with the
   copy-the-file fallback. Done when `scripts/player-check.sh` passes for Android
   on Windows, Mac and Linux from an empty PadMint folder, and a new player with
   no instructions besides PadMint's page reaches a race.
4. **BlueWake app zip and module-only build.** Done when the app zip passes the
   release check, and a PadMint-built DLL beside it starts the game and saves on
   a real x64 Windows PC (not only the ARM VM), with Elliott's sign-off.
5. **Retire the old downloads.** Switch KartPad v0.7.9 to v0.8.3 and BlueWake's
   Windows releases to draft (backups with checksums exist outside the repos).
   Do not publish the KartPad v0.8.4 draft with its APK.
6. **Wording**, in the same pull requests as the file changes, only once the
   files change: KartPad's README (line 45, "includes KartPad's translated game
   code"), `RIGHTS_AND_LICENSES.md` lines 111–121, BlueWake's README and
   `docs/WINDOWS.md` line 3, PadMint's STATUS (lines 17 and 26), README (lines
   65, 80, 231), `catalog/kartpad.json` (`ready_to_play` at line 10,
   `player_next.android` at line 36, the `publication.reason` at line 396),
   `catalog/bluewake.json` (add `windows`) and `launchers/padmint-android.sh`
   (`kartpad_note`, lines 24–27).
7. **Phase 2 and phone builds.** xwin for BlueWake; a measured Termux pack build
   for KartPad.

## Who is affected

- **Android players with a computer:** one PadMint run, then the same app. More
  work than today; fewer steps than 0.6.0 to 0.7.8.
- **Android players without a computer:** lose access until the phone build is
  measured and works. This is the biggest loss; say so plainly.
- **Players updating from 0.7.9 to 0.8.3:** need a pack once.
- **Windows players:** a 15 to 40 minute build, and Visual Studio Build Tools
  until phase 2.
- **Existing installs keep working.** Drafting releases doesn't remove anything
  from players' devices.

## Draft announcement

Neutral; Chris decides whether to add a reason.

> **KartPad (Android) and BlueWake (Windows) are now built on your computer.**
> From this release, the Android app and the Windows app no longer include the
> game. PadMint makes that part on your own computer from your own disc, the same
> way it already does for iPhone, iPad and Mac. Nothing from your disc is
> uploaded.
>
> What to do: download PadMint, choose KartPad for Android (or BlueWake for
> Windows) and your disc, and follow the steps on the page. If your copy works
> today, it keeps working. Older ready-to-play downloads are no longer offered.
>
> Android without a computer isn't supported yet; we're measuring whether a phone
> can do the build. Questions: the Discord #help channel or the repository's
> issues.

## Risks

- **Player drop-off.** 0.7.9 exists because this route was too hard. Milestone 3's
  adb step and the Open with intake are what make it easier; without them, expect
  the same issues as kartpad#366 and #386.
- **A future Android tightens native loading.** The read-only change covers API
  37. If loading a library from app storage is blocked later, option C (personal
  APK) is the fallback.
- **Old copies stay out there.** Anyone who downloaded a full build keeps it, and
  mirrors may exist. Drafting stops new downloads from these repositories only.
- **The release check misses something.** It looks for known patterns. Keep the
  manual audit before each release until it has caught real cases.
- **BlueWake's DLL size.** The training module can pass 2 GB (bluewake#46).
- **No legal guarantee.** This removes the hosted game code, the thing that has
  drawn takedowns before. The public source repositories remain.

## Open questions for Chris

1. Accept that phone-only Android players lose access until the Termux build is
   measured?
2. Does Elliott agree to a source-only Windows release for BlueWake?
3. Is Visual Studio Build Tools acceptable for phase 1?
4. Draft the old releases only after milestones 2 to 4 pass on devices, or
   earlier?
5. Should the announcement give a reason?
6. Should PadMint pin adb (Google's platform-tools) for the install step?
7. Can a reviewed BlueWake optimization profile be published so players skip
   training?
