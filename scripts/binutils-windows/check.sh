#!/usr/bin/env bash
# Run the fixture through every pinned tool and print one SHA-256 per output.
#   scripts/binutils-windows/check.sh BIN_DIR WORK [EXE_SUFFIX]
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
bin=$1; work=$2; exe=${3:-}
t=mips-linux-gnu
mkdir -p "$work"
cd "$work"
cp "$here/fixture.s" "$here/fixture.ld" .
"$bin/$t-as$exe" -march=vr4300 -mabi=32 -EB -G0 -O1 -no-pad-sections fixture.s -o fixture.o
"$bin/$t-ld$exe" -T fixture.ld -EB fixture.o -o fixture.elf
"$bin/$t-objcopy$exe" -O binary fixture.elf fixture.bin
cp fixture.elf fixture-stripped.elf
"$bin/$t-strip$exe" fixture-stripped.elf
"$bin/$t-readelf$exe" -h -S -s fixture.elf | tr -d '\r' > readelf.txt
"$bin/$t-objdump$exe" -d fixture.elf | tr -d '\r' | sed -e 's/^fixture.elf:.*/fixture.elf:/' > objdump.txt
for f in fixture.o fixture.elf fixture.bin fixture-stripped.elf readelf.txt objdump.txt; do
  printf '%s  %s\n' "$(python3 -c 'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$f" 2>/dev/null || py -3 -c 'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$f")" "$f"
done
