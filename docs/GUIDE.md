# PadMint player guide

The [README](../README.md) gets you from download to an installed game. This
guide has the details: what each part of the PadMint window does, every install
route, where PadMint keeps its files, how to remove it, and answers to common
questions.

- [Using PadMint](#using-padmint)
- [Your first game](#your-first-game)
- [Where PadMint keeps its files](#where-padmint-keeps-its-files)
- [More about GitHub Cloud Build](#more-about-github-cloud-build)
- [Installing what you made](#installing-what-you-made)
- [Android phone only (experimental)](#android-phone-only-experimental)
- [Removing PadMint](#removing-padmint)
- [Questions](#questions)

## Using PadMint

**The sidebar.** **My games** lists the games PadMint found on your devices and
the copies it built, with the version on each. **Updates** shows the ones behind
the latest release. **All games** is the full library, with tabs for **Build
here**, **Ready-made apps**, **GitHub Cloud Build** and **Other routes**. Under
**Devices**, each iPhone, iPad, this Mac and Android has its own list.
**Storage** shows the space PadMint uses and frees what it no longer needs.
**Settings**, at the bottom, holds the language (English, Spanish or
Portuguese), your devices, where copies are saved and help. To find a game, just
start typing.

On a Mac with Xcode, PadMint reads the iPhones and iPads you have connected to
that Mac once and lists the Pad games on each. Without Xcode, or on Windows and
Linux, it lists the copies it built.

**A game's page** looks the same on every computer. Under the game's name,
**Your copies** says where you have it and whether one is behind. Then come
numbered steps, each marked ✓ when done:

1. **Where will you play?** The device you'll play on. **This Mac** appears for
   games with a Mac version, on an Apple Silicon Mac.
2. **Your own game file:** click **Choose file…** and pick your disc image or
   ROM (the file window may open behind your browser). The page names the
   version that works, lists matching files in your Downloads folder and checks
   the file straight away. Games that take the file inside the app show this
   step as done.
3. **Build on this Mac** (or **this Windows PC**, **this Linux computer**). When
   every program the build needs is installed, this shows one green line.
   Otherwise it lists what's **not found** and how to get it: Xcode from the App
   Store, and one Homebrew line with a **Copy** button for the rest. Install
   what's missing, click **Check again**, then **Make my copy** (or **Update to
   v…**). If the button is gray, the line under it says why.

Games this computer can't build show one card instead, named for the route:
**Build on GitHub's Mac**, **This iPhone/iPad build needs an Apple Silicon
Mac**, **Build it on another computer** or **Get the ready-made app**.

**While it builds,** the page shows a checklist with each download and build
step. Keep the computer plugged in; PadMint keeps it awake. Finished work is
kept, so **Cancel** is safe and later builds are quicker. When it finishes, the
page shows **Your copy is ready**, the file it saved in Downloads and **What to
do next**. If it stops, it says why: open **Technical log** and use **Copy log
for a bug report** when asking for help.

## Your first game

On a Mac, each game says how much setup it needs:

| Tag on the page | Games | What you need |
|---|---|---|
| **Easiest** | KartPad for Android (Mario Kart Wii) | Any Windows, Mac or Linux computer, an Android phone and the **European** disc. Install the ready-to-play app; PadMint makes its game data. |
| **Needs Xcode** | BlueWake, SunPad, KartPad for Mac and iPhone, AgePad | A Mac with Apple Silicon and [Xcode](https://apps.apple.com/app/xcode/id497799835), free from the App Store. |
| **Needs Xcode + Homebrew** | Most other games | The same, plus one Homebrew line the page shows with a **Copy** button. |

**On a Windows PC,** KartPad needs no extra setup. GoldenPad, BearBirdPad,
BananaPad, SquirrelPad, DinoPad and MeleePad need Visual Studio's free C++ Build
Tools once (the page names the parts). These Windows routes are experimental:
each built on Windows 11 ARM64, but a Windows-built copy hasn't been installed
and played on an iPhone or iPad yet.

Your game file must be the version the page names, for example **Only the US
(North American) version works**. PadMint checks it as soon as you pick it.

## Where PadMint keeps its files

PadMint has no installer. It is the folder you unzipped:

```
PadMint-v…/
├── PadMint          double-click this (PadMint.command on Mac, padmint.sh on Linux)
├── Start here.txt   these steps, in English, Spanish and Portuguese
└── app/             PadMint itself: readable source, the game list and these guides
```

On Windows, `app` also holds a copy of Python. PadMint keeps the game sources,
tools and builds it downloads in a hidden `.padmint` folder in your home folder,
which can grow to tens of GB. **Storage** in the sidebar shows it and frees
space, and after a newer version of a game builds, PadMint deletes what older
versions left behind. Your finished copies go to your Downloads folder.

Before anything starts, PadMint lists every download, where it comes from, its
size and the free space needed. It uploads nothing.

<details>
<summary><strong>Why a ZIP, and not an installer or a .dmg?</strong></summary>

An installer only helps if it is signed: Windows and macOS warn about unsigned
installers exactly as they warn about these launchers, and signing needs a paid
certificate for each system. One ZIP with a double-click launcher works the same
way everywhere, and every release is rebuilt from this repository on separate
computers and compared byte for byte before it is published.

</details>

## More about GitHub Cloud Build

The [README's steps](../README.md#github-cloud-build-no-mac-needed) cover the
17 games in PadMint's shared workflow. On a phone, tap the panel button to the
left of **All workflows** to reveal the workflow list. The artifact download is
separate from the repository's **Code → Download ZIP**; stay signed in to GitHub
to download it.

### HaloPad Xbox edition on GitHub

HaloPad isn't in PadMint's shared workflow. Fork or sync
[HaloPad](https://github.com/chrissotraidis/projectreach#on-windows-linux-or-any-computer),
then choose **Actions → Build HaloPad (Xbox edition) → Run workflow** there.
The run makes an iPhone/iPad app and a Mac app, and GitHub keeps them for 7
days. To sign the iPhone/iPad app, follow
[HaloPad's install guide](https://github.com/chrissotraidis/projectreach/blob/main/docs/INSTALL-IPHONE.md).
Custom Edition, made from your own PC installer, still needs an Apple Silicon
Mac.

### DarkPad: private GitHub build

**Experimental.** A [clean hosted build of DarkPad v0.1.0](https://github.com/chrissotraidis/padmint/actions/runs/40830430386/job/123303170832)
passed on 29 October 2026, without uploading the app. Installing and playing a
copy built this way hasn't been checked yet. The workflow refuses to build
DarkPad from a public repository, so you need a private copy of PadMint. You add
your own Perfect Dark ROM inside the app; the build needs no ROM. Whether every
cloud build should follow the same rule is [an open decision](BUILD_ROUTE_COPY.md#darkpad-is-not-technically-a-different-kind-of-personal-build).

1. Open [GitHub's repository import](https://github.com/new/import), import
   `https://github.com/chrissotraidis/padmint` into a new repository in your
   account and select **Private**. A fork of a public repository can't be made
   private, so use **Import**, not **Fork**.
2. Check your account's [Actions allowance and spending limits](https://docs.github.com/en/billing/concepts/product-billing/github-actions).
   Private macOS runs use your included minutes, and more can be charged if your
   billing allows it. PadMint doesn't change your billing settings.
3. In that private repository, open **Actions → Build a game for iPhone and
   iPad**, enable Actions if asked, choose **darkpad** and press **Run
   workflow**.
4. After the green check, download the DarkPad ZIP from the run's **Artifacts**
   and unzip it. Keep the repository and the app private.
5. Sign and install the app, then import your own Perfect Dark USA Rev 1 / v1.1
   ROM inside DarkPad.

### Why some games can't use GitHub

Games such as SquirrelPad read your ROM while compiling, and your ROM should
never be uploaded. They build on your own computer instead; SquirrelPad has an
experimental [Windows route](WINDOWS.md#every-game-from-a-windows-pc-running-list).

## Installing what you made

**iPhone or iPad:** PadMint saves `<Game>-v…-ios-personal.ipa`, the complete
app ready to sign. The [README](../README.md#install-on-iphone-or-ipad) has the
Sideloadly steps. Some games ask for your ROM, disc or data inside the app
afterwards. [AltStore](https://altstore.io) and [SideStore](https://sidestore.io)
work too.

**HaloPad:** follow its [signing instructions](https://github.com/chrissotraidis/projectreach/blob/main/docs/INSTALL-IPHONE.md).
Its memory features need a suitable signing profile. A limited Xbox-edition iPad
test worked without them, but free Apple IDs and iPhones aren't validated yet.

**From Linux:** copy the `.ipa` to a Windows PC or Mac and follow the same
steps there. Sideloadly has no Linux version, and installing directly from Linux
isn't tested.

**Mac apps:** PadMint saves `<Game>-v…-macos-personal.zip`. Open it, move the
app to Applications and open it; the game asks for your own game file if it
needs one. To update, replace the old app; your saves stay.

**Android (KartPad):** PadMint makes a `KartPad game data` folder. Install
KartPad's APK from the [latest KartPad](https://github.com/chrissotraidis/kartpad/releases/latest),
copy the folder to the phone, then in KartPad tap **Import Game → Import from
Extracted Game Data Folder…**. [KartPad's guide](https://github.com/chrissotraidis/kartpad#get-kartpad)
has every step.

The `…-ios-unsigned.ipa` on a game's release page is PadMint's starting point.
It contains no game code and can't play by itself.

## Android phone only (experimental)

This route makes KartPad's game data folder on a 64-bit Android phone, without a
computer. Most players should use a computer instead. It needs about 8 GB of
memory, 25 GB free, Wi-Fi for about 6 GB of downloads and an hour or more, and
it has only been tried on an emulator.

1. Install **Termux** from [F-Droid](https://f-droid.org/packages/com.termux/)
   or its [GitHub releases](https://github.com/termux/termux-app/releases) (the
   `arm64-v8a` APK), not Google Play, and open it once.
2. Copy your disc image into the phone's **Download** folder.
3. In Termux, paste this line and press Enter:

   ```
   curl -fsSL https://raw.githubusercontent.com/chrissotraidis/padmint/main/launchers/padmint-android.sh | sh
   ```

   It checks the phone before downloading anything. If setup stops, run the
   same line again; finished steps are kept.
4. Tap **Allow** if Android asks about your files. PadMint opens in the phone's
   browser: choose **KartPad**, tap your disc image and tap **Make my copy**.
   Keep Termux open, with the screen on, until it says your copy is ready.

Next time, type `padmint` in Termux. If Android stops the build ("Process
completed (signal 9)"), turn on **Settings → System → Developer options →
Disable child process restrictions** and run `padmint` again.

## Removing PadMint

1. Cancel or finish any running build, then close PadMint's small window.
2. Move the PadMint folder you unzipped to the Trash (Recycle Bin on Windows).
3. Delete the `.padmint` folder:
   - **Mac or Linux:** in Terminal, paste `rm -rf ~/.padmint ~/.padforge` and
     press Return. It deletes both folders immediately, without the Trash.
     (`.padforge` is PadMint's old name; it's fine if you don't have one.) In
     Finder instead: **Go → Home**, press **Command-Shift-.** to show hidden
     folders and move `.padmint` to the Trash.
   - **Windows:** type `%USERPROFILE%` in File Explorer's address bar, press
     Enter and delete `.padmint`.
   - **Android phone:** in Termux, run
     `proot-distro remove padmint; rm -f $PREFIX/bin/padmint $PREFIX/etc/proot-distro/padmint.sh`,
     or uninstall Termux if you installed it only for PadMint.
4. Empty the Trash or Recycle Bin to get the space back.

Your copies in Downloads, the games on your devices, their saves and your game
files all stay. Deleting a game's app from a device deletes its saves too.

**On a Mac, you may also have installed these for PadMint.** Other apps use them
too, so keep them if you're unsure.

- **Apple's command line tools:** `sudo rm -rf /Library/Developer/CommandLineTools`
  ([Apple's steps](https://developer.apple.com/documentation/xcode/installing-the-command-line-tools#Uninstall-the-Command-Line-Tools-for-Xcode-package)).
  Without Xcode, Git and `python3` then stop working until you run
  `xcode-select --install` again.
- **Homebrew:** [its uninstall steps](https://docs.brew.sh/FAQ#how-do-i-uninstall-homebrew)
  remove everything installed with Homebrew.
- **Xcode:** move it to the Trash, and optionally delete
  `~/Library/Developer/Xcode/DerivedData`.
- `~/Library/Caches/com.apple.python` is a small cache from Apple's Python.

## Questions

<details>
<summary><strong>My game isn't in the list, or it's dimmed.</strong></summary>

Choose it anyway: its page says how to get it. **Build here** means PadMint
builds it on this computer. **GitHub Cloud Build** means GitHub builds it on a
temporary Mac you start from your browser. **Needs an Apple Silicon Mac** means
it needs your own Apple Silicon Mac with Xcode. **Paused for now** means there's
nothing to build or download yet.

</details>
<details>
<summary><strong>Can I build iPhone apps on Windows or Linux?</strong></summary>

Yes. A Windows PC builds nine games itself, experimentally: KartPad, GoldenPad,
BearBirdPad, BananaPad, SquirrelPad, DinoPad, MeleePad, BlueWake and SunPad.
Linux builds KartPad and SunPad.
From either, 17 more build on [GitHub's Mac](../README.md#github-cloud-build-no-mac-needed).
The other five (AgePad, AnnePad, NightPad, Ottsel and SnapPad) still need an
Apple Silicon Mac; [Building games on Windows](WINDOWS.md)
tracks each one.

</details>
<details>
<summary><strong>Can I use a Chromebook?</strong></summary>

Partly, and it hasn't been tested. From the browser you can start GitHub Cloud
Build for 17 games, but installing on an iPhone or iPad needs Sideloadly on a
Windows PC or Mac. With ChromeOS's Linux turned on, PadMint for Linux should
build KartPad, which needs plenty of free space. KartPad's
[Android download](https://github.com/chrissotraidis/kartpad/releases/latest)
should install on a Chromebook that runs Android apps.

</details>
<details>
<summary><strong>Can I play KartPad on my Mac?</strong></summary>

Yes, on a Mac with Apple Silicon (M1 or newer) and Xcode: choose **Mario Kart
Wii**, then **This Mac** under **Where will you play?** The first build needs
about 12 GB free. An Intel Mac can build KartPad for iPhone and iPad
(experimental), but the Mac app needs Apple Silicon.

If you only see iPhone/iPad and Android, download the latest PadMint for Mac and
open it from the new folder. PadMint 0.5.3 and newer restart natively when
launched through Rosetta, which fixes the missing **This Mac** option.

</details>
<details>
<summary><strong>The window closed, or nothing seems to happen.</strong></summary>

If no browser opened, the PadMint window shows a link starting with
`http://127.0.0.1`: open it. The first time, it can take a minute before the
page opens or a build gets past **Starting…**.

</details>
<details>
<summary><strong>It says my file is the wrong version, region or size.</strong></summary>

Each game needs one exact version, named on its page (KartPad needs the European
disc, RMCP01). Use an untouched 1:1 dump: trimmed, patched or half-size files
are refused on purpose.

</details>
<details>
<summary><strong>It says my file is stored only in iCloud (Mac).</strong></summary>

In Finder, right-click the file, choose **Download Now**, wait, then choose it
again.

</details>
<details>
<summary><strong>The app I made doesn't open on iOS or iPadOS 27.</strong></summary>

Build it again and install it over the old copy; your saves stay. Every game's
latest release supports iOS 27's required app startup, but copies built before
4 October may not open. If a new copy still doesn't open, report it on the
game's issue page ([details](COMPATIBILITY.md#recorded-mac-builds-4-october)).

</details>
<details>
<summary><strong>It says a download was blocked, or it stops early.</strong></summary>

PadMint names the server it couldn't reach. Check your connection and the
computer's date and time, then run PadMint again; finished downloads are kept.
Keep certificate checks and security software turned on.

</details>
<details>
<summary><strong>Linux asks me to install something (libxml2, Git).</strong></summary>

Run the command PadMint shows, for example `sudo apt install libxml2`, then
start PadMint again.

</details>
<details>
<summary><strong>Can someone send me their IPA or game data?</strong></summary>

No. It's made from their copy of the game, so sharing it means sharing the game.

</details>
<details>
<summary><strong>What was PadForge?</strong></summary>

PadMint's old name. PadMint moves your old PadForge folder over and keeps the
tools you already downloaded.

</details>

