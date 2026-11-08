# Agent instructions

- The library lists only games from PadMint's catalog, which holds only Chris's
  own ports. Never add another person's project, app or fork, and never list a
  game PadMint's catalog doesn't have.
- Never commit game code, disc images, ROMs, extracted game files, box art or
  other game art. Covers come from PadMint's own card art, from the sources in
  `covers.json` after the player agrees, or from the player's own photos.
- Every game in the library needs a `covers.json` entry (official title,
  console, box-art address); `scripts/sync-catalog.py` refuses otherwise.
  Run `scripts/check-covers.py` after changing it.
- Regenerate `library.json` and `Sources/Info.plist` with
  `scripts/sync-catalog.py`; don't edit them by hand.
- Keep it simple: one SwiftUI app, no dependencies.
- Don't claim something works on a device until it has been installed and run on
  one.
