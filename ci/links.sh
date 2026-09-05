#!/usr/bin/env bash
#
# Check that every relative Markdown link resolves: the file exists, and where the link
# carries a #fragment, some heading in that file generates the matching anchor.
#
# The course is a web of cross-references between lecture READMEs, appendices and exercise
# directories, so renaming one file silently breaks links in three others.
#
# External http(s) links are not fetched: this runs offline and should not go stale because
# somebody else's site is down.
#
# Usage:
#   links.sh
set -euo pipefail
shopt -s nullglob globstar

# Navigate to the root directory.
cd "$(dirname "${BASH_SOURCE[0]}")/.."

# GitHub's anchor rules: lowercase, strip anything that is not a word character, a space or a
# hyphen, then turn spaces into hyphens.
anchor_of() {
    printf '%s' "$1" \
        | tr '[:upper:]' '[:lower:]' \
        | sed -e 's/[^a-z0-9 _-]//g' -e 's/ /-/g'
}

checked=0
broken=0

for file in **/*.md; do
    # The submodule brings its own Markdown and .venv holds installed packages, so neither is
    # ours to check. Without this, one `pip install` of a package whose README has a relative
    # link breaks `make links` on a file this repository does not own.
    case "$file" in
        libs/*|.venv/*) continue ;;
    esac

    # Links are relative to the file that contains them, not to the repo root.
    dir="$(dirname "$file")"

    # Pull the target out of every inline [text](target) link.
    while IFS= read -r target; do
        # Skip external links and mailto:. A bare in-page fragment is not skipped: it names a
        # heading in this same file, which goes stale the moment that heading is reworded.
        case "$target" in
            http://*|https://*|mailto:*|'') continue ;;
        esac

        # Split "path#fragment". With no "#", the second expansion returns the whole string,
        # which is how a fragment-less link is told apart from one with an empty fragment.
        path="${target%%\#*}"
        fragment="${target#*\#}"
        [ "$fragment" = "$target" ] && fragment=""

        checked=$((checked + 1))

        # An empty path is a bare "#fragment": the target is the file the link is written in.
        if [ -z "$path" ]; then
            resolved="$file"
        else
            resolved="$dir/$path"
        fi
        if [ ! -e "$resolved" ]; then
            echo "BROKEN $file -> $target (no such file: $resolved)" >&2
            broken=$((broken + 1))
            continue
        fi

        # Where the link names a heading, check that some heading generates that anchor.
        if [ -n "$fragment" ] && [ -f "$resolved" ]; then
            found=0
            while IFS= read -r heading; do
                if [ "$(anchor_of "$heading")" = "$fragment" ]; then
                    found=1
                    break
                fi
            # Every ATX heading in the target file, with its leading #s stripped. Lines inside a
            # fenced code block are skipped: a shell or YAML comment there starts with a # too,
            # and counting it as a heading would let a broken anchor resolve against a listing.
            done < <(awk '/^[[:space:]]*```/ { fence = !fence; next }
                          !fence && /^#{1,6} / { sub(/^#{1,6} +/, ""); print }' "$resolved")
            if [ "$found" -eq 0 ]; then
                echo "BROKEN $file -> $target (no heading matching #$fragment)" >&2
                broken=$((broken + 1))
            fi
        fi
    # Every inline link target in the file: match "](...)", then strip the delimiters. Reference
    # -style links are not used in this course, so the inline form is the whole of it.
    #
    # Fenced code blocks are skipped, the same way the heading scan above skips them: a listing
    # that happens to contain "](" is not a link, and checking it would report a broken target
    # for something nobody can click. A target containing a literal ')' would also be cut short
    # here; none exists in this course, and one would show up as a broken link rather than as a
    # silent pass.
    done < <(awk '/^[[:space:]]*(```|~~~)/ { fence = !fence; next } !fence' "$file" \
             | grep -oE '\]\([^)]+\)' | sed -e 's/^](//' -e 's/)$//')
done

if [ "$broken" -gt 0 ]; then
    echo >&2
    echo "error: $broken broken link(s) out of $checked checked." >&2
    exit 1
fi

echo "Link check: $checked relative link(s) resolve."
