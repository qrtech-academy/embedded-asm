# L01 Test Suite
Unit tests for everything L01 asks you to write, using the
[QAcademy Test](https://github.com/qrtech-academy/test-framework) framework.

```bash
make            # build and run
make clean      # remove the binary
```

`make test` at the repository root runs this and every later suite. Each suite is cumulative, so
L05's will still be running these tests; if work you do later breaks `shift_bits`, this is what
says so.

---

## What runs, and when
Nothing in this course requires you to switch a test on. Three files sit in this directory and
each decides for itself whether it applies.

| File | Runs when | Tests |
|---|---|---|
| `avr/device_test.cpp` | **always** | The pinned ATmega328P constants |
| `asm/utils_test.cpp` | `drivers/source/utils.asm` exists | `shift_bits` and `shift_bits_inverted`, in the simulator |
| `asm/program_test.cpp` | `drivers/app/main.asm` exists too | The whole program, run rather than called |

So the count goes **9** on a fresh clone, **18** once `utils.asm` exists, and **20** once
`main.asm` does.

There is no `#if __has_include` here, because there is no such thing for a `.asm`. The
[Makefile](./Makefile) derives a `-DHAVE_UTILS` and a `-DHAVE_APP` from the files being there
instead, and creating the file is the whole of turning its tests on.

**`avr/device_test.cpp` always runs, and that is not decoration.** `runAllTests()` returns false
when nothing is registered and prints nothing while doing it, so a suite whose every test sat
behind a guard would report red, in silence, on a fresh clone, and look broken when it was merely
empty. Something has to be here from the first day, and it may as well be the arithmetic every
driver in the course depends on: that DDRB is PINB plus one and PORTB is PINB plus two, for all
three ports.

---

## What the assembly tests check
**The values**, strictly: `shift_bits(n)` returns `1 << n`, and returns `0` at `n = 8` because
the register is eight bits wide and the bit leaves it. That last one is the answer a reader
thinking in C is least likely to predict.

**The cost**, also strictly: 6n + 10 cycles, measured. This pins the *specification's instruction
sequence*, not merely its behaviour, and it is meant to. The cross-check exercise asks you to
predict that number by hand before you run anything, and a test that
accepted any cost would have nothing to say about whether your prediction was right. If you
deliberately rewrite the routine, this is the number to update, and updating it is then a
decision rather than an accident.

`shift_bits_inverted` costs 7n + 10: one cycle per trip more, and exactly one, because of the
single extra `inc`. Two routines differing by one instruction differ in cost by that instruction
on every iteration, which is the argument for counting cycles rather than estimating them.

---

## What the program test checks, and why it is different
`asm/program_test.cpp` is the only file here that does not call anything. A subroutine has
arguments and returns a value, so a test puts a number in `r24` and reads one back; a program has
neither. It is started and it never stops, so the only question you can ask is *what did it leave
the machine looking like*, and the only way to ask it is `mcu.run(2000)` followed by a look at
the registers.

It checks that PB5 ends up an output and driven high, as two separate expectations, because they
fail for different reasons: `DDRB` alone failing is a pin with its pull-up on rather than an
output, and it is also what `sts DDRB, r16` produces, because that writes the register `r4`
instead of the port.

**It is the only suite that tests the L01 program**, and that is deliberate rather than an
oversight. `main.asm` is rewritten in L02 and again in L03, where it initialises the LED through
`led_init` and leaves it deliberately *off* so a button press can toggle it. The library only
grows, so its tests are cumulative; the program is replaced, so its tests are not.

Two mistakes L01's exercises describe are **not** tested here, because the finished state of the
machine cannot tell them apart from the right answer: writing `PORTB` before `DDRB` arrives at the
same place after one instruction of pull-up, and a program with no final loop wraps through flash
back to the reset vector and lights the LED again on the way past. Both are worth understanding
and neither is worth a test that would appear to check them.

---

## Two failures that do not mean what they look like
**`Utils.SubroutinesAreDefined` fails but the file is right there.**
`avra` exports every label, so a subroutine that exists is always callable and there is no
directive to forget. A failure here means the label is spelled differently from the name the test
asks for, or the file did not assemble at all. Check the build output above the failure.

**A cycle test reports something like 100001.** That is the harness's budget running out, which
is what an infinite loop looks like from outside. The usual cause is a loop whose exit condition
is evaluated after the counter has already passed it.

---

## Adding a test file
Add its path to `TEST_FILES` in the [Makefile](./Makefile):

```makefile
TEST_FILES := avr/device_test.cpp \
              asm/utils_test.cpp \
              asm/program_test.cpp \
              testsuite.cpp \
```

Bare paths work here because L01 is the first suite and every file it runs is its own. From L02
onwards a suite also runs the earlier lectures' files, and those are referenced through the
`$(LNN_TESTS)` variables rather than copied, so a file added to a later suite gets a prefix.

---
