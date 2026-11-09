# What PadMint still needs

This page answers **"what do we still need to do for PadMint?"** Start here when
continuing work. It was updated on **9 November 2026** for PadMint **0.6.1**,
using the live catalog audit (41 entries, 0 problems) and the open pull requests
in PadMint and each game's repository. Any PR that finishes an item below
updates this page too.

Evidence and history live in other files:

- [WINDOWS.md](WINDOWS.md): the Windows evidence for each game
- [COMPATIBILITY.md](COMPATIBILITY.md): the recipe matrix
- [BUILD_ROUTE_COPY.md](BUILD_ROUTE_COPY.md): wording decisions
- [ROADMAP.md](https://github.com/chrissotraidis/padmint/blob/main/docs/ROADMAP.md): longer-term ideas and earlier handoffs

## The goal

Every game in the catalog builds on the player's own Mac and on the player's own
Windows PC. A copy built on each has been installed and played on a device.
Linux and Chromebook players get a tested answer about what they can do. Every
PadMint page uses the same name for the same thing, in English, Spanish and
Portuguese.

## Where it stands

These counts cover the 39 entries players can use: 31 games PadMint builds and 8
ready-made apps. EctoPad is paused and not counted.

| Measure | Mac (Apple Silicon) | Mac (Intel) | Windows PC | Linux |
|---|---|---|---|---|
| The player can end up with an iPhone/iPad app by any route, including GitHub's Mac | 38/39 (97%) | 26/39 (67%) | 32/39 (82%) | 26/39 (67%), but installing needs a Windows PC or Mac |
| The player's own computer builds it (ready-made apps count) | 38/39 (97%) | 9/39 (23%) | 15/39 (38%) | 9/39 (23%) |
| Built games only, on the player's own computer | 30/31 (97%) | 1/31 (3%) | 7/31 (23%) | 1/31 (3%) |
| A copy built there has been installed and opened or played on a device | Every game's latest build as of 18–21 October opened on an iPad with iPadOS 27; NightPad, added in 0.5.30, has been installed on an iPad, with broad gameplay checks still open | 0 of 1 | 0 of 7 | 0 of 1 |

An Intel Mac builds only KartPad itself (its recipe is the only one declaring
`macos-x86_64`); everything else comes from GitHub's Mac or the ready-made apps,
which Sideloadly installs from an Intel Mac too. Earlier versions of this page
counted only Apple Silicon Macs under "Mac".

The Mac's one miss is **AgePad**: 6 of its 8 pinned Steam files no longer match
an installed Steam, so v0.1.0 stops after Steam updates (reproduced on 8
November). [agepad#15](https://github.com/chrissotraidis/agepad/pull/15) fixes it
for 0.1.1: the build downloads the pinned Steam for Mac libraries from Valve
instead of reading the installed Steam, and the player check passed with it in
21 s. Its release waits for an iPad run of a 0.1.1 build. HaloPad's `actool`
failure ([#220](https://github.com/chrissotraidis/padmint/issues/220)) is fixed
in [HaloPad 0.3.14](https://github.com/chrissotraidis/projectreach/releases/tag/v0.3.14)
(5 November).

The Windows counts break down as follows:

- 8 games build locally, all experimental and all built by a maintainer only on
  Windows 11 ARM64. Their recipes also declare Windows x64, but no maintainer's
  build has run on a native x64 PC (SunPad's still-draft route had one emulated
  x64 run; a BlueWake contributor built and played an x64 copy).
- 17 build on GitHub's Mac.
- All 8 ready-made apps install with Sideloadly.
- 6 games still need an Apple Silicon Mac: SunPad, SnapPad, AnnePad, Ottsel,
  AgePad and NightPad. HaloPad's Custom Edition also needs a Mac.

Linux builds KartPad locally (x64 and ARM64 in its recipe) and can start the
same 17 cloud builds.

**Linux test builds, 8 November.** The six N64 and GameCube Windows routes also
build on Linux with a two-line recipe change: the Windows module steps run on
Linux too. In clean Debian 12 containers on a Mac (ARM64, and x86-64 under
Rosetta), PadMint 0.5.34 built each one from its latest release, the owner's
game file and the published base app. Each IPA was the published app plus the
game module, with only `Info.plist` changed (the launch link). Linux players
need a C++ compiler (`build-essential`), because the route builds small
generator tools natively, the same reason Windows asks for Visual Studio.

| Game | Linux ARM64 | Linux x86-64 | Recipe PR |
|---|---|---|---|
| BearBirdPad | 34 s | 841 s | [bearbirdpad#29](https://github.com/chrissotraidis/bearbirdpad/pull/29) |
| GoldenPad | 24 s | 56 s | [goldenpad#54](https://github.com/chrissotraidis/goldenpad/pull/54) |
| BananaPad | 282 s | 95 s | [bananapad#24](https://github.com/chrissotraidis/bananapad/pull/24) |
| SquirrelPad | 316 s | 89 s | [squirrelpad#11](https://github.com/chrissotraidis/squirrelpad/pull/11) |
| DinoPad | 317 s | 117 s | [dinopad#22](https://github.com/chrissotraidis/dinopad/pull/22) |
| MeleePad | 885 s | 1,116 s | [meleepad#60](https://github.com/chrissotraidis/meleepad/pull/60) |

Times include fresh tool downloads on ARM64 but not on x86-64, so they don't
compare. Players get Linux for each game with its next release, whose recipe
PadMint reads; until then the counts above stay at KartPad only. No Linux-built
copy has been played on a device, and no run used a native Linux PC.

## Chromebooks

No Chromebook has been tested, and the README says so. The answer below follows
from the routes that exist.

- **Browser only** (Linux not turned on, or a school or work Chromebook that
  blocks it): the player can start GitHub Cloud Build for the 17 cloud games
  with a free GitHub account. Installing the resulting `.ipa` needs a Windows PC
  or Mac, because Sideloadly has no ChromeOS or Linux version.
  [KartPad's Android download](https://github.com/chrissotraidis/kartpad/releases/latest)
  should install on a Chromebook that runs Android apps.
- **With ChromeOS's Linux turned on:** PadMint for Linux should run (it needs
  Python 3.9+ and Git). The player then gets the Linux routes: KartPad locally,
  plus the 17 cloud builds. KartPad's first build needs about 12 GB free on a
  Mac, and Linux probably needs about as much, which is a lot for a cheap
  Chromebook. Many cheap Chromebooks have ARM chips. Full game builds have now
  passed on Linux ARM64 in containers (see the table above), but not on a
  Chromebook.
- **To do:** one KartPad build and one cloud build on an Intel/AMD Chromebook
  and on an ARM Chromebook. Then update the README row from "untested".

## The queue, in order

### 1. Prove the routes already published

Nothing new needs building for this step. It turns "experimental" into "works".

- Install and play a Windows-built copy of **KartPad, GoldenPad, BearBirdPad,
  BananaPad, SquirrelPad, DinoPad and MeleePad** on an iPhone or iPad. For each
  game that passes, remove its Windows note (`host_notes` in the catalog) and
  its experimental label. Never upgrade a label without a recorded run.
- Build at least one of them on a **native x64 Windows PC**. All Windows
  evidence so far comes from Windows 11 ARM64.
- Run **GitHub Cloud Build end to end** once: fork, run, download, sign with
  Sideloadly, play. The hosted builds pass, but nobody has installed one yet.
  Do the same for DarkPad's private route.
- **Done when** [WINDOWS.md](WINDOWS.md) records a device result for each game.

### 2. Bring the seven Mac-only games to Windows

A game counts as done when its published recipe declares Windows hosts,
`scripts/player-check.sh` passes, and a copy built on Windows plays on a device.

| Game | What blocks it | Next step |
|---|---|---|
| BlueWake | Done except the device check: 0.11.0 (8 November) publishes a recipe with Windows ARM64 and x64 for iPhone/iPad, and the catalog lists them (\`ios_hosts\`) from PadMint 0.6.2. Between the release and that change, Windows showed BlueWake dimmed | A maintainer installs and plays a Windows-built copy on an iPhone or iPad |
| SunPad | Two draft PRs | Merge [sunpad#57](https://github.com/chrissotraidis/sunpad/pull/57), then [#78](https://github.com/chrissotraidis/sunpad/pull/78), and publish |
| SnapPad | [snappad#12](https://github.com/chrissotraidis/snappad/pull/12) uses a private tool bundle | PadMint publishes its Windows IDO, binutils, Rabbitizer and asm-processor builds (**needs Chris's approval**). SnapPad's release pause still applies |
| AnnePad | [annepad#20](https://github.com/chrissotraidis/annepad/pull/20) built the ROM-to-module step on Windows in 25 min | The same tool publication, then the shell, recipe and device check |
| Ottsel | [ottsel#7](https://github.com/chrissotraidis/ottsel/pull/7): Windows output matches the Mac byte for byte | Device-check the changed Mac output, then a game-free app with a private game library |
| AgePad | Broken on Mac too (stale Steam pins) | Release [agepad#15](https://github.com/chrissotraidis/agepad/pull/15) for the Mac first, then the Mac game files via SteamCMD on Windows |
| NightPad | Added in 0.5.30; its recipe declares only Mac | Finish its iPad gameplay check first, then assess a Windows route |
| HaloPad Custom Edition | Converts the PC game with Wine and Mac tools | No Windows design yet. The Xbox edition is covered by HaloPad's own GitHub workflow |

### 3. Build the GitHub-only games on Windows itself

Sixteen games (the 15 shared cloud games plus DarkPad) build for iPhone/iPad
from Windows only on GitHub's Mac. Their engines still compile against Apple's
SDK. This is the largest piece left for "the whole catalog on Windows".

Prove the pattern on one game, then repeat it for the rest. The pattern is
started in [spaghettipad#29](https://github.com/chrissotraidis/spaghettipad/pull/29)
(cross-host module tooling, draft since 2 October) and PadMint's
[#172](https://github.com/chrissotraidis/padmint/pull/172) (iOS SDK headers,
draft). PaperPad also waits on
[paperpad#24](https://github.com/chrissotraidis/paperpad/pull/24). Until then,
GitHub's Mac keeps these games available from Windows.

### 4. Linux and Chromebooks

- Find and test one way to install an iPhone app from Linux. Until then, the
  Linux pages send the `.ipa` to a Windows PC or Mac.
- The six newer Windows routes now have Linux ARM64 and x86-64 container runs
  and recipe PRs (table above). Next: release each game with its Linux recipe
  (`scripts/player-check.sh` before and after), then one device check of a
  Linux-built copy and one run on a native Linux PC.
- Test Chromebooks as described [above](#chromebooks).

### 5. UI text that makes sense everywhere

Words players see live in [`padmint/say.py`](https://github.com/chrissotraidis/padmint/blob/main/padmint/say.py) (English,
Spanish and Portuguese). A review of the 0.5.29 English strings found these
problems:

- **One name per route.** Each route currently goes by several names. Pick one
  for each and use it in tabs, tags, buttons, cards, the README and the CLI.
  The README already leads with *Build on this computer*, *Build on GitHub's
  Mac* and *Download the app*.

  | Route | Names in the UI today |
  |---|---|
  | Local | **Build here** (tab and library button), *Built locally on this computer*, *Local build on {host}*, *Build on this Windows PC* |
  | Cloud | **GitHub Cloud Build** (tab and tag), *Build on GitHub's Mac*, *GitHub build available*, *GitHub's hosted Mac*, *a temporary macOS machine* |
  | Needs a Mac | *Apple Silicon Mac*, *Needs Apple Silicon Mac*, *Requires Apple Silicon*, *Other build computer*, *Build it on another computer*, *Other routes* |
  | Ready-made | *Ready-made apps*, *No build needed*, *Get the app*, *Download the app*, *ready-to-play app* |

- Fixed on main after 0.5.30 ([#236](https://github.com/chrissotraidis/padmint/pull/236)),
  in all three languages: the home page now says *Your game file stays on this
  computer* where it wrongly promised *Runs only on this computer* (false for the
  17 games built on GitHub's Mac). Ready-made apps are called iPad apps
  everywhere (seven of the eight run on iPad only; Emerald Tablet also runs on
  iPhone). `why_2` names KartPad's ready-to-play download as Android, and
  `update_help` tells Mac and Linux players to use the version button.
- **The GitHub steps (`github_steps`) are one paragraph of about ten actions.**
  Make them numbered steps.
- **"Copy", "app", "build" and ".ipa" are used interchangeably** for what the
  player gets. Decide when each word is used and apply that everywhere.

**Done when** [BUILD_ROUTE_COPY.md](BUILD_ROUTE_COPY.md) holds a short glossary,
and the pages served for Apple Silicon Mac, Intel Mac, Windows and Linux are
checked in all three languages.

### 6. Game updates and previews

A minor game update usually needs **no PadMint release**. On every build,
PadMint reads the recipe (`*-padmint.json`) attached to the game's latest
GitHub release, skipping releases without one. For a game release:

1. Attach its recipe. Windows routes also need the Windows recipe and the
   game-free app.
2. Run `scripts/player-check.sh` before tagging and after publishing.

Players get the update the next time they build. Cloud players press **Sync
fork** and run the workflow again. PadMint itself changes only when something
the catalog describes changes: the computers a game builds on, the programs it
needs, the game file it asks for, its install steps or its card art.

Still open:

- **Previews are invisible.** Seven download-only apps publish prereleases,
  which `/releases/latest` skips, so players never see those updates. Decide a
  release channel for each game, then test preview-only, stable plus preview,
  missing-asset and offline cases.
- **A game update can silently break a Windows route.** The player check runs
  on a Mac, and the daily catalog check reads recipes without building. Add a
  Windows build to the release checklist (or CI) of each game with a Windows
  route.

### 7. Ownership check for `build --repo`

Normal library, `make`, `get` and cached-source routes reject removed games.
`build --repo` still accepts any local `padmint.json`. Enforce the only-Chris's-ports
rule there while keeping development of a new own-port recipe possible (see the
[roadmap](https://github.com/chrissotraidis/padmint/blob/main/docs/ROADMAP.md#next-implementation-pass)). Test with synthetic fixtures
only.

### 8. Small items and drafts to reconcile

- **Launch links and the PadMint library app.** Since 0.5.34 ([#242](https://github.com/chrissotraidis/padmint/pull/242)),
  every iPhone/iPad app PadMint builds answers to `padmint-<game>://`. On 7 November a
  SunPad 0.2.3 build with the link was re-signed and installed on an iPad Pro; iOS opened
  SunPad from the link. PadMint 0.6.0 ships the library app that uses it, built from
  [ios/](../ios/README.md), as `PadMint-ios-unsigned.ipa` in each release (experimental;
  the player sideloads it, using one of a free Apple ID's three slots).
  The 0.6.0 app was installed on an iPad Pro and opened; launching a game from it on a
  device is still unchecked.
  Still open: the eight ready-made apps need the link in their own repositories, games
  installed earlier show up only after a rebuild, and iOS 27 lets an app check at most
  25 links, so six games say *Tap Play to check*.
- **A SunPad 0.2.3 player's rebuild stopped with "Backend has local changes"**
  (7 November) without saying what changed. PadMint 0.5.31 did not reproduce it
  on an M3 Max: a first build (35 min), an interrupted dependency download and a
  rebuild all passed, with Homebrew Git and with Apple's `/usr/bin/git`.
  Since 0.5.33 ([#239](https://github.com/chrissotraidis/padmint/pull/239)),
  `make` and the app's Build button keep a changed download aside and download
  a fresh copy, naming the changed files, instead of refusing every build.
  `build --repo` still refuses, now with the changed files listed. If the same
  files reappear after a fresh copy, the game's build writes them and needs its
  own fix.
- Replace HarkinianPad's card art (`art/harkinianpad.png`, still the old
  ship's wheel) with the blue ocarina from
  [harkinianpad#41](https://github.com/chrissotraidis/harkinianpad/pull/41):
  a 144×144 PNG made from HarkinianPad's `assets/AppIcon.appiconset/AppIcon.png`,
  shipped in the first PadMint release after HarkinianPad v0.2.3 publishes the
  new icon. The latest release is still v0.2.2.
- [#232](https://github.com/chrissotraidis/padmint/pull/232): TribesPad's
  Vengeance in the default build (draft). Its game-side change,
  [tribespad#36](https://github.com/chrissotraidis/tribespad/pull/36), merged on
  2 November, but TribesPad's latest release is still v0.2.0, and the iPad
  performance follow-up [tribespad#37](https://github.com/chrissotraidis/tribespad/pull/37)
  still needs its manual iPad checks. Merge #232 after a TribesPad release with
  Vengeance passes `scripts/player-check.sh`.
- [#172](https://github.com/chrissotraidis/padmint/pull/172): iPhone SDK headers
  for game modules (draft). It belongs to step 3 and waits for the first game
  that needs it.
- [#168](https://github.com/chrissotraidis/padmint/pull/168): plan for KartPad
  Android and BlueWake Windows built locally. Reconcile it with item 9.

### 9. Later: games for desktops and Android

PadMint makes iPhone/iPad apps, Mac apps and KartPad's Android game data. It
doesn't make Windows or Linux desktop games. BlueWake publishes its own desktop
downloads, and CTRPad for PC is only an idea. Building BlueWake for Windows,
Linux and Android, or KartPad's Android app, through PadMint needs Chris's
decision on distribution first.

## Decisions only Chris can make

1. **Cloud output visibility.** DarkPad requires a private copy of PadMint,
   while the other personal builds use public forks. Nothing technical forces
   the difference; it's one catalog setting (`github_build_private`). Choose one
   rule for every personal build
   ([comparison](BUILD_ROUTE_COPY.md#darkpad-is-not-technically-a-different-kind-of-personal-build)).
2. **Publishing PadMint's Windows builds of IDO, binutils, Rabbitizer and
   asm-processor.** This unblocks SnapPad and AnnePad.
3. **A release channel for preview-only apps.**
4. **Whether PadMint should build desktop games or Android apps** in addition to
   iPhone/iPad.
5. **Any new game in the catalog.**

## Keeping this page true

Before editing this page, run
`PADMINT_HOME=$(mktemp -d) python3 scripts/audit-catalog.py` and recheck the
linked PRs and releases. Update the date, the counts and the item that changed.
Raise a platform from experimental only with a recorded run on that platform.
