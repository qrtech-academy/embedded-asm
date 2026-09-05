#!/usr/bin/env bash
#
# Build everything in the repo that can be built: the simulator harness we ship, the AVR
# assembly library the reader writes.
#
# Almost none of that exists on a fresh clone, and that is the normal case rather than an error.
# Every line printed says which of the three it is talking about and what happened to it, because
# a build that quietly skipped the only thing you changed must never read like one that passed.
#
# Two hex files come out of the assembly library, and they are built for different purposes:
#
#   drivers.hex  The subroutines alone, with no vector table and no reset. Nothing ever runs it
#                from the start; the unit tests set the program counter to a symbol and call one
#                subroutine at a time. This is the hex most tests load.
#
#   app.hex      drivers/app/main.asm assembled with the same subroutines: a whole program, with
#                a vector table and a main loop. L03's integration test loads this one and lets
#                it run, which is the only way to exercise an interrupt.
#
# avra has no linker. It assembles one source file, so each of the two is built by generating a
# top-level unit that .includes every source in turn and assembling that. The generated file is
# written into drivers/build alongside its output, and reading it is the fastest way to see what
# order things were assembled in. Because avra makes every label global, no .global directives
# are needed and none appear in the course's assembly.
#
# Usage:
#   build.sh              Build everything.
#   build.sh drivers      Build only the target whose name contains "drivers".
set -euo pipefail
shopt -s nullglob

# Absolute path to the repo root, resolved before the cd below.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Optional substring filter on the target name.
FILTER="${1:-}"

# The clock the course assumes throughout. The Arduino Uno runs its ATmega328P from a 16 MHz
# crystal; every timing number in the course follows from it, and it reaches the assembly as a
# -D define rather than as anything the device file knows about.
#
# There is no MCU variable any more. avra selects the device by which definition file the source
# includes, so "m328Pdef.inc" is the whole of that choice and it lives in the assembly.
F_CPU="${F_CPU:-16000000}"

# Where m328Pdef.inc lives. The Debian/Ubuntu avra package puts its device files here; override
# AVRA_INCLUDE if yours are somewhere else, which is what a non-apt install of avra needs.
AVRA_INCLUDE="${AVRA_INCLUDE:-/usr/share/avra}"

built=0    # Things that were actually built.
skipped=0  # Things that do not exist yet, reported by name.

# True when the target name passes the command-line filter.
selected() {
    [ -z "$FILTER" ] || [[ "$1" == *"$FILTER"* ]]
}

# Report a target that cannot be built yet, and say what would make it buildable.
skip() {
    echo "SKIP  $1: $2"
    skipped=$((skipped + 1))
}

# Terminate with the install line the README gives, rather than with a compiler error nobody can
# act on. A missing toolchain is a setup problem, not a repo that is not ready yet.
require() {
    command -v "$1" >/dev/null 2>&1 || {
        echo "error: $1 not found. Install the toolchain with:" >&2
        echo "  sudo apt -y install git make g++ avra binutils-avr simavr libsimavr-dev \\" >&2
        echo "                      clang-format" >&2
        echo "  sudo apt -y install gcc-avr avr-libc      # L06 only" >&2
        exit 1
    }
}

# Assemble one generated unit, keeping avra's errors and dropping its noise.
#
# Two kinds of noise. m328Pdef.inc carries PRAGMA directives that only Microchip Studio
# understands, and avra reports each one it steps over: eight lines of stderr on every successful
# build, describing the device file rather than anything the reader wrote, arriving in the middle
# of a test suite's output looking like a diagnostic.
#
# And avra prefixes every message with the directory of the unit it was given, then prints the
# include path as written, so an error in a driver arrives as
#
#     drivers/build//home/you/course/drivers/source/utils.asm(3) : Error : ...
#
# when the reader needs to see drivers/source/utils.asm(3). Both prefixes are stripped below.
# Real errors have a shape neither filter touches, and avra's exit status decides the outcome
# regardless of what was filtered out of the text.
assemble() {
    local unit="$1" stem="$2" errors status
    errors="$(mktemp)"

    avra -I "$AVRA_INCLUDE" -I drivers/include -D F_CPU="$F_CPU" \
        -l "$stem.lst" -m "$stem.map" -o "$stem.hex" "$unit" > /dev/null 2> "$errors" \
        && status=0 || status=$?

    grep -v "PRAGMA .* directive currently ignored" < "$errors" \
        | sed -e "s|^$(dirname "$unit")/||" -e "s|^$ROOT/||" >&2 || true
    rm -f "$errors"

    # avra writes these next to its output whether or not anything asked for them.
    rm -f "${unit%.asm}.obj" "${unit%.asm}.eep.hex"
    return $status
}

# --------------------------------------------------------------------------------------------
# The simulator harness. This is ours, it ships, and it always builds.
# --------------------------------------------------------------------------------------------
if selected "avrsim"; then
    if [ -f tools/avrsim/Makefile ]; then
        require g++
        echo "BUILD avrsim: the simulator harness, and the cycles measuring tool"
        make -s -C tools/avrsim lib tool
        built=$((built + 1))
    else
        skip "avrsim" "tools/avrsim is empty. Run 'git submodule update --init'."
    fi
fi

# --------------------------------------------------------------------------------------------
# The AVR assembly library, and the application program built on top of it.
# --------------------------------------------------------------------------------------------
if selected "drivers"; then
    # Collected into an array so that a legitimately empty directory is a length of zero rather
    # than a literal '*.asm' argument: `shopt -s nullglob` above is what makes that work, and an
    # empty drivers/source is the normal state of a fresh clone.
    sources=(drivers/source/*.asm)
    if [ ${#sources[@]} -eq 0 ]; then
        skip "drivers" "no .asm files in drivers/source yet; L01 is where the first one appears"
    else
        require avra
        mkdir -p drivers/build

        # The top-level unit avra assembles. The device file comes first so that register names
        # resolve in every source below it; each source may include it again, and m328Pdef.inc
        # guards itself against that.
        unit=drivers/build/drivers_unit.asm
        {
            echo "; Generated by ci/build.sh. Do not edit; edit drivers/source instead."
            echo ".include \"m328Pdef.inc\""
            for source in "${sources[@]}"; do echo ".include \"$ROOT/$source\""; done
        } > "$unit"

        echo "BUILD drivers: ${#sources[@]} assembly source(s) -> drivers/build/drivers.hex"
        assemble "$unit" drivers/build/drivers
        built=$((built + 1))

        app=(drivers/app/*.asm)
        if [ ${#app[@]} -eq 0 ]; then
            skip "app" "no .asm files in drivers/app yet; L03's integration test needs one"
        else
            # The app goes first: it carries the vector table, and .org counts from the start of
            # the assembled unit. A library subroutine assembled ahead of it would push every
            # handler past its slot, which is the one ordering mistake here that matters.
            unit=drivers/build/app_unit.asm
            {
                echo "; Generated by ci/build.sh. Do not edit; edit drivers/app instead."
                echo ".include \"m328Pdef.inc\""
                for source in "${app[@]}" "${sources[@]}"; do echo ".include \"$ROOT/$source\""; done
            } > "$unit"

            echo "BUILD app: ${#app[@]} program source(s) + the library -> drivers/build/app.hex"
            assemble "$unit" drivers/build/app
            built=$((built + 1))
        fi
    fi
fi

echo
echo "Build: $built built, $skipped not written yet."
