#!/bin/bash
# Build a game the way a Mac player's PadMint does, before you announce a release.
#
#   scripts/player-check.sh GAME PLATFORM GAME_FILE              the game's latest release
#   scripts/player-check.sh GAME PLATFORM GAME_FILE CHECKOUT     a clean copy of CHECKOUT's HEAD
#   GAME_FILE "-": the game has no file to select (its build downloads its own inputs)
#
# Players start PadMint.command, which runs Apple's /usr/bin/python3 (3.9), with nothing
# downloaded yet. A maintainer's `python3 -m padmint` usually runs a newer Python with warm
# caches, and passes builds that fail for players (padmint#142). This uses Apple's Python and
# an empty PadMint folder, and builds a fresh copy of the source. Run it with CHECKOUT before
# tagging and without it after publishing. The folder it prints holds your personal build
# and translated game code: keep it private and delete it when you are done.
set -euo pipefail
if [ $# -lt 3 ] || [ $# -gt 4 ]; then
  sed -n 4,5p "$0" | sed 's/^# *//'
  exit 2
fi
game=$1 platform=$2 game_file=$3 checkout=${4:-}
disc=(--disc "$game_file")
if [ "$game_file" = - ]; then disc=(); fi
player_python=/usr/bin/python3
padmint_root=$(cd "$(dirname "$0")/.." && pwd)
check_folder=$(mktemp -d "${TMPDIR:-/tmp}/padmint-player-check.XXXXXX")
echo "Python: $("$player_python" --version 2>&1) at $player_python, as PadMint.command runs it"
echo "Folder: $check_folder"
cd "$padmint_root"
if [ -n "$checkout" ]; then
  revision=$(git -C "$checkout" rev-parse HEAD)
  git clone --quiet --no-hardlinks "$checkout" "$check_folder/source"
  git -C "$check_folder/source" checkout --quiet --detach "$revision"
  PADMINT_HOME="$check_folder/padmint" "$player_python" -m padmint build "$game" \
    --repo "$check_folder/source" --revision "$revision" --target "$platform" ${disc[@]+"${disc[@]}"}
else
  PADMINT_HOME="$check_folder/padmint" "$player_python" -m padmint make "$game" "$platform" \
    ${disc[@]+"${disc[@]}"} --out "$check_folder/out"
fi
echo "Player check passed. Delete $check_folder when you are done with it."
