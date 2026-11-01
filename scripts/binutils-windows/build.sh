#!/usr/bin/env bash
# Build the pinned GNU MIPS binutils for this machine or, with a MinGW-w64 host
# triple, for Windows. Maintainer tooling only: it never installs or publishes.
#
#   scripts/binutils-windows/build.sh OUTPUT [HOST]
#
# HOST is empty for a native build, or x86_64-w64-mingw32 for Windows x64
# executables (they also run on Windows 11 ARM64). Downloads go to OUTPUT/cache.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
out=$(mkdir -p "$1" && cd "$1" && pwd)
host=${2:-}
lock="$here/inputs.json"
field() { python3 -c 'import json,sys; v=json.load(open(sys.argv[1]))[sys.argv[2]]; print(" ".join(v) if isinstance(v, list) else v)' "$lock" "$1"; }
version=$(field version)
mkdir -p "$out/cache"
archive="$out/cache/binutils-$version.tar.xz"
[[ -f "$archive" ]] || curl -fsSL -o "$archive" "$(field url)"
actual=$(python3 -c 'import hashlib,sys; print(hashlib.sha512(open(sys.argv[1],"rb").read()).hexdigest())' "$archive")
[[ "$actual" == "$(field sha512)" ]] || { echo "binutils archive checksum mismatch" >&2; exit 1; }
name=${host:-native}
src="$out/src-$name"; build="$out/build-$name"; prefix="$out/mips-binutils-$version-$name"
rm -rf "$src" "$build" "$prefix"
mkdir -p "$src" "$build"
tar -xf "$archive" -C "$src" --strip-components=1
extra=()
if [[ -n "$host" ]]; then
  # Static: the Windows tools must not need MinGW runtime DLLs beside them.
  extra=(--host="$host" LDFLAGS="-static -static-libgcc")
fi
# shellcheck disable=SC2046
(cd "$build" && "$src/configure" --prefix="$prefix" --target="$(field target)" $(field configure) ${extra[@]+"${extra[@]}"} MAKEINFO=true)
make -C "$build" -j"$(nproc 2>/dev/null || sysctl -n hw.ncpu)" MAKEINFO=true
make -C "$build" install MAKEINFO=true
for tool in $(field tools); do
  ls "$prefix/bin/$(field target)-$tool"* >/dev/null
done
echo "$prefix"
