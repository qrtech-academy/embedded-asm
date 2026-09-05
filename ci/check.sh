#!/usr/bin/env bash
#
# Check the course's own conventions, which nothing else can check.
#
# ci/links.sh checks that a link resolves and ci/markdown.sh checks how wide a line is. Neither
# knows what a lecture is supposed to look like. These do:
#
#   1. Every lecture has a README and an appendix directory.
#   2. Every lecture README carries the eight sections, in order, and ends with a rule.
#   3. Appendix letters run contiguously from a, the exercises appendix is second-to-last, and
#      the solutions appendix is last. That rule is stated once in lectures/README.md; this is
#      what makes it true rather than aspirational.
#   4. Every test suite ships at least one always-on test. This is the important one.
#      qacademy::test::runAllTests() returns false when nothing is registered and prints nothing
#      while doing it, so a suite whose every test sits behind an #if guard reports red, in
#      silence, before the reader has written a line. A suite like that looks broken and is not.
#   5. Every test suite Makefile defines the variables ci/test.sh overrides. Grepped as an
#      assignment rather than as a bare word, because a Makefile that merely mentions ROOT_DIR
#      in a comment would satisfy a looser pattern and then ignore what CI passes it.
#   6. Every committed figure is referenced by some Markdown file, and every image reference
#      carries alt text long enough to be a description rather than a filename. A figure nobody
#      embeds is a figure nobody has looked at since it went stale.
#
# Everything here is skipped loudly when the thing it checks does not exist yet, and says so by
# name. A check that silently did not run must never read like one that passed.
#
# Usage:
#   ci/check.sh
set -euo pipefail
shopt -s nullglob globstar

# Absolute path to the repo root, resolved before the cd below.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# The section set of a lecture README, in the order they must appear. Taken from the digital
# design course's L03, which is the shape every lecture in this course follows.
SECTIONS=(
    "## Agenda"
    "## Lecture plan"
    "## Before the lecture"
    "## After the lecture"
    "## What you should be able to do afterwards"
    "## Questions to test yourself"
    "## Reference"
    "## Next lecture"
)

# Variables ci/test.sh passes into every suite Makefile.
SUITE_VARS=(ROOT_DIR QACADEMY_TEST_DIR)

# Shortest alt text that can plausibly describe a figure rather than name it.
MIN_ALT_TEXT=25

problems=0
checked=0

# Failures recorded since the last reset, so that a subject which failed anything is never also
# reported as having passed. Getting this wrong makes a broken check read like a working one,
# which is the single failure mode this whole script exists to prevent.
local_failures=0

reset_local() { local_failures=0; }
fail() { echo "FAIL  $1" >&2; problems=$((problems + 1)); local_failures=$((local_failures + 1)); }
pass_if_clean() { [ "$local_failures" -eq 0 ] && pass "$1"; return 0; }
pass() { echo "ok    $1"; checked=$((checked + 1)); }
skip() { echo "SKIP  $1"; }

# --------------------------------------------------------------------------------------------
# 1 and 2: lecture layout and README section set.
# --------------------------------------------------------------------------------------------
# A lecture directory holding figures but no prose is a lecture whose figures were drawn
# first, which is the order this course is built in: prose written before its figures gets
# rewritten around them. Such a directory is reported as staged rather than checked, because
# every rule below is about prose that does not exist yet. The moment any Markdown appears,
# the full check applies and nothing has to be remembered.
staged() {
    [ ! -f "$1/README.md" ] && [ -z "$(echo "$1"/appendix/*.md)" ]
}

lectures=(lectures/L[0-9][0-9])
if [ ${#lectures[@]} -eq 0 ]; then
    skip "lecture layout: no lectures/LNN directories yet."
else
    for lecture in "${lectures[@]}"; do
        name="$(basename "$lecture")"
        readme="$lecture/README.md"
        reset_local

        if staged "$lecture"; then
            figures=("$lecture"/appendix/images/*.png)
            skip "$name: ${#figures[@]} figure(s) drawn, no prose written yet."
            continue
        fi

        if [ ! -f "$readme" ]; then
            fail "$name has no README.md"
            continue
        fi
        [ -d "$lecture/appendix" ] || fail "$name has no appendix/ directory"

        # The third of the three things lectures/README.md says every lecture holds. Checked per
        # lecture rather than across all of them: rule 4 below only notices when *no* lecture has
        # a suite, and ci/test.sh's glob simply passes over a lecture that lacks one, so without
        # this a suite-less lecture is invisible to both.
        [ -f "$lecture/exercises/test/Makefile" ] \
            || fail "$name has no exercises/test/Makefile"

        # The title carries a hyphen, not an en dash or a colon.
        head -n 1 "$readme" | grep -qE "^# $name - .+" \
            || fail "$name README.md line 1 is not '# $name - Title'"

        # The eight sections, in order. Walking one cursor through the file is what makes this
        # check the order as well as the presence: a section that appears but out of order finds
        # no match from where the cursor already is.
        cursor=0
        for section in "${SECTIONS[@]}"; do
            # The last lecture has no next lecture, so it closes with '## After the course'
            # instead. That is the one substitution allowed anywhere in the section set, and it
            # is allowed only for the final heading: a lecture that skipped 'Next lecture' in
            # the middle of the course would leave the reader with no thread to the next one.
            wanted="$section"
            if [ "$section" = "## Next lecture" ] \
                && grep -qxF "## After the course" "$readme"; then
                wanted="## After the course"
            fi

            line="$({ grep -nxF "$wanted" "$readme" || true; } | cut -d: -f1 | head -n 1)"
            if [ -z "$line" ]; then
                fail "$name README.md is missing the section '$section'"
            elif [ "$line" -lt "$cursor" ]; then
                fail "$name README.md has '$wanted' out of order"
            else
                cursor="$line"
            fi
        done

        # A rule closes the file.
        [ "$(tail -n 1 "$readme")" = "---" ] || fail "$name README.md does not end with '---'"

        pass_if_clean "$name README.md"
    done
fi

# --------------------------------------------------------------------------------------------
# 3: appendix letters.
# --------------------------------------------------------------------------------------------
for lecture in "${lectures[@]}"; do
    name="$(basename "$lecture")"
    staged "$lecture" && continue
    appendices=("$lecture"/appendix/[a-z]_*.md)
    if [ ${#appendices[@]} -eq 0 ]; then
        skip "$name appendix letters: no appendix files yet."
        continue
    fi

    # Anything in appendix/ that is not <letter>_<name>.md is invisible to the glob above, so the
    # contiguity rule would be checked against a filtered list and a stray file would pass by not
    # being looked at. Name the strays instead.
    all_appendices=("$lecture"/appendix/*.md)
    if [ ${#all_appendices[@]} -ne ${#appendices[@]} ]; then
        for candidate in "${all_appendices[@]}"; do
            case "$(basename "$candidate")" in
                [a-z]_*.md) ;;
                *) fail "$name: $(basename "$candidate") is not named <letter>_<name>.md" ;;
            esac
        done
    fi

    expected=({a..z})
    if [ ${#appendices[@]} -gt ${#expected[@]} ]; then
        fail "$name has ${#appendices[@]} appendices; the letters run out at ${#expected[@]}"
        continue
    fi

    index=0
    ok=1
    for appendix in "${appendices[@]}"; do
        letter="$(basename "$appendix")"
        letter="${letter:0:1}"
        if [ "$letter" != "${expected[$index]}" ]; then
            fail "$name appendix letters are not contiguous: expected ${expected[$index]}_*.md, found $(basename "$appendix")"
            ok=0
            break
        fi
        index=$((index + 1))
    done

    # The solutions appendix is published after its lecture rather than with it, so a lecture
    # ends either with exercises-then-solutions or with the exercises alone. Both are correct,
    # and the difference is reported rather than tolerated silently: a lecture whose solutions
    # went out is a different state from one whose solutions are still held back, and a check
    # that printed the same line for both would be no help in telling them apart.
    published=0
    if [ "$ok" -eq 1 ]; then
        last="$(basename "${appendices[-1]}")"
        case "$last" in
            *solutions*.md) published=1 ;;
            *exercises*.md) published=0 ;;
            *) fail "$name: the last appendix must be the exercises or the solutions, found $last"
               ok=0 ;;
        esac
    fi
    if [ "$ok" -eq 1 ] && [ "$published" -eq 1 ] && [ ${#appendices[@]} -ge 2 ]; then
        second_last="$(basename "${appendices[-2]}")"
        case "$second_last" in
            *exercises*.md) ;;
            *) fail "$name: the second-to-last appendix must be the exercises appendix, found $second_last"; ok=0 ;;
        esac
    fi
    if [ "$ok" -eq 1 ]; then
        if [ "$published" -eq 1 ]; then
            pass "$name appendix letters (${#appendices[@]} appendices, solutions published)"
        else
            pass "$name appendix letters (${#appendices[@]} appendices, solutions not published)"
        fi
    fi
done

# --------------------------------------------------------------------------------------------
# 4 and 5: test suites.
# --------------------------------------------------------------------------------------------
suites=(lectures/*/exercises/test)
if [ ${#suites[@]} -eq 0 ]; then
    skip "test suites: none exist yet."
else
    for suite in "${suites[@]}"; do
        # An always-on test is one whose TEST( sits at conditional-compilation depth zero.
        # Counting the guards rather than looking for them is what tells a guarded suite apart
        # from one that merely mentions #if somewhere below its always-on cases.
        # Collected first, because with nullglob a suite that has only a Makefile expands to no
        # file arguments at all, and awk with no files reads standard input: `make check` would
        # block on a terminal rather than report anything.
        sources=("$suite"/**/*.cpp)
        if [ ${#sources[@]} -eq 0 ]; then
            skip "$suite: no test sources yet."
            continue
        fi

        # depth is reset per file so that an unbalanced #if in one cannot suppress counting in
        # every file after it.
        always_on="$(awk '
            FNR == 1 { depth = 0 }
            /^[[:space:]]*#[[:space:]]*(if|ifdef|ifndef)([^[:alnum:]_]|$)/ { depth++; next }
            /^[[:space:]]*#[[:space:]]*endif([^[:alnum:]_]|$)/ { if (depth > 0) depth--; next }
            depth == 0 && /^[[:space:]]*TEST[[:space:]]*\(/ { count++ }
            END { print count + 0 }
        ' "${sources[@]}")"

        if [ "${always_on:-0}" -eq 0 ]; then
            fail "$suite has no always-on test: runAllTests() will report red in silence"
        else
            pass "$suite ($always_on always-on test case(s))"
        fi

        makefile="$suite/Makefile"
        if [ ! -f "$makefile" ]; then
            fail "$suite has no Makefile"
            continue
        fi
        for var in "${SUITE_VARS[@]}"; do
            grep -qE "^ *$var *[?:]?=" "$makefile" \
                || fail "$suite/Makefile does not assign $var, which ci/test.sh overrides"
        done
    done
fi

# --------------------------------------------------------------------------------------------
# 6: figures are embedded, and their alt text describes them.
# --------------------------------------------------------------------------------------------
figures=(lectures/*/appendix/images/*.png info/images/*.png)
markdown=()
for file in **/*.md; do
    case "$file" in libs/*|.venv/*) continue ;; esac
    markdown+=("$file")
done

if [ ${#figures[@]} -eq 0 ]; then
    skip "figures: none committed yet."
elif [ ${#markdown[@]} -eq 0 ]; then
    skip "figures: no Markdown to check them against yet."
else
    unembedded=0
    for figure in "${figures[@]}"; do
        # A figure belonging to a lecture whose prose is not written yet is staged, not
        # orphaned, and counted rather than reported one line at a time.
        lecture="${figure%/appendix/images/*}"
        if [ "$lecture" != "$figure" ] && staged "$lecture"; then
            unembedded=$((unembedded + 1))
            continue
        fi
        base="$(basename "$figure")"
        # Allowed to match nothing: an unembedded figure is exactly what this looks for.
        hits="$({ grep -lF "$base" "${markdown[@]}" || true; })"
        [ -n "$hits" ] || fail "$figure is committed but no Markdown embeds it"
    done
    [ "$unembedded" -eq 0 ] && checked_figures=${#figures[@]} \
        || skip "figures: $unembedded of ${#figures[@]} await the prose that will embed them."

    # Alt text, from every image reference in the course.
    short="$(awk '
        {
            line = $0
            while (match(line, /!\[[^]]*\]\(/)) {
                alt = substr(line, RSTART + 2, RLENGTH - 4)
                if (length(alt) < min) { printf "%s:%d: alt text \"%s\"\n", FILENAME, FNR, alt }
                line = substr(line, RSTART + RLENGTH)
            }
        }
    ' min="$MIN_ALT_TEXT" "${markdown[@]}")"

    if [ -n "$short" ]; then
        printf '%s\n' "$short" >&2
        fail "image alt text shorter than $MIN_ALT_TEXT characters; describe the figure, do not name it"
    elif [ "${checked_figures:-0}" -gt 0 ]; then
        pass "figures ($checked_figures committed, all embedded, all with descriptive alt text)"
    fi
fi

# --------------------------------------------------------------------------------------------
# 7: the assembler dialect.
#
# This course was converted from GNU `as` to AVRASM2, and a conversion like that does not fail
# loudly. What it leaves behind is prose telling the reader to write something `avra` will not
# assemble: `lo8(RAMEND)` in the first program, `#include "led.inc"` where `.include` is meant,
# `.bss` in an assembler that has no sections. Every one of those reads perfectly well, passes
# every other check in this file, and stops the reader at the first thing they type.
#
# So the tokens that can only be GNU are named here, and the files allowed to contain them are
# named too. The allow list is short on purpose: L06 is the one lecture that legitimately writes
# both dialects, and everything else in the course has exactly one.
# --------------------------------------------------------------------------------------------
GNU_TOKENS='lo8\(|hi8\(|\.bss|\.section|\.globl?\b|#include "'

# A line that names the other toolchain is discussing it rather than instructing you to use it.
# "`low()` and `high()` are AVRASM2's; GNU `as` spells them `lo8()` and `hi8()`" is the sentence
# this course wants, and the sentence a bare token search cannot tell from a mistake. Naming the
# other dialect on the same line is the signal, and it costs an author one word to give.
GNU_CONTRAST='GNU|avr-gcc|avr-libc|C program|C runtime|C compiler'

# Files that teach the GNU dialect on purpose, or name a GNU token while contrasting the two.
gnu_allowed() {
    case "$1" in
        lectures/L06/appendix/c_c_abi.md) return 0 ;;
        lectures/L06/appendix/d_what_to_build.md) return 0 ;;
        lectures/L06/appendix/e_exercises.md) return 0 ;;
        lectures/L06/appendix/f_solutions.md) return 0 ;;
        lectures/L06/exercises/test/README.md) return 0 ;;
        exam/paper_2.md|exam/paper_2_solutions.md) return 0 ;;
        device/README.md) return 0 ;;
        ci/check.sh) return 0 ;;
    esac
    return 1
}

dialect_files=()
for candidate in **/*.md **/*.inc drivers/source/*.asm drivers/app/*.asm; do
    case "$candidate" in
        libs/*|.venv/*|tools/avrsim/*) continue ;;
    esac
    gnu_allowed "$candidate" && continue
    dialect_files+=("$candidate")
done

if [ ${#dialect_files[@]} -eq 0 ]; then
    skip "assembler dialect: no Markdown or assembly to check yet."
else
    leftovers="$({ grep -nE "$GNU_TOKENS" "${dialect_files[@]}" \
                     | { grep -vE "$GNU_CONTRAST" || true; } || true; })"
    if [ -n "$leftovers" ]; then
        printf '%s\n' "$leftovers" >&2
        fail "GNU as syntax outside the files that teach it; this course assembles with avra"
    else
        pass "assembler dialect (${#dialect_files[@]} file(s), no unexplained GNU as syntax)"
    fi
fi

# --------------------------------------------------------------------------------------------
# 8: the structure offsets, in both languages.
#
# Every driver structure's layout is written down twice: as .equ constants in drivers/include
# for the assembly, and as constants in device/include/avr/drivers.hpp for the tests that read a
# structure out of the simulator. Two copies of a set of numbers is exactly what drifts, and this
# pair drifts silently: the always-on suite checks that the C++ copy is internally consistent, so
# renaming a field or swapping two offsets in the .inc leaves every test passing and every test
# reading the wrong bytes.
#
# So the two are compared here, by name. LED_PIN_REG must equal LedPinReg, BTN_SIZE must equal
# BtnSize: the .inc's SNAKE_CASE with the underscores removed and each word capitalised. A
# constant present in one and missing from the other is reported too, because that is what a
# rename looks like from this side.
# --------------------------------------------------------------------------------------------
offsets_header="device/include/avr/drivers.hpp"
inc_files=(drivers/include/*.inc)

if [ ${#inc_files[@]} -eq 0 ] || [ ! -f "$offsets_header" ]; then
    skip "structure offsets: nothing to compare yet."
else
    mismatches="$(awk '
        # The .inc side: NAME = value, skipping the include guards.
        FILENAME ~ /\.inc$/ && /^[[:space:]]*\.equ/ {
            name = $2; value = $4
            if (name ~ /_INC$/) { next }
            gsub(/[^0-9].*$/, "", value)
            split(tolower(name), parts, "_")
            camel = ""
            for (i in parts) { }
            n = split(tolower(name), parts, "_")
            for (i = 1; i <= n; i++) {
                camel = camel toupper(substr(parts[i], 1, 1)) substr(parts[i], 2)
            }
            asm_value[camel] = value
            asm_name[camel] = name
            next
        }
        # The C++ side: inline constexpr std::uint16_t Name{value};
        FILENAME ~ /\.hpp$/ && /^inline constexpr std::uint16_t/ {
            name = $4
            sub(/\{.*$/, "", name)
            value = $4
            sub(/^[^{]*\{/, "", value); sub(/U?\};?$/, "", value)
            cpp_value[name] = value
            next
        }
        END {
            for (k in asm_value) {
                if (!(k in cpp_value)) {
                    printf "  %s is in the .inc but %s is not in drivers.hpp\n", asm_name[k], k
                } else if (asm_value[k] != cpp_value[k]) {
                    printf "  %s is %s but %s is %s\n", asm_name[k], asm_value[k], k, cpp_value[k]
                }
            }
        }
    ' "${inc_files[@]}" "$offsets_header")"

    if [ -n "$mismatches" ]; then
        printf '%s\n' "$mismatches" >&2
        fail "structure offsets disagree between drivers/include and $offsets_header"
    else
        pass "structure offsets (${#inc_files[@]} .inc file(s) agree with drivers.hpp)"
    fi
fi

# --------------------------------------------------------------------------------------------
# 9: labels that collide with constants.
#
# avra's symbol table is case-insensitive, so a subroutine called timer_count and an .equ called
# TIMER_COUNT are the same symbol, and a source that defines both does not assemble:
#
#     timer_count has already been defined as a .EQU constant
#
# That is a good error message and a terrible place to meet it, because the reader meets it after
# writing a whole driver to a specification that named both. The names are ours, they are in two
# different files, and nothing else brings them together until an assembler does. So they are
# brought together here instead.
#
# The subroutine names come from the test suites, which resolve them by name and are therefore
# the authority on what the reader has to call things.
# --------------------------------------------------------------------------------------------
inc_files=(drivers/include/*.inc)
asm_tests=(lectures/*/exercises/test/asm/*.cpp)

if [ ${#inc_files[@]} -eq 0 ] || [ ${#asm_tests[@]} -eq 0 ]; then
    skip "symbol collisions: nothing to compare yet."
else
    collisions="$(awk '
        FILENAME ~ /\.inc$/ && /^[[:space:]]*\.equ/ {
            name = $2
            if (name !~ /_INC$/) { constant[tolower(name)] = name }
            next
        }
        FILENAME ~ /\.cpp$/ {
            line = $0
            while (match(line, /"[a-z][a-z0-9_]*_[a-z0-9_]+"/)) {
                sym = substr(line, RSTART + 1, RLENGTH - 2)
                seen[sym] = 1
                line = substr(line, RSTART + RLENGTH)
            }
            next
        }
        END {
            for (s in seen) {
                if (tolower(s) in constant) {
                    printf "  the subroutine %s and the constant %s are one symbol to avra\n", \
                           s, constant[tolower(s)]
                }
            }
        }
    ' "${inc_files[@]}" "${asm_tests[@]}")"

    if [ -n "$collisions" ]; then
        printf '%s\n' "$collisions" >&2
        fail "a subroutine name collides with an .equ constant; avra is case-insensitive"
    else
        pass "symbol collisions (no subroutine name matches an .equ constant)"
    fi
fi

# --------------------------------------------------------------------------------------------
# 10: a horizontal rule before every ## section.
#
# The course's Markdown separates sections with a --- rule, and the rule is what makes a long
# appendix scannable: a reader flicking through sees where one section stops rather than a wall
# of headings at the same weight.
#
# The exception is a ## that sits directly under the document's own # title, where there is no
# preceding section to separate it from. Every other one gets a rule, and a fence's contents are
# skipped so that a ## inside a code block is not mistaken for a heading.
# --------------------------------------------------------------------------------------------
markdown_files=()
for candidate in **/*.md; do
    case "$candidate" in
        libs/*|.venv/*|tools/*) continue ;;
    esac
    markdown_files+=("$candidate")
done

if [ ${#markdown_files[@]} -eq 0 ]; then
    skip "section rules: no Markdown yet."
else
    unruled="$(awk '
        FNR == 1 { fence = 0; seen_content = 0 }
        /^[[:space:]]*(```|~~~)/ { fence = !fence; prev2 = prev1; prev1 = $0; next }
        fence { prev2 = prev1; prev1 = $0; next }
        /^## / {
            # A ## directly under the document title has nothing to separate it from.
            if (seen_content > 1 && !(prev1 == "" && prev2 ~ /^-{3,}[[:space:]]*$/)) {
                printf "  %s:%d: %s\n", FILENAME, FNR, $0
            }
            seen_content++
            prev2 = prev1; prev1 = $0
            next
        }
        { if ($0 !~ /^[[:space:]]*$/) { seen_content++ } ; prev2 = prev1; prev1 = $0 }
    ' "${markdown_files[@]}")"

    if [ -n "$unruled" ]; then
        printf '%s\n' "$unruled" >&2
        fail "a ## section is not preceded by a --- rule"
    else
        pass "section rules (${#markdown_files[@]} file(s), every ## preceded by a rule)"
    fi
fi

echo
if [ "$problems" -gt 0 ]; then
    echo "error: $problems convention problem(s); $checked check(s) passed." >&2
    exit 1
fi
echo "Conventions: $checked check(s) passed."
