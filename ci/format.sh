#!/usr/bin/env bash
#
# Format the sources, or check that they are already formatted.
#
# Three kinds of file, three different treatments, because only one of them has a formatter:
#
#   C++      clang-format, against the .clang-format at the repo root. That file is the one from
#            the machine learning course, unchanged, so a reader moving between the two courses
#            is reading the same layout.
#
#   Python   whitespace and width only, deliberately not black. The figure pipeline is the
#            digital design course's, copied so that a reader moving between the two courses
#            reads one layout; black disagrees with that layout in a dozen places and would
#            rewrite a file this repo does not own the style of. A formatter that fights the
#            source it was pointed at is worse than no formatter.
#
#   Assembly no formatter exists that is worth imposing on AVR assembly, and column alignment in
#            a listing is a deliberate choice rather than something to normalize.
#
# What the last two have in common is the check they get: trailing whitespace, hard tabs, and
# for Python the same 100-column limit the C++ is held to. None of those three is ever a
# deliberate choice, and a hard tab in particular renders at a different width in every viewer
# and wrecks a hand-aligned comment column the moment somebody opens the file somewhere else.
#
# Usage:
#   ci/format.sh          Format in place.
#   ci/format.sh --check  Fail if anything is unformatted.
set -euo pipefail
shopt -s globstar nullglob

# Absolute path to the repo root, resolved before the cd below.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

CHECK=0
[ "${1:-}" = "--check" ] && CHECK=1

# Matches ColumnLimit in .clang-format, so one number governs every source in the repo.
COLUMN_LIMIT=100

# The submodules, read from .gitmodules rather than listed here. Each one is a separate
# repository with its own conventions, its own CI and its own idea of a line length, so none of it
# is ours to format; deriving the paths means adding a submodule needs no edit in this file.
submodule_paths=()
if [ -f .gitmodules ]; then
    while read -r path; do
        submodule_paths+=("$path")
    done < <(sed -n 's/^[[:space:]]*path[[:space:]]*=[[:space:]]*//p' .gitmodules)
fi

# Whether a path lies inside a submodule, or inside .venv, which holds installed packages.
not_ours() {
    local candidate="$1" path
    case "$candidate" in .venv/*) return 0 ;; esac
    for path in "${submodule_paths[@]}"; do
        case "$candidate" in "$path"/*) return 0 ;; esac
    done
    return 1
}

# Collect the files of one kind into the named array, skipping anything this repository does not
# own: each submodule carries its own formatting configuration.
collect() {
    local -n out="$1"; shift
    local file pattern
    out=()
    for pattern in "$@"; do
        for file in **/$pattern; do
            if not_ours "$file"; then continue; fi
            out+=("$file")
        done
    done
}

failures=0

# --------------------------------------------------------------------------------------------
# C++.
# --------------------------------------------------------------------------------------------
collect CPP_FILES '*.hpp' '*.cpp' '*.h' '*.c'
if [ ${#CPP_FILES[@]} -eq 0 ]; then
    echo "SKIP  clang-format: no C/C++ sources yet."
elif ! command -v clang-format >/dev/null 2>&1; then
    echo "error: clang-format not found. Install it, e.g. 'sudo apt -y install clang-format'." >&2
    exit 1
elif [ "$CHECK" -eq 1 ]; then
    # --Werror exits non-zero, which under `set -e` would take the script down here and skip the
    # whitespace, tab and width checks below. Route it through the counter instead, so one run
    # reports everything that is wrong rather than only the first category.
    if clang-format --dry-run --Werror "${CPP_FILES[@]}"; then
        echo "clang-format: ${#CPP_FILES[@]} C/C++ file(s) already formatted."
    else
        failures=$((failures + 1))
    fi
else
    changed=0
    for file in "${CPP_FILES[@]}"; do
        before="$(md5sum "$file")"
        clang-format -i "$file"
        [ "$before" = "$(md5sum "$file")" ] || { echo "Formatted: $file"; changed=$((changed + 1)); }
    done
    echo "clang-format: reformatted $changed of ${#CPP_FILES[@]} C/C++ file(s)."
fi

# --------------------------------------------------------------------------------------------
# Assembly and Python: whitespace, hard tabs, and (Python only) line width.
# --------------------------------------------------------------------------------------------
collect PLAIN_FILES '*.asm' '*.inc' '*.S' '*.py'
if [ ${#PLAIN_FILES[@]} -eq 0 ]; then
    echo "SKIP  whitespace: no assembly or Python sources yet."
elif [ "$CHECK" -eq 1 ]; then
    # Every grep here is allowed to match nothing, which is the passing case, so each is
    # wrapped to keep `set -o pipefail` from treating a clean repo as a failed command.
    trailing="$({ grep -nE '[[:space:]]+$' "${PLAIN_FILES[@]}" || true; })"
    tabs="$({ grep -nP '\t' "${PLAIN_FILES[@]}" || true; })"
    [ -n "$trailing" ] && { echo "error: trailing whitespace in:" >&2
                            printf '%s\n' "$trailing" >&2; failures=$((failures + 1)); }
    [ -n "$tabs" ] && { echo "error: hard tabs in:" >&2
                        printf '%s\n' "$tabs" >&2; failures=$((failures + 1)); }

    collect PY_FILES '*.py'
    if [ ${#PY_FILES[@]} -gt 0 ]; then
        # Characters, not bytes, and the same measure ci/markdown.sh uses: LC_ALL=C puts mawk and
        # gawk both in byte mode, and subtracting the UTF-8 continuation bytes gives characters in
        # either. Without it the two disagree about any line holding a non-ASCII character.
        wide="$(LC_ALL=C awk -v limit="$COLUMN_LIMIT" '
            function width(line,   bytes, continuations) {
                bytes = length(line)
                continuations = gsub(/[\200-\277]/, "&", line)
                return bytes - continuations
            }
            width($0) > limit { printf "%s:%d: %d columns\n", FILENAME, FNR, width($0) }' \
            "${PY_FILES[@]}")"
        [ -n "$wide" ] && { echo "error: Python over $COLUMN_LIMIT columns:" >&2
                            printf '%s\n' "$wide" >&2; failures=$((failures + 1)); }
    fi

    [ "$failures" -eq 0 ] && echo \
        "whitespace: ${#PLAIN_FILES[@]} file(s), no trailing whitespace, no tabs, none too wide."
else
    for file in "${PLAIN_FILES[@]}"; do
        before="$(md5sum "$file")"
        sed -i -e 's/[[:space:]]*$//' -e 's/\t/    /g' "$file"
        [ "$before" = "$(md5sum "$file")" ] || echo "Cleaned: $file"
    done
    echo "whitespace: cleaned ${#PLAIN_FILES[@]} file(s)."
fi

[ "$failures" -eq 0 ] || exit 1
