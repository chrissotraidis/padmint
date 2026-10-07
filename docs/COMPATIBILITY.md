# Build compatibility

Public recipe snapshot: **4 October 2026**, rechecked against each game's latest release
recipe with PadMint **v0.3.5** (KartPad rechecked at v0.7.9: same hosts as v0.7.8).
The table describes the recipe shipped with each game's latest public release.
It does not promote a declared host to tested gameplay support. See
[catalog-wide compatibility work](https://github.com/chrissotraidis/padmint/issues/75)
for the remaining implementation and acceptance work.

**Choose by the game and device you want to play on.** A Windows or Linux
PadMint download does not make a Mac-only game recipe portable.

- **Experimental:** the recipe permits this combination; check the limitations
  below before downloading tools. This label alone is not proof of a completed build.
- **Planned:** no runnable player route for that combination.
- **Unavailable:** the recipe does not permit the host, or does not declare it.
- Host pairs are **x64 / ARM64**, in that order. Mac here means **Apple Silicon**;
  Intel Mac is listed separately where declared. iOS means iPhone/iPad output,
  subject to each game's device requirements.

## Current player recipes

Every release link is the exact version checked. macOS targets marked planned
are omitted. KartPad's declared macOS target is included for completeness;
guided setup offers its Android and iOS targets only.

| Project and release | Output | Mac ARM64 | Windows x64 / ARM64 | Linux x64 / ARM64 |
|---|---|---|---|---|
| [AgePad v0.1.0](https://github.com/chrissotraidis/agepad/releases/tag/v0.1.0) | iOS IPA | Experimental | Unavailable / Unavailable | Unavailable / Unavailable |
| [AnnePad v0.2.1](https://github.com/chrissotraidis/annepad/releases/tag/v0.2.1) | iOS IPA | Experimental | Unavailable / Unavailable | Unavailable / Unavailable |
| [BallPad v1.1.1](https://github.com/chrissotraidis/ballpad/releases/tag/v1.1.1) | iOS IPA | Experimental | Unavailable / Unavailable | Unavailable / Unavailable |
| [BananaPad v0.2.1](https://github.com/chrissotraidis/bananapad/releases/tag/v0.2.1) | iOS IPA | Experimental | Unavailable / Unavailable | Unavailable / Unavailable |
| [BarrelPad v0.2.0](https://github.com/chrissotraidis/barrelpad/releases/tag/v0.2.0) | iOS IPA | Experimental | Unavailable / Unavailable | Unavailable / Unavailable |
| [BearBirdPad v0.2.2](https://github.com/chrissotraidis/bearbirdpad/releases/tag/v0.2.2) | iOS IPA | Experimental | Unavailable / Unavailable | Unavailable / Unavailable |
| [BellPad v0.2.1](https://github.com/chrissotraidis/bellpad/releases/tag/v0.2.1) | iOS IPA | Experimental | Unavailable / Unavailable | Unavailable / Unavailable |
| [BlueWake v0.1.0](https://github.com/chrissotraidis/bluewake/releases/tag/v0.1.0) | iOS IPA | Experimental | Unavailable / Unavailable | Unavailable / Unavailable |
| [BrawlerPad v0.2.0](https://github.com/chrissotraidis/brawlerpad/releases/tag/v0.2.0) | iOS IPA | Experimental | Unavailable / Unavailable | Unavailable / Unavailable |
| [CTRPad v0.2.2](https://github.com/chrissotraidis/ctrpad/releases/tag/v0.2.2) | iOS IPA | Experimental | Unavailable / Unavailable | Unavailable / Unavailable |
| [CTRPad v0.2.2](https://github.com/chrissotraidis/ctrpad/releases/tag/v0.2.2) | macOS app | Experimental | Unavailable / Unavailable | Unavailable / Unavailable |
| [DinoPad v0.2.0](https://github.com/chrissotraidis/dinopad/releases/tag/v0.2.0) | iOS IPA | Experimental | Unavailable / Unavailable | Unavailable / Unavailable |
| [GoldenPad v0.2.2](https://github.com/chrissotraidis/goldenpad/releases/tag/v0.2.2) | iOS IPA | Experimental | Planned / Unavailable | Planned / Unavailable |
| [HarkinianPad v0.2.0](https://github.com/chrissotraidis/harkinianpad/releases/tag/v0.2.0) | iOS IPA | Experimental | Unavailable / Unavailable | Unavailable / Unavailable |
| [KartPad v0.7.9](https://github.com/chrissotraidis/kartpad/releases/tag/v0.7.9) | iOS IPA | Experimental | Experimental / Experimental | Experimental / Experimental |
| [KartPad v0.7.9](https://github.com/chrissotraidis/kartpad/releases/tag/v0.7.9) | macOS app | Experimental | Unavailable / Unavailable | Unavailable / Unavailable |
| [KartPad v0.7.9](https://github.com/chrissotraidis/kartpad/releases/tag/v0.7.9) | Android game pack | Experimental | Experimental / Experimental | Experimental / Experimental |
| [MaskPad v0.2.0](https://github.com/chrissotraidis/maskpad/releases/tag/v0.2.0) | iOS IPA | Experimental | Unavailable / Unavailable | Unavailable / Unavailable |
| [MeleePad v0.2.1](https://github.com/chrissotraidis/meleepad/releases/tag/v0.2.1) | iOS IPA | Experimental | Unavailable / Unavailable | Unavailable / Unavailable |
| [PaperPad v0.2.1](https://github.com/chrissotraidis/paperpad/releases/tag/v0.2.1) | iOS IPA | Experimental | Unavailable / Unavailable | Unavailable / Unavailable |
| [SpaghettiPad v0.2.1](https://github.com/chrissotraidis/spaghettipad/releases/tag/v0.2.1) | iOS IPA | Experimental | Unavailable / Unavailable | Unavailable / Unavailable |
| [StarshipPad v0.2.0](https://github.com/chrissotraidis/starshippad/releases/tag/v0.2.0) | iOS IPA | Experimental | Unavailable / Unavailable | Unavailable / Unavailable |
| [SunPad v0.2.0](https://github.com/chrissotraidis/sunpad/releases/tag/v0.2.0) | iOS IPA | Experimental | Unavailable / Unavailable | Unavailable / Unavailable |

**Android as the build host:** only KartPad's phone route is offered, through
Termux and a Linux ARM64 environment. It remains experimental: the recorded
build/export/import check used a phone-sized emulator, not physical Android
hardware or verified racing. Allow about 25 GB free and 8 GB RAM; follow the
[phone guide](../README.md#android-phone-only-experimental). Linux ARM64 CI
does not establish Android/Termux acceptance.

**Intel Mac:** KartPad's Android recipe declares it experimental. The other
Mac build routes in this snapshot require Apple Silicon.

**No build needed:** CaesarPad, DaggerPad, DevilTouch, Emerald Tablet, KidPad,
PeonPad and VaultPad publish apps without game files; PadMint lists them with
download and data-import steps. **SnapPad** downloads remain paused and no public
PadMint recipe is available.

## Status by game

Where each tracker app stands on the shared pipeline, and the smallest next step.
Games are grouped by family: one game proves a family, and the rest follow it.
Off-Mac work resumed on 7 October
([D16](DECISIONS.md#d16-iphone-and-ipad-copies-from-windows-bluewake-first-owner-decision-7-oct-2026)),
BlueWake first; the order of work is in
[iPhone and iPad copies from a Windows PC](IPHONE_FROM_WINDOWS.md).
**Off-Mac** means a build on a Windows or Linux computer, as recorded below.

**GameCube and Wii recompilations** (reference: BlueWake)

| Game | Status | Smallest next step |
|---|---|---|
| KartPad | **Ships ready-to-play builds from v0.7.9** (Android, iPhone/iPad, Mac) on [its releases](https://github.com/chrissotraidis/kartpad/releases/latest); PadMint is optional. The v0.7.9 APK includes the game code, so on Android PadMint's useful output is the `KartPad game data` folder. Earlier: Android packs built on Mac, Windows and Linux raced on an Android 16 emulator; iPhone off a Mac is experimental | A data-only Android target in KartPad's recipe, so PadMint skips the 1 GB NDK and the unused pack |
| BlueWake | **First game for iPhone/iPad from Windows** ([draft #100](https://github.com/chrissotraidis/bluewake/pull/100), which includes #42). Its iPhone module built through PadMint's open-source SDK on Linux x64 and on an Apple Silicon Mac (Mac: 757 units in 57 minutes), and on Windows on ARM its Windows step made the same verified source. Windows players' ready-to-play Windows builds come from BlueWake's own releases | Finish the Windows module build and play it on an iPad ([checklist](IPHONE_FROM_WINDOWS.md#bluewake-first)) |
| SunPad | iPhone module built on Linux ARM64 through PadMint's open-source SDK and inserted into the v0.2.0 app, IPA check passed ([draft #57](https://github.com/chrissotraidis/sunpad/pull/57)) | A device check, then a release under its tracker row (releases are paused) |
| MeleePad | Mac only. Its game module also carries Slippi's native code: `build-slippi-dependencies.py` builds open-vcdiff, semver and Slippi's Rust library for iOS with `xcrun`, and `package-ios.sh` adds Slippi's settings, bootloader and game files to the app (with `ditto` and `codesign`, which are Mac-only) | Three parts: a pinned Rust toolchain for `aarch64-apple-ios` in PadMint, the Slippi C++ libraries through `{ios_toolchain}`, and module insertion that can add several files (or a portable packager). Then SunPad's [#57](https://github.com/chrissotraidis/sunpad/pull/57) changes apply |

**N64 recompilations** (reference: GoldenPad)

| Game | Status | Smallest next step |
|---|---|---|
| GoldenPad | Mac only: builds the whole app with Xcode from the generated sources | A published app without game code that loads a module (the SpaghettiPad #29 pattern); about one to two days, plus its tracker release decision |
| AnnePad, BananaPad, BearBirdPad, DinoPad | Mac only | Follow GoldenPad once it is proven |

**Engine and decompilation ports** (reference: SpaghettiPad)

| Game | Status | Smallest next step |
|---|---|---|
| SpaghettiPad | [Draft #29](https://github.com/chrissotraidis/spaghettipad/pull/29) builds iPhone modules on Windows and Linux x64/ARM64 | A complete released recipe with matching runtime delivery |
| HarkinianPad | Resources build on five hosts ([#35](https://github.com/chrissotraidis/harkinianpad/pull/35)); app is Mac only | Follow SpaghettiPad #29 |
| MaskPad, StarshipPad, PaperPad, BrawlerPad, BarrelPad, BellPad, BallPad | Mac only | Follow SpaghettiPad #29. StarshipPad's merged recipe fix (#22) waits on its tracker row |
| CTRPad | Mac only (iPhone/iPad app and Mac app) | Follow SpaghettiPad #29 |
| AgePad | Mac only by design: it packages the Mac edition from Steam | None planned off a Mac |

**Listed, not available yet** (the page's "Not available yet" section, with
where each stands and a link): GalaxyPad (118 address-named references need a
decision), F0X (decompiled-context patch lines need a decision), EctoPad (needs a
bootstrap script first), RAtouch (license-notice review before PadMint lists its
install steps), UTP (owner decision on official builds), OpenRCT2 Touch (no iPad
download) and SnapPad (downloads paused).

**HaloPad** (ProjectReach) builds for iPhone, iPad and Mac on Apple silicon Macs from
the player's own Halo Custom Edition installer and product key, experimental: Mac only by
design, since it translates the player's own game. Its Xbox edition is built in the same
run from the upstream halo-ce-universal engine, fetched on the player's Mac; the player
adds their own disc image in the app.

**No build needed:** CaesarPad, DaggerPad, DevilTouch, Emerald Tablet, KidPad,
PeonPad and VaultPad appear in the PadMint page with download and data-import
steps.

**CTRPad** (from PadMint 0.4.2) builds the whole app on an Apple Silicon Mac from
its public source: an unsigned IPA for iPhone and iPad, or a ZIP of the Mac app.
Players choose their own NTSC-U disc image in the app; the build does not read it.
Its releases publish the recipe only. On 5 October, with Xcode 27, PadMint built
both targets from a clean checkout in about a minute each, both outputs passed
`padmint audit`, and the IPA opened to its disc prompt on the iOS 27.0 Simulator.
The Mac copy from released PadMint 0.4.3 started the game from the owner's disc
image and ran its demo race; driven with the keyboard, a v0.2.1 Mac copy went
through the menus into an Arcade race on Crash Cove that responded to accelerate
and steering. From v0.2.1, an iPhone/iPad build first checks for
Xcode's iOS platform and says how to add it. On an iPhone 14 (iOS 26.6.2), the
v0.2.1 app PadMint built, signed with a development profile and installed over
CTRPad 0.1.0, kept the imported disc and touch layout and ran the title menu,
intro and Crash Cove demo race at 30 fps with sound. Touch input was not driven
in that run. v0.2.2 (Mac window title without "| Internal") was then installed
over it the same way and opened with the same settings at 30 fps.

## Recorded Mac builds, 4 October

On 4 October, the public PadMint **v0.3.5** Mac package ran `make <game> ios` for
every game it builds, one after another, against each game's latest public
release recipe. The host was an Apple Silicon Mac (macOS 26.6.2, **Xcode 27.0**)
that already had each README's Homebrew packages; some games reused earlier work.

| Game (release) | Build | Minutes | iOS 27 startup |
|---|---|---|---|
| AnnePad v0.2.1 | Completed | 36.5 | At risk |
| BallPad v1.1.1 | Completed | 4.9 | Scene callback in code |
| BananaPad v0.2.1 | Completed | 30.7 | At risk |
| BarrelPad v0.2.0 | Completed (cached) | 0.9 | At risk |
| BearBirdPad v0.2.2 | Not run: the test cartridge file on this Mac is half size, and PadMint refused it with the right message | — | — |
| BellPad v0.2.1 | Completed (cached) | 1.7 | Scene callback in code |
| BrawlerPad v0.2.0 | Completed | 13.8 | At risk |
| GoldenPad v0.2.2 | Completed | 6.6 | SwiftUI app (scene-based) |
| HarkinianPad v0.2.0 | Completed | 22.8 | At risk |
| KartPad v0.7.9 | Completed (cached): IPA and game data folder | 0.9 | Declared |
| MaskPad v0.2.0 | Completed | 21.5 | At risk |
| MeleePad v0.2.1 | Completed | 25.1 | At risk |
| PaperPad v0.2.1 | Completed | 4.7 | At risk |
| SpaghettiPad v0.2.1 | Completed | 25.6 | Declared |
| StarshipPad v0.2.0 | Completed: the earlier SDK-selection failure no longer happens | 12.5 | At risk |
| SunPad v0.2.0 | Completed | 32.9 | At risk |

Not run: DinoPad (no input file on this Mac), AgePad and BlueWake (skipped when
free space fell under the run's 30 GB guard). These are completed builds and
package checks only: no app was installed or played in this run.

**iOS 27 startup.** Apple requires apps built with the iOS 27 SDK to start through
UIKit scenes. *At risk* means the app was linked with the iOS 27 SDK and PadMint
found no scene startup, so it may not open on iOS or iPadOS 27. SpaghettiPad
crashed on launch for this reason until its fix
([#26](https://github.com/chrissotraidis/spaghettipad/issues/26)), and SunPad
[#54](https://github.com/chrissotraidis/sunpad/issues/54) looks the same. Not
checked on an iOS 27 device here (this Mac has no iOS 27 Simulator). Apps built
with Xcode 26 are not affected, and iOS 26 devices are not affected. The fix is
per game: add scene startup, as SpaghettiPad v0.2.1, StarshipPad
[#22](https://github.com/chrissotraidis/starshippad/pull/22) and SunPad
[#55](https://github.com/chrissotraidis/sunpad/pull/55) did, then release a new
recipe. From 0.3.7, PadMint's finish screen tells the player when their copy is
at risk.

**Fixed and released, 4 October.** Each game now starts through UIKit scenes,
and the version below is its latest release, so PadMint builds it:

| Game | Fix | Release | iOS 27.0 Simulator |
|---|---|---|---|
| AnnePad | [#17](https://github.com/chrissotraidis/annepad/pull/17) | [0.2.2](https://github.com/chrissotraidis/annepad/releases/tag/v0.2.2) | Opens (Choose ROM) |
| BananaPad | [#20](https://github.com/chrissotraidis/bananapad/pull/20) | [0.2.2](https://github.com/chrissotraidis/bananapad/releases/tag/v0.2.2) | Opens (Choose ROM) |
| BarrelPad | [#20](https://github.com/chrissotraidis/barrelpad/pull/20) | [0.2.1](https://github.com/chrissotraidis/barrelpad/releases/tag/v0.2.1) | Opens (Game ROM) |
| BearBirdPad | [#25](https://github.com/chrissotraidis/bearbirdpad/pull/25) | [0.2.3](https://github.com/chrissotraidis/bearbirdpad/releases/tag/v0.2.3) | Opens (title menu) |
| BrawlerPad | [#16](https://github.com/chrissotraidis/brawlerpad/pull/16) | [0.2.1](https://github.com/chrissotraidis/brawlerpad/releases/tag/v0.2.1) | Opens (first-run setup) |
| DinoPad | [#14](https://github.com/chrissotraidis/dinopad/pull/14) | [0.2.1](https://github.com/chrissotraidis/dinopad/releases/tag/v0.2.1) | Not run (no input on the build Mac) |
| HarkinianPad | already on main (pinned forks) | [0.2.1](https://github.com/chrissotraidis/harkinianpad/releases/tag/v0.2.1) | Opens (first-run dialog) |
| MaskPad | [#17](https://github.com/chrissotraidis/maskpad/pull/17) | [0.2.1](https://github.com/chrissotraidis/maskpad/releases/tag/v0.2.1) | Opens (ROM prompt) |
| MeleePad | [#42](https://github.com/chrissotraidis/meleepad/pull/42) | [0.2.2](https://github.com/chrissotraidis/meleepad/releases/tag/v0.2.2) (with the app) | Opens (home screen) |
| PaperPad | [#19](https://github.com/chrissotraidis/paperpad/pull/19) | [0.2.2](https://github.com/chrissotraidis/paperpad/releases/tag/v0.2.2) | Opens (Choose ROM) |
| StarshipPad | [#22](https://github.com/chrissotraidis/starshippad/pull/22) | [0.2.1](https://github.com/chrissotraidis/starshippad/releases/tag/v0.2.1) | Opens (setup) |
| SunPad | [#55](https://github.com/chrissotraidis/sunpad/pull/55) | [0.2.1](https://github.com/chrissotraidis/sunpad/releases/tag/v0.2.1) (with the app) | Opens (game screen) |

The SDL-based games share one SDL 2.32.10 backport ([fork commit](https://github.com/chrissotraidis/SDL/commit/c6756fcd3de8090a8f72ac1a0b6fb6e50f0021d1));
MeleePad and SunPad use their own scene delegates. "Opens" means a Simulator build
of the merged source keeps running on iOS 27.0 and shows its first screen, where an
app with the old startup stops at launch. No physical iOS 27 device was used. A copy
built before these releases may not open on iOS 27: build the game again with
PadMint and install it over the old one. PadMint's finish screen still warns if a
copy may not open on iOS 27.

## Recorded KartPad builds on x64

On 3 October, public PadMint **v0.3.1** made both KartPad **v0.7.4** outputs on
**Ubuntu 24.04 x86-64** (a Docker container under Rosetta on an Apple Silicon Mac,
so every PadMint-downloaded x64 tool really ran), from a fresh PadMint home and the
Europe **RMCP01 revision 0** WBFS, with six build jobs:

| Output | Result |
|---|---|
| Android game pack | Completed in about 18 minutes: AArch64, 16 KB-aligned, with the 2,043-file game data folder |
| iPhone/iPad IPA | Completed in about 32 minutes; PadMint's IPA check passed |
| That Android pack, played | Added with **Help → Replace Game Pack** in KartPad 0.7.4 on an Android 16 emulator; Luigi Circuit raced at about 60 FPS |

A Windows 11 on ARM VM cannot stand in for a Windows x64 PC: PadMint's bundled
x64 Python still reports ARM64 there, so it builds the ARM64 way. **Native Windows
x64 and Intel Mac builds remain unverified**, and the IPA was not installed on a
device in this check.

## Recorded Android pack builds

On 3 October, the public PadMint **v0.2.9** packages completed the normal
`make kartpad android` command with the public **KartPad v0.7.3 / build 246**
recipe and Europe **RMCP01 revision 0** WBFS input, using two build jobs.
The release selected source `9f973c4ecc46284edfba06eb7dede67f629eb4c5`.

| Build host | Setup | Result |
|---|---|---|
| macOS 26.6.2, ARM64, Apple Python 3.9.6 | Cached tools; fresh game checkout and build | Pack and data export completed |
| Ubuntu 24.04, ARM64, Python 3.12.3 | Provisioned container; fresh PadMint home and tool downloads | Pack and data export completed |
| Windows 11, ARM64, bundled Python 3.13.15 | VM with a fresh PadMint home; Windows x64 NDK compiler under emulation | Pack and data export completed; build phase about 96 minutes |

All three outputs passed ELF/AArch64 and 16 KB alignment checks. Each set of
**2,043** exported game-data files matched the build-cache hashes, and the recomputed
pack interface matched the actual published Android app. The runtime-state
symbol check also passed. Generated personal outputs remain private.

These are completed player commands and static output checks. None of the outputs
was played on a physical Android device in this run. They do not establish
Windows x64, Linux x64, Intel Mac or Android/Termux acceptance. The timings are
observations from different environments, not a performance comparison.

## Known limits and useful evidence

| Route | What is established | What remains |
|---|---|---|
| PadMint v0.2.9 | Released Windows/macOS/Linux ZIPs and checksums; packaged player-flow tests on Windows and Linux | These checks use fixtures and do not build every game |
| KartPad iOS off a Mac | Experimental route previously tried on Windows 11 ARM and Ubuntu with iPhone 14; a Windows 11 Surface Laptop 2 user [reports a v0.7.3 IPA build and updates on iPhone/iPad](https://github.com/chrissotraidis/kartpad/issues/310#issuecomment-5961520278) | The Surface report has no gameplay check and reports an exit opening the import menu; independent Intel/AMD build-and-play and broader device acceptance remain open |
| KartPad iOS folder import | [Reporter confirmed the app-folder workaround](https://github.com/chrissotraidis/kartpad/issues/380#issuecomment-5945178374) on an M2 iPad Air | The disabled Files-picker Open button remains an app bug |
| SpaghettiPad v0.2.1 | [Reporter confirmed both iPhone and iPad work](https://github.com/chrissotraidis/spaghettipad/issues/26#issuecomment-5955452885) after the SDK 27 startup fix | This validates those reported devices, not every host or device |
| SpaghettiPad off-Mac work | [Draft #29](https://github.com/chrissotraidis/spaghettipad/pull/29): native Windows/Linux x64 and ARM64 module builds, resource generation and portable package fixtures | Complete released PadMint recipe, matching runtime delivery and target-device acceptance of each host's output |
| HarkinianPad | [Merged #35](https://github.com/chrissotraidis/harkinianpad/pull/35): resources on five native hosts and full Mac-hosted iOS CI at the reviewed candidate | Portable resources do not establish complete off-Mac apps. Released in v0.2.1 (4 October) |
| StarshipPad | Public v0.2.0 builds through PadMint 0.3.5 with Xcode 27 (4 October, 12.5 minutes); the earlier SDK-selection failure no longer happens. That app has no scene startup (iOS 27 risk); [merged #22](https://github.com/chrissotraidis/starshippad/pull/22) adds it | Released in v0.2.1 (4 October); no physical iOS 27 check |
| SunPad | v0.2.0's SDK 27 app lacked the scene startup iOS/iPadOS 27 requires; [merged #55](https://github.com/chrissotraidis/sunpad/pull/55) adds it, and v0.2.1 (4 October) ships the updated app, which opens to the game screen on the iOS 27.0 Simulator | Physical iOS 27/game/save acceptance; [#54](https://github.com/chrissotraidis/sunpad/issues/54) reporter OS and crash cause are unconfirmed |
| AgePad | Packages a matching supported Mac Steam installation without Xcode | Updated Steam client was rejected in prior checks; exact-profile support required. Do not bypass fingerprint checks |
| Other Mac recipes | Release manifests declare experimental Mac ARM64 iOS builds | Per-project tools, source/input requirements and device acceptance still apply; no blanket fresh-host or gameplay claim |

For KartPad's confirmed workaround, keep your original data and put a complete
copy inside **Files → On My iPad → KartPad**, for example `KartPad/DATA` with
`sys` and `files` directly inside. Return to **Game Data Required** and tap
**Import from Extracted Folder…**. Do not replace existing app files or saves.

## Before calling a route verified

Record three distinct checks, against the same candidate:

1. **Player path:** the packaged PadMint version, game release/recipe, host OS
   and architecture, input profile, actual command, result and safe rerun.
2. **Output:** architecture, target platform/minimum OS, package integrity,
   source/tool provenance and required content checks. Keep personal outputs private.
3. **Device:** install/update with data preserved, launch, meaningful gameplay,
   audio/input and save/relaunch on the intended device. Record limitations.

After merging, verify the default branch and release-selected recipe again.
A source fix does not change an older release's recipe. Content scans are
technical checks, not rights clearance.

To refresh this table, read the latest public release and its checksummed
`*-padmint.json` for every [catalog entry](../catalog/), including host
architecture and target. Compare with the source manifest and any pending PR,
but keep unreleased capabilities separate. Use the explicit preview links
above for preview-only projects; a missing latest release is not proof of no
preview. Keep unsupported combinations unavailable until their real route is ready.
