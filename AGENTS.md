# Agent instructions

- The library lists only games from PadMint's catalog, which holds only Chris's
  own ports. Never add another person's project, app or fork, and never list a
  game PadMint's catalog doesn't have.
- Never commit game code, disc images, ROMs, extracted game files, box art or
  other game art. Covers come from PadMint's own card art or, later, from a
  source the player agrees to.
- Regenerate `library.json` and `Sources/Info.plist` with
  `scripts/sync-catalog.py`; don't edit them by hand.
- Keep it simple: one SwiftUI app, no dependencies.
- Don't claim something works on a device until it has been installed and run on
  one.
