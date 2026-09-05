#!/usr/bin/env bash
#
# Build and run every lecture test suite.
#
# Each suite is cumulative: it covers everything written up to and including that lecture, and
# every suite runs against the same two trees, which grow lecture by lecture:
#
#   drivers/   the AVR assembly library
#   device/    the pinned ATmega328P constants the suites check against
#
# Running every suite against the current state of both is what catches regressions across
# lectures: if the work added in L05 breaks a subroutine L02 built, L02's suite is what says so.
#
# A suite does not need either tree to exist. Tests for a class that has not been written are
# compiled out by `#if __has_include`, and tests for an assembly subroutine that has not been
# written are compiled out by a -DHAVE_<DRIVER> the suite's Makefile derives from what is
# actually present in drivers/source. Both switch themselves on the moment the file appears,
# with no list to edit anywhere.
#
# What that leaves is the trap this script exists to avoid. `qacademy::test::runAllTests()`
# returns false when no tests are registered, and prints nothing while doing it, so a suite whose
# every test sits behind a guard reports red, silently, before the reader has started. Every
# suite therefore ships at least one always-on test, and ci/check.sh enforces that rule rather
# than trusting it.
#
# Usage:
#   ci/test.sh
set -euo pipefail
shopt -s nullglob

# Absolute path to the repo root, resolved before the cd below.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

FRAMEWORK_DIR="$ROOT/libs/test"

suites=0
skipped=0

# Terminate if the test framework submodule has not been checked out. Nothing here can run
# without it, and the failure it would otherwise produce is a missing header nobody can act on.
if [ ! -f "$FRAMEWORK_DIR/Makefile" ]; then
    echo "error: test framework not found in libs/test. Run 'git submodule update --init'." >&2
    exit 1
fi

# The same courtesy for libsimavr. Every suite links against it, and without the development
# package the failure arrives as "/usr/bin/ld: cannot find -lsimavr" out of a `make -s` recipe,
# which is a linker error nobody can act on. README.md calls this the package people miss.
if ! printf 'int main(void){return 0;}\n' \
    | g++ -x c++ - -lsimavr -o /dev/null >/dev/null 2>&1; then
    echo "error: libsimavr not found. The suites link against the library, not the command." >&2
    echo "       sudo apt -y install simavr libsimavr-dev" >&2
    exit 1
fi

makefiles=(lectures/*/exercises/test/Makefile)
if [ ${#makefiles[@]} -eq 0 ]; then
    echo "SKIP  no lecture test suites exist yet (lectures/*/exercises/test/Makefile)."
    echo
    echo "Test: 0 suite(s) run, 0 skipped."
    exit 0
fi

for makefile in "${makefiles[@]}"; do
    test_dir="$(dirname "$makefile")"

    # A suite deliberately left behind at an older lecture opts out rather than being deleted.
    # Grepped as an assignment, not as a bare string: a Makefile that merely mentions FROZEN in a
    # comment would match a looser pattern and silently stop being run.
    if grep -qE '^ *FROZEN *[?:]?= *1' "$makefile"; then
        echo "SKIP  $test_dir (frozen)"
        skipped=$((skipped + 1))
        continue
    fi

    echo "TEST  $test_dir"
    # The closing clean runs whether the suite passed or not. Under `set -e` a red suite aborts
    # the script, and without the trap the binary it built would be left in the lecture tree.
    trap 'make -s -C "$test_dir" clean >/dev/null 2>&1 || true' EXIT
    make -s -C "$test_dir" clean build run \
        ROOT_DIR="$ROOT" QACADEMY_TEST_DIR="$FRAMEWORK_DIR"
    make -s -C "$test_dir" clean
    trap - EXIT
    suites=$((suites + 1))
done

echo
echo "Test: $suites suite(s) run, $skipped skipped."
