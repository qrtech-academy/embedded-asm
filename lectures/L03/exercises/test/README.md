# L03 Test Suite
Unit tests for everything L03 asks you to write, **and everything L01 and L02 asked you to
write**, using the [QAcademy Test](https://github.com/qrtech-academy/test-framework) framework.

```bash
make            # build and run
make clean      # remove the binary
```

---

## Cumulative, by reference rather than by copy
This suite names L01's and L02's test files where they live rather than copying them, so work you
do here that breaks `shift_bits` or the LED driver fails in L03, where you are looking.

| File | Runs when | Tests |
|---|---|---|
| L01's files | see [L01's README](../../../L01/exercises/test/README.md) | the core's constants and `utils.asm` |
| L02's files | see [L02's README](../../../L02/exercises/test/README.md) | the board's pin numbering and `led.asm` |
| `avr/vector_data_test.cpp` | **always** | The 26 vector numbers, and slot arithmetic |
| `asm/btn_test.cpp` | `drivers/source/btn.asm` exists | The button driver, in the simulator |
| `asm/app_test.cpp` | `drivers/app/` holds a program, **and** `btn.asm` exists | The whole program, running on its own |

`vector_data_test.cpp` is this suite's always-on file.

---

## Two tests that exist because of two specific mistakes
Most of the button tests check behaviour you would think to check yourself. Two do not, and both
catch code that assembles, runs, and looks entirely reasonable.

**`Btn.InterruptEnabledReportsTheTruth`** catches a `btn_interrupt_enabled` that returns 1
and 0 the wrong way round. The branch is there and both constants are there and they are swapped.
It is caught here, but it *surfaces* in `Btn.ToggleAlternates`, because a toggle built on an
inverted answer stops toggling and starts latching. A failure two steps from its cause is the
expensive kind, which is why both tests exist rather than just the first.

**`Btn.DisablingOneButtonLeavesAnother`** catches a `btn_disable_interrupt` that writes the mask
register instead of clearing one bit of it. With one button, clearing the whole register and
clearing only that button's bit are indistinguishable from outside, so the test needs two. A
disable that shifts by the wrong field of the structure, offset 0 where offset 9 belongs, is caught
sooner: its mask is zero, it clears nothing, and `Btn.DisableClearsOnlyTheMaskBit` sees the bit
still set.

---

## The one test that cannot call anything
Every other assembly test in this course calls one subroutine and looks at what came back.
`app_test.cpp` cannot, because **an interrupt is not something you can call.** It arrives, or it
does not. So that file loads `app.hex`, lets it run, changes a pin from outside, and watches what
the program does about it.

That is the only way to test four things, and all four are wrong in real programs:

* the vector table entry actually points at your handler,
* `sei` ran, and ran after the structures were built,
* the handler asks the button whether it is pressed rather than toggling on both edges,
* and the handler ends with `reti` rather than `ret`.

The last one is worth its own sentence. A handler ending in `ret` returns to exactly the right
place and passes every other test in this file: **the first press works perfectly.** What `ret`
does not do is set the global interrupt enable again, so nothing is ever served afterwards.
`App.TheSecondPressStillArrives` is the test that notices, and when the handler is wrong it is the
only one that fails.

What is deliberately not in that file is a cycle count. From L02 onwards these suites check the
relationships a specification forces and leave the constants alone, and your handler saves the
registers your handler uses. Measuring it is the next section's job.

**A press produces two interrupts here**, one per edge, because nothing holds the pin down after
the test lets go and the pull-up takes it back up. That is not the simulator being unrealistic; it
is [C.7](../../appendix/c_button_driver.md#c7-what-this-driver-does-not-do) arriving early.

---

## Measuring a handler
`make measure` reaches into your program as well as your driver library:

```bash
make measure IMAGE=app CALLS="led_init:0x0200:13 btn_init:0x0240:12 --drive B4=0 isr_pcint0"
```

`IMAGE=app` loads `app.hex`, because a handler lives in your program. `--drive B4=0` holds the
button's pin low, which is a press. Calling a handler directly works because `reti` pops a return
address exactly as `ret` does, even though nothing ever calls one for real.

---

## Adding a test file
Add its path to `TEST_FILES` in [the Makefile](./Makefile).

---
