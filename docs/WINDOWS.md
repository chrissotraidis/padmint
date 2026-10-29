# Building games on Windows

Published-route snapshot: **29 October 2026**, PadMint **v0.5.24**.

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

## Recently completed

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
| **Private GitHub Cloud Build** | DarkPad | iPhone/iPad `.ipa` | Experimental, prepared in source; clean hosted build not yet recorded. [Private setup and Actions allowance](../README.md#darkpad-private-github-build) |
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

1. Fix SnapPad's recipe to advertise Windows x64 and ARM64, publish a new
   recipe, and run the physical-device check.
2. Fix MeleePad's `windows-x64` recipe key, publish a new recipe, and run the
   physical-device check. Add a pinned-manifest CI check to that game so the
   invalid key cannot recur.
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
