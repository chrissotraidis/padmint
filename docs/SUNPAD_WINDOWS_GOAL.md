# Goal: build SunPad for iPhone/iPad on a Windows PC

Players keep asking for this (Discord, 10 November 2026). This page is a goal
loop: hand it to an agent with "work through docs/SUNPAD_WINDOWS_GOAL.md", and
each turn moves one step forward until the goal is met or a step needs Chris.

## The goal

A Windows player opens PadMint, picks SunPad, chooses **Build on this Windows
PC**, gives it their own GMSE01 disc, and gets an `.ipa` that installs with
Sideloadly and plays on an iPad. SunPad then counts as done in
[REMAINING.md](REMAINING.md#2-bring-the-seven-mac-only-games-to-windows): its
published recipe declares Windows hosts, `scripts/player-check.sh` passes, and a
copy built on Windows plays on a device.

## Where it starts (10 November 2026)

Most of the engineering is already done, in two drafts:

- [sunpad#57](https://github.com/chrissotraidis/sunpad/pull/57) builds the game
  module through PadMint off a Mac (Linux). Draft, CI green, 11 commits behind
  `main`.
- [sunpad#78](https://github.com/chrissotraidis/sunpad/pull/78), stacked on #57,
  adds the Windows ARM64 and x64 steps. Draft, CI green including
  `windows-route`. A full PadMint build on Windows 11 ARM64 passed the gate; an
  x64 build passed under ARM emulation; all 225 generated files match the Mac.
- Since then SunPad 0.2.3 shipped (30 October) and `main` changed 32 files,
  including bundled xxHash for device packaging (d1e14cb) and stricter
  game-data extraction (a7c74c1). The Windows module step has never run with
  those changes.
- PadMint's `catalog/sunpad.json` has no `ios_hosts`, so Windows shows SunPad
  as *Needs Apple Silicon Mac* even once a release supports Windows.
- The Windows machine is the Parallels VM "Windows 11" (ARM64) on Chris's Mac.
  No native x64 PC is available.

## Each turn

1. Recheck live state: both PRs (`gh pr view`), SunPad's latest release,
   PadMint `main`, and this page's checklist. Recorded state goes stale.
2. Take the first unchecked step below. Do only that step.
3. Record the evidence beside the step: commit, run link, host, time and
   result. Say exactly what was and wasn't checked (build, install, launch,
   audio, saves). A build is not a device result.
4. Tick the step only when its **Done when** is fully true. Commit this page in
   the same PR as the work.
5. Stop and ask Chris when the step says **Chris**, or when a stop rule below
   triggers. Otherwise continue to the next step.

Stop rules: any failure of `python3 -m padmint audit`, the private release
gate or `scripts/player-check.sh` is a stop. So is a change that alters the
Mac route's output (then the Mac build needs its own device check first). Never
commit disc contents, translated code, keys or personal builds.

## Steps

- [x] **S1. Bring #57 up to date.** Rebase `codex/padmint-ios-module` on
  SunPad `main` and resolve conflicts, keeping `main`'s 0.2.3 behavior.
  **Done when** CI is green and `scripts/player-check.sh sunpad ios DISC
  CHECKOUT` passes on the Mac with the rebased checkout.
  - 10 Nov: `main` merged into #57 (no conflicts; merging avoids
    force-pushing a stacked branch). #57 had also moved the Mac to PadMint's
    LLVM module build, which would change the Mac's output without a device
    check. [065f76c](https://github.com/chrissotraidis/sunpad/commit/065f76c)
    keeps the Mac on 0.2.3's Xcode steps and uses `ios_module` only off the
    Mac (recipe schema 2), as BlueWake 0.11.0 does. A Mac player downloads no
    LLVM. CI green (iOS, tvOS, safety). Mac player check at 065f76c **passed**
    (Apple Python 3.9.6, empty PadMint 0.6.3 folder, published v0.2.3 app as
    APP; 4,576 s). A first run without APP failed at packaging: a checkout
    build gets no published app unless given one, while `padmint make`
    downloads it, so players are unaffected.
- [x] **S2. Bring #78 up to date.** Rebase it on the new #57. Make the Windows
  module and package steps build the bundled xxHash the same way `main` now
  does for the Mac. **Done when** CI, including `windows-route`, is green, and
  the Mac player check from S1 still passes on this branch.
  - 10 Nov: #57 merged into #78 at
    [4b7c2d7](https://github.com/chrissotraidis/sunpad/commit/4b7c2d7); only
    `padmint.json` conflicted (Windows steps kept, Mac on Xcode, `ios_module`
    on Windows and Linux). The xxHash fix needs no Windows change: it touches
    only the Xcode core build, the iOS module template uses no xxHash, and the
    Windows desktop tools already build every bundled library
    (`-DUSE_SYSTEM_LIBS=OFF`). 19 Windows builder tests pass locally. Mac
    steps are identical to #57's, so S1's player check covers this branch.
    The only Mac-relevant recipe difference is that `python3` and `rg` now
    list their hosts (Mac included); the four Mac scripts are unchanged. CI
    green, including `windows-route` (22 min).
- [x] **S3. Build on Windows from the branch.** In the Windows 11 ARM64 VM,
  with a fresh PadMint folder and the released PadMint for Windows, build
  SunPad for iOS from the #78 checkout and the player's disc. **Done when** the
  IPA passes the publication gate and differs from the published app only by
  the game module, its identity file and the launch link. Record build time.
  - 10 Nov: released PadMint 0.6.3 for Windows (its bundled Python 3.13.15,
    reported host `windows-arm64`), fresh PadMint folder on a new local NTFS
    disk, clean clone at 4b7c2d7, published v0.2.3 app, disc read from the Mac
    share. `padmint tools` 1,591 s; `padmint build` 8,556 s (2 jobs; module
    stage 77 min). Record `completed`, publication gate PASS (0 findings),
    IPA SHA-256 409ae0e9…720b. Readback: 2,796 of 2,797 published entries
    identical; `Info.plist` changes only `CFBundleURLTypes` (padmint-sunpad);
    one entry added, `gGMSE01_recomp.dylib` (arm64, iOS 16.0, libSystem only,
    imports `ldexp`, `ldexpf`, `dyld_stub_binder`). Not checked: install,
    launch, audio, saves. The IPA stays private on the Mac.
- [ ] **S4. Launch it on an iPad. (Chris)** Install the S3 IPA with Sideloadly.
  **Done when** it reaches gameplay. Note audio, a save and reload, and
  controller input if checked. This is a stop before release because a
  Windows-only compiler difference would show up here first.
  - 10 Nov: saves backed up from the iPad Pro 12.9 (6th gen) first, including
    `GC/USA/Card A/01-GMSE-super_mario_sunshine.gci`. The S3 IPA was signed
    with the team's development profile and installed in place over 0.2.3
    with `devicectl`. Launched with `DYLD_PRINT_LIBRARIES=1`: dyld loaded
    `SunPad.app/gGMSE01_recomp.dylib` from the app bundle (UUID
    4C4C44D3-5555-3144-A185-F1293527A62D, the Windows-built module), and the
    runtime logged `module loaded … entry=0x8000522C`. SunPad reported 30.0 fps,
    59.9 VPS, speed ratio 1.003, thermal nominal; audio RemoteIO running at
    48 kHz on the speaker. Mirrored screen: the attract scene and then the
    title screen. Not yet checked: gameplay after START, hearing the sound,
    saving and reloading. These need touch or controller input on the iPad.
- [ ] **S5. Release SunPad with Windows hosts. (Chris approves)** Mark #57 and
  #78 ready, merge them in order, and prepare the next SunPad release with
  `windows-arm64` and `windows-x86_64` marked experimental in `padmint.json`.
  Every asset passes `python3 -m padmint audit` and the release gate. Ask Chris
  before tagging and publishing. **Done when** the release is published and
  `scripts/player-check.sh sunpad ios DISC` (no checkout) passes against it.
- [ ] **S6. Show it in PadMint.** Add `ios_hosts` (`macos-arm64`,
  `windows-arm64`, `windows-x86_64`) and a Windows `host_notes` entry in
  English, Spanish and Portuguese to `catalog/sunpad.json`, as MeleePad does.
  `tests/test_later.py` uses SunPad as its *Needs Apple Silicon Mac* example;
  move it to a game that still needs one. Update [WINDOWS.md](WINDOWS.md),
  [COMPATIBILITY.md](COMPATIBILITY.md), [REMAINING.md](REMAINING.md) and
  `STATUS.md`. Release PadMint with it. **Done when** the post-release player
  check reports no catalog mismatch.
  - 10 Nov: drafted as [padmint#257](https://github.com/chrissotraidis/padmint/pull/257).
    The recipe also declares Linux, so `ios_hosts` lists both Linux hosts
    too, with a Linux note (container builds only; installing needs a Windows
    PC or Mac); otherwise the post-release check fails. SnapPad replaces
    SunPad in `tests/test_later.py`. 520 tests pass and the catalog audit
    against #78's recipe reports nothing. Merge only after S5's release;
    update the notes and docs from S4's result first.
- [ ] **S7. Build as a player would.** In the VM, with a fresh PadMint folder,
  run `padmint make sunpad ios --disc DISC` against the published release.
  **Done when** it produces the IPA and the Windows game page shows **Build on
  this Windows PC** with the experimental note.
- [ ] **S8. Tell players. (Chris)** Chris posts the news. The note says it is
  experimental on Windows and asks for reports from native x64 PCs.

## After the goal

These remove the experimental label and are tracked in
[REMAINING.md](REMAINING.md#1-prove-the-routes-already-published):

- A Windows-built copy played on an iPad with audio and saves checked.
- A build on a native x64 Windows PC (a player's report counts if it includes
  the PadMint log).
