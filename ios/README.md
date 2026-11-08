# PadMint Library

PadMint for iPhone and iPad: one library for the games you've built with
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
  underneath. Until then it shows PadMint's own card art and names.
- **Your own covers.** Long-press any game, or use its page, to pick a picture from
  Photos.
- **Settings** for the layout, sort order, covers and titles, and what the app
  opens to: the library or the last game you played.

Covers keep their real shapes: wide N64 boxes, square PlayStation cases and tall
GameCube, Wii, PS2, Xbox and PC boxes all stand on one line.

## Install

1. Download `PadMint-Library-v…-ios-unsigned.ipa` from the
   [latest release](https://github.com/chrissotraidis/padmint-library/releases/latest).
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

## Covers and titles

This repository holds no game art. `covers.json` gives each game's official
title, console and the address of its box art:

| Source | Games |
|---|---|
| [libretro-thumbnails](https://github.com/libretro/libretro-thumbnails) | The 27 console games, plus Warcraft II and Red Alert (DOS) |
| Steam | Age of Empires II, Daggerfall, RollerCoaster Tycoon 2, Unreal Tournament, Fallout 2 |
| GOG | Caesar III, Pharaoh + Cleopatra |
| Wikipedia | Diablo, Tribes 2, Kid Pix (its title screen: no box scan is available) |

The app downloads them only after the player agrees and keeps them on the device.
A game's page names where its box art came from. A picture the player chooses
always comes first. `scripts/check-covers.py` checks that every address still
loads and prints each cover's shape.

## Build

```sh
python3 scripts/sync-catalog.py ../padmint   # library.json and Sources/Info.plist
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

A release: `scripts/package-release.sh OUTPUT` syncs the catalog, builds the
unsigned IPA in `build/release` and writes `SHA256SUMS`. Two runs give
identical files. Check the IPA with PadMint's `python3 -m padmint audit` before
publishing.

## Next

- Play a game launched from the app on a device.
- Give the ready-made apps a `padmint-<game>://` link in their own repositories.

