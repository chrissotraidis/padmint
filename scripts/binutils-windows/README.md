# Pinned MIPS binutils for Windows

Maintainer tooling only, like `scripts/ido-windows`: it builds a local
candidate and checks it. It does not install tools, publish binaries or change
a game's recipe.

SnapPad's (and AnnePad's) Windows routes rebuild the original N64 ROM from its
decompilation, which needs GNU binutils for `mips-linux-gnu`. SnapPad builds
2.46.1 from a SHA-512-pinned archive with fixed configure flags on a Mac.
`inputs.json` pins the same archive, target and flags. `build.sh` builds them
natively, or for Windows with a MinGW-w64 host triple (statically linked, so no
MinGW runtime DLLs are needed beside them).

`check.sh` runs a synthetic MIPS fixture (`fixture.s`, `fixture.ld`) through
`as`, `ld`, `objcopy`, `strip`, `readelf` and `objdump` and prints a SHA-256
per output. `.github/workflows/binutils-windows.yml` builds native Linux and
Windows x64 tools, then requires the Windows tools on Windows x64 and Windows
11 ARM64 to produce byte-identical outputs to the native Linux build.

Before a recipe can use these, they need a published, checksummed archive and a
`tools.lock.json` entry, with the owner's approval to publish tool binaries.
