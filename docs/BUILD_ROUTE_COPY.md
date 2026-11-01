# Build-route wording

**1 November 2026.** Chris asked for clearer Mac, Windows and Linux choices after
PadMint 0.5.28. The proposal in this file was applied in **PadMint 0.5.29**,
using the existing game page and its numbered steps, in English, Spanish and
Portuguese. Button destinations, workflows, publication permissions and catalog
hosts are unchanged; one decision stays open
([DarkPad](#darkpad-is-not-technically-a-different-kind-of-personal-build)).

## What the player needs to know

Each game page answers three questions in order, and names both ends of a build
("build on this Windows PC, play on iPhone/iPad"):

1. **Where will you play?** iPhone/iPad, this Mac or Android. Desktop copies
   are not something PadMint makes; BlueWake's own Windows and Linux downloads
   are linked from its card.
2. **Your own game file.** Needed now, or added inside the app after installing.
3. **Get your app.** The route this computer supports: build here, build on
   GitHub's Mac, or download the ready-made app, followed by how to install it.
   Alternatives stay under **Other ways to build**.

Players never choose compilers, recipes or app shells. Those details appear only
in setup when they change the next action.

## What changed in 0.5.29

| Where | Before | Now |
|---|---|---|
| Build step title | **Build on this computer** | **Build on this Mac**, **Build on this Windows PC** or **Build on this Linux computer** |
| Per-game note, beside the build | none | Catalog `host_notes` by system. The six new Windows routes say they built on Windows 11 ARM64 but have no device or native x64 check yet; AgePad says on the Mac that updated Steam files can stop its 0.1.0 recipe, with a link to the fix, before any tools are installed |
| Linux | install steps began "On this computer, install Sideloadly" | Before the build or download: installing directly from Linux isn't tested. Install steps start with copying the `.ipa` to a Windows PC or Mac |
| Cloud cards and steps | "a few minutes to about 40"; "this computer only starts the workflow" | GitHub compiles on a temporary Mac; you start it on GitHub; build time varies and GitHub may queue the run; the buttons only open GitHub |
| Mac-only card | **Needs an Apple Silicon Mac** | **This iPhone/iPad build needs an Apple Silicon Mac**, and you still play on your iPhone or iPad |
| Exact-host card | **Not buildable on this computer yet** | **Build it on another computer**, naming the computers that can |
| BlueWake | "Windows app available" on every host; Linux told to build from source | **Windows and Linux downloads**: BlueWake.exe or the AppImage, AVX2, your own disc; iPhone/iPad still on an Apple Silicon Mac; the button opens BlueWake's Install section |
| HaloPad | Xbox workflow only | Both editions and signing: the Xbox run makes iPhone/iPad and Mac apps kept 7 days; signing follows HaloPad's guide; Custom Edition needs an Apple Silicon Mac |
| DarkPad | "a public fork cannot run this personal build" | "This route currently requires a private copy of PadMint", with no technical reason claimed |

The README now opens with these three routes and one table of what each
computer builds, instead of repeating the roster in several places.

### After an end-to-end pass on 0.5.29 (on main, next release)

Clicking through the published 0.5.29 on a real Apple Silicon Mac, and as
Windows and Linux, found four rough spots, now fixed in all three languages:

- The library line named ports ("BananaPad, BearBirdPad…") while the rows show
  game titles, and counted 6 "other" games while the **Other routes** tab showed
  7. It now lists game titles and counts the paused game too.
- On a GitHub Cloud Build page the green button said **Build on GitHub** but only
  opened the README, while step 1 said to press **Fork PadMint**. **Fork PadMint**
  is now the main button, the README link is **Step-by-step guide**, and step 1
  no longer repeats the card's first sentence. It now says how to update: open an
  existing fork and press **Sync fork**. Guide-only buttons (DarkPad, HaloPad, the
  Mac's **Other ways to build**) say **Open the GitHub build guide**.
- Ready-made apps had no button; the download link sat inside step 1. They now
  have **Open the download page**, to the project's releases (most publish
  previews, which the latest-release link skips).
- On Linux the install warning was glued to "To get it:" before the steps. It is
  now its own line above the download button.

## DarkPad is not technically a different kind of personal build

Chris's distinction is between **ready-made apps he has authorized for
distribution** and **personal builds made through PadMint**. Requiring a ROM,
compiling an app, or importing a ROM after installation does not by itself
explain a unique private-repository requirement for DarkPad.

The released recipes inspected on 1 November show:

| Personal build | Published recipe | `publication.public_binaries` | PadMint cloud setup |
|---|---|---|---|
| DarkPad | [v0.1.0](https://github.com/chrissotraidis/darkpad/blob/v0.1.0/padmint.json) | `false` | Private repository required |
| BallPad | [v1.1.2](https://github.com/chrissotraidis/ballpad/blob/v1.1.2/padmint.json) | `false` | Public fork allowed |
| BellPad | [v0.2.3](https://github.com/chrissotraidis/bellpad/blob/v0.2.3/padmint.json) | `false` | Public fork allowed |
| BrawlerPad | [v0.2.2](https://github.com/chrissotraidis/brawlerpad/blob/v0.2.2/padmint.json) | `false` | Public fork allowed |
| PaperPad | [v0.2.3](https://github.com/chrissotraidis/paperpad/blob/v0.2.3/padmint.json) | `false` | Public fork allowed |

DarkPad's behavior comes from `github_build_private: true` in its catalog entry,
enforced by [`scripts/github-build.py`](https://github.com/chrissotraidis/padmint/blob/main/scripts/github-build.py).
The recipe's `public_binaries` field does not choose cloud visibility. The
[addition in PR #216](https://github.com/chrissotraidis/padmint/pull/216)
preserved that restriction; it does not establish a technical distinction from
the other personal builds above. A public repository's downloadable artifact is
also not private merely because it expires or is absent from the Releases page.

**Open decision for Chris:** give DarkPad the same cloud explanation and steps as
other personal builds, or apply one hosted-output rule to all of them. Until
then the route stays as shipped: the card and README say it currently requires a
private copy of PadMint, link the private setup guide, and mention the Actions
allowance. No restriction was removed or added, and no exception is claimed
from the word "decompilation".

Authorized ready-made downloads remain downloads. They do not establish
permission to distribute other personal outputs, and nothing here withdraws an
existing authorized download.

## Checks for 0.5.29

- Pages served by PadMint with its host check set to Apple Silicon Mac, Windows
  ARM64, Linux x64 and Intel Mac, each with an empty PadMint folder: GoldenPad and
  KartPad local builds, BellPad cloud, DarkPad, HaloPad, BlueWake, AgePad, a
  ready-made app and paused EctoPad. Linux lists only KartPad locally and shows
  none of the six Windows notes.
- Every button and link those pages offer (51 destinations, anchors included)
  resolved on 1 November.
- Spanish and Portuguese pages show the new titles, notes and Linux wording.
- Route tests cover the host titles, notes by system and the Linux wording.

These checks are page and route evidence. They are not device, gameplay or
cloud-artifact acceptance.

## What remains

| Work | State | Next action |
|---|---|---|
| Personal cloud-output visibility | DarkPad private, other personal builds public; copy is neutral | Chris decides one rule; then change `github_build_private` and the guide together |
| Seven local Windows routes | Published; six built on Windows 11 ARM64 | Install and play a Windows-built copy of each; one native x64 PC build |
| Cloud end-to-end use | Hosted builds pass | A private manual DarkPad run, signing and a device check |
| Linux installation | Not tested | Find and test one iPhone install route from Linux before documenting it |
| AgePad | 0.1.0 can stop after Steam updates | Release agepad#15's fix; remove the AgePad note with it |
| Remaining local Windows games | AnnePad, SnapPad, SunPad, BlueWake, Ottsel, AgePad | Follow each row of [WINDOWS.md](WINDOWS.md) |
| Preview updates and ownership checks | Shared-builder backlog | [Resume work](https://github.com/chrissotraidis/padmint/blob/main/docs/ROADMAP.md#resume-work) |

When a row is done, update the owning document and link the evidence. A build
proof, a published recipe, an enabled route and a device check are separate
milestones.
