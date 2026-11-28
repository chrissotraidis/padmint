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

Worked through on 28 November without the TV. Every fix below is on a draft
PR; nothing from this list is released. "On the iPad" means installed in place
after a verified backup of the game's data; each still needs the TV retest
named under it before it can ship.

### 1. MeleePad is unplayable (blocks its release)

**Cause:** on Melee v1.02 the game's DVD and sound-load wait loops call the
yield at 0x800195D0 directly, so ModernGekko's idle shortcut never fired for
them. Menus, character select and loads ran at 0.21–0.33 speed on the iPad's
own screen too, so the slowdown isn't specific to the TV
([meleepad#64](https://github.com/chrissotraidis/meleepad/issues/64)).

**Fix:** RecompCore idles at the yield's return when the saved caller is one of
those wait loops
([RecompCore#71](https://github.com/chrissotraidis/RecompCore/pull/71) →
[ModernGekko#5](https://github.com/chrissotraidis/ModernGekko/pull/5) →
[meleepad#63](https://github.com/chrissotraidis/meleepad/pull/63), 0.3.2 build 40).
Forcing the same idle on the iPad took character select and menus to 60 fps
and cut slow frames from 552 to 16.

**Status:** on the iPad (build 40). On the iPad's own screen with no overrides,
the classic-v1 route now runs menus and character select at 60 fps (speed
1.00); build 39 ran character select at 12.6 fps (speed 0.21). Matches are a
separate limit: 33–44 fps with the CPU thread at 99%, also in the 20 November
TV log.

**Retest on the TV:** start a match from the main menu. Character select, menus
and loading should run at full speed. Note the match frame rate.

### 2. Tribes 2 crashes on launch (blocks TribesPad's release)

**Cause:** build 7 made the display-mode answer read the window size
(`tb_content_window_points`), which the checked engine's host-only list
didn't allow, so it stopped the game when Play was pressed.

**Fix:** that call is approved, and the two proofs that hash the list were
rerun and recorded ([tribespad#47](https://github.com/chrissotraidis/tribespad/pull/47),
0.3.2 build 8).

**Status:** on the iPad. Started directly, Tribes 2 now reaches the original
engine and keeps running, with no crash report. Starsiege's input stopping
until the controller was disconnected hasn't been looked at.

**Retest on the TV:** press Play for Tribes 2 in the launcher and play a round;
then check Starsiege with the controller connected.

### 3. Screen flashing

- **KidPad:** KidPad plays a short sound on almost every tap, each through a
  new player, so the HDMI audio stream starts and stops constantly. Some TVs
  blank the picture for a moment whenever HDMI audio starts. While audio goes
  to HDMI or AirPlay and KidPad is in front, a silent audio engine now keeps
  the output running ([kidpad#8](https://github.com/chrissotraidis/kidpad/pull/8),
  2.0.1 build 4, on the iPad). The `v2.0.1` tag already points at the
  previous main, so releasing this needs a moved tag or 2.0.2.
- **Several games when they close:** a game closing also stops its audio, so
  the same TV behaviour explains a flash on close. **Test first:** on the TV,
  play and pause any sound from the Home Screen. If the picture blanks, it is the
  TV resyncing HDMI audio, and the TV's audio settings (passthrough, eARC,
  auto audio format) are the place to look.
- **ETPad (found in the crash logs):** ETPad crashed at 18:50 on 26 November
  when the TV scene was torn down, in SDL 2.30.9's `UIKit_DelDisplay`. It
  now carries SDL 2.30.12's one-line fix
  ([etpad#6](https://github.com/chrissotraidis/etpad/pull/6), 0.1.1 build 3).
  On the iPad. Retest: play, then unplug the TV or switch away and back.

### 4. AgePad

- **Closes the first time:** found and fixed. The app declares
  `LSSupportsOpeningDocumentsInPlace`, so UIKit requires an
  `application:openURL:options:` handler and aborted every cold start through
  PadMint's `padmint-agepad://` link without one. A Home Screen launch carries
  no link, which is why the second try worked
  ([agepad#20](https://github.com/chrissotraidis/agepad/pull/20), 1.2.1 build 6,
  on the iPad). A cold start through the link now opens the game.
- **Black screen on quit:** still open. Steam's logs show the quit session never
  ended (it stayed alive for two days); the game leaves through C `exit()`.
  AgePad now keeps the previous session's logs. **Retest:** open AgePad from
  PadMint once (it should start first time), quit from the game menu, then open
  it again so the kept log shows where the quit stops.
- Stutter in a skirmish and the Steam "newer version" warning are unchanged
  (the warning needs a data refresh from Steam).

### 5. GoldenPad: right-stick turning is too slow

Settings → Controller now has **Right-stick speed** (0.5× to 3×, default 1×),
which scales hip look only; 1× keeps today's turning and Aim keeps the game's
own sight ([goldenpad#63](https://github.com/chrissotraidis/goldenpad/pull/63),
0.3.3 build 22, on the iPad). **Retest:** try 1.5× and 2× with the controller.
The textures that looked wrong haven't been looked at.

### 6. DaggerPad: controller

Unity numbers an iPad controller differently from the Windows layout Daggerfall
Unity's defaults assume, so UI clicks sat on Menu and the right stick read the
wrong axes. DaggerPad now has an iPad controller scheme: left stick move, right
stick look, A activate/click, B jump/back, X weapon, Y cast, R2 attack, L2
recast, R1 run, L1 character sheet, d-pad automap/inventory/rest/travel map,
Menu pauses. A controller driving play keeps look mode, so the pointer goes
away ([daggerpad#12](https://github.com/chrissotraidis/daggerpad/pull/12),
build 7, on the iPad). **Retest:** every control
above, in play and in menus.

### 7. PadMint library

- The logo now sits in the bar, level with Search, Layout and Settings
  ([#294](https://github.com/chrissotraidis/padmint/pull/294), on the iPad).
- Text size on a TV taller than 720 points (#294) hasn't been checked on such a
  TV yet; choose a higher-resolution option for the TV in iPadOS Settings to
  check it.
- Choose file opens one dialog at a time
  ([#296](https://github.com/chrissotraidis/padmint/pull/296), for
  [#295](https://github.com/chrissotraidis/padmint/issues/295)) and ships in the
  next PadMint release.

**Retest on the TV:** the logo position, and text size with the TV set to a
higher resolution.

### 8. RAtouch: sidebar on the TV

No bug found in the code. Red Alert keeps its sidebar hidden until there is a
Construction Yard or the **Sidebar** tab at the top right is tapped
(`AllowSidebarToggle`, on by default), and early missions have no base. Pinch
zoom also crops the frame: at 2× the right quarter, where the sidebar sits,
is off screen. **Retest:** in a skirmish, deploy the MCV with zoom at 1×; the
sidebar should appear. Tap the Sidebar tab to toggle it.

## Parked

- **SunPad:** 0.4.0 on its new engine shipped on 28 November (PadMint 0.6.11)
  and is on the iPad; it needs its own TV pass.
- **KartPad:** 0.8.13 shipped on 28 November without the TV change, which is on
  the pushed branch `codex/tv-extended-display-rebased`; ship it with the next
  KartPad release.
- **BlueWake 0.13.0:** a draft release made on 22 November waits for review.
- **UTP:** the trackpad cursor offset is in UTP's known issues and needs a
  trackpad session.

## How to work through this list

For each issue, in order: reproduce it from the device logs, fix it on a branch,
run the game's own checks, build from a clean checkout, and install it in place
on the iPad after a verified backup of the game's data. Chris retests on the TV,
then the fix is released and this page is updated.

