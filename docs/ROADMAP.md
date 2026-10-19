# PadMint roadmap: every game, on every computer

Updated 19 October 2026, PadMint 0.5.11. This is the working checklist for what
PadMint builds where, and what to do next. Update it in the same pull request as
the work: tick the box, move the game in the table, and refresh the numbers with
`scripts/demand-report.py` and `scripts/audit-catalog.py`. Background and
earlier decisions are in [DECISIONS.md](DECISIONS.md) (D5, D13–D15) and
per-game details in [COMPATIBILITY.md](COMPATIBILITY.md). Tracking issue: #75.

## Where things stand

The catalog has 37 games: 29 that PadMint builds and 8 ready-made apps.

| Computer | What PadMint does there today |
|---|---|
| Mac with Apple Silicon | Builds all 29 for iPhone and iPad, and 12 of them for the Mac too. Shows what's on the player's iPhones and iPads. |
| Windows, Linux, Intel Mac | Builds Mario Kart Wii (KartPad): Android game data, and iPhone/iPad (experimental). The other 28 are listed under **Needs a Mac**. |
| Any computer | The 8 ready-made apps (Caesar III, Daggerfall, Diablo, Fallout 2, Kid Pix, Pharaoh, Red Alert, Warcraft II) install with Sideloadly on Windows or a Mac. |

PadMint says this plainly: the library's top line names what the computer can do,
Windows and Linux get a **Needs a Mac** group, and each game's page says why.

**Mac copies stay Mac-only.** A Mac app has to be built and signed with Apple's
SDK, which only runs on a Mac, and anyone who wants a Mac copy has a Mac. The
off-Mac goal is iPhone/iPad (and Android, where a game has an Android port: only
KartPad today).

## Demand

PadMint itself, all releases: **Windows 1,299, Mac 1,270, Linux 434** downloads.
Windows players download PadMint as often as Mac players, while only one game
builds for them.

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

Stars and 14-day unique visitors are from GitHub on 19 Oct 2026. Downloads are
player installs over all releases; IPA counts also include the code-free apps
PadMint fetches while building, and older releases that shipped full apps.
OpenRCT2Touch is a GitHub fork, so its stars may include the fork's parent.
Earlier requests: BlueWake's issues mention Windows 64 times and Linux 101
times; KartPad's mention Android 213 times.

## Three ways a game reaches Windows and Linux

Apple's iPhone SDK only runs on a Mac, so an iPhone app can't be built from
scratch on Windows or Linux (D15). There are three routes around that.

**A. A ready-made app, built once on a Mac.** For games where the player adds their
game file **inside the app**, the app holds nothing made from the player's file,
so it can be built once at release and installed from any computer with
Sideloadly. 16 of the 29 work this way. No PadMint engineering, only release work
per game. D5 already allows this for clean engines (no game code). For
decompilation ports it needs an owner decision: D5 currently publishes those as
recipes only. Their upstreams publish ready-made Windows, Mac and Linux builds:
Ship of Harkinian, 2Ship2Harkinian, Starship and SpaghettiKart (checked 19 Oct
2026).

**B. Build the game part off a Mac.** For games that read the player's disc or ROM
**while building** (13 of 29), the game's release ships an app with no game code,
and PadMint compiles the game part on the player's computer and adds it (D13,
D14). PadMint's half exists and KartPad uses it end to end. Each game needs its
code split and Windows/Linux build steps; families share most of the work.

**C. Mac only by design (D15).** AgePad and HaloPad. HaloPad's Xbox edition has
its own route without a Mac, through GitHub's free Mac runner.

## Every game

| Game | Port | Game file | Builds today on | Route to Windows/Linux | Family / next step |
|---|---|---|---|---|---|
| Mario Kart Wii | KartPad | build | Mac, Windows, Linux | B, **done** | GameCube/Wii; Android game data too |
| The Wind Waker | BlueWake | build | Mac | B | GameCube/Wii; draft bluewake#100, about a day |
| Ocarina of Time | HarkinianPad | in the app | Mac | A (decision) or B | Harbour Masters engine |
| GoldenEye 007 | GoldenPad | build | Mac | B | N64 recompilation; translator off-Mac first |
| Super Mario Sunshine | SunPad | build | Mac | B | GameCube/Wii; draft sunpad#57, about a day |
| RollerCoaster Tycoon 2 | OpenRCT2 Touch | in the app | Mac | A, allowed now | Clean engine (GPL); publish the full app |
| Halo | HaloPad | build | Mac | C | GitHub runner route for the Xbox edition |
| Super Mario Galaxy | GalaxyPad | in the app | Mac | A (decision) or B | One-off decompilation |
| Mario Kart 64 | SpaghettiPad | in the app | Mac | A (decision) or B | Harbour Masters; draft spaghettipad#29 is B's reference |
| Majora's Mask | MaskPad | in the app | Mac | A (decision) or B | Harbour Masters engine |
| Super Smash Bros. Melee | MeleePad | build | Mac | B | GameCube/Wii; 2–3 days, needs multi-file insert |
| Metroid Prime | EctoPad | in the app | Mac | A, check | Metaforce engine; confirm it holds no game code |
| Paper Mario | PaperPad | in the app | Mac | A (decision) or B | Harbour Masters engine |
| Animal Crossing | BellPad | in the app | Mac | A (decision) or B | One-off decompilation |
| Pokémon Stadium | AnnePad | build | Mac | B | N64 recompilation |
| Super Mario Strikers | BallPad | in the app | Mac | A (decision) or B | One-off decompilation |
| Star Fox 64 | StarshipPad | in the app | Mac | A (decision) or B | Harbour Masters engine |
| Super Smash Bros. | BrawlerPad | in the app | Mac | A (decision) or B | Harbour Masters engine |
| Banjo-Kazooie | BearBirdPad | build | Mac | B | N64 recompilation |
| Donkey Kong 64 | BananaPad | build | Mac | B | N64 recompilation |
| Pokémon Snap | SnapPad | build | Mac | B | One-off; reads the ROM while building |
| Unreal Tournament | UTP | in the app | Mac | A, check | Original engine; confirm its licence allows a published app |
| Diddy Kong Racing | BarrelPad | in the app | Mac | A (decision) or B | One-off decompilation |
| Dinosaur Planet | DinoPad | build | Mac | B | N64 recompilation |
| F-Zero X | F0X | in the app | Mac | A (decision) or B | One-off decompilation |
| Jak and Daxter | Ottsel | build | Mac | B | One-off; reads the disc while building |
| Conker's Bad Fur Day | SquirrelPad | build | Mac | B | N64 recompilation |
| Crash Team Racing | CTRPad | in the app | Mac | A (decision) or B | One-off; compiles as one unit |
| Age of Empires II | AgePad | in the app | Mac | C | Mac only by design (D15) |

## Checklist

### Decisions for Chris

- [ ] **D5 for Harbour Masters ports:** publish ready-made iPhone/iPad apps for
  HarkinianPad, MaskPad, StarshipPad and SpaghettiPad, as their upstreams publish
  builds. Unlocks four games on every computer, including the third most-starred repo.
- [ ] **D5 for the other in-app decompilation ports** (GalaxyPad, PaperPad,
  BrawlerPad, BellPad, BallPad, BarrelPad, F0X, CTRPad): same question; most of
  their upstreams don't publish builds. If the answer is no, they take route B.
- [ ] **Apple Developer ID** (US$99 a year): lets PadMint for Mac ship as a .dmg
  that opens without **Open Anyway**.

### Now (no decision needed)

- [ ] OpenRCT2 Touch: publish the full iPhone/iPad app with its next release (D5
  allows clean engines). Its v0.1.0 IPA was taken off the release when it was
  published; check why first.
- [ ] EctoPad and UTP: confirm the engine holds no game code and its licence allows
  a published app. If so, publish the full app (route A).
- [ ] BlueWake off a Mac (route B): bring draft bluewake#100 up to date,
  build on Windows through PadMint, install with Sideloadly, start the game on an iPhone.
- [ ] SunPad off a Mac, the same way (draft sunpad#57).
- [ ] PadMint for route B: Sideloadly install steps on the game page for Windows,
  a release check that the code-free app and its recipe match, and an off-Mac
  column in `audit-catalog.py` (about 2–3 days, D15).
- [ ] Linux iPhone installs: Sideloadly has no Linux version. Test a Linux tool
  (for example Dadoum's Sideloader) and add its steps.
- [ ] Real hardware: one PadMint run on a real Windows PC, and the Termux route
  on a real Android phone with 8 GB of memory.

### Next

- [ ] MeleePad off a Mac (2–3 days, plus inserting several files in PadMint).
- [ ] N64 recompilations (route B): the translator on Windows and Linux plus
  GoldenPad (2–4 days), then AnnePad, BananaPad, BearBirdPad, DinoPad and
  SquirrelPad (half a day to a day each).
- [ ] If D5 stays for Harbour Masters ports: finish spaghettipad#29 (2–3 days),
  then HarkinianPad, MaskPad, StarshipPad, PaperPad, BrawlerPad (1–2 days each).

### Later

- [ ] One-offs that read the game while building: SnapPad, Ottsel.
- [ ] One-off decompilations if they take route B: GalaxyPad, BellPad, BallPad,
  BarrelPad, F0X, CTRPad (2–4 days each).

Every game that moves needs a device check before PadMint offers it: built on the
new computer, installed, and the game starts on a real device.
