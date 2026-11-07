# PadMint Library

An iPhone and iPad app that gathers the games you've built with
[PadMint](https://github.com/chrissotraidis/padmint) and installed on the device
in one library:

- **Your games:** your installed games as large covers you swipe through, the
  most recently played first. Tap a cover to play.
- **All games:** PadMint's whole catalog in a grid, with search and an
  All / Installed filter. Games you don't have are greyed out.
- **A page for each game,** with its cover, when you last played it, a Play
  button, or how to get it with PadMint.
- **Covers:** box art you choose to download, or any picture from Photos
  (long-press a game, or use its page).

**Status: early prototype.** In the iOS 27 simulator it finds games that answer
to PadMint's links and opens them. On 7 November it was installed on an iPad Pro
next to a SunPad build with the link, but the iPad's screen was off, so nothing
has been checked on the device yet.

## How it finds your games

Each iPhone/iPad app PadMint builds answers to a link named after its game, such
as `padmint-sunpad://` ([padmint#242](https://github.com/chrissotraidis/padmint/pull/242),
not yet released). Games installed before that release show up after you rebuild
them. The library asks iOS which of those links it can open.

iOS answers that question only for links the app declares, and iOS 27 answers
for the first 25 only. PadMint builds 31 iPhone/iPad games, so the app checks
the first 25 in the catalog. Each of the others shows **Tap to open**: the
library tries its link, and if the game opens it's remembered as installed.
Opening a link needs no declaration, so every game can be launched from here.

Ready-made apps (the ones you download instead of building) don't answer to a
link yet, so the library lists them without knowing whether they're installed.

## What it shows

Only games in PadMint's catalog, which lists Chris's own ports. The list comes
from `library.json`, which `scripts/sync-catalog.py` makes from a PadMint
checkout. The app fetches the newest copy from this repository and falls back to
the copy inside the app when offline.

## Covers

This repository holds no game art. Each game starts with PadMint's card art,
loaded from PadMint's repository. On first launch, the app asks whether to
download box art. If the player agrees, it fetches box art for the 27 console
games from [libretro-thumbnails](https://github.com/libretro/libretro-thumbnails)
(`thumbnails.libretro.com`) and keeps it on the device. `covers.json` stores
only each game's system and file name there. The PC games have no box art
source yet, so for those the player can choose a picture from Photos. A chosen
picture works for any game and comes first.

## Build

```sh
python3 scripts/sync-catalog.py ../padmint   # library.json and Sources/Info.plist
xcodegen generate
open PadMintLibrary.xcodeproj
```

A UI test opens the library and a game's page. Run it with `xcodebuild test
-scheme PadMintLibrary -destination 'platform=iOS Simulator,name=iPad Air
11-inch (M4)'`.

Needs Xcode 26 or newer and XcodeGen (`brew install xcodegen`). The app targets
iOS 17 and later.

## Next

- Install it on an iPad next to a game built with padmint#242, signed with
  Sideloadly, and check that the link survives re-signing.
- Box art for the PC games (SteamGridDB needs each player's own API key).
- Decide how players get the app. With a free Apple ID, iOS allows three
  sideloaded apps at a time, and the library would use one of them.
