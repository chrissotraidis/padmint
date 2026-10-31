# Building games on Windows

Published-route snapshot: **31 October 2026**, PadMint **v0.5.27**.

This page answers one question: **which game builds can run on a Windows
computer with PadMint?** It is about the *build computer*. The result is an
iPhone/iPad `.ipa` (or, for KartPad, an Android pack), not a Windows desktop
game.

On Windows and Linux, the downloaded launcher runs PadMint on the player's
computer and opens its interface in a browser at `127.0.0.1`. Local tools and
builds run on that computer. GitHub Cloud Build is a separate hosted route.

Use these labels consistently in the app and documentation:

- **Build here**: the game's published recipe supports local compilation on
  this Windows PC.
- **GitHub Cloud Build**: GitHub runs a temporary macOS build machine for your
  GitHub repository; Windows only starts the workflow. Your game files are
  never uploaded. DarkPad requires a private repository and its Actions allowance.
- **Apple Silicon Mac**: the iPhone/iPad or Mac app needs an Apple Silicon Mac
  with Xcode, unless the game's project documents another route.

## Every game from a Windows PC: running list

Updated **31 October 2026** for PadMint **0.5.27**, from the live catalog audit
(`scripts/audit-catalog.py`) and each game's open pull requests. This is the
work queue for "every game can be built from Windows". A game moves to **Build
here** only after the gates in [Active queue](#active-queue) are met.

**Today, from Windows:** 18 of the 31 buildable ports reach an iPhone/iPad
(1 built locally, 17 on GitHub's Mac), and all 8 ready-made apps install with
Sideloadly. Twelve ports still need an Apple Silicon Mac for iPhone/iPad, and
EctoPad is paused.

| Game (port) | From Windows today | Why there is no local Windows build yet | Next fix |
|---|---|---|---|
| Mario Kart Wii (KartPad) | **Build here**: Android game data, iPhone/iPad (experimental) | — | Physical-device check of a Windows-built IPA |
| 15 games on the shared workflow: BallPad, BarrelPad, BellPad, BrawlerPad, CTRPad, F0X, GalaxyPad, HarkinianPad, MaskPad, OpenRCT2 Touch, PaperPad, SpaghettiPad, StarshipPad, TribesPad, UTP | **GitHub Cloud Build** | The app's engine still needs Apple's SDK to compile; the game is added in the app, so GitHub's Mac can build it | None for players. Local builds follow [spaghettipad#29](https://github.com/chrissotraidis/spaghettipad/pull/29); PaperPad's pinned downloads wait for [paperpad#24](https://github.com/chrissotraidis/paperpad/pull/24) |
| Perfect Dark (DarkPad) | **GitHub Cloud Build**, private copy of PadMint (0.5.27) | Same as above | A private manual run, then install and play it |
| Halo (HaloPad) | Xbox edition: **HaloPad's own GitHub workflow** | Custom Edition converts the PC game with Wine and Mac tools | No Windows design for Custom Edition yet |
| Conker's Bad Fur Day (SquirrelPad) | Apple Silicon Mac | Reads the ROM while compiling, so it can't use GitHub (D15) | [squirrelpad#7](https://github.com/chrissotraidis/squirrelpad/pull/7): publish the game-free shell and Windows recipe, then a device check |
| GoldenEye 007 (GoldenPad) | Apple Silicon Mac | Reads the ROM while compiling | [goldenpad#52](https://github.com/chrissotraidis/goldenpad/pull/52): recipe declares Windows; publish shell and recipe, device check |
| Banjo-Kazooie (BearBirdPad) | Apple Silicon Mac | Reads the ROM while compiling | [bearbirdpad#27](https://github.com/chrissotraidis/bearbirdpad/pull/27): publish shell and recipe, device check |
| Donkey Kong 64 (BananaPad) | Apple Silicon Mac | Reads the ROM while compiling | [bananapad#22](https://github.com/chrissotraidis/bananapad/pull/22): test the recipe (still `draft-untested`), publish, device check |
| Super Mario Sunshine (SunPad) | Apple Silicon Mac | Reads the disc while compiling | Merge [sunpad#57](https://github.com/chrissotraidis/sunpad/pull/57), then [#78](https://github.com/chrissotraidis/sunpad/pull/78); publish, device check |
| Super Smash Bros. Melee (MeleePad) | Apple Silicon Mac | Reads the disc while compiling | [meleepad#52](https://github.com/chrissotraidis/meleepad/pull/52): host name fixed to `windows-x86_64` and checked on 31 Oct; publish, device check |
| Pokémon Snap (SnapPad) | Apple Silicon Mac | Reads the ROM while compiling; its decompilation tools still come from a private, locally verified bundle | [snappad#12](https://github.com/chrissotraidis/snappad/pull/12): publish those tools through PadMint's managed tools, then add Windows hosts to the recipe. SnapPad's release pause still applies |
| The Wind Waker (BlueWake) | Ready-to-play **Windows desktop** download; iPhone/iPad needs a Mac | Reads the disc while compiling | [bluewake#100](https://github.com/chrissotraidis/bluewake/pull/100) is current with main again (31 Oct); finish the original-disc Windows build |
| Pokémon Stadium (AnnePad) | Apple Silicon Mac | Reads the ROM while compiling | Finish the portable module and app pipeline (decompilation already matches on Windows) |
| Dinosaur Planet (DinoPad) | Apple Silicon Mac | Reads the ROM while compiling | A full private Windows build with the supported ROM |
| Jak and Daxter (Ottsel) | Apple Silicon Mac | Reads the disc while compiling | Design the Windows host tools and module delivery |
| Age of Empires II: DE (AgePad) | Apple Silicon Mac | Adds the player's installed **Mac** Steam edition to the app | The inject step is Python with no Xcode. Test fetching the Mac edition on Windows with SteamCMD (`+@sSteamCmdForcePlatformType macos`) from the player's own account, then run the same step |
| Metroid Prime (EctoPad) | Paused | Its engine (Metaforce) is private until its developers publish it | Wait for Metaforce |
| 8 ready-made apps: CaesarPad, DaggerPad, DevilTouch, Emerald Tablet, KidPad, PeonPad, RAtouch, VaultPad | **No build needed**: download and install with Sideloadly | — | — |

## Recently completed

- **0.5.27:** DarkPad joins GitHub Cloud Build (private copy of PadMint) and
  HaloPad's own workflow is listed there, so 17 games build for iPhone/iPad from
  Windows. Every game page uses the same numbered steps on every system.
- **0.5.24:** removed Melee PC, another person's project. The catalog contains
  only Chris's own ports.
- **0.5.23:** added DarkPad's Apple Silicon Mac → iPhone/iPad recipe.
- **0.5.18:** update controls now reflect their actual state: the sidebar update
  label fits, the PadMint updater hides its action while downloading, and a
  missing game file or device gets a direct route back to that step.
- **0.5.17:** the catch-all tab is now **Other routes**, so BlueWake's Windows
  download and paused games are not incorrectly described as Apple Silicon Macs.
- **0.5.16:** the app shows **Build here**, **GitHub Cloud Build**, and **Apple
  Silicon Mac**; GitHub Cloud Build means GitHub's temporary hosted macOS
  build machine. The stale compatibility table was refreshed from live releases.
- **0.5.15:** shared Windows toolchains, cache and retry safety, Unicode paths,
  a private UTF-8 build console and complete cancellation cleanup were released.
- The 0.5.15–0.5.18 infrastructure releases did not enable new game host flags.

## What Windows can build today

| Route | Games | Result | Current status |
|---|---|---|---|
| **Build here with PadMint** | KartPad | iPhone/iPad `.ipa`, or a KartPad game-data pack for the published Android app | Experimental; published recipe |
| **GitHub Cloud Build** | BallPad, BarrelPad, BellPad, BrawlerPad, CTRPad, F0X, GalaxyPad, HarkinianPad, MaskPad, OpenRCT2 Touch, PaperPad, SpaghettiPad, StarshipPad, TribesPad, UTP | iPhone/iPad `.ipa` | Published workflow; not a local Windows build |
| **Separate GitHub workflow** | HaloPad, Xbox edition | iPhone/iPad `.ipa` or Mac app | [Use HaloPad's own repository and workflow](https://github.com/chrissotraidis/projectreach#on-windows-linux-or-any-computer); Custom Edition still needs an Apple Silicon Mac |
| **Private GitHub Cloud Build** | DarkPad | iPhone/iPad `.ipa` | Experimental; [clean hosted build passed](https://github.com/chrissotraidis/padmint/actions/runs/40830430386/job/123303170832), with no IPA uploaded. Installation and gameplay are unvalidated. [Private setup and Actions allowance](../README.md#darkpad-private-github-build) |
| **Apple Silicon Mac** | The other buildable titles, including the seven Windows proofs below | iPhone/iPad `.ipa`, and for some games a personal Mac app | The app must show **Apple Silicon Mac**; a private Windows proof alone does not enable it |
| **No build needed** | CaesarPad, DaggerPad, DevilTouch, Emerald Tablet, KidPad, PeonPad, RAtouch, VaultPad | iPhone/iPad app from its release | Download and install; add your own game files in the app where required |

**Windows desktop is a separate product.** BlueWake publishes a ready-to-play
Windows x64 build from its own releases. PadMint's Windows work does not turn
the other games into Windows desktop ports.

The 39-entry catalog passed the live recipe audit on 29 October 2026 with
zero inconsistencies. This checks published declarations and links, not fresh
game builds or device acceptance. KartPad remains the only published local
Windows/Linux recipe.

[PR #216](https://github.com/chrissotraidis/padmint/pull/216) is unmerged and
unreleased. It adds a private-repository DarkPad cloud route and makes HaloPad's
existing workflow easier to find. Hosted build checks passed, but private manual
dispatch, signing/install and physical gameplay still need validation. It does
not add SquirrelPad, which needs the player's ROM during compilation.

## Windows build proofs that are not enabled yet

These games have a complete or substantial private Windows build, but the
latest **public** recipe still does not offer a local Windows build. The app must
remain labeled **Apple Silicon Mac** until the listed release and device gates
are complete. These proof records come from earlier work; the 29 October
recipe audit did not repeat them. A Windows ARM64 run, an emulated x64 run and a
native x64 run are separate evidence. None of them qualifies Linux: Linux x64
and ARM64 need their own complete builds and acceptance checks.

| Game | Proven on the build side | Missing before Windows can be selected |
|---|---|---|
| [SquirrelPad #7](https://github.com/chrissotraidis/squirrelpad/pull/7) | Packaged Windows ARM64 build; generated files matched Mac; native x64 generator CI | Publish the code-free `SquirrelPad-v…-ios-shell.ipa`, publish the Windows recipe, device launch/audio/save |
| [GoldenPad #52](https://github.com/chrissotraidis/goldenpad/pull/52) | Private Windows ARM64 and emulated x64 toolchain; matching shell | Publish the shell and recipe, device check; native private x64 hardware remains separate |
| [BearBirdPad #27](https://github.com/chrissotraidis/bearbirdpad/pull/27) | Private Windows ARM64 and emulated x64; generated files match Mac | Publish the shell and recipe, device check; native private x64 hardware remains separate |
| [BananaPad #22](https://github.com/chrissotraidis/bananapad/pull/22) | Private Windows ARM64; matching iOS shell/module readback; public generator CI | Publish the shell and recipe, device check; recipe is still marked `draft-untested` |
| [SnapPad #12](https://github.com/chrissotraidis/snappad/pull/12) | Full Windows ARM64 ROM-to-IPA pipeline; byte-identical generated output; warm rebuild performs no compilation | Add Windows hosts to the recipe, publish it, device check; current recipe has no Windows host |
| [MeleePad #52](https://github.com/chrissotraidis/meleepad/pull/52) | Windows ARM64 and emulated x64 backend; existing app has module-loading support | Fix the recipe's invalid `windows-x64` key to `windows-x86_64`, publish it, device check; native private x64 hardware remains separate |
| [SunPad #78](https://github.com/chrissotraidis/sunpad/pull/78) | Windows ARM64 and emulated x64 backend; PRs #57 and #78 pass | Merge prerequisite [#57](https://github.com/chrissotraidis/sunpad/pull/57) and then #78, publish the recipe, device check |

## Remaining local-Windows work

**Partial or blocked:**

| Game | Current position |
|---|---|
| [BlueWake](https://github.com/chrissotraidis/bluewake/pull/100) | Windows desktop release works outside PadMint. Its iPhone-build route from Windows has a native backend proof but its complete original-disc build is unfinished. |
| AnnePad | Fresh Mac and Windows decompilation match the supported ROM; the portable module/app pipeline is unfinished. |
| AgePad | Portable checks pass, but the available installed Steam files were incompatible with the expected app. A successful real-input build is still required. |
| DinoPad | The supported ROM needed for a full private build is unavailable. |
| Ottsel | No usable local Windows route has been implemented. |

**No local Windows game build recorded here:** BallPad, BarrelPad, BellPad,
BrawlerPad, CTRPad, DarkPad, F0X, GalaxyPad, HarkinianPad, MaskPad, OpenRCT2 Touch,
PaperPad, HaloPad, SpaghettiPad, StarshipPad, TribesPad and UTP. Most already use GitHub
Cloud Build for iPhone/iPad. HaloPad has its own documented GitHub Cloud Build
route for the Xbox edition.

**Paused:** EctoPad, because Metaforce is not publicly available.

## Active queue

Broader implementation is deferred after the 29 October documentation handoff.
On the next request to continue, start with [Resume work](https://github.com/chrissotraidis/padmint/blob/main/docs/ROADMAP.md#resume-work)
and recheck each affected PR and release before using this per-game queue.

1. SnapPad: publish its decompilation tools through PadMint's managed tools
   (its backend still reads a private, locally verified bundle), then add
   Windows x64 and ARM64 to the recipe, publish it and run the physical-device
   check. SnapPad's release pause still applies.
2. MeleePad: the recipe now uses `windows-x86_64`, and a test checks every host
   name against PadMint's list ([meleepad#52](https://github.com/chrissotraidis/meleepad/pull/52),
   31 October). Publish the recipe, then run the physical-device check.
3. Merge SunPad #57 and #78, publish the recipe, and run the physical-device
   check.
4. Publish and test SquirrelPad's code-free shell. Once that shell workflow is
   proven, reuse it for GoldenPad and BearBirdPad, then BananaPad.
5. Finish BlueWake's original-disc Windows backend, then AnnePad. AgePad needs
   matching installed files; DinoPad needs its supported ROM; Ottsel needs the
   host-tool and module-delivery design implemented.

Do not mark another game as **Build here** merely because a private proof
exists. A row moves only after all of these are true:

- its published recipe lists the exact Windows host(s);
- its matching app shell or complete package is in the release and checksummed;
- the build produces the expected signed library or IPA on that host;
- the result launches on a physical iPhone/iPad, with audio and saves checked;
- this page, [compatibility](COMPATIBILITY.md), `STATUS.md` and the game catalog
  are updated together.

## Checking this page

The catalog audit checks the routes declared by current public releases. It
does not run game builds or qualify a host or device:

```sh
PADMINT_HOME=$(mktemp -d) python3 -B scripts/audit-catalog.py --json
```

The JSON `games[].targets[].hosts` records the live host state for every game.
Update the tables above whenever a game release changes that output. A private
build proof belongs in the proof table until the recipe and matching app are
published.
