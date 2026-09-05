# Appendix D - Your First Subroutine

## D.1 The task
Write two subroutines in `drivers/source/utils.asm`, and one program in `drivers/app/main.asm`.

The subroutines compute `1 << n` and `~(1 << n)` for a value of `n` that is not known until the
program runs. In C that is one operator each and you would not give it a second thought. Here it
is a loop, because the AVR has no barrel shifter
([A.7](./a_avr_core.md#a7-what-this-machine-does-not-have)): `lsl` shifts by exactly one place,
and shifting by `n` places means going round `n` times.

That is not a curiosity. Every driver in this course is handed a pin number and has to turn it
into a bit mask, and these two subroutines are how. `led_on` in L02 calls `shift_bits`;
`button_init` in L03 calls both. Getting them right now means the rest of the course is about
peripherals rather than about bit twiddling.

Creating the file is all it takes to switch its tests on; see
[the suite's README](../exercises/test/README.md).

---

## D.2 Where the arguments live
This course follows the AVR C calling convention from the first line of assembly it writes, and
keeps following it, so that L06's "call your assembly from C" is a demonstration rather than a
rewrite. The whole of what you need for now:

| Register | Role |
|---|---|
| `r24` | First argument, if it is a byte. Also where a byte-sized return value goes. |
| `r25:r24` | First argument, if it is a pointer or another 16-bit value. |
| `r22` | Second argument, if it is a byte. |
| `r18` to `r27`, `r30`, `r31` | **Call-clobbered.** A subroutine may destroy these freely. |
| `r2` to `r17`, `r28`, `r29` | **Call-saved.** A subroutine that uses one must put it back. |

So both subroutines here take their argument in `r24` and leave their result in `r24`, and both
may use `r18` and `r19` as scratch without saving anything.

---

## D.3 `shift_bits`
Returns `1` shifted left by the number of places given.

| Given `r24` | Returns `r24` | Because |
|---|---|---|
| 0 | `0x01` | Shifted no times at all. |
| 1 | `0x02` | |
| 5 | `0x20` | Which is bit 5, the Arduino Uno's pin 13. |
| 7 | `0x80` | |
| 8 | `0x00` | The bit has been shifted off the end of an eight-bit register. |

Write it like this:

1. Put `0x01` in a scratch register; this is the value being shifted. Put `0` in a second scratch
   register; this is the count of shifts done so far.
2. At the top of the loop, compare the count against `r24`. If they are equal, leave the loop.
3. Otherwise shift the value left once, add one to the count, and jump back to the top.
4. On leaving, move the value into `r24` and return.

Two things about that shape are worth being deliberate about, because they are what the cost
depends on ([C.3](./c_counting_cycles.md#c3-a-branch-costs-more-when-it-branches)):

**The comparison is at the top, not the bottom.** So an argument of zero does no shifts at all,
which is what makes `shift_bits(0)` return `0x01` rather than `0x02`. A loop with the test at the
bottom always runs its body once, and would be wrong for exactly one input, which is the input
your driver will use for pin 8.

**The exit branch runs once more than the body does.** That last comparison, the one that finds
the count has reached `r24` and leaves, is a real instruction with a real cost. It is the reason
the answer is 10 cycles at `n = 0` and not 7.

The last row of the table is the interesting one. Nothing in the routine says "stop at eight"; the
zero falls out of the register being eight bits wide, and the bit simply leaves. A reader thinking
in C, where `1 << 8` is 256, will predict `0x100` and there is nowhere to put it.

---

## D.4 `shift_bits_inverted`
Returns the complement of the same value: `~(1 << n)`.

| Given `r24` | Returns `r24` |
|---|---|
| 0 | `0xFE` |
| 1 | `0xFD` |
| 5 | `0xDF` |
| 7 | `0x7F` |
| 8 | `0xFF` |

The obvious implementation is to call `shift_bits` and complement the result with `com`. Do not;
write it as its own loop. Start the scratch value at `0xFE` instead of `0x01`, and each time round
shift left *and then increment*, which shifts a zero in at the bottom and turns it back into a one.

The reason for the detour is that this routine exists to produce a mask for clearing a bit, and
L02's driver calls it directly. Writing it as its own loop also makes the point that
[C.3](./c_counting_cycles.md#c3-a-branch-costs-more-when-it-branches) is really making: two
routines differing by a single `inc` differ in cost by that `inc` on every trip, and you can say
by how much before running either.

---

## D.5 Why `r18` and `r19`
Use `r18` and `r19` as the scratch registers, not `r16` and `r17`.

Both pairs are in the upper half, so both can take an `ldi`
([A.2](./a_avr_core.md#a2-the-register-file)). The difference is the calling convention in D.2:
`r18` and `r19` are call-clobbered, and `r16` and `r17` are call-saved. A subroutine that writes
to `r16` without restoring it has broken its contract with whoever called it, and the caller has
no way to know.

Right now nothing calls these subroutines but a test, and a test does not care. By L06 the caller
may be a C function that had a live value in `r16`, and then the bug is a variable that changes on
its own across a function call, which is about as unpleasant a thing to debug as this course
contains. Choosing the right registers now costs nothing and means that never happens.

If you are comparing against AVR assembly you have found elsewhere, note that a good deal of it
uses `r16` and `r17` here. It works, right up until it does not.

---

## D.6 The program
`drivers/app/main.asm` is the first thing in this course that is a program rather than a subroutine.
For L01 it needs four things:

**A reset vector.** The first word of program memory is where the machine starts, so the first
instruction in your file has to be a jump to your code. Use `.org 0` followed by an `rjmp`.

**A stack pointer.** `rcall` pushes a return address and `ret` pops one, and both use `SP`. Set it
to `RAMEND` by writing `high(RAMEND)` to `SPH` and then `low(RAMEND)` to `SPL`, with `out` rather
than `sts` ([A.5](./a_avr_core.md#a5-the-io-window-two-names-for-one-register)). `low()` and
`high()` are AVRASM2's; GNU `as` spells the same two functions `lo8()` and `hi8()`, which matters
once in L06 and nowhere else.

The hardware already does this on the ATmega328P, and it does it after **every** reset, watchdog
resets included. You will find a good deal of AVR code carrying a comment saying otherwise; on
this device that comment is wrong, and repeating it is how the belief survives.

Write the four instructions anyway, for the two reasons that are actually true. Older AVRs reset
`SP` to `0x0000` rather than to `RAMEND`, so code that omits this is not portable to them, and the
failure there is a stack that grows down out of memory on the first `rcall`. And a reset is not
the only way to arrive at your code: a bootloader that jumps into it has performed no reset at
all, and `SP` holds whatever the bootloader left in it.

Neither of those applies to anything in this course. Knowing *which* reason applies, rather than
carrying a habit you cannot justify, is the point.

**Something to do, and somewhere to stop.** Call `shift_bits` with an argument, then sit in a
loop that jumps to itself. There is no operating system to return to; a program that runs off the
end of its own code executes whatever is in flash after it, which is `0xFF` repeated, and the
results are not interesting. An infinite loop is how an embedded program ends.

**And something you can see.** Light the LED on PB5.

```asm
    sbi  DDRB, 5                ; PB5 is an output
    sbi  PORTB, 5               ; and it is high
```

That is the whole of it, and every part of it is already in this lecture. `DDRB` is `0x04` and
`PORTB` is `0x05`, both I/O addresses, so `sbi` reaches them and `sts` would not
([A.5](./a_avr_core.md#a5-the-io-window-two-names-for-one-register)); `sbi` costs two cycles and
not one, which [C.2](./c_counting_cycles.md#c2-what-each-instruction-costs) says and which is worth
noticing now rather than in L05 when you are counting a timer's handler.

The one thing that is new is what the two registers mean, and it is one sentence: **`DDRx` decides
whether a pin is an output, and `PORTx` decides what an output drives.** Both are per-bit, both
default to zero, and zero means "input, not driven". So an LED needs both writes and in that order:
setting `PORTB` first would briefly enable a pull-up on an input pin instead, which is a different
thing that happens to look similar.

PB5 is Arduino pin 13, which is the one with an LED already fitted to the board, and the reason
this course lights that one rather than any other. On a real Uno there is a resistor beside it; in
the simulator there is nothing to protect, and
[L02 A.4](../../L02/appendix/a_io_ports.md#a4-an-led-and-a-resistor-that-is-not-optional) is where
that stops being a detail.

**Two instructions, one pin, hard-coded.** That is deliberate, and it is exactly as far as this
lecture goes. It only works for PB5, it cannot be told which LED to light, and nothing else in the
program can reuse it. Turning it into something a program can call with a pin number is L02, and
so is the reason that turns out to be more work than it sounds.

---

## D.7 How to check it
Three things, in this order.

**Does it assemble?**

```bash
make build
```

**Does it do the right thing, and cost the right amount?**

```bash
make test
```

Nine tests were passing before you wrote anything, eighteen once `utils.asm` exists, and twenty
once `main.asm` does. If `Utils.SubroutinesAreDefined` fails while the file is plainly there, the
label is spelled differently from the name the test asks for, or the file did not assemble
([B.2](./b_toolchain.md#b2-avra-as-an-assembler)).

The tests for `main.asm` work differently from the rest, and it is worth knowing why before one of
them fails. A subroutine can be called: a test sets the program counter to `shift_bits`, puts a
number in `r24` and reads `r24` back. A program cannot. It has no arguments, it never returns, and
the only way to find out what it does is to **let it run** and then look at the machine:

```asm
    mcu.run(2000);                      // 2000 cycles of your program
    mcu.data(0x24) & (1 << 5)           // DDRB, in the data space
```

Note the `0x24`. The test reads the **data space** address where your program wrote the **I/O**
address `0x04`, and both are correct, because they are two names for one register. That is A.5
again, seen from the third side, and it is the last time this course will point it out.

**What does it actually cost?**

```bash
make measure SYMBOL=shift_bits ARG=5
```

Do not run that until you have predicted the answer. Predicting it, twice, and then reconciling
both predictions against the measurement is [Appendix E](./e_exercises.md)'s cross-check, and it
is the exercise this whole lecture exists to set up.

---
