# PadMint status

Updated **5 October 2026**. The [compatibility page](docs/COMPATIBILITY.md) has
the per-game detail, including **Status by game**, which is where the
compatibility work resumes.

**Scope today ([D15](docs/DECISIONS.md#d15-any-device-from-any-computer-is-the-goal-off-mac-work-is-paused-owner-decision-5-oct-2026)):**
PadMint makes the builds that exist work well: iPhone/iPad copies on an Apple
Silicon Mac for every buildable game, Mac copies for CTRPad and HaloPad, and
KartPad's existing Android and off-Mac routes. Windows players use ready-to-play
downloads where a game publishes them (BlueWake). Building any game for any device
from any computer is the long-term goal and is paused; D15 records the remaining
work and when to revisit it.

## Which games use PadMint

- **KartPad ships ready-to-play builds again from v0.7.9**: an Android APK with
  the game code built in, a full iPhone/iPad IPA and a Mac app, on
  [KartPad's releases](https://github.com/chrissotraidis/kartpad/releases/latest).
  PadMint is optional for KartPad. The page and terminal say so when KartPad is
  chosen, and the Android phone setup says so before it downloads anything.
  On Android, PadMint's useful output is now the `KartPad game data` folder.
- **BlueWake on Windows** downloads its ready-to-play build from
  [BlueWake's releases](https://github.com/chrissotraidis/bluewake/releases/latest).
  PadMint's Windows route for BlueWake
  ([draft #46](https://github.com/chrissotraidis/bluewake/pull/46)) is parked.
  This exception may change.
- **Every other Pad game** builds through PadMint, or is a no-build download
  listed in PadMint.

## PadMint itself

- **v0.3.6**: one directory of every game (tabs for Build with PadMint, Download
  and Not available yet, console badges, search, back buttons). Games this
  computer can't build stay listed with the reason (**Needs an M1+ Mac**) instead
  of disappearing ([bellpad#20](https://github.com/chrissotraidis/bellpad/issues/20)).
  On a Mac the plan shows each game's install-once Homebrew line with a Copy
  button. README rewritten for every game.
- **v0.4.7**: every iPhone build made with Xcode checks Xcode's iOS platform before
  it starts (12 games had no check), and a missing program now stops PadMint before
  it downloads the game's source instead of after. PaperPad no longer asks for the
  ROM before building (the app asks for it). `scripts/audit-catalog.py` checks the
  whole catalog against each game's published recipe; it reports no problems.
- **v0.4.6**: HaloPad builds for Mac too: the same app on Apple Silicon Macs, with
  keyboard and mouse and no Apple account needed.
- **v0.4.5**: build-time wording matches reality: the first build takes "a few
  minutes to a few hours" (CTRPad takes about a minute), and the terminal plan no
  longer says the copy is built from your game file when the game asks for it in
  the app. CTRPad v0.2.1 and v0.2.2 from PadMint ran on an iPhone 14 (iOS 26.6.2).
- **v0.4.4**: a release recipe that couldn't be read is tried again on the next
  plan instead of leaving an empty plan for the rest of the window. Copies from
  decompilation ports built without the player's game say only that they hold
  game code. README covers Mac copies.
- **v0.4.3**: a game's Mac copy is offered only on Apple Silicon Macs, where it
  runs, and the choice reads **This Mac**. CTRPad gets Mac finishing steps and a
  PlayStation badge.
- **v0.4.2**: CTRPad is back: PadMint builds Crash Team Racing for iPhone, iPad
  and Apple Silicon Mac from CTRPad's public source, and players choose their own
  disc image in the app. CTRPad's releases publish the recipe only.
- **v0.4.1**: HaloPad can be built: your own Halo Custom Edition installer and
  product key make HaloPad for iPhone and iPad, with your game package handed over
  beside it.
- **v0.4.0**: the unzipped folder shows only the launcher, **Start here.txt**
  (English, Spanish, Portuguese) and an **app** folder. On the page, **How it
  works** is at the top, the PadMint logo takes you back to the game list, and
  **Make another copy** goes back to the list instead of showing the finished
  build again. New logo.
- **v0.3.9**: SwiftUI apps (GoldenPad) are recognised as scene-based, so they get
  no iOS 27 warning.
- **v0.3.8**: the download apps (CaesarPad, DaggerPad, DevilTouch, Emerald
  Tablet, KidPad, PeonPad, VaultPad) show all their steps again; 0.3.6 and 0.3.7
  showed only the first.
- **v0.3.7**: the finish screen warns when a copy may not open on iOS 27
  (see below).
- **v0.3.5**: alphabetical game list with console filters and search, language
  switching that keeps your choices, release lookup that skips releases
  without a PadMint recipe, and the KartPad ready-to-play notice.
- The player page (0.3.4 and later) shows each step as it happens: release,
  source, every tool download with its size and source, the build stages and
  where the result is saved. English, Spanish and Portuguese.
- Checks: source tests, packaged player-flow CI on Windows, Mac and Linux, and
  the packages' content gate.

## Where the compatibility work stands

**Mac builds, 4 October:** every game PadMint builds was built from its latest
public recipe on one Apple Silicon Mac with Xcode 27; all that ran completed,
including StarshipPad v0.2.0, whose old SDK-selection failure no longer happens
([recorded Mac builds](docs/COMPATIBILITY.md#recorded-mac-builds-4-october)).
**iOS 27:** 10 of those apps were linked with the iOS 27 SDK without UIKit scene
startup, which Apple requires. Every game now has it in its latest release
(published 4 October), checked on the iOS 27.0 Simulator, so a PadMint build made
now includes it ([details](docs/COMPATIBILITY.md#recorded-mac-builds-4-october)).

Families, in order; one game proves each family. Details and next steps per game
are in [Status by game](docs/COMPATIBILITY.md#status-by-game).

1. **GameCube and Wii** (reference BlueWake): the iPhone module builds without
   Xcode through PadMint for BlueWake on Linux and on a Mac
   ([draft #42](https://github.com/chrissotraidis/bluewake/pull/42)) and for SunPad on
   Linux ([draft #57](https://github.com/chrissotraidis/sunpad/pull/57)). Both still need
   a device check and a release. MeleePad is blocked on its Slippi parts (a
   Rust toolchain for iOS, Slippi's C++ libraries and multi-file insertion); see
   its row. Recipes that compile these
   generated chunks with clang 22 need `-fno-slp-vectorize -mllvm
   -large-interval-freq-threshold=10`: without them one chunk can take hours.
2. **N64** (reference GoldenPad): Mac only. Needs a published app without game
   code that loads a module.
3. **Engine ports** (reference SpaghettiPad): iPhone modules build on Windows and
   Linux in [draft #29](https://github.com/chrissotraidis/spaghettipad/pull/29);
   needs a released recipe.

Open, not started: a data-only Android target in KartPad's recipe (skips the
1 GB NDK), physical Android and x64 Windows acceptance, and StarshipPad's and
SunPad's updated public recipes ([#22](https://github.com/chrissotraidis/starshippad/pull/22),
[#55](https://github.com/chrissotraidis/sunpad/pull/55)).
[Issue #75](https://github.com/chrissotraidis/padmint/issues/75) tracks the
catalog-wide work.

Personal game outputs stay private. Content scans are technical checks;
publication and rights decisions are reviewed separately.

## Earlier evidence

The [historical status record](STATUS-HISTORY.md) keeps earlier versions of this
page verbatim.
