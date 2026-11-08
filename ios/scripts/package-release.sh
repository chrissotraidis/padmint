#!/bin/bash
# Build the unsigned release IPA players sideload, and its SHA256SUMS.
# Usage: scripts/package-release.sh OUTPUT_FOLDER
# Needs Xcode 26+, XcodeGen and a PadMint checkout beside this one (for the catalog).
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
out=$(mkdir -p "$1" && cd "$1" && pwd)
version=$(sed -n 's/^ *MARKETING_VERSION: "\(.*\)"/\1/p' "$root/project.yml")
cd "$root"
python3 scripts/sync-catalog.py "${PADMINT_CHECKOUT:-../padmint}"
if [ -n "$(git status --porcelain library.json Sources/Info.plist)" ]; then
  echo "library.json or Info.plist changed after syncing the catalog: commit it first." >&2
  exit 1
fi
xcodegen generate --quiet
# A fixed folder: build paths end up in the binary, so a fixed one keeps rebuilds identical.
work="$root/build/release"
rm -rf "$work" && mkdir -p "$work"
xcodebuild -project PadMintLibrary.xcodeproj -target PadMintLibrary -configuration Release \
  -sdk iphoneos -arch arm64 SYMROOT="$work/build" CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO -quiet
mkdir -p "$work/Payload"
ditto "$work/build/Release-iphoneos/PadMint.app" "$work/Payload/PadMint.app"
ipa="PadMint-Library-v$version-ios-unsigned.ipa"
(cd "$work" && find Payload -exec touch -h -t 200101010000 {} + && zip -qrX -y "$out/$ipa" Payload)
(cd "$out" && shasum -a 256 "$ipa" > SHA256SUMS)
cat "$out/SHA256SUMS"
