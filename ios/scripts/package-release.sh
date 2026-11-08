#!/bin/bash
# Build PadMint-ios-unsigned.ipa, the iPhone/iPad app players sideload, into OUTPUT_FOLDER.
# Usage: ios/scripts/package-release.sh OUTPUT_FOLDER
# Run it before scripts/package-release.py, which adds the IPA to SHA256SUMS and the gate.
# Needs Xcode 26+ and XcodeGen.
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
out=$(mkdir -p "$1" && cd "$1" && pwd)
version=$(sed -n 's/^__version__ = "\(.*\)"/\1/p' "$root/../padmint/__init__.py")
if ! grep -q "MARKETING_VERSION: \"$version\"" "$root/project.yml"; then
  echo "ios/project.yml's MARKETING_VERSION must match PadMint's version ($version)." >&2
  exit 1
fi
cd "$root"
python3 scripts/sync-catalog.py
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
ipa="PadMint-ios-unsigned.ipa"
(cd "$work" && find Payload -exec touch -h -t 200101010000 {} + && zip -qrX -y "$out/$ipa" Payload)
(cd "$out" && shasum -a 256 "$ipa")
