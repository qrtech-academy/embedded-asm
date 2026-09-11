# L02 Test Suite
Unit tests for the LED driver L02 asks you to write, **and for the two subroutines L01 asked you
to write**, using the [QAcademy Test](https://github.com/qrtech-academy/test-framework) framework.
Nothing here tests `drivers/app/main.asm`: L01's program tests stay in L01's suite, because the
program is rewritten from L02 onwards, and L02's version of it (exercise 9) has no test.

```bash
make            # build and run
make clean      # remove the binary
```

---

## Cumulative, by reference rather than by copy
This suite runs two of L01's test files as well as its own. They are named in
[the Makefile](./Makefile) where they live, in `lectures/L01/exercises/test`, rather than copied
here: a copy would be a second thing to keep in step, and the copy is the one that goes stale.

So work you do in L02 that breaks `shift_bits` fails here, in L02, which is where you are looking.

| File | Runs when | Tests |
|---|---|---|
| `../../../L01/.../avr/device_test.cpp` | always | The ATmega328P constants |
| `../../../L01/.../asm/utils_test.cpp` | `drivers/source/utils.asm` exists | `shift_bits` |
| `avr/board_test.cpp` | **always** | The Arduino Uno pin numbering |
| `asm/led_test.cpp` | `drivers/source/led.asm` exists | The LED driver, in the simulator |

`board_test.cpp` is this suite's always-on file. Every suite has one, because `runAllTests()`
returns false when nothing is registered and prints nothing while doing it, so a suite whose every
test sat behind a guard would report red in silence on a fresh clone.

---

## What the LED tests check, and what they deliberately do not
**Behaviour, strictly.** The structure `led_init` builds, field by field, at the offsets
[`led.inc`](../../../../drivers/include/led.inc) declares. That pin 8 is bit 0. That an
out-of-range pin is refused *and* leaves the structure untouched. That driving one bit leaves the
other seven alone, checked with two LEDs on one port and with two on different ports.

**Cost, only as a relationship.** `led_on` must cost exactly six cycles more per bit, `led_off`
seven, and `led_enabled` one cycle more when the answer is yes. Nothing asserts what any of them
costs in total.

That is a change from L01, where the specification gave `shift_bits` instruction by instruction
and the test pinned 6n + 10 exactly. A driver is a bigger thing with more than one reasonable
shape, and the slope follows from what it has to do rather than from how you wrote it. The
constant does not, so it is not asserted.

---

## Three failures that do not mean what they look like
**`Led.SubroutinesAreDefined` fails but the file is right there.** A label spelled differently
from the name the test asks for; `avra` exports every label, so it is never a missing directive.

**Everything about `led_on` fails, but `led_init` passes.** Look at the order of your reads.
`shift_bits` destroys `r18`, `r19` and `r24`, so a driver that loads the port register *before*
calling it finds the mask sitting where the port contents should be. This is the most common way
to write a driver that assembles, runs, and does nothing at all.

**`Led.InitLeavesTheRestOfThePortAlone` fails on its own.** You assigned to a port register
instead of reading, modifying and writing it. With one LED nothing looks wrong; the test sets two
other bits of `DDRB` first for exactly this reason.

---

## Adding a test file
Add its path to `TEST_FILES` in [the Makefile](./Makefile).

---
