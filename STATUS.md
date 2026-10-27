# PadMint status

**v0.5.21:** MeleePad’s detail page now points directly to the separate Melee PC save-fix test and its private GitHub build guide. The test build is labeled in the library, and its GitHub option is visible on Mac as well as Windows/Linux. The app/save acceptance status is unchanged.

**v0.5.20:** Melee PC can build on GitHub’s hosted Mac without a local Mac. Its downloadable personal IPA requires a private repository. [Hosted compilation and package check passed](https://github.com/chrissotraidis/padmint/actions/runs/40473291597/job/122085358107) on 27 October; CI uploaded no IPA. LiveContainer saving still needs reporter confirmation.

Updated **27 October 2026**. The [compatibility page](docs/COMPATIBILITY.md) has
the per-game detail, including **Status by game**, which is where the
compatibility work resumes.

**Scope today:** Windows build hardening resumed on 26 October at the owner's
request ([D17](docs/DECISIONS.md#d17-windows-build-hardening-resumes-26-oct-2026)).
The work covers reliable recipes, managed tools, safe retries, and private game
modules built on the player's computer. Current published routes remain the
source of truth: draft build evidence does not enable a catalog button or
establish device launch, audio or save compatibility. Game releases and device
deployment keep their separate approval and validation gates.

**Building on Windows today:** the only game PadMint compiles locally on a
Windows PC through a published recipe is **KartPad**, for Android or iPhone/iPad
(experimental). Fifteen iPhone/iPad games can be compiled by **GitHub's free
Mac** after Windows starts the workflow. The other games currently need an Apple
Silicon Mac or their project's own route. None of these options is a Windows
desktop build. The dated roster, seven private Windows proofs, and active queue
are in [Building games on Windows](docs/WINDOWS.md).

## Which games use PadMint

- **KartPad for Android is a ready-to-play download** (the APK has the game code
  built in) on [KartPad's releases](https://github.com/chrissotraidis/kartpad/releases/latest).
  On Android, PadMint makes the `KartPad game data` folder. KartPad for iPhone, iPad
  and Mac is built with PadMint; the release's `ios-for-padmint.ipa` has no game in it
  and is only for PadMint. The 0.7.9–0.7.13 ready-to-play iPhone/iPad and Mac
  downloads won't get updates.
- **HaloPad's Xbox edition** can also be built without a Mac, using GitHub Cloud Build
  Build ([steps](https://github.com/chrissotraidis/projectreach#on-windows-linux-or-any-computer)).
  On Windows and Linux PadMint points there instead of saying it needs a Mac.
- **BlueWake on Windows** downloads its ready-to-play build from
  [BlueWake's releases](https://github.com/chrissotraidis/bluewake/releases/latest).
  The iPhone module route from Windows remains
  [draft #100](https://github.com/chrissotraidis/bluewake/pull/100), refreshed on
  current main. A native Windows backend build from preserved extracted inputs
  and its warm repeat passed; a complete current original-disc build is pending.
- **Every other Pad game** builds through PadMint, or is a no-build download
  listed in PadMint.

## PadMint itself

- **v0.5.19**: adds **Melee PC** as a separate Apple Silicon Mac personal-build route for iPhone/iPad. Its source-only recipe patches melee-pc 0.4.2 save creation; the existing MeleePad entry is unchanged. The player imports their own disc after installation. LiveContainer confirmation remains open.

- **v0.5.18**: polish for the update flow. The sidebar pill now fits its column,
  the PadMint update dialog hides its action while downloading, and game
  updates with a missing file or device offer a direct button that returns to
  that step. Disabled build actions no longer look green, and requirement text
  no longer refers to misleading step numbers.

- **v0.5.17**: completes the route labels from 0.5.16. A tab called **Other
  routes** now holds games that need an Apple Silicon Mac, have a separate
  Windows download, use their project's own workflow, or are paused; each card
  still names its specific state. The README and roadmap use **GitHub Cloud
  Build** consistently.

- **v0.5.16**: build locations are named plainly. **Build here** means PadMint
  compiles on that computer; **GitHub Cloud Build** means GitHub runs a temporary macOS
  build machine for the player's PadMint fork; **Apple Silicon Mac** means the
  game needs the player's own Mac. The page says that all three routes produce
  iPhone/iPad or Android results, never Windows desktop games, and each card
  shows its exact route. [Building games on Windows](docs/WINDOWS.md) is the
  dated support roster and active release queue. The compatibility table now
  matches the current public recipes. Fixed an explicit CLI checkout check that
  misread non-English Git roots on Windows.

- **v0.5.15**: the shared foundation for private iPhone modules built on
  Windows. Managed Windows tool builds, source and release selection, cache
  reuse, non-English paths, Unicode compiler dependencies and cancellation now
  share one tested path. Cancelling a build also stops its backend and child
  processes while preserving earlier output. The strict iPhone module check
  accepts Apple's verified thread-local runtime entry and its public probe
  covers a real TLS descriptor. Local Windows game buttons remain off in this
  release; each proven game needs its own merged recipe, matching app release
  and device check before PadMint enables it.

- **v0.5.14**: no Mac? Fifteen games (BallPad, BarrelPad, BellPad, BrawlerPad,
  CTRPad, F0X, GalaxyPad, HarkinianPad, MaskPad, OpenRCT2 Touch, PaperPad,
  SpaghettiPad, StarshipPad, TribesPad, UTP) can be built for iPhone and iPad on
  GitHub Cloud Build from Windows, Linux or any browser (\`build-for-iphone.yml\`;
  README "GitHub Cloud Build"). Off a Mac they get their own **GitHub Cloud Build**
  tab, and each game page gives numbered steps with Fork PadMint,
  Step-by-step guide and Get Sideloadly buttons. Game pages on a Mac say how the
  copy gets onto the device (an .ipa installed with Sideloadly), fold the game-file
  note into one line, and label setup as **Setup: Xcode + Homebrew**. EctoPad is
  paused while Metaforce is private. SquirrelPad asks for 6 GB free instead of 30.
  EctoPad's and MeleePad's Rust setup lines work on a fresh Mac again.

- **v0.5.13**: a clearer library. The filters say what they hold (**Build your
  copy**, **Ready-made apps**, **Not on your devices**, **All systems**); a game
  that is already installed and current shows **Details** instead of a build or
  download button; ready-made apps with a newer release show **Update**; and My
  games groups everything without an update as **Installed, nothing to update**,
  with a note on apps PadMint can't check for updates. Tribes 2 (TribesPad) joins
  the catalog with its own icon.

- **v0.5.12**: the iOS 27 heads-up says what players actually see: a copy built
  with Xcode 27 that has no UIKit scene startup will probably close as soon as it
  opens on iOS or iPadOS 27, before it can write a log. PaperPad 0.2.2 did exactly
  that on an iPhone 18 Pro and an iPad ([paperpad#21](https://github.com/chrissotraidis/paperpad/issues/21));
  PaperPad 0.2.3, F0X 0.1.1 and SnapPad 0.2.1 fix it
  ([details](docs/COMPATIBILITY.md#ios-27-on-a-physical-ipad-18-to-21-october)).

- **v0.5.5**: a launcher. A sidebar lists **My games**, **Updates** and each
  iPhone, iPad and Mac PadMint can see; every game shows which version is on
  which device (read with Xcode's devicectl and from the Applications folders),
  and updates are compared with each game's latest release. Storage shows and
  frees PadMint's folder; PadMint can update itself on Mac and Linux.
  New builds: F0X, EctoPad, SnapPad, OpenRCT2 Touch and UTP. New Mac targets:
  F0X, EctoPad, SnapPad, BellPad, AnnePad, SunPad, MeleePad and BrawlerPad. RAtouch is listed as a download.
- **v0.5.5** also: after a newer version of a game builds, PadMint empties the
  `build/` folders that older versions left in `.padmint/games` and says how
  much space it freed. Source and `private/` folders stay, because KartPad's Mac
  guide points players at game files there; a folder another PadMint is using is
  skipped. The README now says KartPad for iPhone and iPad also builds on Windows
  and Linux (experimental, no Xcode).

- **v0.5.4**: KartPad's Mac build asks for about 12 GB free instead of 60 GB
  ([KartPad #489](https://github.com/chrissotraidis/kartpad/issues/489)). A clean
  KartPad 0.8.3 Mac build from an empty PadMint folder peaked at 9.3 GB; the 60 GB
  figure was never measured. Mobile copies keep their 16 GB budget.

- **v0.5.3**: clearer KartPad setup on Mac. PadMint restarts natively when opened
  through Rosetta on Apple Silicon, restoring **This Mac**. Intel Macs show why
  that copy is unavailable while retaining supported choices. KartPad's Mac plan
  showed a 60 GB disk budget (corrected in 0.5.4), and completion
  links directly to the Mac installation guide. Update guidance explains how to
  open the new ZIP without deleting existing builds, caches or saves.

- **v0.5.2**: GalaxyPad. PadMint builds GalaxyPad 0.2.0 for iPhone and iPad on an
  Apple Silicon Mac with Xcode, with no game file during the build: players import
  their own Super Mario Galaxy WBFS image in the app. `scripts/player-check.sh` takes
  `-` as the game file for games like this, whose game is chosen in the app.

- **v0.5.1**: KartPad on a Mac. With KartPad 0.8.0, PadMint offers KartPad's Mac copy
  again on Apple Silicon Macs (**This Mac**), using PadMint's own build tools (no
  Homebrew), and builds KartPad for iPhone and iPad on Intel Macs (with Xcode and its
  iOS platform). A recipe can say a program is needed only for some targets, so
  building KartPad for Android on a Mac doesn't ask for Xcode. When PadMint holds back
  a game's device on purpose, step 3 shows it dimmed and marked **Not yet**, with the
  devices to choose instead.

- **v0.5.0**: easier for someone new. The README starts with direct Mac, Windows and
  Linux download links (the ZIPs are now named `PadMint-macos.zip` and so on), and the
  Mac no longer needs a Terminal step first. On a Mac, each card says how much setup
  the game needs (**Easiest**, **Needs Xcode**, **Needs Xcode + Homebrew**). The file
  step says which version works ("Only the US (North American) version works"). The
  setup list says how to get Xcode when it's missing or not in use, gives one Homebrew
  line for everything missing, marks programs needed only for some files, finds
  Homebrew programs installed after PadMint started, and has **Check again**. A gray
  **Make my copy** says why. The file window opens in front. iPhone and iPad copies
  come with step-by-step Sideloadly instructions, also shown before the build.

- **v0.4.13**: clearer downloads. KartPad's card says its ready-to-play download is
  for Android ("Android: ready-to-play app"), and the download note appears only when
  you choose Android, with a **Download the Android app** button. It no longer
  suggests ready-to-play iPhone, iPad or Mac downloads. The Android plan says you get
  a game data folder. On Windows and Linux, HaloPad points to its Xbox edition's
  GitHub build instead of "Needs an M1+ Mac". README FAQs answer "Can I play KartPad
  on my Mac?" and building iPhone apps without a Mac.

- **v0.4.12**: PadMint checks the file you choose against the game's recipe before it
  builds: HaloPad says when you picked Bungie's 1.10 patch instead of the original
  installer, and choosing an Xbox ISO/XISO asks only for the Xbox tools (no Wine or
  PC tools). HaloPad 0.3.8's install line adds `llvm` and `sdl3`. Answers that arrive
  late from an older file choice no longer overwrite a newer one.

- **v0.4.11**: SquirrelPad joins the catalog for experimental iPhone/iPad personal
  builds on Apple Silicon Macs. Supply your own supported US Conker ROM; full
  Xcode and Metal Toolchain are required. Source and recipe only, no public IPA.
  BlueWake’s setup link now follows its current Install section.

- **v0.3.6**: one directory of every game (tabs for Build with PadMint, Download
  and Not available yet, console badges, search, back buttons). Games this
  computer can't build stay listed with the reason (**Needs an M1+ Mac**) instead
  of disappearing ([bellpad#20](https://github.com/chrissotraidis/bellpad/issues/20)).
  On a Mac the plan shows each game's install-once Homebrew line with a Copy
  button. README rewritten for every game.
- **v0.4.10**: KartPad's iPhone build on Windows and Linux works again. Since v0.4.7
  PadMint asked those computers for Xcode's iOS platform, which only exists on a Mac,
  and stopped before building. The check now runs on Macs only, and
  `scripts/audit-catalog.py` reports any Windows or Linux route that asks for Xcode.
- **v0.4.9**: HaloPad's setup opens its Wine installation guide instead of asking
  Homebrew to install the disabled `wine-stable` cask. Existing working Wine installs
  can still be used. HaloPad 0.3.6 supplies the matching recipe guidance.
- **v0.4.8**: HaloPad builds both editions: Custom Edition and the Xbox edition
  (its engine fetched from upstream and built on your Mac), for iPhone, iPad and Mac.
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
startup, which Apple requires. On a physical iPad with iPadOS 27 (18 October), every
game's latest PadMint build opened except PaperPad 0.2.2, whose 4 October fix had
reached only PaperPad Original; F0X 0.1.0 and SnapPad 0.2.0, released later, also
lacked it. PaperPad 0.2.3, F0X 0.1.1 and SnapPad 0.2.1 (21 October) fix them
([details](docs/COMPATIBILITY.md#ios-27-on-a-physical-ipad-18-to-21-october)).

Current Windows work, with [per-game evidence and remaining gates](docs/COMPATIBILITY.md#status-by-game):

- All 15 games offered through the hosted Mac route passed the earlier matrix at
  `4a78bb0` ([run](https://github.com/chrissotraidis/padmint/actions/runs/40209016384)).
  A later matrix passed 14 and exposed PaperPad 0.2.3's stale dependency URL;
  [PaperPad draft #24](https://github.com/chrissotraidis/paperpad/pull/24) fixes it
  with immutable, checksummed downloads and passed its Mac build. The published
  recipe still needs that release. A fresh matrix at `2c2079a` is in progress.
  This route is available from Windows; its app builds execute on Macs.
- Shared drafts [#177](https://github.com/chrissotraidis/padmint/pull/177),
  [#178](https://github.com/chrissotraidis/padmint/pull/178),
  [#179](https://github.com/chrissotraidis/padmint/pull/179),
  [#180](https://github.com/chrissotraidis/padmint/pull/180) and
  [#182](https://github.com/chrissotraidis/padmint/pull/182) preserve failed source
  attempts, validate released recipes, distinguish installed build inputs, package
  revision-specific modules with identity files, and provide Windows MIPS patch
  compilation. Host selection keeps existing Mac packagers and options intact.
  Later drafts, through [#192](https://github.com/chrissotraidis/padmint/pull/192),
  add source/tool provenance, safe cache reuse, native host-tool producers and
  Unicode-path fixes. At `cb43178`, 487 Apple Python 3.9 tests passed, alongside
  native Windows x64/ARM64 packaged runner and public module checks. The IDO
  compiler producer also passed a fresh offline Windows build: only its corrected
  IDO 5.3 diagnostic catalog and provenance changed, with every compiler executable
  and reference object preserved. These changes and tool artifacts are unreleased.
- SquirrelPad and GoldenPad have complete private Windows ARM64 module builds
  through packaged PadMint. Their private x64-toolchain backends also passed
  under ARM emulation, with native x64 generator CI as separate evidence.
  Matching empty shells exist locally; recipes and shells still need review,
  device testing and authorized releases.
- MeleePad's offline route builds both supported revisions on Mac without
  rebuilding Slippi. Packaged Windows ARM64 and an emulated x64-toolchain backend
  passed with maintained compiler defaults. SunPad also completed both private
  Windows ARM64 and emulated x64-toolchain builds. Native generator CI is separate
  from private hardware acceptance; Unicode-path follow-ups are in progress.
  Native Slippi online builds remain a separate developer route.
- BearBirdPad's matching shell/module and static Mac builds passed. Private
  Windows ARM64 and emulated x64 backends passed with identical output. The
  normal packaged Windows ARM64 recipe also passed with fresh source preparation
  and cached tools. GoldenPad, BearBirdPad, BananaPad and SnapPad subsequently
  passed complete Windows backends in non-English work/TEMP folders with
  independent IPA readback. SnapPad's fresh ROM-to-IPA pipeline and no-build warm
  repeat also passed. Matching shells and private outputs remain local.
- AnnePad reproduces the original ROM on Mac and Windows, with semantic CPU-source
  parity; its full module route is still being built. DinoPad's public checks and
  empty shell pass, but its supported ROM is missing. AgePad's real-input Windows
  run correctly rejects incompatible installed Steam files; successful injection
  still needs matching files. Ottsel's Windows route remains unimplemented.
- BlueWake completed a native Windows backend from preserved extracted inputs,
  independent module/IPA checks and a no-build warm repeat. Current original-disc
  extraction and preparation passed; the full original-disc build remains pending.

No published catalog host flags or releases are changed by this evidence.
The generic pipeline must ship before recipes that require it, followed by each matching game release
and its catalog change. [Issue #75](https://github.com/chrissotraidis/padmint/issues/75)
tracks the broader work.

Personal game outputs stay private. Content scans are technical checks;
publication and rights decisions are reviewed separately.

## Earlier evidence

The [historical status record](STATUS-HISTORY.md) keeps earlier versions of this
page verbatim.
