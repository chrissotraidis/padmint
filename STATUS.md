# PadMint status

What each recent PadMint release changed. Updated **7 November 2026**.

**Next work:** [What PadMint still needs](docs/REMAINING.md) is the current
queue. Older releases, from 0.5.22 back, and the October build evidence are in
[STATUS-HISTORY.md](STATUS-HISTORY.md).

**Catalog: Lemonade Remixed added (7 November):** Lemonade Tycoon Deluxe as a Mac app, built on an Apple Silicon Mac with no game file; the player chooses their own Setup.exe in the app. Its recipe comes from the [Lemonade Remixed 1.0.1 release](https://github.com/chrissotraidis/lemonaderemixed/releases/tag/v1.0.1), and the player check passed before tagging and after publishing.

**v0.5.31:** the README is rewritten as a short player page, with the details in a new [player guide](docs/GUIDE.md) and
[developer guide](docs/DEVELOPING.md), and a [docs index](docs/README.md). The
release ZIP now carries every guide. DarkPad's help link opens the guide.
When PadMint puts a game module into its app, it now aligns the module's string
table the way recent iOS versions require ([#234](https://github.com/chrissotraidis/padmint/pull/234)).
Four in-app strings are fixed in English, Spanish and Portuguese ([#236](https://github.com/chrissotraidis/padmint/pull/236)):
the home page says *Your game file stays on this computer* instead of promising
everything runs locally, update help tells Mac and Linux players to use the
version button, KartPad's ready-to-play download is named as Android, and
ready-made apps are called iPad apps everywhere. HaloPad's
[0.3.14](https://github.com/chrissotraidis/projectreach/releases/tag/v0.3.14)
finishes builds when Apple's `actool` crashes on its icon
([#220](https://github.com/chrissotraidis/padmint/issues/220)); PadMint picks it
up automatically, so this release changes nothing for HaloPad itself.

**v0.5.30:** Adds NightPad (007: Nightfire, Xbox) to the Apple Silicon Mac → iPhone/iPad catalog, with its app icon, tool requirements and sideloading/import/update instructions. PadMint reads the player's own Xbox disc image during the build and hands over a personal unsigned IPA plus a NightPad game data folder, which the player imports in the app. NightPad releases contain only source, a recipe and checksums; PadMint builds the app on the player's Mac.

**v0.5.29:** clearer choices on every computer. A game's build step is named
for the computer (**Build on this Mac**, **this Windows PC**, **this Linux
computer**), and a short note beside it gives a route's known limit: the six
new Windows routes have no device or native x64 check yet, and AgePad 0.1.0 can
stop after Steam updates. On Linux, pages say before a build or download that
installing on an iPhone directly from Linux isn't tested, and the install steps
start by copying the app to a Windows PC or Mac. GitHub Cloud Build cards say
GitHub compiles on a temporary Mac while you start the run on GitHub, without
promising a build time. BlueWake's card offers its Windows and Linux downloads;
HaloPad's covers both editions and signing; DarkPad's says its route currently
requires a private copy of PadMint, without claiming a technical reason. All of
it is in English, Spanish and Portuguese. The README opens with the three routes
and one table of what each computer builds. What changed, the checks and the
open DarkPad decision are in [Build-route wording](docs/BUILD_ROUTE_COPY.md).

**v0.5.28:** six more games build for iPhone and iPad on a Windows PC, marked
experimental: **GoldenPad, BearBirdPad, BananaPad, SquirrelPad, DinoPad and
MeleePad**. Each game's new release (GoldenPad, BearBirdPad, BananaPad and
MeleePad 0.3.0, DinoPad 0.3.1, SquirrelPad 0.2.0) carries a Windows recipe and
an app without game code. On Windows PadMint asks for Visual Studio's C++ Build
Tools, installs the pinned compilers, builds the game from the player's own ROM or disc and
adds it to that app; on a Mac the build is unchanged. Before this PadMint was
released, PadMint 0.5.27's `padmint make <game> ios` built each published
release on Windows 11 ARM64 (SquirrelPad 103 s, BananaPad 134 s, GoldenPad
126 s, BearBirdPad 155 s, DinoPad 196 s, MeleePad 3,863 s), and PadMint's player
check passed on a Mac before tagging and after publishing. Not checked yet: a
Windows-built copy on an iPhone or iPad, and a native x64 Windows PC. The
catalog audit now applies its Apple Python 3.9 check only to Mac build steps.

**v0.5.27:** a cleaner window, the same on Mac, Windows and Linux. Every
game page now has numbered steps marked ✓ as they're done: **Where will you
play?**, **Your own game file** (shown as done when the game takes its file in the
app) and **Build on this computer**. When every program is installed, setup folds
to one green line; anything missing is listed first. The build's plan and the
install steps open on request, several file choices fold under one question, and
an older copy says how to update. GitHub Cloud Build moves to **Other ways to
build** at the bottom of Mac pages. Games built elsewhere, and ready-made apps,
use one card named for the route (**Build on GitHub's Mac**, **Needs an Apple
Silicon Mac**, **Get the ready-made app**). The library has one search row with a
systems menu and a single row of tabs, and rows no longer repeat where they build.
Storage leads with three plain totals and groups everything removable under
**Safe to remove** and **App and extra downloads**, each with **Remove all**.
Settings is grouped, and no longer stays visible under every page after it has
been opened once. The README screenshot is current.
On a computer a game can't build on, `padmint doctor` now names the computers
that can, instead of listing Homebrew and Xcode installs (found on Linux).

This release also lists **DarkPad** under GitHub Cloud Build (experimental; it
currently requires a private copy of PadMint; see [Build-route wording](docs/BUILD_ROUTE_COPY.md#darkpad-is-not-technically-a-different-kind-of-personal-build))
and shows **HaloPad's** own Xbox-edition workflow there, so 17 games can be built for
iPhone/iPad from Windows or Linux without a Mac. A clean hosted DarkPad build
passed; installing and playing that build still need testing. SquirrelPad stays
local because it reads the player's ROM while compiling.

**v0.5.26:** RAtouch's download instructions now point to the latest unsigned
IPA and its matching checksum in English, Spanish and Portuguese, instead of
directing players to a fixed older version. Its existing download route stays
the same. Follow-up importer tests reproduced defects in UTP, VaultPad, SunPad,
RAtouch and BallPad; the [audit](https://github.com/chrissotraidis/bellpad/blob/main/docs/FILE_IMPORT_AUDIT.md)
records the individual fixes and release verification. App updates deliver
those corrections; PadMint does not contain their importers.

**v0.5.25:** BellPad's iPhone/iPad finishing steps explain its 0.2.3 ISO/GCM
import and the Files → BellPad → Import fallback, while preserving the normal
sideloading/update instructions. SquirrelPad finishing steps also explain that
the same supported ROM used to build the app must be selected inside it after
installation, with import progress in 0.1.3 or newer. The compatibility record distinguishes five
projects with selection reports from unconfirmed source risks. Game fixes come
from rebuilding the corresponding game release; PadMint does not replace the
apps' own importers. Catalog and recipe JSON is decoded as UTF-8 on every host,
so Windows displays accented text and folder arrows correctly.

This release also includes host-neutral cloud-build wording for Windows/Linux
and a **View guide** fallback for existing project routes without a card label,
including HaloPad, from #217. These label fixes add no build route. Cloud-route
PR #216 shipped later, in 0.5.27.

**v0.5.24:** Removed Melee PC. It built 999sian/melee-pc, another person's project, and PadMint lists only Chris's own ports (AGENTS.md now says so, and `tests/test_catalog_ownership.py` checks it). MeleePad no longer links to it, and the GitHub workflow no longer offers it.

**v0.5.23:** Adds DarkPad (Perfect Dark) to the Apple Silicon Mac → iPhone/iPad catalog, with its original icon, tool requirements and sideloading/import/update instructions. It builds a personal unsigned IPA; the player supplies a USA Rev 1 / v1.1 ROM in the app. DarkPad releases contain only source, a recipe and checksums; PadMint builds the app on the player’s Mac.
