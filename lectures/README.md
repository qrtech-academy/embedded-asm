# Lecture Material
The following material is covered in the lectures. An entry becomes a link once that lecture has
been written; an unlinked entry is a lecture that does not exist yet, which is different from one
you have not read.

* [L01](./L01/README.md): The AVR core and the toolchain - the register file, SREG, the three
  memory spaces, instruction encoding, cycle counts, and a first program that assembles, runs in
  the simulator and lights an LED.
* [L02](./L02/README.md): I/O ports and subroutines - `DDRx`, `PORTx` and `PINx`, the internal
  pull-up, the AVR calling contract, and the LED driver.
* [L03](./L03/README.md): Interrupts - the vector table, pin change interrupts, what the hardware
  saves and what it does not, atomicity, latency, and the button driver.
* [L04](./L04/README.md): Pointers, arrays and structs in SRAM - `X`, `Y` and `Z`, displacement
  addressing, the stack, and driver structs passed by reference.
* [L05](./L05/README.md): Timers - prescalers, CTC and overflow, the arithmetic of a period the
  hardware cannot express exactly, and an interrupt-driven blinker that keeps real time.
* [L06](./L06/README.md): Watchdog, sleep, and the C ABI - the timed write sequence, sleep modes,
  and calling assembly from C and C from assembly.

---

## How a lecture is laid out
Every lecture directory holds the same three things:

```text
lectures/LNN/
├── README.md            What the lecture covers, what to read before it and do after it.
├── appendix/            The material itself, plus the exercises and their solutions.
└── exercises/test/      The test suite for everything written up to and including this lecture.
```

**The appendices carry the material.** The lecture README is a map; the appendices are the
territory. Read them in order.

**The appendix letters follow one rule, and it holds in every lecture of this course.** The
theory appendices come first, as many letters as the material needs. Then, always:

* the **second-to-last** appendix is the **exercises**, and
* the **last** appendix is the **worked solutions**.

So a lecture with three theory appendices runs A, B, C, then D for the exercises and E for the
solutions; a lecture with one theory appendix runs A, then B and C. You can always find the
exercises and the answers by counting backwards from the end, without reading the titles.
`ci/check.sh` enforces this rather than trusting it.

**Until a lecture has been given, its last appendix is missing.** The solutions go out after the
lecture rather than with it, so a lecture you are reading ahead of ends with the exercises and
the letter after them is not there yet. `ci/check.sh` accepts both shapes and says which one it
found, so a solutions appendix that is merely unpublished never reads like one that was
forgotten.

**`ci/check.sh` enforces twelve rules, not one.** The appendix-letter rule above is the one worth
stating in prose; these are the rest, listed here because a rule nobody has written down is a rule
that fails at the worst moment:

| Rule | What it wants |
|---|---|
| Layout | Every `lectures/LNN/` holds `README.md`, `appendix/` and `exercises/test/Makefile`. |
| Title | The README's first line is exactly `# LNN - Title`, with a hyphen: not an en dash, not a colon. |
| Sections | The eight `##` sections, in order. The last lecture may close with `## After the course` in place of `## Next lecture`, and no other substitution is allowed. |
| Closing rule | The README's last line is `---`. |
| Always-on tests | Every suite has at least one `TEST(` outside every `#if`, because `runAllTests()` reports red, silently, when nothing is registered. |
| Figures | Every committed PNG is embedded by some Markdown, and every image carries at least 25 characters of alt text. |
| Suite variables | Every suite Makefile assigns `ROOT_DIR` and `QACADEMY_TEST_DIR`. |
| Assembler dialect | No GNU `as` syntax outside L06, which is the one lecture that writes both, and the second exam paper. A line that names GNU on the same line is contrast rather than instruction, and passes. |
| Structure offsets | Every `.equ` in `drivers/include/*.inc` matches its counterpart in `device/include/avr/drivers.hpp`, by name and by value. Two copies of a layout is what drifts, and this pair drifts silently. |
| Symbol collisions | No subroutine the suites resolve shares a name with an `.equ` constant. `avra`'s symbol table is case-insensitive, so `timer_tick` and `TIMER_TICK` would be one symbol and the file would not assemble. |
| Section rules | Every `##` is preceded by a `---`, except one sitting directly under the document's own `#` title, where there is no earlier section to separate it from. |

A suite deliberately left behind at an older lecture opts out of `make test` by setting
`FROZEN = 1` in its Makefile, rather than by being deleted. `ci/test.sh` reports it as a `SKIP`
line with its name on it, which is the point: a suite that stopped running should say so.

---

**The solutions are published, in full, once the lecture has been given.** This is a self-study
course, and a reader with nobody to ask cannot be left with an exercise nobody answers. But an
answer that arrives before the attempt is worth less than one that arrives after it, so the
solutions appendix follows its lecture rather than shipping alongside it. Where an exercise has a
plausible wrong answer, the solution gives that too, and says why it is wrong.

---

## What the exercises look like
There are six to ten exercises per lecture, and each one is labelled with its kind:

| Kind | What it asks of you |
|---|---|
| **Recall** | State something from the appendix, in your own words. No tools. |
| **Hand calculation** | Work a number out on paper, from the datasheet and the instruction set summary. |
| **Design** | Decide something before writing it: a register allocation, a struct layout, a prescaler. |
| **Code** | Write assembly. Checked by that lecture's test suite, in the simulator. |
| **Cross-check** | Exactly one per lecture. See below. |

**The Cross-check is the signature exercise of this course.** You compute a number by hand, you
run your own code on the same problem, and you reconcile the two. Its solution says how large a
discrepancy to expect and where it comes from, because "your two answers differ by 8%" is the
lesson, not a sign that you did it wrong. Some of these discrepancies close to zero and some do
not, and knowing which is which is most of what separates an engineer who can time a routine from
one who assumes the datasheet did it for them.

---
