# iPhone and iPad copies from a Windows PC

**Goal:** a player with a Windows PC makes an iPhone or iPad copy of any game PadMint
builds, the same way a Mac player does today: choose the game, add their own game file,
get a personal IPA, install it with their own Apple ID. Linux gets the same route, since
the steps after the game's source step are identical. BlueWake comes first.
Owner decision: [D16](DECISIONS.md#d16-iphone-and-ipad-copies-from-windows-bluewake-first-owner-decision-7-oct-2026).
Tracking issue: [#75](https://github.com/chrissotraidis/padmint/issues/75).

## How it works

An iPhone app has two kinds of code:

- **The app:** screen, sound, touch, controllers and the file picker. These use Apple's
  iPhone SDK, which may only be used on Apple computers. It holds no game code, so the
  game's maintainer builds it once on a Mac and publishes it
  (`<Game>-vX.Y.Z-ios-unsigned.ipa`).
- **The game:** plain C/C++ made from the player's own game file. PadMint compiles it on
  the player's computer with LLVM and Apple's open-source headers (D12, D13), checks it
  against the published app and puts it inside (D14).

KartPad already works this way on Windows and Linux. Each other game needs the four parts
in [Adding a game](ADDING_A_GAME.md#iphone-modules-on-any-computer): a published app with
no game code, a source step per system, a module build with `{ios_toolchain}`, and
`ios_module` in its recipe.

**What a Windows player needs:** PadMint's Windows ZIP, their own game file, any build
tools the game lists (BlueWake: Visual Studio Build Tools with C++ Clang), the free space
the game lists and a few hours for the first build. To install: [Sideloadly](https://sideloadly.io)
with iTunes and iCloud from Apple's website (not the Microsoft Store versions) and a USB
cable. With a free Apple ID an install lasts 7 days, and a device holds up to 3 sideloaded
apps at a time.

## Routes we don't take

| Route | Why not |
|---|---|
| Apple's SDK on the PC (for example xtool with an extracted Xcode) | Apple's license limits the SDK to Apple computers. It would also miss Xcode-only tools that several games use (asset catalogs, SwiftUI, Metal shader builds) |
| A cloud Mac | Uploads the player's game files |
| A macOS virtual machine on a PC | macOS's license limits it to Apple computers |
| Publishing complete IPAs | They contain game code (D5) |

## Order of work

One game proves each family; the rest follow it. Sizes are focused work, before the
device check each game needs.

| Order | Games | State on 7 Oct 2026 | Next step | Size |
|---|---|---|---|---|
| Done | KartPad | Experimental on Windows and Linux | Wider device checks | — |
| 1 | **BlueWake** | [Draft #100](https://github.com/chrissotraidis/bluewake/pull/100), checklist below | Finish the Windows build and play it on an iPad | 2–3 days |
| 2 | PadMint shared pieces | — | Windows install steps on the finish screen and in the README; a release check that a recipe and its published app come from the same commit; an off-Mac column in `scripts/audit-catalog.py`; inserting several files (MeleePad) | 2–3 days |
| 3 | SunPad, MeleePad | SunPad's module builds on Linux ([draft #57](https://github.com/chrissotraidis/sunpad/pull/57)); MeleePad not started | SunPad: a Windows source step. MeleePad: Rust and Slippi libraries through `{ios_toolchain}` | SunPad 1 day, MeleePad 2–3 |
| 4 | SpaghettiPad, then HarkinianPad, MaskPad, StarshipPad, BrawlerPad, PaperPad | SpaghettiPad's module builds on Windows and Linux ([draft #29](https://github.com/chrissotraidis/spaghettipad/pull/29)) | A released recipe with its published app | 2–3 days, then 1–2 each |
| 5 | GoldenPad, then AnnePad, BananaPad, BearBirdPad, DinoPad | One combined app each | Split GoldenPad; run its translator on Windows | 2–4 days, then about 1 each |
| 6 | CTRPad, BellPad, BallPad, BarrelPad | One combined app each | Split each app | 2–4 days each |
| — | AgePad, HaloPad | Mac only by design | None | — |
| — | Download-tab games | Nothing to build; sideload from Windows today | None | — |

About 5–9 weeks for the whole catalog. Steps 4–6 publish apps without game code for
decompilation ports, which changes D5 for them (D16).

## BlueWake first

- [x] Recipe: Windows translate step plus the shared module steps (#100), updated to
  BlueWake 0.6.0's `main` on 7 October.
- [x] Windows source: on a Windows 11 ARM64 VM with the owner's disc, PadMint's Windows
  step produced composite digest `54f54434…`, the same verified source the Mac and
  Linux builds produce (4 October).
- [x] Module compile on Windows with PadMint's LLVM 21.1.8: all 757 files, then
  PadMint's import check, insertion, IPA check and publication gate passed (7 October;
  #100 as of 4 October with the v0.2.0 app, in a Windows 11 ARM64 VM on a busy Mac).
- [x] Runs on an iPad: that IPA, signed on the Mac and installed as a separate test app
  on an iPad Pro (M2, iPadOS 27.0.1), loaded the Windows-built module and ran the title
  sequence at 30 FPS and full speed with no audio drops.
- [x] The same build for 0.6.0 (#100 at `43a8bd8`) against 0.6.0's app without game code:
  built on Windows on ARM in 285 minutes, passed PadMint's checks and ran on the iPad Pro.
- [ ] **Mods.** The Windows and Linux route stops before the mods step, so its copies have
  no Widescreen or Better Wind Waker options (`[mods] available=0`; a Mac copy has 3). The
  builders need a stop after the mods step for PadMint.
- [ ] **Speed.** In the title's automatic demo on the iPad Pro (M2), the game thread is 69–82%
  busy in the Windows-built 0.6.0 copy and 48–55% in the Mac-built one, both at 30 FPS. The
  bundled optimization profile made no measurable difference with PadMint's LLVM; find out
  whether it applies at all and which of the Mac build's compile flags matter. An A13 device
  has much less headroom.
- [ ] **Mac copies through the same recipe.** PadMint's insert step left Xcode-built modules
  unloadable on iOS 27 (`mis-aligned LINKEDIT string pool`); PadMint 0.4.11 aligns them
  ([#136](https://github.com/chrissotraidis/padmint/pull/136)). Players on older PadMint would
  still get a broken Mac-built copy, so the Mac step must not change until that is solved.
- [ ] Played: file select, a save, relaunch, sound, controller and touch; installed
  from Windows with Sideloadly.
- [ ] Speed against the Mac build. The Windows build compiles without the Mac build's
  training run; try BlueWake's committed `composite-rt.profdata` if it is slower.
- [ ] A native Windows x64 PC (so far only Windows on ARM in a VM).
- [ ] Release: a BlueWake release whose recipe lists the Windows hosts, with its app
  without game code built from the same commit; then `ios_off_mac: true` in
  `catalog/bluewake.json` and the README steps.

The module must come from the same commit as the published app: a module built for a
different version can fail PadMint's import check or crash at launch.

## When a game counts as working from Windows

The three checks in [Before calling a route verified](COMPATIBILITY.md#before-calling-a-route-verified),
on a Windows PC: the player path through packaged PadMint, the output checks, and the
game played on a device. Until then the host stays `experimental` in the recipe and the
game is not offered on Windows.

Android copies are outside this plan: only KartPad has an Android port.
