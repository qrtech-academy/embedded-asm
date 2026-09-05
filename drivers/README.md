# The Driver Library
Your AVR assembly, grown one lecture at a time. This directory ships the build, the contracts
and nothing else: every subroutine in it is yours to write.

```text
drivers/
├── include/     Shared .inc files: struct offsets and the constants tests agree on. Ours.
├── source/      The subroutines. Yours. utils.asm in L01, then led.asm, btn.asm, led_array.asm...
├── app/         The program that composes them, with a vector table and a main loop. Yours.
└── build/       Assembled output. Generated, never committed.
```

---

## Two images, for two different jobs
`make build` produces both, and they exist for different reasons.

**`build/drivers.hex`** is the subroutines alone, with no vector table and no reset vector.
Nothing ever runs it from the start. The unit tests set the program counter straight to a symbol
and call one subroutine at a time, which is the only way to test a driver in isolation on a
machine that has no notion of doing so. This is the image nearly every test loads.

**`build/app.hex`** is `app/main.asm` assembled together with those same subroutines: a whole
program, with a vector table and a main loop. L03's integration test, `app_test.cpp`, loads this
one and lets it run, because an interrupt cannot be called; it has to arrive.

Each has a `.map` beside it, written by the same `avra` run, and the two are read together: the hex
is the program and the map is the names.

---

## The file name is the switch
A test for a subroutine you have not written cannot compile. In C++ that is solved by
`#if __has_include`, which needs nothing from a build system. Assembly has no equivalent, so
each lecture's test makefile derives one `-DHAVE_<NAME>` per `.asm` file it finds here:

```text
drivers/source/utils.asm   ->  -DHAVE_UTILS    switches on asm/utils_test.cpp
drivers/source/led.asm     ->  -DHAVE_LED      switches on asm/led_test.cpp
```

So the file name matters, and creating the file is the whole of turning its tests on. There is no
list to edit anywhere, and no way to forget.

---

## What is not here
Nothing you write is committed. `.gitignore` ignores `source/*.asm` and `app/*.asm` outright, so
solving an exercise and running `git add -A` cannot publish your answer, and does not depend on
you remembering that it would.

---

## Assembler syntax
AVRASM2, through `avra`, so `.include "m328Pdef.inc"` gives
you every register and bit name the datasheet uses. This is the syntax Microchip Studio
assembles, which is the point: a file from `drivers/source` opens in Studio and single-steps
there without being translated first.

`avra` has no linker. It assembles one file, so `ci/build.sh` generates a top-level unit that
`.include`s every source it finds and assembles that; you never write or edit it, and
`drivers/build/drivers_unit.asm` is there to be read when you want to know what order things
were assembled in.

Three conventions the whole library follows, and the tests assume:

* **Every label is global**, because avra makes them so. There is no `.global` directive in this
  course and nothing needs one.
* **Start each file with `.include "m328Pdef.inc"`.** The generated unit includes it too, and the
  device file guards itself against being included twice, so the line costs nothing here and is
  what makes the file stand alone in Studio.
* **Arguments arrive in r24 (or r25:r24 for a pointer), then r22, then r20**, and a result leaves
  in r24.
  That is the AVR C calling convention, and following it from the first lecture is what makes
  L06's "call your assembly from C" a demonstration rather than a rewrite.

Register and bit names are case-insensitive to `avra`, and this course writes them as the
datasheet does. **A name in `m328Pdef.inc` is whichever address that register is normally reached
by**, and the two are not the same width of number:

* `PORTB` is `0x05`, an **I/O** address. `out PORTB, r16` is right; reaching it with `sts` needs
  `sts PORTB + 0x20, r16`.
* `WDTCSR` is `0x60` and `TCCR1B` is `0x81`, **data space** addresses, because those registers
  live above the I/O window and `out` cannot reach them at all. `sts WDTCSR, r16` is right, and
  there is no `+ 0x20` to add.

The device file marks the second kind `; MEMORY MAPPED`, and grepping for that comment is the
fastest way to settle which one you are holding. This is the same distinction
[L01 A.5](../lectures/L01/appendix/a_avr_core.md#a5-the-io-window-two-names-for-one-register)
draws, seen from the assembler's side.

---
