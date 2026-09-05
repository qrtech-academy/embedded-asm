#!/usr/bin/env bash
#
# Remove everything the build generates, and nothing else.
#
# Deliberately conservative: it deletes named artifacts and named build directories, never a
# pattern that could reach a source file. The reader's own work lives in drivers/source,
# drivers/app, and neither is touched by anything here.
#
# Usage:
#   ci/clean.sh
set -euo pipefail
shopt -s nullglob globstar

# Absolute path to the repo root, resolved before the cd below.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

removed=0

# Remove a path if it exists, and say so.
drop() {
    [ -e "$1" ] || return 0
    rm -rf "$1"
    echo "removed $1"
    removed=$((removed + 1))
}

# The assembled hex, and the listing, map and unit files beside it.
drop drivers/build

# The simulator harness, through its own makefile so that a target added there is honoured here
# without this script learning about it.
for dir in tools/avrsim; do
    [ -f "$dir/Makefile" ] && { make -s -C "$dir" clean; echo "cleaned $dir"; removed=$((removed + 1)); }
done

# Test suite binaries.
for suite in lectures/*/exercises/test; do
    [ -f "$suite/Makefile" ] && { make -s -C "$suite" clean; echo "cleaned $suite"; removed=$((removed + 1)); }
done

# The test framework's static library, which ci/test.sh rebuilds on demand.
[ -f libs/test/Makefile ] && { make -s -C libs/test clean >/dev/null 2>&1 || true; }

# Python bytecode from the figure pipeline, and the scratch tree.
for cache in **/__pycache__; do drop "$cache"; done
drop temp

echo
echo "Clean: removed $removed item(s)."
