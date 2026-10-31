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
| GoldenEye 007 (GoldenPad) | Apple Silicon Mac | Reads the ROM while compiling | [goldenpad#52](https://github.com/chrissotraidis/goldenpad/pull/52): on 1 Nov the packaged PadMint 0.5.27 build completed on Windows 11 ARM64 in 70 s with a shell built from the same revision. Next: publish the shell and recipe, device check |
| Banjo-Kazooie (BearBirdPad) | Apple Silicon Mac | Reads the ROM while compiling | [bearbirdpad#27](https://github.com/chrissotraidis/bearbirdpad/pull/27): on 1 Nov the packaged PadMint 0.5.27 build completed on Windows 11 ARM64 in 98 s with a shell built from the same revision. Next: publish the shell and recipe, device check |
| Donkey Kong 64 (BananaPad) | Apple Silicon Mac | Reads the ROM while compiling | [bananapad#22](https://github.com/chrissotraidis/bananapad/pull/22): on 1 Nov the packaged PadMint 0.5.27 build completed on Windows 11 ARM64 in 108 s, and the recipe is now `experimental`. Next: publish the shell and recipe, device check |
| Super Mario Sunshine (SunPad) | Apple Silicon Mac | Reads the disc while compiling | Merge [sunpad#57](https://github.com/chrissotraidis/sunpad/pull/57), then [#78](https://github.com/chrissotraidis/sunpad/pull/78); publish, device check |
| Super Smash Bros. Melee (MeleePad) | Apple Silicon Mac | Reads the disc while compiling | [meleepad#52](https://github.com/chrissotraidis/meleepad/pull/52): host names fixed, and on 31 Oct the packaged PadMint 0.5.27 build completed on Windows 11 ARM64 from the reviewed v1.02 disc in 15.5 min. Next: release the recipe, device check |
| Pokémon Snap (SnapPad) | Apple Silicon Mac | Reads the ROM while compiling; its decompilation tools still come from a private, locally verified bundle | [snappad#12](https://github.com/chrissotraidis/snappad/pull/12): publish those tools through PadMint's managed tools, then add Windows hosts to the recipe. SnapPad's release pause still applies |
| The Wind Waker (BlueWake) | Ready-to-play **Windows desktop** download; iPhone/iPad needs a Mac | Reads the disc while compiling | [bluewake#100](https://github.com/chrissotraidis/bluewake/pull/100): on 31 Oct the complete route ran on Windows 11 ARM64 through PadMint 0.5.27: original disc to personal IPA in 2 h 19 min, warm repeat with nothing recompiled. Next: release the recipe with Windows hosts, then a device check |
| Pokémon Stadium (AnnePad) | Apple Silicon Mac | Reads the ROM while compiling | [annepad#20](https://github.com/chrissotraidis/annepad/pull/20) saves the module work with repeatable shell and module builds. On 31 Oct the module compiled on Windows 11 ARM64 and on Mac and passed PadMint's import audit on both. Next: one Windows script from ROM to module, then a published shell, recipe and device check |
| Dinosaur Planet (DinoPad) | Apple Silicon Mac | Reads the ROM while compiling | [dinopad#19](https://github.com/chrissotraidis/dinopad/pull/19): the supported ROM built completely on Windows 11 ARM64 and Mac on 31 Oct, and the recipe's Windows module route ran through packaged PadMint 0.5.27 on Windows 11 ARM64; publish the shell and recipe, device check |
| Jak and Daxter (Ottsel) | Apple Silicon Mac | Reads the disc while compiling, and its iOS app links the compiled game code | [ottsel#7](https://github.com/chrissotraidis/ottsel/pull/7): on 31 Oct Windows 11 ARM64 extracted, decompiled and compiled the owner's disc, and the game code matched the Mac byte for byte after two compiler fixes. Next: a device check of the changed Mac output, then a game-free app with the compiled game in a private library |
| Age of Empires II: DE (AgePad) | Apple Silicon Mac | Adds the player's installed **Mac** Steam edition and Steam for Mac's libraries to the app | [agepad#15](https://github.com/chrissotraidis/agepad/pull/15): the Steam libraries now download from Valve's public packages on any computer. On 31 Oct, 6 of 8 pinned Steam files no longer matched an installed Steam, so the v0.1.0 Mac route currently fails after Steam updates. Next: an iPad run, a base-app release with the new pins, then the Mac game via SteamCMD on Windows |
| Metroid Prime (EctoPad) | Paused | Its engine (Metaforce) is private until its developers publish it | Wait for Metaforce |
| 8 ready-made apps: CaesarPad, DaggerPad, DevilTouch, Emerald Tablet, KidPad, PeonPad, RAtouch, VaultPad | **No build needed**: download and install with Sideloadly | — | — |

## Managed Windows tools still to publish

SnapPad's and AnnePad's Windows routes rebuild the original N64 ROM from its
decompilation before generating code, which needs the original IDO compilers and
MIPS tools. PadMint does not manage these yet, so both still read a private,
locally verified tool bundle (SnapPad's `scripts/build-windows-module.py
--tools`). The roles SnapPad's backend checks, and where PadMint stands:

| Tool | PadMint today |
|---|---|
| IDO 5.3 and 7.1 compilers | Producer and synthetic checks in `scripts/ido-windows` (also covers AnnePad); not published |
| Rabbitizer 1.14.3 wheel with the unsigned-value fix (`1.14.3+padmint.1`) | Producer in `scripts/rabbitizer-windows`; not published |
| asm-processor (Python implementation) | Preparation in `scripts/asm-processor-windows`; not published |
| MIPS binutils 2.46.1: `as`, `ld`, `objcopy`, `strip`, `readelf`, `objdump` | Producer in `scripts/binutils-windows` ([#225](https://github.com/chrissotraidis/padmint/pull/225)): Windows builds give byte-identical fixture outputs to a native build on x64 and ARM64; not published |
| `pigment64`, `uv`, `cpp`, and the setuptools, wheel and packaging build wheels | No producer or pin yet |

Publishing these needs a pinned, checksummed archive for each, a
`tools.lock.json` entry per Windows host, and the owner's approval to publish
tool binaries. Then the SnapPad and AnnePad recipes can declare Windows hosts
the way GoldenPad, BearBirdPad, BananaPad, SquirrelPad and DinoPad do.

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
| [GoldenPad #52](https://github.com/chrissotraidis/goldenpad/pull/52) | Packaged PadMint 0.5.27 build on Windows 11 ARM64 (1 Nov) from a fresh clone and a shell built at the same revision, adding only the module; earlier emulated x64 toolchain | Publish the shell and recipe, device check; native private x64 hardware remains separate |
| [BearBirdPad #27](https://github.com/chrissotraidis/bearbirdpad/pull/27) | Packaged PadMint 0.5.27 build on Windows 11 ARM64 (1 Nov), all 279 shell entries unchanged; earlier emulated x64; generated files match Mac | Publish the shell and recipe, device check; native private x64 hardware remains separate |
| [BananaPad #22](https://github.com/chrissotraidis/bananapad/pull/22) | Packaged PadMint 0.5.27 build on Windows 11 ARM64 (1 Nov), all 248 shell entries unchanged; public generator CI | Publish the shell and recipe, device check; native private x64 hardware remains separate |
| [SnapPad #12](https://github.com/chrissotraidis/snappad/pull/12) | Full Windows ARM64 ROM-to-IPA pipeline; byte-identical generated output; warm rebuild performs no compilation | Add Windows hosts to the recipe, publish it, device check; current recipe has no Windows host |
| [MeleePad #52](https://github.com/chrissotraidis/meleepad/pull/52) | Packaged PadMint 0.5.27 build on Windows 11 ARM64 from the reviewed v1.02 disc (31 Oct), with corrected `windows-x86_64` host names; earlier emulated x64 backend | Publish the recipe, device check; native private x64 hardware remains separate |
| [SunPad #78](https://github.com/chrissotraidis/sunpad/pull/78) | Windows ARM64 and emulated x64 backend; PRs #57 and #78 pass | Merge prerequisite [#57](https://github.com/chrissotraidis/sunpad/pull/57) and then #78, publish the recipe, device check |
| [DinoPad #19](https://github.com/chrissotraidis/dinopad/pull/19) | Supported ROM to module on Windows 11 ARM64 through PadMint 0.5.27's release ZIP and freshly installed tools (31 Oct), and on Mac; all 219 translated game-code files and the RSP code match Mac; PadMint's import, iOS 15 and insertion checks pass on both | Recipe declares Windows hosts (31 Oct); publish the shell and recipe, device check; native x64 hardware remains separate |

## Remaining local-Windows work

**Partial or blocked:**

| Game | Current position |
|---|---|
| [BlueWake](https://github.com/chrissotraidis/bluewake/pull/100) | Windows desktop release works outside PadMint. Its iPhone/iPad route now completes on Windows 11 ARM64 from the original disc through packaged PadMint, and a warm repeat recompiles nothing. A release with Windows hosts and a device check remain. |
| [AnnePad](https://github.com/chrissotraidis/annepad/pull/20) | Fresh Mac and Windows decompilation match the supported ROM. The game-free shell and private module pass PadMint's import, iOS 16 and insertion checks on Mac and Windows 11 ARM64 (31 Oct), from repeatable scripts. One Windows script from ROM to module remains. |
| [AgePad](https://github.com/chrissotraidis/agepad/pull/15) | The build is a portable Python inject step. Its Steam for Mac files can now be fetched from Valve on any computer and inject succeeded with them on Mac. The Mac game files still have to reach a Windows PC (SteamCMD with the player's own login), and the v0.1.0 recipe's Steam pins are out of date. |
| [Ottsel](https://github.com/chrissotraidis/ottsel/pull/7) | The patched OpenGOAL tools build and run natively on x64 and ARM64 Windows. On Windows 11 ARM64 the supported disc went through extraction, decompilation and `goalc --isa arm64`. Two compiler fixes (a retry outside a `catch` block, and a stable sort in register allocation) make `KERNEL.CGO`, `GAME.CGO` and 320 of 321 outputs byte-identical with the Mac. The iOS app still links the compiled game code, so a game-free shell and module boundary are needed. |

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
   proven, reuse it for GoldenPad and BearBirdPad, then BananaPad. All four
   passed a packaged PadMint Windows ARM64 build with a shell built from the
   same revision; a shell from an older revision has a different module
   identity and is refused.
5. BlueWake: mark its Windows hosts experimental, publish, device check. Then
   AnnePad's one Windows script from ROM to module. AgePad needs the Mac game
   through SteamCMD; Ottsel needs a game-free shell and module boundary.

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
