# PadMint roadmap: every game, from every computer

Player-route summary audited 29 October 2026 against PadMint 0.5.24; the demand
snapshot below remains dated 19 October. This is the working checklist for which
games PadMint can make on which computer, for which device, and what to do next.
Update it in the same pull request as the work: tick the box, change the cell,
and refresh the numbers with `scripts/demand-report.py` and
`scripts/audit-catalog.py`. Earlier decisions are in [DECISIONS.md](DECISIONS.md)
(D5, D13–D18); per-game details are in [COMPATIBILITY.md](COMPATIBILITY.md).
The focused Windows roster and active queue are in [WINDOWS.md](WINDOWS.md).
Tracking issues: [#75](https://github.com/chrissotraidis/padmint/issues/75)
(local Windows/Linux coverage) and
[#215](https://github.com/chrissotraidis/padmint/issues/215) (more cloud choices).

## Resume work

**Current queue: [What PadMint still needs](REMAINING.md)** (2 November 2026).
It replaces the lists below as the place to start; they stay as dated notes.

**Owner handoff, 29 October 2026:** save the documentation and small fixes now,
then stop. A later request to **continue working on improvements to PadMint**
means resume this queue: make more of Chris's existing ports buildable, with
clearer choices on Windows, Linux and Mac. Recheck the affected release and PR
before acting; the dated findings below are a starting point, not proof that a
draft is still current. No background builds or scheduled work are requested.

### Current state, 1 November 2026

PadMint **0.5.29** applied the requested route wording
([Build-route wording](BUILD_ROUTE_COPY.md)): build steps name the computer,
games carry a short note for a host where a route has a known limit, Linux says
before a build that installing from Linux isn't tested, and the BlueWake,
HaloPad and DarkPad cards were corrected, in all three languages. The README
leads with the three routes. One decision is open: the visibility rule for
personal cloud output (DarkPad private, other personal builds public).

PadMint exposes seven local Windows routes; Linux exposes KartPad only. Both
hosts can start 17 cloud routes (15 public PadMint choices, private DarkPad and
HaloPad Xbox in its own repository). The catalog has 30 ports with build
routes, eight guided downloads and one paused entry. Six of the 30 still need a
local Apple Silicon Mac for iPhone/iPad, including AgePad with its known
Steam-version problem. The live recipe audit on 1 November checked all 39
entries with zero inconsistencies; it did not run game builds or establish
device acceptance. Use [the current roster](WINDOWS.md) and
[recipe matrix](COMPATIBILITY.md) for details.

### Historical baseline, 29 October 2026

- **0.5.24**, main at `d6f0f59`: all three release ZIPs passed checksums and
  contained the same 39-entry catalog. The live recipe audit found zero
  inconsistencies; all eight download-only entries had public IPA assets and
  working help links. These checks do not establish full-game or device acceptance.
- The catalog contains **30 buildable ports, 8 guided downloads and 1 paused
  port**. Windows/Linux offer **1 local build (KartPad, experimental), 15 shared
  GitHub Cloud Build choices and 15 other routes**. The other routes are 12
  Mac-only ports, BlueWake's and HaloPad's separate routes, and paused EctoPad.
- Windows/Linux run PadMint locally and show its interface in a browser. The
  private Mac app wraps the same interface in a native window. A hosted Mac
  build is a separate route; it is not local Windows/Linux compilation.
- Melee PC was removed in [#214](https://github.com/chrissotraidis/padmint/pull/214).
  Its wrapper is retired. Reviewing all 39 repositories found no second
  recipe-only wrapper; MeleePad is Chris's separate port. Namespace checks alone
  do not prove ownership. New catalog entries still require owner approval.
- [Packaged host checks](https://github.com/chrissotraidis/padmint/actions/runs/40683571175)
  passed on real Windows x64/ARM64 and Linux x64 runners; small iOS module
  probes also passed on Linux ARM64. This is packaging and compiler evidence,
  not full games, interactive file dialogs or physical-device acceptance.

### Next implementation pass

1. **Keep the ownership rule consistent.** Normal library, `make`, `get` and
   cached-source routes reject removed games. Advanced `build --repo` still
   accepts an uncatalogued local manifest without requiring catalog membership
   or checking repository origin. This is also the documented development path for a
   new own-port recipe before catalog registration. Define how those legitimate
   checkouts remain supported, then enforce the ownership rule before planning,
   downloads or execution. Test unknown and retired IDs, mismatched origins,
   existing-port edits, uncatalogued own-port fixtures, worktrees and offline
   operation. Use synthetic fixtures; never build someone else's app to test it.
2. **Settle and finish the cloud routes.** Chris decides one visibility rule
   for personal cloud output; today DarkPad requires a private copy while
   BallPad, BellPad, BrawlerPad, PaperPad and the other personal builds use
   public forks ([the comparison](BUILD_ROUTE_COPY.md#darkpad-is-not-technically-a-different-kind-of-personal-build)).
   Change `github_build_private`, the guide and the card together afterwards.
   Hosted builds pass, but a private manual DarkPad run, signing/install and
   device gameplay still need validation. SquirrelPad needs the player's ROM
   during compilation and stays local.
3. **Turn private local-build proofs into usable released routes.** On
   1 November GoldenPad, BearBirdPad, BananaPad, SquirrelPad, DinoPad and
   MeleePad published Windows recipes with matching app shells (experimental;
   PadMint's page lists them from 0.5.28). Next, follow
   [the per-game queue](WINDOWS.md#active-queue): install and play a
   Windows-built copy of each (then drop their Windows note in the catalog); a Windows-enabled iPhone recipe following
   [bluewake#100](https://github.com/chrissotraidis/bluewake/pull/100) (published
   BlueWake 0.10.0 still declares only Mac for iPhone); SunPad
   #57 then #78; AnnePad and SnapPad once PadMint publishes its IDO, binutils,
   Rabbitizer and asm-processor builds; then Ottsel and AgePad.
   Reuse shared runner/module work. Record Windows x64, Windows ARM64, Linux
   x64 and Linux ARM64 separately; Windows evidence does not qualify Linux.
   A private successful build cannot enable a public **Build here** button.
4. **Make update status reliable for preview apps.** Seven download-only ports
   publish prereleases; the stable `/releases/latest` lookup cannot report
   their latest version. Define the intended per-game release channel, then
   test preview-only, stable-plus-preview, missing-asset and offline cases.
   Do not silently opt stable users into previews or show unknown as current.
5. **Validate the player experience on the actual hosts.** Check ZIP extraction,
   launch, browser/file selection, non-English paths, cancellation/retry,
   updates and output installation on Windows/Linux. Add a tested Linux iPhone
   installation route before documenting it as supported; until then the Linux
   pages send the `.ipa` to a Windows PC or Mac. The 0.5.29 wording was checked
   on pages served for each host, not on the physical hosts. Keep native x64,
   ARM64, emulation, synthetic checks and device gameplay evidence distinct.

Keep source, recipes, matching app artifacts, public host labels and these docs
in sync. Before announcing a game release, use the repository's artifact audits
and PadMint's clean `scripts/player-check.sh` before tagging and after publishing,
plus the relevant host and device checks. Keep private game inputs local.

### Existing branches to reconcile before replacing work

| PR | State at the audit | Next decision |
|---|---|---|
| [#216](https://github.com/chrissotraidis/padmint/pull/216) | Merged; released in 0.5.27 | Validate a private manual run, signing/install and device gameplay |
| [#172](https://github.com/chrissotraidis/padmint/pull/172) | Draft iOS SDK header work; checks pass | Reuse where a real module build needs it; this alone is not a complete game route |
| [#168](https://github.com/chrissotraidis/padmint/pull/168) | Docs-only Android/Windows distribution proposal | Reconcile with each game's current owner-approved distribution before implementation |
| [#136](https://github.com/chrissotraidis/padmint/pull/136) | Conflicted older BlueWake draft | Preserve its useful alignment fix, rebase and remove premature host enablement |
| [#135](https://github.com/chrissotraidis/padmint/pull/135) | Conflicted older plan; obsolete D16 numbering | Reconcile with current D16/D17 rather than merging the old plan unchanged |

The older checklist below records longer-term ideas. Its distribution proposals
are not a change to KartPad's current Android exception or other games' release
rules, and its demand figures are historical. Start with this resume queue.

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
2. **Build here:** KartPad, GoldenPad, BearBirdPad, BananaPad, SquirrelPad,
   DinoPad and MeleePad compile locally for iPhone/iPad on Windows, experimental.
   KartPad also prepares Android game data. Sign/install the IPA with Sideloadly.
3. **GitHub Cloud Build:** 15 games use public PadMint forks, DarkPad currently
   requires a private copy, and HaloPad Xbox uses its own workflow. PadMint opens
   the guide; the player starts the build on GitHub's temporary Mac. No player
   ROM or disc is uploaded. Personal-output visibility is an open decision in
   [Build-route wording](BUILD_ROUTE_COPY.md).
4. **A ready-made app** (Caesar III, Daggerfall, Diablo, Fallout 2, Kid Pix,
   Pharaoh, Red Alert, Warcraft II): the page links the download and the install
   steps; there's nothing to build.
5. **My games** shows only copies PadMint built on this PC: PadMint can't see
   what's on an iPhone or iPad without a Mac with Xcode, and can't check Android
   phones.
6. **Apple Silicon Mac:** every other buildable game is dimmed with the reason.
   Some have private Windows proofs, but those proofs are not a published route.
   HaloPad's PC Custom Edition also needs an Apple Silicon Mac. The active
   release queue is in [WINDOWS.md](WINDOWS.md).

Linux offers KartPad locally and the same 17 cloud routes, not the six new
Windows-only local routes. Installing an iPhone app directly from Linux is
not validated. On Intel Macs, KartPad's local iPhone route uses Xcode; the
other hosted choices remain available.

### Windows and Linux build routes

iPhone/iPad builds from Windows and Linux use these routes, depending on when
they read the player's game file. Only the published routes below are available
to players; the rest remain development work:

| Route | What compiles | Games |
|---|---|---|
| **Build here** | The player's computer compiles from their game file | Windows: KartPad plus GoldenPad, BearBirdPad, BananaPad, SquirrelPad, DinoPad and MeleePad. Linux: KartPad only. All experimental |
| **GitHub Cloud Build** | GitHub runs a temporary macOS machine and runs PadMint's shared workflow (`build-for-iphone.yml`) | BallPad, BarrelPad, BellPad, BrawlerPad, CTRPad, F0X, GalaxyPad, HarkinianPad, MaskPad, OpenRCT2 Touch, PaperPad, SpaghettiPad, StarshipPad, TribesPad, UTP |
| **GitHub Cloud Build, private** | The same shared workflow in a private copy of PadMint | DarkPad, experimental; output-policy consistency remains to resolve |
| **GitHub Cloud Build, project-owned** | The game's own GitHub macOS workflow | HaloPad's Xbox edition |
| **Apple Silicon Mac** | The player's Mac with Xcode | Local iPhone routes for AnnePad, SnapPad, SunPad, BlueWake, Ottsel and AgePad are Mac-only; AgePad has a known blocker. Windows proofs do not enable buttons |

Uploading a player's disc or ROM to GitHub stays out (D15), which is why the
games that read those files during the build need the local route.

EctoPad is paused (24 October 2026). It takes its game in the app, but its engine,
Metaforce, and Metaforce's Zeus library were made private by their developers
(AxioDL) until their own public release, so no build can download them. EctoPad
is listed as paused; its local and GitHub routes can be reassessed once those
sources are public again.

## Private inputs and distribution

Any build step that reads the player's disc or ROM stays **on the player's
computer**. Hosted builds take no private game input; players add their own
files inside the app afterward. Each game's current owner-approved distribution
still applies, including KartPad's ready-to-play Android exception and the
existing guided downloads. Recipe-only releases remain recipe-only; an upstream
project publishing binaries is not permission to change a Pad game's formula.

The **First** checklist below proposes replacing some current downloads with
personal PadMint builds. It is future work, not a change to today's published
routes or authorization to change their distribution.

## Who can make what, today

Rows are the computer PadMint runs on; columns are the device the player plays on.
"PadMint" means PadMint builds it; "the game's builder" means the game's own
repository builds it from the player's disc, but PadMint doesn't run it yet.

| PadMint on → to play on | iPhone / iPad | Mac | Android | Windows PC | Linux PC |
|---|---|---|---|---|---|
| **Mac, Apple Silicon** | 30 declared routes; AgePad has a blocker | PadMint: 12 | PadMint: KartPad's game part (see First). The game's builder: BlueWake | — | — |
| **Mac, Intel** | Local: KartPad (experimental). Cloud: 15 public PadMint games, private DarkPad, HaloPad Xbox | HaloPad Xbox builds with GitHub Cloud Build for playing on Apple Silicon | PadMint: KartPad's game part | — | — |
| **Windows** | Local: seven games (experimental; see WINDOWS.md). Cloud: 15 public PadMint games, private DarkPad, HaloPad Xbox | HaloPad Xbox builds with GitHub Cloud Build for playing on Apple Silicon | PadMint: KartPad's game part. The game's builder: BlueWake (checked on a phone) | BlueWake Windows x64 download; PadMint does not build desktop copies | — |
| **Linux** | Local: KartPad (experimental). Cloud: 15 public PadMint games, private DarkPad, HaloPad Xbox. Installing from Linux is not validated | HaloPad Xbox builds with GitHub Cloud Build for playing on Apple Silicon | PadMint: KartPad's game part. The game's builder: BlueWake (untested past the disc check) | — | BlueWake Linux x86-64 AppImage; PadMint does not build desktop copies |
| **Android phone** (Termux) | — | — | PadMint: KartPad's game data (emulator only so far) | — | — |

The 8 authorized ready-made apps (Caesar III, Daggerfall, Diablo,
Fallout 2, Kid Pix, Pharaoh, Red Alert, Warcraft II) install on an iPhone or iPad
from any computer that runs Sideloadly (Windows or Mac).

**Installing what PadMint made:**

| Device | From Mac | From Windows | From Linux |
|---|---|---|---|
| iPhone / iPad | Sideloadly or AltStore | Sideloadly | **Gap:** no tested tool (Sideloadly has no Linux version) |
| Android | Copy the APK or folder | Same | Same |
| Mac | Unzip to Applications | — | — |
| Windows / Linux PC (BlueWake download) | — | Unzip and run | Make the AppImage executable and run |

**Why some cells are empty.** A Mac app has to be built with Apple's SDK, which
only runs on a Mac. An iPhone app can still be made off a Mac when its release
ships an app with no game code and PadMint builds the game part on the player's
computer (D13, D14); KartPad works this way. The hosted routes above instead use
GitHub Cloud Build to make apps that take the game file after installation. Further
local iPhone builds need a portable game pipeline and matching app release.
Android, Windows and Linux copies need a port to that system: only
KartPad, BlueWake (Android, Windows, Linux) and CTRPad (Windows, Linux, from its
upstream code) have one.

## What PadMint shows players

PadMint's library tells each computer what it can make above the search box and
uses **Build here** and **GitHub Cloud Build**, plus an **Other routes** list for
games that need an Apple Silicon Mac, use a project-owned workflow, have a
separate Windows download, or are paused. Each card states which applies.
HaloPad's project-owned workflow is explained on its game page.
Every unavailable game explains which route applies. When a recipe or release
changes, the catalog, those labels, [WINDOWS.md](WINDOWS.md) and this roadmap
change in the same pull request.

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

The **First** section is an older distribution proposal, not the active queue
or permission to replace authorized ready-made downloads. Current implementation
work starts at [Resume work](#resume-work); the route wording is recorded in
[Build-route wording](BUILD_ROUTE_COPY.md).

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
  BlueWake's existing builders. Its 0.10.0 Linux AppImage is already published;
  a PadMint-managed Linux build remains separate work.
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
- [x] PadMint 0.5.16 labels the three routes in the app and publishes the
  focused [Windows roster and active queue](WINDOWS.md).
- [ ] BlueWake's original-disc Windows backend (PadMint #135, #136;
  bluewake#100); Windows desktop is already published separately.
- [ ] Publish SnapPad's managed tools, matching shell and Windows recipe.
- [x] MeleePad's host key is corrected and its Windows route shipped in 0.3.0;
  native Windows x64 and physical-device acceptance remain.
- [ ] Merge SunPad #57 and #78, then publish its Windows recipe and run the
  physical-device check.
- [x] Publish SquirrelPad, GoldenPad, BearBirdPad, BananaPad and DinoPad
  Windows shells/recipes; PadMint 0.5.28 exposes them.
- [ ] Install and play all six new Windows-built apps on physical devices, and
  validate on native Windows x64.
- [ ] Finish AnnePad; resolve AgePad's Steam pins and installed inputs; finish
  Ottsel's signed game execution and portable packaging.
- [ ] A tested way to install on an iPhone from Linux, then its steps.
- [ ] Engine ports through spaghettipad#29: SpaghettiPad, then HarkinianPad,
  MaskPad, StarshipPad, PaperPad, BrawlerPad.
- [x] Keep the GitHub build check off changes it cannot affect. Pull requests
  that change only the browser window (`padmint/ui.py`) no longer rebuild every
  listed game on hosted Macs; documentation was already outside the filter.

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
