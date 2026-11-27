# TV test results and open issues

The TV pass checks every port on an iPad connected to a TV (iPadOS extended
display) with an Xbox controller. This page records the latest pass, what
shipped from it, and the issues still open, in the order to fix them. Update it
in the same PR as a fix or a retest.

Latest pass: **26 November 2026**, iPad Pro 12.9-inch (6th generation),
iPadOS 27.2.1, PadMint library 0.6.10 (build 16, with
[#294](https://github.com/chrissotraidis/padmint/pull/294)). Earlier pass:
20 November 2026 on a 1280×720 TV.

## Passed and shipped

| Game | Release | Notes |
|---|---|---|
| DevilTouch | [1.5.6 Preview 3](https://github.com/chrissotraidis/deviltouch/releases/tag/v1.5.6-preview.3) | Opens from PadMint again: it now answers `padmint-deviltouch://` ([deviltouch#18](https://github.com/chrissotraidis/deviltouch/pull/18)) |
| VaultPad | [0.1.1 Preview 4](https://github.com/chrissotraidis/vaultpad/releases/tag/v0.1.1-preview.4) | Opens from PadMint again: it now answers `padmint-vaultpad://` ([vaultpad#17](https://github.com/chrissotraidis/vaultpad/pull/17)) |
| CaesarPad | [0.1.1 Preview 3](https://github.com/chrissotraidis/caesarpad/releases/tag/v0.1.1-preview.3) | |
| PeonPad | [0.1.1 Preview 4](https://github.com/chrissotraidis/peonpad/releases/tag/v0.1.1-preview.4) | |
| RAtouch | [0.1.3](https://github.com/chrissotraidis/ratouch/releases/tag/v0.1.3) | See the sidebar item below |
| SquirrelPad | [0.2.2](https://github.com/chrissotraidis/squirrelpad/releases/tag/v0.2.2) | Saves kept |
| ETPad | [0.1.1](https://github.com/chrissotraidis/etpad/releases/tag/v0.1.1) | Bot round on Fuel Dump |
| BearBirdPad | [0.3.2](https://github.com/chrissotraidis/bearbirdpad/releases/tag/v0.3.2) | |
| OpenTTDPad | [0.2.1](https://github.com/chrissotraidis/OpenTTDPad/releases/tag/v0.2.1) | |
| BananaPad | [0.3.2](https://github.com/chrissotraidis/bananapad/releases/tag/v0.3.2) | |
| DinoPad | [0.3.3](https://github.com/chrissotraidis/dinopad/releases/tag/v0.3.3) | Restored Adventure present |
| Emerald Tablet | [0.1.1 Preview 3](https://github.com/chrissotraidis/emeraldtablet/releases/tag/v0.1.1-preview.3) | The main menu now fills the TV |
| PadMint | Unreleased (#294) | Hint bar and layout look right on the TV |

The TV changes for DaggerPad, AgePad and GoldenPad passed and are merged
(daggerpad#11, agepad#19, goldenpad#62); each game keeps an open issue below and
releases after it. The 20 recipe-only releases of 21 November (AnnePad, BallPad,
BarrelPad, BellPad, BrawlerPad, DarkPad, F0X, GalaxyPad, HaloPad, HarkinianPad,
MaskPad, NightPad, Ottsel, PaperPad, RingPad, SnapPad, SpaghettiPad,
StarshipPad, UTP, OpenRCT2 Touch) passed on 20 November.

## Open issues, in order

### 1. MeleePad is unplayable (blocks its release)

Starting a match takes a long time, character select drags for many seconds per
input, and the stage stutters while loading. A player reports the same on an
iPhone 14 ([meleepad#64](https://github.com/chrissotraidis/meleepad/issues/64)),
so it isn't only the TV.

What is known: the ModernGekko pin, patches and idle-loop settings are the same
in 0.2.2 and 0.3.2, and 0.2.2 ran character select at 60 fps on this iPad's own
screen (6 November log). On the 20 November TV run, 0.3.2 (39) ran character
select at exactly a third of full speed with the CPU thread below saturation;
matches mostly held 60 fps. Audio underruns were much higher on the TV.

Next: run 0.3.2 on the iPad's own screen and on an iPhone, then 0.2.2 again, to
tell a 0.3.x regression from the external-display path. If it's 0.3.x, bisect
the app changes since 0.2.2 (input publisher on its own queue, NSO controller
bridge, home-screen play). [meleepad#63](https://github.com/chrissotraidis/meleepad/pull/63)
(TV orientations, 1.02 module) stays a draft until this is fixed.

### 2. Tribes 2 crashes on launch (blocks TribesPad's release)

Tribes 2 crashes every time Play is pressed in the launcher. Starsiege: Tribes
started but then stopped taking input until the controller was disconnected.
Tribes: Vengeance works, more slowly. Tribes 2 started and played on
20 November, so this is new. Next: collect the crash report and TribesPad's log
from the iPad, and compare with the build installed on 20 November.
[tribespad#47](https://github.com/chrissotraidis/tribespad/pull/47) stays a draft.

### 3. Screen flashing

- **KidPad:** on the TV, every tap on the canvas or a menu flashes the screen.
  It doesn't happen on the iPad's own screen. KidPad 2.0.1 (draft release) waits
  for this fix.
- **Several games** flash when they close, and some flash while running on the
  TV. This wasn't seen before the 26 November pass. Because it shows up across
  games, look for one shared cause first (scene teardown on the external
  display, or presenting at the TV's refresh rate) before fixing games one by one.

### 4. AgePad

- Closes the first time it is opened; it starts normally the second time.
- Quitting leaves a black screen, and the app has to be closed from the app
  switcher.
- Some stutter in a skirmish.
- Steam warns that a newer version exists: the game data on the iPad is Steam
  build 25464371 and Steam's public build is now 26272505. Clearing it means
  refreshing the data from Steam and requalifying the executable.

### 5. GoldenPad: right-stick turning is too slow

Looking with the right stick is slower than the player wants, and there's only a
touch-look sensitivity setting. Add a controller look-speed setting in the
menu. Some textures also look wrong.

### 6. DaggerPad: controller

The controller is barely mapped for Daggerfall, and the mouse stays active while
the controller is in use. Daggerfall needs a controller scheme designed for it
(movement, look, interact, menus, spells, map) with the mouse pointer hidden
while the controller drives play.

### 7. PadMint library

- The PadMint logo on the main screen sits lower than it should; center it
  better in the header.
- Text size on a TV taller than 720 points (#294) hasn't been checked on such a
  TV yet; choose a higher-resolution option for the TV in iPadOS Settings to
  check it.
- The UI test `testConsoleBadgeShowsConsole` fails on `main` (BlueWake's tile
  isn't found in the grid).
- Choose file opens one dialog at a time
  ([#296](https://github.com/chrissotraidis/padmint/pull/296), for
  [#295](https://github.com/chrissotraidis/padmint/issues/295)) and ships in the
  next PadMint release.

### 8. RAtouch: sidebar on the TV

Red Alert's side menu didn't appear on the TV. It may be a layout choice for a
wide screen; check whether it can be opened there.

## Parked

- **SunPad:** moving to a decompilation port; its status-bar PR was closed.
- **KartPad:** the TV change is ready on a local branch; decide whether it ships
  alone or with the next KartPad release.
- **BlueWake 0.13.0:** a draft release made on 22 November waits for review.
- **UTP:** the trackpad cursor offset is in UTP's known issues and needs a
  trackpad session.

## How to work through this list

For each issue, in order: reproduce it from the device logs, fix it on a branch,
run the game's own checks, build from a clean checkout, and install it in place
on the iPad after a verified backup of the game's data. Chris retests on the TV,
then the fix is released and this page is updated.

