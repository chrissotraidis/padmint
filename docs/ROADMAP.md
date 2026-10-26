# PadMint roadmap: every game, from every computer

Player-route summary updated 26 October 2026 against PadMint 0.5.15; the demand
snapshot below remains dated 19 October. This is the working checklist for which
games PadMint can make on which computer, for which device, and what to do next.
Update it in the same pull request as the work: tick the box, change the cell,
and refresh the numbers with `scripts/demand-report.py` and
`scripts/audit-catalog.py`. Earlier decisions are in [DECISIONS.md](DECISIONS.md)
(D5, D13–D16); per-game details are in [COMPATIBILITY.md](COMPATIBILITY.md).
Tracking issue: #75.

## How PadMint ships today

- **Three ZIPs, one per system** (Mac, Windows, Linux) on PadMint's releases page.
  Each holds a launcher and an `app` folder. There is no installer, and no .dmg
  or .exe. The launcher starts PadMint on the player's own computer and opens its
  page in the web browser at `127.0.0.1`. The Windows ZIP includes Python; Mac
  and Linux use the system's Python 3.9 or newer.
- **PadMint.app** (a native Mac window around the same page, in a .dmg) is made by
  `scripts/package-mac-app.py` but is not published. It is signed ad hoc, so it
  only suits the Mac that built it; publishing it without the **Open Anyway** step
  needs an Apple Developer ID.
- **Updates:** Mac and Linux update themselves from the version button; Windows
  players download the new ZIP.
- **Everything PadMint downloads** (game sources, tools, builds) goes in
  `.padmint` in the player's home folder; finished copies go to Downloads.

### What a Windows player can actually do

1. Download the Windows ZIP, extract it, run PadMint, and get past SmartScreen
   (**More info → Run anyway**). The browser opens PadMint's page.
2. The library offers local KartPad builds, 15 **Build on GitHub** games and
   8 ready-made apps. Other game pages explain their Mac requirement, paused
   status or separate route. HaloPad's Xbox edition has its own GitHub workflow.
3. **Mario Kart Wii:** choose the European disc, then **Android** (PadMint makes
   KartPad's game data folder for the Android app) or **iPhone or iPad**
   (experimental: PadMint builds the IPA, the player installs it with Sideloadly).
4. **A ready-made app** (Caesar III, Daggerfall, Diablo, Fallout 2, Kid Pix,
   Pharaoh, Red Alert, Warcraft II): the page links the download and the install
   steps; there's nothing to build.
5. **My games** shows only copies PadMint built on this PC: PadMint can't see
   what's on an iPhone or iPad without a Mac with Xcode, and can't check Android
   phones.
6. **Games that take the game file in the app** (15, marked `github_build` in the
   catalog): their page says **Build on GitHub** and gives the steps. The player
   forks PadMint and runs **Build a game for iPhone and iPad** in Actions; GitHub's
   free Mac runs the same `padmint make GAME ios` a Mac player runs, and the IPA
   stays with the player's run for a day. Nothing of the player's is uploaded,
   because these builds read no game file. README: "No Mac? Build on GitHub's Mac".
7. **HaloPad's Xbox edition** uses
   [HaloPad's own GitHub workflow](https://github.com/chrissotraidis/projectreach#on-windows-linux-or-any-computer),
   separate from PadMint's 15 choices. Its PC Custom Edition build still needs
   an Apple Silicon Mac.

Linux is the same, except that there's no tested way yet to put an iPhone app on
the device from Linux. An Intel Mac is the same as Windows.

### Two routes off a Mac

iPhone/iPad builds from Windows and Linux use two approaches, depending on when
they read the player's game file. Only the released routes below are available
to players; the rest remain development work:

| The game reads your file | Route | Games |
|---|---|---|
| Inside the app, after installing | GitHub's Mac builds the whole app (`build-for-iphone.yml`); one workflow for all of them, no per-game work | BallPad, BarrelPad, BellPad, BrawlerPad, CTRPad, F0X, GalaxyPad, HarkinianPad, MaskPad, OpenRCT2 Touch, PaperPad, SpaghettiPad, StarshipPad, TribesPad, UTP |
| Inside the app, after installing | The game's own GitHub Mac workflow | HaloPad's Xbox edition |
| While building | The release's app without game code, plus the game part PadMint builds on the player's computer (D13, D14) | KartPad is available (experimental). Additional local Windows routes remain in development; see [Status by game](COMPATIBILITY.md#status-by-game) for evidence and remaining checks. |

Uploading a player's disc or ROM to GitHub stays out (D15), which is why the
games that read those files during the build need the local route.

EctoPad is paused (24 October 2026). It takes its game in the app, but its engine,
Metaforce, and Metaforce's Zeus library were made private by their developers
(AxioDL) until their own public release, so no build can download them. EctoPad
is listed as paused and returns, on the GitHub route too, once they are public.

## The rule

Any build step that reads the player's disc or ROM stays **on the player's
computer**. Hosted builds take no private game input; players add their own
files inside the app afterward. Releases publish source, recipes and apps with no
game code in them. A route that needs a ready-made app with game code inside
isn't a route; the answer is a PadMint build instead.

That rules out shortcuts such as publishing built decompilation apps, even where
an upstream project publishes builds. It also means some downloads that players
use today need a PadMint route before they can be replaced (see **First**).

## Who can make what, today

Rows are the computer PadMint runs on; columns are the device the player plays on.
"PadMint" means PadMint builds it; "the game's builder" means the game's own
repository builds it from the player's disc, but PadMint doesn't run it yet.

| PadMint on → to play on | iPhone / iPad | Mac | Android | Windows PC | Linux PC |
|---|---|---|---|---|---|
| **Mac, Apple Silicon** | PadMint: all 29 | PadMint: 12 | PadMint: KartPad's game part (see First). The game's builder: BlueWake | — | — |
| **Mac, Intel** | Local: KartPad (experimental). Hosted: 15 PadMint games + HaloPad Xbox | HaloPad Xbox builds on GitHub for playing on Apple Silicon | PadMint: KartPad's game part | — | — |
| **Windows** | Local: KartPad (experimental). Hosted: 15 PadMint games + HaloPad Xbox | HaloPad Xbox builds on GitHub for playing on Apple Silicon | PadMint: KartPad's game part. The game's builder: BlueWake (checked on a phone) | The game's builder: BlueWake. Upstream code: CTRPad | — |
| **Linux** | Local: KartPad (experimental). Hosted: 15 PadMint games + HaloPad Xbox. Installing from Linux is not validated | HaloPad Xbox builds on GitHub for playing on Apple Silicon | PadMint: KartPad's game part. The game's builder: BlueWake (untested past the disc check) | — | The game's builder: BlueWake. Upstream code: CTRPad |
| **Android phone** (Termux) | — | — | PadMint: KartPad's game data (emulator only so far) | — | — |

The 8 apps that hold no game code at all (Caesar III, Daggerfall, Diablo,
Fallout 2, Kid Pix, Pharaoh, Red Alert, Warcraft II) install on an iPhone or iPad
from any computer that runs Sideloadly (Windows or Mac).

**Installing what PadMint made:**

| Device | From Mac | From Windows | From Linux |
|---|---|---|---|
| iPhone / iPad | Sideloadly or AltStore | Sideloadly | **Gap:** no tested tool (Sideloadly has no Linux version) |
| Android | Copy the APK or folder | Same | Same |
| Mac | Unzip to Applications | — | — |
| Windows / Linux PC | — | Unzip and run | Unzip and run |

**Why some cells are empty.** A Mac app has to be built with Apple's SDK, which
only runs on a Mac. An iPhone app can still be made off a Mac when its release
ships an app with no game code and PadMint builds the game part on the player's
computer (D13, D14); KartPad works this way. The hosted routes above instead use
GitHub's Mac to build apps that take the game file after installation. Further
local iPhone builds need a portable game pipeline and matching app release.
Android, Windows and Linux copies need a port to that system: only
KartPad, BlueWake (Android, Windows, Linux) and CTRPad (Windows, Linux, from its
upstream code) have one.

## What PadMint shows players

PadMint's library tells each computer what it can make (the line above the
search box), offers the hosted games under **Build on GitHub**, and explains
other routes and requirements on each game's page. When a route above moves,
the catalog entry and these texts move with it; check them in the same pull request.

## Demand

PadMint itself, all releases: Windows 1,299, Mac 1,270, Linux 434 downloads.

| Game | Stars | Visitors, 14 days | iPhone/iPad | Android | Mac | Windows | Linux |
|---|---:|---:|---:|---:|---:|---:|---:|
| kartpad | 685 | 13630 | 12592 | 73921 | 2149 | 0 | 0 |
| bluewake | 414 | 13379 | 869 | 0 | 0 | 13358 | 0 |
| harkinianpad | 393 | 534 | 1934 | 0 | 0 | 0 | 0 |
| goldenpad | 188 | 153 | 853 | 0 | 334 | 0 | 0 |
| sunpad | 188 | 864 | 1775 | 0 | 0 | 0 | 0 |
| openrct2touch | 134 | 35 | 0 | 0 | 0 | 0 | 0 |
| projectreach | 129 | 3198 | 9 | 0 | 9 | 0 | 0 |
| galaxypad | 96 | 2782 | 407 | 0 | 32 | 0 | 0 |
| spaghettipad | 59 | 50 | 525 | 0 | 0 | 0 | 0 |
| maskpad | 51 | 101 | 600 | 0 | 0 | 0 | 0 |
| meleepad | 51 | 275 | 889 | 0 | 0 | 0 | 0 |
| caesarpad | 50 | 30 | 38 | 0 | 0 | 0 | 0 |
| ectopad | 45 | 56 | 0 | 0 | 0 | 0 | 0 |
| paperpad | 42 | 68 | 315 | 0 | 0 | 0 | 0 |
| peonpad | 42 | 31 | 39 | 0 | 0 | 0 | 0 |
| deviltouch | 40 | 27 | 33 | 0 | 0 | 0 | 0 |
| agepad | 37 | 57 | 28 | 0 | 0 | 0 | 0 |
| bellpad | 37 | 108 | 212 | 0 | 0 | 0 | 0 |
| padmint | 28 | 2069 | 0 | 0 | 1270 | 1299 | 434 |
| annepad | 26 | 126 | 198 | 0 | 0 | 0 | 0 |
| ballpad | 25 | 104 | 102 | 0 | 0 | 0 | 0 |
| vaultpad | 21 | 15 | 25 | 0 | 0 | 0 | 0 |
| starshippad | 20 | 13 | 359 | 0 | 0 | 0 | 0 |
| brawlerpad | 18 | 110 | 197 | 0 | 0 | 0 | 0 |
| bearbirdpad | 17 | 42 | 175 | 0 | 0 | 0 | 0 |
| bananapad | 12 | 34 | 77 | 0 | 0 | 0 | 0 |
| snappad | 12 | 38 | 105 | 0 | 0 | 0 | 0 |
| utp | 12 | 36 | 98 | 0 | 0 | 0 | 0 |
| barrelpad | 11 | 27 | 60 | 0 | 0 | 0 | 0 |
| dinopad | 11 | 7 | 28 | 0 | 0 | 0 | 0 |
| f0x | 10 | 18 | 303 | 0 | 0 | 0 | 0 |
| daggerpad | 8 | 23 | 22 | 0 | 0 | 0 | 0 |
| ottsel | 8 | 159 | 0 | 0 | 0 | 0 | 0 |
| ratouch | 7 | 9 | 82 | 0 | 0 | 0 | 0 |
| emeraldtablet | 3 | 29 | 23 | 0 | 0 | 0 | 0 |
| kidpad | 3 | 9 | 56 | 0 | 0 | 0 | 0 |
| squirrelpad | 3 | 58 | 0 | 0 | 0 | 0 | 0 |
| ctrpad | 1 | 91 | 336 | 0 | 52 | 0 | 0 |

Stars and 14-day unique visitors from GitHub on 19 Oct 2026; downloads over all
releases. IPA counts include the code-free apps PadMint downloads while
building. OpenRCT2Touch is a GitHub fork.

## Checklist

### First: PadMint routes for the downloads players use most

- [ ] **KartPad on Android, built by PadMint.** PadMint already builds KartPad's
  Android game part (a library) from the player's disc on every computer. Add a
  KartPad Android app with no game code to KartPad's release, as its iPhone release
  already does (`ios-for-padmint.ipa`); point the recipe's `published_app` at
  it; have PadMint put the game part into it and save the finished APK; check it
  on a real phone, including updating over an older copy with saves.
- [ ] **BlueWake on Windows, built by PadMint.** Add a `windows` target to
  BlueWake's recipe that runs BlueWake's existing Windows builder from the player's
  disc; player-check it on a Windows PC; the game page says how to run it.
- [ ] **BlueWake on Android and Linux, built by PadMint**, the same way, from
  BlueWake's existing builders (Android is checked on a phone; Linux untested past
  the disc check).
- [ ] **Wording.** Once those exist, KartPad's and BlueWake's READMEs and PadMint's
  game pages point Android and Windows players at PadMint.
- [ ] **Android without a computer.** The Termux route makes KartPad's game data.
  With a code-free app it also needs the game part, which is a much heavier build
  for a phone; measure it before promising it.

### Next: iPhone and iPad from Windows and Linux

- [x] Release the shared Windows build foundation in PadMint 0.5.15: managed
  tools, cache/retry handling, non-English paths and cancellation. This does
  not enable additional local game buttons by itself.
  [Status by game](COMPATIBILITY.md#status-by-game) records the completed builds
  and remaining release and device checks.
- [ ] BlueWake (PadMint #135, #136; bluewake#100), then SunPad (sunpad#57) and
  MeleePad. These are development work, not released local Windows routes.
- [x] PadMint's part for all of these: Sideloadly steps on the game page, a release
  check that each code-free app matches its recipe, and an off-Mac column in
  `audit-catalog.py`.
- [ ] A tested way to install on an iPhone from Linux, then its steps.
- [ ] N64 recompilations: the translator on Windows and Linux plus GoldenPad, then
  AnnePad, BananaPad, BearBirdPad, DinoPad, SquirrelPad.
- [ ] AgePad's portable installed-input route: complete a Windows build with
  compatible game files, then device and release checks.
- [ ] Engine ports through spaghettipad#29: SpaghettiPad, then HarkinianPad,
  MaskPad, StarshipPad, PaperPad, BrawlerPad.

### Later

- [ ] CTRPad for Windows and Linux PCs through PadMint, from its upstream code.
- [ ] More local iPhone builds on Windows and Linux: GalaxyPad, BellPad, BallPad,
  BarrelPad, F0X, CTRPad, SnapPad, Ottsel, EctoPad, UTP, OpenRCT2 Touch. Several
  already have hosted routes above; EctoPad remains paused.
- [ ] Real-hardware checks: a PadMint run on a real Windows PC; the Termux route on a
  real Android phone with 8 GB of memory.

### Not planned

- Compiling Mac apps locally on Windows or Linux (needs Apple's SDK). The
  hosted Mac build for HaloPad above is a separate route.
- Uploading private game files to GitHub for builds (D15). Windows work resumed
  under D17 with those inputs kept local; see [Status by game](COMPATIBILITY.md#status-by-game).

Every route that moves needs a check before PadMint offers it: built on that
computer, installed, and the game starts on a real device.
