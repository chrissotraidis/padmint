# PadMint Library

An iPhone and iPad app that gathers the games you've built with
[PadMint](https://github.com/chrissotraidis/padmint) and installed on the device
in one library. Swipe through your installed games as large covers, tap one to
play, and browse the rest of PadMint's catalog below.

**Status: early prototype.** It builds and runs in the iOS 27 simulator. It has
not been installed on a device yet.

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
the copy inside the app when offline. For now, covers are PadMint's card art,
loaded from PadMint's repository. This repository holds no game art.

## Build

```sh
python3 scripts/sync-catalog.py ../padmint   # library.json and Sources/Info.plist
xcodegen generate
open PadMintLibrary.xcodeproj
```

Needs Xcode 26 or newer and XcodeGen (`brew install xcodegen`). The app targets
iOS 17 and later.

## Next

- Install it on an iPad next to a game built with padmint#242, signed with
  Sideloadly, and check that the link survives re-signing.
- Box art: download covers from an outside source only after the player agrees,
  or let the player choose a picture from Photos.
- Decide how players get the app. With a free Apple ID, iOS allows three
  sideloaded apps at a time, and the library would use one of them.
