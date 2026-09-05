#!/usr/bin/env bash
#
# Check that the Markdown prose is hard-wrapped at 100 columns.
#
# The reason for the rule is review: a paragraph rewrapped by an editor turns a one-word change
# into a twenty-line diff, and a course whose diffs are unreadable stops getting reviewed.
#
# The rule collides with three things Markdown gives no way to break, so each is exempt and each
# exemption is deliberate rather than a convenience:
#
#   Fenced code blocks   An assembly listing, a register dump or a shell command line has no
#                        sentence boundary in it, and breaking one changes what it means. Both
#                        ``` and ~~~ fences count, and ```math is a fence like any other.
#
#   Display math         An equation is one expression. There is nowhere in $$ ... $$ to put a
#                        line break that does not make the source harder to read than the long
#                        line was. Tracked by toggling on each $$, including the case where a
#                        line opens and closes one on its own.
#
#   Link-only lines      Descriptive alt text plus a path routinely exceeds 100 columns, and a
#                        vendor's datasheet URL exceeds it on its own. Markdown has no line
#                        continuation inside a link, so there is nowhere to break. A line that is
#                        nothing but one link or image is exempt; a link sitting in the middle of
#                        a sentence is not, because that line can be broken before the link.
#
#   Table rows           A table's column widths are set by its widest cell, and rewrapping a row
#                        is not possible at all. Lines starting with | are exempt.
#
# It also checks one rule about the prose itself, which is a house rule rather than a mechanical
# one: no dash is used as mid-sentence punctuation. Not an em dash, not an en dash, and not the
# ASCII stand-in " -- ". A dash in the middle of a sentence is almost always a comma, a semicolon
# or a full stop that has not been chosen yet, and choosing is the author's job.
#
# The single hyphen separator is deliberately still allowed, because in this course it is
# structure rather than punctuation: it separates a lecture number from its title in "# L04 -
# Stacks", and an index entry from its summary in lectures/README.md. Those are labels, and a
# label is not a sentence.
#
# Usage:
#   ci/markdown.sh
#   ci/markdown.sh --limit 120
set -euo pipefail
shopt -s globstar nullglob

# Absolute path to the repo root, resolved before the cd below.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

LIMIT=100
if [ "${1:-}" = "--limit" ]; then LIMIT="${2:?--limit needs a number}"; fi

# The submodules, read from .gitmodules rather than listed here. Each one is a separate
# repository with its own conventions, its own CI and its own idea of a line length, so none of it
# is ours to check; deriving the paths means adding a submodule needs no edit in this file.
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

# Every Markdown file this repository actually owns.
files=()
for file in **/*.md; do
    if not_ours "$file"; then continue; fi
    files+=("$file")
done

if [ ${#files[@]} -eq 0 ]; then
    echo "SKIP  no Markdown files to check yet."
    exit 0
fi

# Collected rather than streamed, so the summary can count them. Wrapped in a command
# substitution whose grep is allowed to match nothing: with `set -o pipefail` a grep that
# legitimately finds no violations would otherwise take the whole script down.
violations="$(LC_ALL=C awk -v limit="$LIMIT" '
    # Characters, not bytes. Ubuntu default awk is mawk, which counts bytes, while gawk in a UTF-8
    # locale counts characters, so the two disagree about any line holding a micro sign, an ohm, a
    # multiplication sign or an em dash -- and the appendices are full of all four. LC_ALL=C puts
    # both in byte mode, and subtracting the UTF-8 continuation bytes gives the character count in
    # either. A continuation byte is any of 0x80 to 0xBF, and every non-ASCII character has at
    # least one.
    function width(line,   bytes, continuations) {
        bytes = length(line)
        continuations = gsub(/[\200-\277]/, "&", line)
        return bytes - continuations
    }

    FNR == 1 { fence = 0; math = 0 }

    # A fence line toggles the block and is itself exempt, whatever its length.
    /^[[:space:]]*(```|~~~)/ { fence = !fence; next }
    fence { next }

    # Display math. An even number of $$ on one line opens and closes it again, so toggle once
    # per occurrence rather than once per line.
    {
        line  = $0
        count = gsub(/\$\$/, "$$", line)
        for (i = 0; i < count; i++) { math = !math }
        if (count > 0 || math) { next }
    }

    # A line that is nothing but one link or image, and a table row.
    /^[[:space:]]*([*+-][[:space:]]+)?!?\[[^]]*\]\([^)]*\)[[:space:]]*[.,;:]?[[:space:]]*$/ { next }
    /^[[:space:]]*\|/ { next }

    width($0) > limit { printf "%s:%d: %d columns\n", FILENAME, FNR, width($0) }
' "${files[@]}")"

count="$({ printf '%s' "$violations" | grep -c . || true; })"

if [ "$count" -gt 0 ]; then
    printf '%s\n' "$violations" >&2
    echo >&2
    echo "error: $count line(s) over $LIMIT columns in ${#files[@]} Markdown file(s)." >&2
    exit 1
fi

# --------------------------------------------------------------------------------------------
# Dashes used as punctuation.
#
# Code spans are stripped before the test, because a hyphen inside `avr-gcc` or a minus sign
# inside an expression is not punctuation. Mathematics is stripped for the same reason, display
# blocks first: stripping the inline form first would match the empty string between the two
# dollars of a "$$" and leave the expression behind, which reports every equation as a dash.
# --------------------------------------------------------------------------------------------
dashes="$(LC_ALL=C.UTF-8 awk '
    FNR == 1 { fence = 0; math = 0 }

    /^[[:space:]]*(```|~~~)/ { fence = !fence; next }
    fence { next }
    /^[[:space:]]*\|/ { next }
    /^[[:space:]]*#/  { next }

    {
        body = $0
        sub(/^[[:space:]]*([-*+]|[0-9]+\.)[[:space:]]+/, "", body)
        gsub(/`[^`]*`/, "", body)

        copy       = body
        delimiters = gsub(/\$\$/, "&", copy)
        gsub(/\$\$[^$]*\$\$/, "", body)
        gsub(/\$[^$]*\$/, "", body)
    }

    delimiters == 1 { math = !math; next }
    math            { next }

    body ~ / -- / || body ~ /\xe2\x80\x93/ || body ~ /\xe2\x80\x94/ {
        printf "%s:%d: dash used as punctuation; use a comma, a semicolon or a full stop\n",
               FILENAME, FNR
    }
' "${files[@]}")"

dash_count="$({ printf '%s' "$dashes" | grep -c . || true; })"

if [ "$dash_count" -gt 0 ]; then
    printf '%s\n' "$dashes" >&2
    echo >&2
    echo "error: $dash_count dash(es) used as punctuation in ${#files[@]} Markdown file(s)." >&2
    exit 1
fi

echo "Markdown width: ${#files[@]} file(s), every prose line within $LIMIT columns."
echo "Markdown prose: no dash used as punctuation."
