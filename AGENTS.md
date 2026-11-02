# Agent instructions

Start with [What PadMint still needs](docs/REMAINING.md). It answers "what do we
still need to do for PadMint?": where every computer stands, the ordered work
queue, the decisions only Chris can make and the evidence each step needs. Keep
it current in the same PR as the work. [STATUS.md](STATUS.md) says what each
release changed; [Resume work](docs/ROADMAP.md#resume-work) keeps earlier handoffs.

- This repository holds only the shared Builder: its pipeline, profiles, tests and docs. Never commit or upload game code (translated or decompiled), disc images, ROMs, extracted game files, saves, console keys or personal builds.
- Before any public release, every asset must pass `python3 -m padmint audit <asset>` (and the private `~/.codex/release-gate/release_gate.py` while it remains the reference). A failure is a stop, not a note.
- Before announcing a game release PadMint builds on a Mac, `scripts/player-check.sh` must pass for it (with the checkout before tagging, without it after publishing). A build through `python3 -m padmint` with a newer Python and warm caches is not player evidence. A failure is a stop.
- Never commit key bytes, key hex or key byte lists, even in tests or gate code. Identify keys by prefix + SHA-256 only (see `padmint/gate.py`). Build detector strings at runtime so this repository passes its own gate.
- **Only Chris's own games.** The catalog, recipes, workflow choices, `other_ports` links and docs list only games whose repository is Chris's own port: his app and code live in that `chrissotraidis/...` repository. Never add, wrap, patch or repackage another person's project (an upstream port, someone else's app or fork), not even under a `chrissotraidis` repository, a recipe-only repository, or to fix a user's report. If an issue turns out to be about someone else's app, say so and point the reporter to that project. A new game entry needs Chris's explicit go-ahead. `tests/test_catalog_ownership.py` enforces part of this; Melee PC (999sian/melee-pc) was removed in 0.5.24 for breaking it.
- Game-specific logic stays in each game's repository behind its `padmint.json`; PadMint owns validation, running, progress, records and the gate. There must be only one Builder.
- Only document commands that exist. Label platforms as verified, experimental or planned and do not upgrade a label without a recorded run.
- Keep it simple: a generic runner plus one small manifest per game.
