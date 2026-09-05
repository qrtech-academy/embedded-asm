#!/usr/bin/env bash
#
# Measure what one of your subroutines costs.
#
# The cross-check exercises ask you to predict a cycle count three ways and reconcile them: by
# hand from the instruction set summary, and by measurement. This is the
# measurement, and it is a tool rather than a test because what a cross-check needs is the number
# itself rather than a verdict on it.
#
# Two forms, because most of the course needs the simple one and the drivers need the other.
#
#   ci/measure.sh shift_bits 5
#       One call, with r24 = 5.
#
#   ci/measure.sh led_init:0x0200:13 led_on:0x0200
#       Several calls, in order, on the same machine. From L02 onwards a driver subroutine takes
#       a pointer to a structure that another subroutine had to build first, so measuring one on
#       its own would measure it against a structure full of zeros.
#
# The two forms are told apart by a colon or a leading double dash, neither of which can appear
# in a bare symbol name.
#
# IMAGE=app measures against drivers/build/app rather than drivers/build/drivers, which is what
# you want for an interrupt handler: a handler lives in your program, not in the library. It
# works because reti pops a return address exactly as ret does, so a handler can be called like
# any other subroutine even though nothing ever calls one for real.
#
# The extension is not given and not guessed at the call site. avra writes a .hex and L06's
# avr-gcc build writes an .elf, so whichever exists is the one measured; the harness reads both.
set -euo pipefail

# Absolute path to the repo root, resolved before the cd below.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ "$#" -eq 0 ]; then
    echo "usage: ci/measure.sh <symbol> [arg1] [arg2]" >&2
    echo "   or: ci/measure.sh <symbol>[:arg1[:arg2]] ..." >&2
    echo "   or: make measure SYMBOL=shift_bits ARG=5" >&2
    echo "   or: make measure CALLS=\"led_init:0x0200:13 led_on:0x0200\"" >&2
    exit 2
fi

# Turn the plain form into a specification, leaving the colon form alone.
case "$*" in
    *:*|*--*) SPECS=("$@") ;;
    *)        SPECS=("${1}:${2:-0}:${3:-0}") ;;
esac

# Assemble and build the tool through the same script the rest of the repo uses, so there is one
# definition of how anything here gets built.
./ci/build.sh avrsim >/dev/null
./ci/build.sh drivers >/dev/null

STEM="drivers/build/${IMAGE:-drivers}"
if [ -f "$STEM.hex" ]; then
    IMAGE_PATH="$STEM.hex"
elif [ -f "$STEM.elf" ]; then
    IMAGE_PATH="$STEM.elf"
else
    echo "SKIP  nothing to measure: neither $STEM.hex nor $STEM.elf exists yet. drivers.hex" >&2
    echo "      needs a .asm file in drivers/source, and app.hex needs one in drivers/app as" >&2
    echo "      well. L06's mixed.elf is built by the command in its appendix, not by this." >&2
    exit 0
fi

exec ./tools/avrsim/avrsim "$IMAGE_PATH" "${SPECS[@]}"
