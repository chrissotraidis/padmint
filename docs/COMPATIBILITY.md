# Build compatibility

Public recipe snapshot: **30 October 2026**, checked against each game's latest
release recipe with PadMint **v0.5.25**. The live audit checked **39 entries**
with zero inconsistencies. The daily Catalog check (`scripts/audit-catalog.py`)
compares the live catalog with each latest release; trust its output over this
table when they differ. This audit did not repeat the game builds recorded below.
The table describes the recipe shipped with each game's latest public release.
It does not promote a declared host to tested gameplay support. See
[catalog-wide compatibility work](https://github.com/chrissotraidis/padmint/issues/75)
for the remaining implementation and acceptance work.

**Choose by the game and device you want to play on.** A Windows or Linux
PadMint download does not make a Mac-only game recipe portable.

On Windows and Linux, the downloaded launcher runs PadMint locally and opens
its interface in a browser at `127.0.0.1`. **Windows local** and **Linux local**
mean compilation on that computer. **GitHub Cloud Build** links to a guide and
workflow that the player starts on GitHub's temporary macOS machine. These
routes produce iPhone/iPad apps, Mac apps where offered, or Android packs.
See [Building games on Windows](WINDOWS.md) for published routes and private
proofs, and [Resume work](https://github.com/chrissotraidis/padmint/blob/main/docs/ROADMAP.md#resume-work) for the deferred improvements.
Windows evidence does not qualify Linux; each OS and architecture needs its own
recorded build. Physical-device acceptance remains a separate check.

- **Verified build:** the recorded build flow passed; this does not establish
  device launch, audio, saves or gameplay acceptance.
- **Experimental:** the recipe permits this combination; check the limitations
  below before downloading tools. This label alone is not proof of a completed build.
- **Planned:** no runnable player route for that combination.
- **Unavailable:** the recipe does not permit the host, or does not declare it.
- Host pairs are **x64 / ARM64**, in that order. Mac here means **Apple Silicon**;
  Intel Mac is listed separately where declared. iOS means iPhone/iPad output,
  subject to each game's device requirements.

## DarkPad route

DarkPad uses its own recipe from the [0.1.0 release](https://github.com/chrissotraidis/darkpad/releases/tag/v0.1.0).
Its catalog entry is included in PadMint 0.5.23. Apple Silicon Mac → iPhone/iPad
passed `scripts/player-check.sh` on October 28 using PadMint main `7e4c44c`
(v0.5.22), Apple's Python 3.9.6 and an empty PadMint folder. DarkPad source:
`c13d20d3b1a91518583955140868b6dd8f590995`; build time about 14 minutes.

Install full Xcode and its iOS platform plus `brew install cmake ninja xcodegen`;
allow 30 GB free after installing tools. Import a Perfect Dark USA Rev 1 / v1.1
ROM in the app after sideloading. The output is a personal unsigned IPA; the game
release contains only its recipe and checksum. Local Intel Mac, Windows and
Linux builds are not offered. An experimental private GitHub build is prepared
in PadMint source; a clean hosted build has not yet been recorded. Public manual
runs are refused and PR checks do not upload the app. See the
[private setup guide](../README.md#darkpad-private-github-build).
Physical gameplay remains preview-scoped; a successful build does not establish
device acceptance.

The library uses DarkPad's original app icon, copied unchanged from
`app/ios/icon/AppIcon1024.png` at the original checked revision. Its
[art provenance](https://github.com/chrissotraidis/darkpad/blob/26ac4bd14d05ef353d0544767ad6b97ee98dbdf6/docs/ART.md)
records its creation.

## Current player recipes

Every release link is the exact version checked. macOS targets marked planned
are omitted. Guided setup offers each Mac target on Apple Silicon (This Mac),
alongside the game's other targets. Intel Macs show why the Mac target is unavailable.

| Project and release | Output | Apple Silicon Mac | Intel Mac | Windows local x64 / ARM64 | Linux local x64 / ARM64 | GitHub Cloud Build |
|---|---|---|---|---|---|---|
| [agepad v0.1.0](https://github.com/chrissotraidis/agepad/releases/tag/v0.1.0) | iPhone/iPad | Experimental | Unavailable | Unavailable / Unavailable | Unavailable / Unavailable | — |
| [annepad v0.2.3](https://github.com/chrissotraidis/annepad/releases/tag/v0.2.3) | iPhone/iPad | Experimental | Unavailable | Unavailable / Unavailable | Unavailable / Unavailable | — |
| [annepad v0.2.3](https://github.com/chrissotraidis/annepad/releases/tag/v0.2.3) | macOS | Experimental | Unavailable | Unavailable / Unavailable | Unavailable / Unavailable | — |
| [ballpad v1.1.1](https://github.com/chrissotraidis/ballpad/releases/tag/v1.1.1) | iPhone/iPad | Experimental | Unavailable | Unavailable / Unavailable | Unavailable / Unavailable | Yes, iPhone/iPad |
| [bananapad v0.2.2](https://github.com/chrissotraidis/bananapad/releases/tag/v0.2.2) | iPhone/iPad | Experimental | Unavailable | Unavailable / Unavailable | Unavailable / Unavailable | — |
| [barrelpad v0.2.1](https://github.com/chrissotraidis/barrelpad/releases/tag/v0.2.1) | iPhone/iPad | Experimental | Unavailable | Unavailable / Unavailable | Unavailable / Unavailable | Yes, iPhone/iPad |
| [bearbirdpad v0.2.3](https://github.com/chrissotraidis/bearbirdpad/releases/tag/v0.2.3) | iPhone/iPad | Experimental | Unavailable | Unavailable / Unavailable | Unavailable / Unavailable | — |
| [bellpad v0.2.3](https://github.com/chrissotraidis/bellpad/releases/tag/v0.2.3) | iPhone/iPad | Experimental | Unavailable | Unavailable / Unavailable | Unavailable / Unavailable | Yes, iPhone/iPad |
| [bellpad v0.2.3](https://github.com/chrissotraidis/bellpad/releases/tag/v0.2.3) | macOS | Experimental | Unavailable | Unavailable / Unavailable | Unavailable / Unavailable | — |
| [bluewake v0.9.0](https://github.com/chrissotraidis/bluewake/releases/tag/v0.9.0) | iPhone/iPad | Experimental | Unavailable | Unavailable / Unavailable | Unavailable / Unavailable | — |
| [brawlerpad v0.2.2](https://github.com/chrissotraidis/brawlerpad/releases/tag/v0.2.2) | iPhone/iPad | Experimental | Unavailable | Unavailable / Unavailable | Unavailable / Unavailable | Yes, iPhone/iPad |
| [brawlerpad v0.2.2](https://github.com/chrissotraidis/brawlerpad/releases/tag/v0.2.2) | macOS | Experimental | Unavailable | Unavailable / Unavailable | Unavailable / Unavailable | — |
| [ctrpad v0.2.4](https://github.com/chrissotraidis/ctrpad/releases/tag/v0.2.4) | iPhone/iPad | Experimental | Unavailable | Unavailable / Unavailable | Unavailable / Unavailable | Yes, iPhone/iPad |
| [ctrpad v0.2.4](https://github.com/chrissotraidis/ctrpad/releases/tag/v0.2.4) | macOS | Experimental | Unavailable | Unavailable / Unavailable | Unavailable / Unavailable | — |
| [dinopad v0.2.3](https://github.com/chrissotraidis/dinopad/releases/tag/v0.2.3) | iPhone/iPad | Experimental | Unavailable | Unavailable / Unavailable | Unavailable / Unavailable | — |
| [darkpad v0.1.0](https://github.com/chrissotraidis/darkpad/releases/tag/v0.1.0) | iPhone/iPad | Verified build | Unavailable | Unavailable / Unavailable | Unavailable / Unavailable | Private, experimental; hosted check pending |
| [f0x v0.1.1](https://github.com/chrissotraidis/f0x/releases/tag/v0.1.1) | iPhone/iPad | Experimental | Unavailable | Unavailable / Unavailable | Unavailable / Unavailable | Yes, iPhone/iPad |
| [f0x v0.1.1](https://github.com/chrissotraidis/f0x/releases/tag/v0.1.1) | macOS | Experimental | Unavailable | Unavailable / Unavailable | Unavailable / Unavailable | — |
| [galaxypad v0.2.2](https://github.com/chrissotraidis/galaxypad/releases/tag/v0.2.2) | iPhone/iPad | Experimental | Unavailable | Unavailable / Unavailable | Unavailable / Unavailable | Yes, iPhone/iPad |
| [goldenpad v0.2.2](https://github.com/chrissotraidis/goldenpad/releases/tag/v0.2.2) | iPhone/iPad | Experimental | Unavailable | Planned / Unavailable | Planned / Unavailable | — |
| [harkinianpad v0.2.2](https://github.com/chrissotraidis/harkinianpad/releases/tag/v0.2.2) | iPhone/iPad | Experimental | Unavailable | Unavailable / Unavailable | Unavailable / Unavailable | Yes, iPhone/iPad |
| [kartpad v0.8.6](https://github.com/chrissotraidis/kartpad/releases/tag/v0.8.6) | iPhone/iPad | Experimental | Experimental | Experimental / Experimental | Experimental / Experimental | — |
| [kartpad v0.8.6](https://github.com/chrissotraidis/kartpad/releases/tag/v0.8.6) | macOS | Experimental | Unavailable | Unavailable / Unavailable | Unavailable / Unavailable | — |
| [kartpad v0.8.6](https://github.com/chrissotraidis/kartpad/releases/tag/v0.8.6) | Android | Experimental | Experimental | Experimental / Experimental | Experimental / Experimental | — |
| [maskpad v0.2.1](https://github.com/chrissotraidis/maskpad/releases/tag/v0.2.1) | iPhone/iPad | Experimental | Unavailable | Unavailable / Unavailable | Unavailable / Unavailable | Yes, iPhone/iPad |
| [meleepad v0.2.4](https://github.com/chrissotraidis/meleepad/releases/tag/v0.2.4) | iPhone/iPad | Experimental | Unavailable | Unavailable / Unavailable | Unavailable / Unavailable | — |
| [meleepad v0.2.4](https://github.com/chrissotraidis/meleepad/releases/tag/v0.2.4) | macOS | Experimental | Unavailable | Unavailable / Unavailable | Unavailable / Unavailable | — |
| [OpenRCT2Touch touch-v0.1.0](https://github.com/chrissotraidis/OpenRCT2Touch/releases/tag/touch-v0.1.0) | iPhone/iPad | Experimental | Unavailable | Unavailable / Unavailable | Unavailable / Unavailable | Yes, iPhone/iPad |
| [ottsel v0.1.0](https://github.com/chrissotraidis/ottsel/releases/tag/v0.1.0) | iPhone/iPad | Experimental | Unavailable | Unavailable / Unavailable | Unavailable / Unavailable | — |
| [ottsel v0.1.0](https://github.com/chrissotraidis/ottsel/releases/tag/v0.1.0) | macOS | Experimental | Unavailable | Unavailable / Unavailable | Unavailable / Unavailable | — |
| [paperpad v0.2.3](https://github.com/chrissotraidis/paperpad/releases/tag/v0.2.3) | iPhone/iPad | Experimental | Unavailable | Unavailable / Unavailable | Unavailable / Unavailable | Yes, iPhone/iPad |
| [projectreach v0.3.13](https://github.com/chrissotraidis/projectreach/releases/tag/v0.3.13) | iPhone/iPad | Experimental | Unavailable | Unavailable / Unavailable | Unavailable / Unavailable | Project route |
| [projectreach v0.3.13](https://github.com/chrissotraidis/projectreach/releases/tag/v0.3.13) | macOS | Experimental | Unavailable | Unavailable / Unavailable | Unavailable / Unavailable | Project route |
| [snappad v0.2.1](https://github.com/chrissotraidis/snappad/releases/tag/v0.2.1) | iPhone/iPad | Experimental | Unavailable | Unavailable / Unavailable | Unavailable / Unavailable | — |
| [snappad v0.2.1](https://github.com/chrissotraidis/snappad/releases/tag/v0.2.1) | macOS | Experimental | Unavailable | Unavailable / Unavailable | Unavailable / Unavailable | — |
| [spaghettipad v0.2.1](https://github.com/chrissotraidis/spaghettipad/releases/tag/v0.2.1) | iPhone/iPad | Experimental | Unavailable | Unavailable / Unavailable | Unavailable / Unavailable | Yes, iPhone/iPad |
| [squirrelpad v0.1.3](https://github.com/chrissotraidis/squirrelpad/releases/tag/v0.1.3) | iPhone/iPad | Experimental | Unavailable | Unavailable / Unavailable | Unavailable / Unavailable | — |
| [starshippad v0.2.1](https://github.com/chrissotraidis/starshippad/releases/tag/v0.2.1) | iPhone/iPad | Experimental | Unavailable | Unavailable / Unavailable | Unavailable / Unavailable | Yes, iPhone/iPad |
| [sunpad v0.2.2](https://github.com/chrissotraidis/sunpad/releases/tag/v0.2.2) | iPhone/iPad | Experimental | Unavailable | Unavailable / Unavailable | Unavailable / Unavailable | — |
| [sunpad v0.2.2](https://github.com/chrissotraidis/sunpad/releases/tag/v0.2.2) | macOS | Experimental | Unavailable | Unavailable / Unavailable | Unavailable / Unavailable | — |
| [tribespad v0.2.0](https://github.com/chrissotraidis/tribespad/releases/tag/v0.2.0) | iPhone/iPad | Experimental | Unavailable | Unavailable / Unavailable | Unavailable / Unavailable | Yes, iPhone/iPad |
| [tribespad v0.2.0](https://github.com/chrissotraidis/tribespad/releases/tag/v0.2.0) | macOS | Experimental | Unavailable | Unavailable / Unavailable | Unavailable / Unavailable | — |
| [utp v0.1.0](https://github.com/chrissotraidis/utp/releases/tag/v0.1.0) | iPhone/iPad | Experimental | Unavailable | Unavailable / Unavailable | Unavailable / Unavailable | Yes, iPhone/iPad |

**Android as the build host:** only KartPad's phone route is offered, through
Termux and a Linux ARM64 environment. It remains experimental: the recorded
build/export/import check used a phone-sized emulator, not physical Android
hardware or verified racing. Allow about 25 GB free and 8 GB RAM; follow the
[phone guide](../README.md#android-phone-only-experimental). Linux ARM64 CI
does not establish Android/Termux acceptance.

**Intel Mac:** KartPad's Android recipe declares it experimental. From KartPad 0.8.0 and
PadMint 0.5.1 its iPhone/iPad build is also experimental on Intel Macs (Xcode). The other Mac build
routes require Apple Silicon. HaloPad's Xbox edition can be built without a Mac on
GitHub Cloud Build ([steps](https://github.com/chrissotraidis/projectreach#on-windows-linux-or-any-computer)).

**Intel Mac iPhone candidate (9 October 2026):** [KartPad #443](https://github.com/chrissotraidis/kartpad/pull/443)
and [PadMint #138](https://github.com/chrissotraidis/padmint/pull/138) add an
experimental Xcode route. A native GitHub Intel Mac on macOS 15 with Xcode 16.4
passed pinned x64 tool setup, two translator code-generation tests and the
production iPhone pack build with synthetic inputs (ARM64 iOS 16 library,
symbol check, strip and IPA insertion). A separate full private-disc build
passed locally with x64 tools under Rosetta and Xcode 27 in 350.53 seconds;
the app and ARM64 iOS 16 library have matching interface fingerprints and the
IPA passes structure validation. Neither run establishes device gameplay or
a complete disc build on physical Intel hardware. KartPad 0.8.0 publishes the
matching recipe, and PadMint 0.5.1 offers the route. Native Mac gameplay still requires Apple Silicon.

**No build needed on any computer:** CaesarPad, DaggerPad, DevilTouch, Emerald
Tablet, KidPad, PeonPad, RAtouch and VaultPad publish iPhone/iPad apps without a
PadMint compilation step. PadMint links their download and data-import steps.

## Status by game

Where each tracker app stands on the shared pipeline, and the smallest next step.
Games are grouped by family so shared build work can be reused; each port still
requires its own validation.
Windows build hardening resumed on 26 October 2026
([D17](DECISIONS.md#d17-windows-build-hardening-resumes-26-oct-2026)).
The 29 October handoff defers broader implementation until the next owner
request; [Resume work](https://github.com/chrissotraidis/padmint/blob/main/docs/ROADMAP.md#resume-work) records that queue. The rows
preserve earlier published routes and private proof records. A completed build
does not establish device launch or gameplay. The 5 October pause remains a
historical decision.
**Off-Mac** means a build on the specific Windows or Linux host recorded below;
it does not imply both operating systems were tested.

**GameCube and Wii recompilations** (reference: BlueWake)

| Game | Status | Smallest next step |
|---|---|---|
| KartPad | **Android is a ready-to-play download** on [its releases](https://github.com/chrissotraidis/kartpad/releases/latest): the APK includes the game code, so on Android PadMint's useful output is the `KartPad game data` folder. iPhone/iPad is built through PadMint (the release's `ios-for-padmint.ipa` has no game code). The Mac copy builds through PadMint on Apple Silicon Macs. The 0.7.9–0.7.13 ready-to-play Apple downloads won't get updates. Earlier: Android packs built on Mac, Windows and Linux raced on an Android 16 emulator; iPhone off a Mac is experimental | A data-only Android target in KartPad's recipe, so PadMint skips the 1 GB NDK and the unused pack |
| BlueWake | Ready-to-play Windows desktop downloads remain outside PadMint. The iPhone module [draft #100](https://github.com/chrissotraidis/bluewake/pull/100) completed a native Windows backend build from preserved extracted inputs, with module/companion, ABI, imports and IPA readback checks. A warm repeat performed no compilation. The current original-disc run passed production extraction and source preparation; its complete module build is still pending | Finish the original-disc build and native Unicode-path checks, then device checks; Windows/Linux iPhone hosts stay planned |
| SunPad | [Draft #78](https://github.com/chrissotraidis/sunpad/pull/78), stacked on #57, records a complete private Windows ARM64 PadMint build and a private x64-toolchain disc build under ARM emulation. All 225 generated files match Mac after newline normalization; 2,797 base-app entries stay unchanged. Native x64 CI separately covers public tools and module checks | Finish Unicode-path hardening, then device launch/audio/saves and release review. Emulation is not native private x64 hardware acceptance |
| MeleePad | [Draft #52](https://github.com/chrissotraidis/meleepad/pull/52) builds the offline module directly with pinned DolRecomp. Both supported revisions built on Mac; packaged Windows ARM64 and an emulated x64-toolchain backend passed with maintained compiler defaults. All 241 generated files match Mac after newline normalization, and 3,317 base-app entries stay unchanged. Shared [#179](https://github.com/chrissotraidis/padmint/pull/179) adds the module and DOL identity sidecar. Slippi online builds stay separate | Finish Unicode-path hardening, device checks and release ordering; no native private x64 hardware or published Windows recipe claim |

**N64 recompilations** (reference: GoldenPad)

| Game | Status | Smallest next step |
|---|---|---|
| SquirrelPad | [Draft #7](https://github.com/chrissotraidis/squirrelpad/pull/7) completed a packaged Windows ARM64 build from a fresh PadMint home, with all 127 generated files matching Mac after newline normalization. Native x64 generator CI also passes; a private x64-toolchain backend build passed under ARM emulation | Matching empty shell and prerequisite PadMint release, plus device launch/audio/save checks. Emulation is not native x64 private-hardware acceptance |
| GoldenPad | [Draft #52](https://github.com/chrissotraidis/goldenpad/pull/52) builds a private module and matching empty shell. Packaged Windows ARM64 and an emulated x64-toolchain backend passed; the static Mac route also passed. The final ARM64 backend passed with non-English work/TEMP paths and default Windows Python encoding, followed by independent IPA readback. Native x64/ARM64 generator CI passes | Device testing, matching shell release and PadMint prerequisites; native private x64 hardware remains unverified |
| BearBirdPad | [Draft #27](https://github.com/chrissotraidis/bearbirdpad/pull/27) has matching Mac shell/module checks and a static Mac regression build. Private Windows ARM64 and emulated x64 backends passed; all 433 generated source files match Mac with the same MIPS compiler after newline normalization. The packaged recipe and a final Unicode-path backend both passed, with independent IPA readback | Device checks, matching shell release and PadMint prerequisites |
| BananaPad | [Draft #22](https://github.com/chrissotraidis/bananapad/pull/22) completed a Windows ARM64 backend from the player's ROM, including non-English work/TEMP paths. Its 274 generated code/header files match the prior validated build; independent readback verifies the matching iOS 15 shell/module and preserved base files. Native public generator CI passes on Mac ARM64 and Windows x64/ARM64 | Device checks, matching shell release and PadMint prerequisites |
| SnapPad | [Draft #12](https://github.com/chrissotraidis/snappad/pull/12) completed the Windows ARM64 ROM-to-IPA pipeline with fresh source and Python-environment preparation using verified cached tools, plus non-English work/TEMP paths. All 89 generated code/header files are byte-identical to Mac, all 63 shell entries stay unchanged, and a warm repeat performs no build. Independent IPA readback and native public generator CI pass | Device checks and reviewed, published compiler tools, matching shell and PadMint prerequisites |
| DinoPad | [Draft #19](https://github.com/chrissotraidis/dinopad/pull/19) has an empty-shell build and public generator/module checks on Mac ARM64 and Windows x64/ARM64. A supported original ROM is unavailable for this validation; these checks do not establish a full game build | Obtain the supported input and complete the private pipeline; host entries remain planned |
| AnnePad | Work in progress: fresh Mac and native Windows decompilation reproduce the supported ROM exactly. All 1,006 generated CPU files match semantically, allowing newline differences and two complete-function ordering differences. The module boundary retains all four maintained RSP implementations; the complete shell/module pipeline is not yet validated | Complete source/input guards, shell/module and private Windows build validation, then device checks |

**Engine and decompilation ports** (reference: SpaghettiPad)

| Game | Status | Smallest next step |
|---|---|---|
| SpaghettiPad | Published recipe builds on the hosted Mac route from a Windows or Linux browser. [Draft #29](https://github.com/chrissotraidis/spaghettipad/pull/29) separately builds local iPhone modules on Windows and Linux x64/ARM64 | Complete released local-module recipe with matching runtime delivery |
| HarkinianPad | Published recipe builds on the hosted Mac route from a Windows or Linux browser. Resources have separate five-host evidence in [#35](https://github.com/chrissotraidis/harkinianpad/pull/35) | Complete and validate a local Windows app/module route |
| MaskPad, StarshipPad, PaperPad, BrawlerPad, BarrelPad, BellPad, BallPad | Published recipes build on the hosted Mac route from a Windows or Linux browser; local app builds remain Mac-hosted | Complete and validate local Windows routes with matching runtimes |
| CTRPad | Published iPhone/iPad recipe builds on the hosted Mac route from a Windows or Linux browser. The local iPhone/iPad and Mac app builds remain Mac-hosted | Complete and validate a local Windows iPhone route |
| AgePad | Requires compatible installed Mac Steam game files. [Draft #13](https://github.com/chrissotraidis/agepad/pull/13) makes injection portable and preserves ZIP metadata; synthetic Windows x64/ARM64 checks pass, including non-English paths. An actual Windows run correctly rejected six incompatible installed Steam files and preserved the previous output. Shared [#178](https://github.com/chrissotraidis/padmint/pull/178) marks these as private build inputs | A successful Windows build with files matching the base app is still required; no private-input upload or public host promotion |
| GalaxyPad | Published recipe builds on the hosted Mac route from a Windows or Linux browser, then accepts the player’s supported WBFS in the app. This does not establish a local Windows compiler route | Complete and validate a local Windows route; keep device acceptance separate |
| Ottsel | Published recipe remains Mac-only: it builds an unsigned iPhone/iPad IPA or Mac app plus a data folder from the player's USA `SCUS-97124` Black Label disc. The earlier Mac player check passed. Current source inspection identifies native extractor/GOAL compiler, offline module emitter, data-pack and Apple app-build steps; no Windows route has been validated | Prove portable host tools and local private-data preparation, then a matching app/module delivery route. Existing Mac playability evidence does not qualify a Windows build |

**New in PadMint 0.5.5:** F0X, EctoPad, SnapPad, OpenRCT2 Touch and UTP build
through PadMint (each passed a clean player check before its first recipe
release), RAtouch is listed as a download, and nothing is listed as not
available yet. Mac targets were added for F0X, EctoPad, SnapPad, BellPad, AnnePad, SunPad, MeleePad and BrawlerPad; each Mac
recipe signs the app for the player's Mac and zips it, and each passed a clean
player check whose app was launched to its first screen. Games whose Mac app is
a developer test binary (AgePad, BarrelPad, SquirrelPad, OpenRCT2 Touch's
headless host), starts with a ROM fixed at build time (BananaPad), or has an
official signed Mac download upstream (HarkinianPad, MaskPad, SpaghettiPad,
StarshipPad, BearBirdPad, UTP) stay iPhone/iPad only.

**HaloPad** (ProjectReach) builds for iPhone, iPad and Mac on Apple silicon Macs,
experimental. Choosing an Xbox ISO/XISO builds the Xbox edition alone from the OpenCE engine
recorded for that HaloPad release; the player adds the same disc in the app. Choosing the
Custom Edition installer (with product-key.txt) builds both editions and needs Wine.
Off a Mac, the Xbox edition has no game input to build from: HaloPad's README shows how a
player's own GitHub fork runs [GitHub Cloud Build](https://github.com/chrissotraidis/projectreach#on-windows-linux-or-any-computer).
This published project route is available from Windows or Linux and appears
under Other routes in PadMint 0.5.24. PR #216 changes its placement; it does not
create the HaloPad workflow or add it to PadMint's shared game dropdown.

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
| PaperPad | [#19](https://github.com/chrissotraidis/paperpad/pull/19) reached PaperPad Original only; [#22](https://github.com/chrissotraidis/paperpad/pull/22) | [0.2.3](https://github.com/chrissotraidis/paperpad/releases/tag/v0.2.3) (21 October) | 0.2.2's "Opens" was the Original app; see below |
| StarshipPad | [#22](https://github.com/chrissotraidis/starshippad/pull/22) | [0.2.1](https://github.com/chrissotraidis/starshippad/releases/tag/v0.2.1) | Opens (setup) |
| SunPad | [#55](https://github.com/chrissotraidis/sunpad/pull/55) | [0.2.1](https://github.com/chrissotraidis/sunpad/releases/tag/v0.2.1) (with the app) | Opens (game screen) |

The SDL-based games share one SDL 2.32.10 backport ([fork commit](https://github.com/chrissotraidis/SDL/commit/c6756fcd3de8090a8f72ac1a0b6fb6e50f0021d1));
MeleePad and SunPad use their own scene delegates. "Opens" means a Simulator build
of the merged source keeps running on iOS 27.0 and shows its first screen, where an
app with the old startup stops at launch. No physical iOS 27 device was used. A copy
built before these releases may not open on iOS 27: build the game again with
PadMint and install it over the old one. PadMint's finish screen still warns if a
copy may not open on iOS 27.

## iOS 27 on a physical iPad, 18 to 21 October

On 18 October, PadMint builds of each catalog game's latest release (Xcode 27.1)
were installed over the existing copies on an iPad Pro with iPadOS 27.0.1 and
opened. AgePad, AnnePad, BallPad, BananaPad, BarrelPad, BearBirdPad, BellPad,
BlueWake, BrawlerPad, CTRPad, DinoPad, GalaxyPad, GoldenPad, HaloPad, HarkinianPad,
KartPad, MaskPad, MeleePad, SpaghettiPad, SquirrelPad, StarshipPad and SunPad each
reached their intro, title screen or launcher. BananaPad's one crash on first
launch is a known game fault, not startup. These are launch checks, not gameplay.

**PaperPad 0.2.2 closed at launch**, in UIKit's check for apps that skip scene
startup, so it never wrote a log. Its fix (#19) reached PaperPad Original only;
PadMint builds PaperBoat, which kept plain SDL and no scene manifest. The Simulator
"Opens" above came from the Original app. PadMint's finish screen did warn.
[PaperPad 0.2.3](https://github.com/chrissotraidis/paperpad/releases/tag/v0.2.3)
([#22](https://github.com/chrissotraidis/paperpad/pull/22)) fixes it: it opened on
the same iPad with its saves, after an
[iPhone 18 Pro report](https://github.com/chrissotraidis/paperpad/issues/21).

**Releases since then**, checked on 21 October:

| Game | Release | iOS 27 startup |
|---|---|---|
| AnnePad, BellPad, BrawlerPad, KartPad, HaloPad | 0.2.3, 0.2.2, 0.2.2, 0.8.5, 0.3.11 | No startup files changed since the iPad check |
| DinoPad, SunPad, MeleePad | 0.2.3, 0.2.2, 0.2.3 | PadMint builds of the release record scene startup |
| UTP, OpenRCT2 Touch | 0.1.0, 0.1.0 | Scene manifest in source (not built here) |
| EctoPad | 0.1.3 | SDL 3.4's scene startup in source (not built here) |
| F0X | [0.1.1](https://github.com/chrissotraidis/f0x/releases/tag/v0.1.1) | 0.1.0 had none (libultraship fetched plain SDL); fixed |
| SnapPad | [0.2.1](https://github.com/chrissotraidis/snappad/releases/tag/v0.2.1) | 0.2.0 had none (it kept PaperPad's old SDL pin); fixed |

F0X, SnapPad and PaperPad now use the same SDL fork commit as the other SDL games.
Their PadMint builds record scene startup; none of the three was opened on an
iOS 27 iPhone here. A copy built from F0X 0.1.0, SnapPad 0.2.0 or PaperPad 0.2.2
with Xcode 27 will close at launch on iOS 27: build the game again and install it
over the old one.

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
| KartPad iOS folder import | [#380](https://github.com/chrissotraidis/kartpad/issues/380): folder opening replaced copy mode in 0.7.4; 0.8.1 separated folder selection from file selection and added feedback | The issue remains open; those changes do not establish physical-device picker acceptance for every provider |
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

## iPhone and iPad file selection, 30 October 2026

The issue audit found selection reports in **five of Chris's projects**. These
are reports across different releases and import paths, not evidence that all
five current releases fail for the same reason. The
[source audit](https://github.com/chrissotraidis/bellpad/blob/main/docs/FILE_IMPORT_AUDIT.md)
records the full 39-project roster and separates reports from unconfirmed
source risks:

| Project | Report and source history | Remaining evidence |
|---|---|---|
| BellPad | [#26](https://github.com/chrissotraidis/bellpad/issues/26) reports an unresponsive ISO selection in 0.2.2 on iOS 27.2 and no BellPad folder in Files; [0.2.3](https://github.com/chrissotraidis/bellpad/releases/tag/v0.2.3) adds a dedicated Files import folder and clearer import handling | Clean PadMint builds before and after publication passed, along with iPhone/iPad Simulator import and regression checks; the reporter's device/provider and LiveContainer behavior remain unconfirmed |
| KartPad | [#1](https://github.com/chrissotraidis/kartpad/issues/1) includes confirmation after a file-copy picker change; [#380](https://github.com/chrissotraidis/kartpad/issues/380) tracks the separate folder-selection fixes described above | No confirmed regression in the current PadMint-built release was established by this audit; device/provider retesting remains |
| HaloPad | [#29](https://github.com/chrissotraidis/projectreach/issues/29): 0.3.11 widened selectable ISO/XISO types to include disk images and generic data | The issue remains open without reporter confirmation |
| SunPad | [#6](https://github.com/chrissotraidis/sunpad/issues/6): Preview 2 changed file selection to copy mode and added a Documents fallback | The closed report does not include a user retest |
| SquirrelPad | [#3](https://github.com/chrissotraidis/squirrelpad/issues/3) includes an October 27 report that 0.1.2 still cannot select a ROM; [0.1.3](https://github.com/chrissotraidis/squirrelpad/releases/tag/v0.1.3) publishes the broader selection and background import from [merged #8](https://github.com/chrissotraidis/squirrelpad/pull/8) | The clean pre-release PadMint build passed with app version 0.1.3/build 4 and package validation; the reporter's physical-device/provider result remains unconfirmed |

A follow-up investigation reproduced additional defects: interrupted rollback
retry in UTP, failed source reads and self-import in VaultPad, incomplete
extraction in SunPad, partial mixed selections in RAtouch, and folder discovery
and picker-copy handling in BallPad. The
[detailed audit](https://github.com/chrissotraidis/bellpad/blob/main/docs/FILE_IMPORT_AUDIT.md)
keeps the regression evidence and each release's verification separate from
physical-device/provider acceptance. GalaxyPad and F0X remain unconfirmed by
this investigation; their picker patterns alone did not justify a release.

PadMint builds each app's own importer. File type filtering, file-provider
access, folder selection and container-hosted installations can fail at
different points, so an across-the-board picker rewrite is not justified.
Import behavior and format validation stay in the game repositories; PadMint
provides release-selected builds and the relevant post-install instructions.

For import changes, exercise the actual first-run screen on the target device:
select a local file, cancel and retry, try a supported cloud provider, and use
the documented local-folder fallback. Check that unsupported files show a
useful error and an in-place update preserves existing data. Record a
LiveContainer installation separately from a directly installed app. A package
check, Simulator run or clean PadMint build does not establish these outcomes.

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
