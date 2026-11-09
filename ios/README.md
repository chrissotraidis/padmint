# PadMint for iPhone and iPad

One library for the games you've built with
[PadMint](https://github.com/chrissotraidis/padmint) and installed on the device.
It uses PadMint's icon and lists only games from PadMint's catalog.

- **Four layouts.** *Shelf* has a banner for the game you played last, your
  installed games and then everything. *Grid* shows every cover. *Carousel* shows
  each game as a 3D box on a reflective floor, sized to fill the screen: swipe
  through them, tap the front box to open it, double-tap to spin it. Each box's
  depth and spines follow its console (black GameCube and PS2 cases with the
  title down the spine, white Wii cases, Xbox's green band, deep printed N64 and
  PC boxes). A flat cover flow is available in Settings. *List* is compact,
  with a Play button on each row. Switch layouts from the toolbar.
- **Sorting and filters.** Sort by recently played, title or console (with a
  heading per console), search by title, PadMint name or console, and show only
  installed games.
- **Installed games** carry a green check mark. Tap a cover in *Your games* to
  play; tap a game anywhere else to open its page.
- **A page for each game,** with its cover over a blurred copy of it, its console,
  when you last played it, Play (or how to get it with PadMint) and cover options.
- **Official covers and titles, if you want them.** On first launch the app asks.
  If you agree, it downloads box art for every game and shows each game's official
  title (*The Legend of Zelda: The Wind Waker*) with the PadMint name (*BlueWake*)
  underneath, and the 3D boxes get their real backs (36 games) and spines (29).
  Until then it shows PadMint's own card art and names.
- **Your own covers.** Long-press any game, or use its page, to pick a picture from
  Photos.
- **Settings** for the layout, sort order, covers and titles, and what the app
  opens to: the library or the last game you played.

Covers keep their real shapes: wide N64 boxes, square PlayStation cases and tall
GameCube, Wii, PS2, Xbox and PC boxes all stand on one line.

## Install

1. Download `PadMint-ios-unsigned.ipa` from the
   [latest PadMint release](https://github.com/chrissotraidis/padmint/releases/latest).
2. Sign and install it with the same tool you use for your games (Sideloadly,
   AltStore or SideStore). It needs iOS or iPadOS 17 or later.
3. Rebuild your games with PadMint 0.5.34 or newer so they answer to their
   links. Games built earlier still launch from their own icons but don't show
   up as installed here.

With a free Apple ID, iOS lets you keep three sideloaded apps at a time, and
this app is one of them. With a paid developer account there's no such limit.

**Status: experimental.** The layouts, box art, game pages and launching pass
UI tests in the iOS 27 simulator on iPad and iPhone. On an iPad Pro with iPadOS
27, the app was installed and shown working through screen mirroring, and iOS
opened SunPad from its `padmint-sunpad://` link. Playing a game launched from
the app hasn't been checked on a device yet.

## How it finds your games

Each iPhone/iPad app PadMint builds answers to a link named after its game, such
as `padmint-sunpad://` (since [PadMint 0.5.34](https://github.com/chrissotraidis/padmint/releases/tag/v0.5.34)).
Games installed before that release show up after you rebuild them. The library
asks iOS which of those links it can open.

iOS answers that question only for links the app declares, and iOS 27 answers
for the first 25 only. PadMint builds 31 iPhone/iPad games, so the app checks
the first 25 in the catalog. Each of the others shows **Tap Play to check**: the
library tries its link, and if the game opens it's remembered as installed.
Opening a link needs no declaration, so every game can be launched from here.

Ready-made apps (the ones you download instead of building) don't answer to a
link yet, so the library lists them without knowing whether they're installed.

One app can hold several games. TribesPad is listed as Starsiege: Tribes, Tribes 2
and Tribes: Vengeance (the `also` entries in `covers.json`): all three share
TribesPad's link, so they show as installed together, and Play opens TribesPad's
game picker.

## Covers and titles

This repository holds no game art. `covers.json` gives each game's official
title, console and the addresses of its box art, back (`box_back`) and spine
(`box_spine`):

| Source | Games |
|---|---|
| [libretro-thumbnails](https://github.com/libretro/libretro-thumbnails) | The 27 console games, plus Warcraft II and Red Alert (DOS) |
| Steam | Age of Empires II, Daggerfall, RollerCoaster Tycoon 2, Unreal Tournament, Fallout 2 |
| GOG | Caesar III, Pharaoh + Cleopatra |
| Wikipedia | Diablo, Tribes 2, Kid Pix (its title screen: no box scan is available) |
| [LaunchBox Games Database](https://gamesdb.launchbox-app.com) | Fronts of Starsiege: Tribes and Tribes: Vengeance; every back and spine, matched by title and console in its `Metadata.zip`, North American scans first. Spines printed in another language are left out |

The app downloads them only after the player agrees and keeps them on the device.
A game's page names where its box art came from. A picture the player chooses
always comes first, and then the box keeps its plain back and drawn spine.
Games with no scan (Kid Pix, Pharaoh + Cleopatra, Dinosaur Planet's back) keep
them too. `scripts/check-covers.py` checks that every address, including backs,
spines and the GitHub copy of each libretro cover, still loads.

## Build

```sh
cd ios
python3 scripts/sync-catalog.py   # library.json and Sources/Info.plist, from ../catalog
xcodegen generate
open PadMintLibrary.xcodeproj
```

Needs Xcode 26 or newer and XcodeGen (`brew install xcodegen`). The app targets
iOS 17 and later. The icon is `Icon/AppIcon.svg`, PadMint's own icon drawn edge
to edge. `swift scripts/render-icon.swift` renders it into the asset catalog;
then flatten it with `magick Assets.xcassets/AppIcon.appiconset/AppIcon.png
-alpha off Assets.xcassets/AppIcon.appiconset/AppIcon.png`.

A UI test opens the grid and a game's page:
`xcodebuild test -scheme PadMintLibrary -destination 'platform=iOS Simulator,name=iPad Air 11-inch (M4)'`.

`UITests/ShowcaseUITests.swift` holds the scripted tours used for release videos (the
carousel, a game page, the shelf and the grid). They run only with
`TEST_RUNNER_PADMINT_SHOWCASE=1`; record each with `xcrun simctl io <device> recordVideo`.
Debug builds accept `-demoInstalled id,id,...` and `-demoLastPlayed id` so the
simulator, where no game is installed, shows a real player's library.

The app ships with each PadMint release and carries PadMint's version
(`MARKETING_VERSION` in `project.yml` must match `padmint/__init__.py`).
`ios/scripts/package-release.sh OUTPUT` syncs the catalog and builds the unsigned
`PadMint-ios-unsigned.ipa` in `build/release`; two runs give identical files.
Then `scripts/package-release.py OUTPUT` makes the Mac, Windows and Linux ZIPs
and adds the IPA to `SHA256SUMS` and the release gate.

## Next

- Play a game launched from the app on a device.
- Give the ready-made apps a `padmint-<game>://` link in their own repositories.

