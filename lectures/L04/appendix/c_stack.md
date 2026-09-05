# Appendix C - The Stack, and How Deep It Goes

## C.1 One pointer, four users, no referee
`SP` lives in `SPH:SPL` at data space `0x5E:0x5D`, it starts at `RAMEND`, and it moves downwards.
Four unrelated things use it and none of them coordinates with the others:

| What | Costs |
|---|---|
| `rcall` and `ret` | 2 bytes, for a return address |
| `push` and `pop` | 1 byte each |
| An interrupt | 2 bytes, pushed by the hardware before your handler starts |
| Your handler's own saves | 1 byte each |

**`SP` points at the next free byte, not the last used one.** So the number of bytes in use is
`RAMEND - SP`, and the lowest byte actually occupied is one *above* where `SP` is. That
off-by-one is worth getting right once: it is the difference between "my structure at `0x08F1` is
safe" and "my structure at `0x08F1` was overwritten".

---

## C.2 Counting the worst case
![Seven rows showing stack use accumulating: nothing in the main loop, two bytes for a call, four for a nested call, six when an interrupt pushes the program counter, eleven after the handler saves five registers, thirteen and fifteen for two more nested calls](./images/stack_depth.png)

That is L03's program at its deepest, and every number in it is measured. The rule behind them is
simple enough to apply to any program:

```math
\text{bytes} = 2 \times (\text{calls deep in the main program})
             + 2 + (\text{registers the handler saves})
             + 2 \times (\text{calls deep inside the handler})
```

The `+ 2` in the middle is the hardware's, and it is there even for a handler that is nothing but
`reti`. The handler's saves are one byte each, SREG's holder included.

**The worst case is not the common case, and it is the only one worth computing.** The interrupt
does not arrive politely between main-loop iterations; it arrives while the main loop is as deep
as it ever gets, because that is the state the program spends its time in. Assume it lands at the
worst possible moment, because eventually it will.

**Everything is measurable except the worst moment.** You can watch the stack pointer and record
how low it went, and this course's harness does exactly that, but a measurement only tells you
about the interrupts that actually arrived and where they actually landed. The arithmetic tells
you about the one that has not happened yet. [Appendix E](./e_exercises.md)'s cross-check is
about the two agreeing, and about what it would mean if the measurement came out *lower*.

---

## C.3 What running out looks like
Nothing.

There is no stack limit register, no guard page, no fault and no message. The stack grows down
into whatever is below it and keeps going. What you observe is one of these, days later:

* a variable that changes on its own, because a `push` landed on it;
* a subroutine that returns somewhere it was never called from, because something wrote over a
  saved return address;
* a program that restarts for no reason, because that somewhere was unprogrammed flash
  (L01 F.6, exercise 6).

None of those points at the stack, which is what makes the arithmetic worth doing in advance
rather than the debugging worth doing afterwards.

**Recursion is the fast way there.** A handler that enables interrupts inside itself, or a
subroutine that calls itself, adds a frame per repetition with nothing counting them
([L03 B.6](../../L03/appendix/b_isr_contract.md#b6-what-a-handler-must-not-do)). Neither appears
in this course, and both appear in real AVR code.

---

## C.4 How much room is there really
2048 bytes sounds like a lot until you write the subtraction down.

L03's program uses 15 bytes of stack at its worst and 17 bytes of structures, one LED and one
button, which leaves 2016 free. An array of six LEDs adds 42 bytes of structures and one more call
level, so the figures move to 17 and 59, leaving 1972. Neither is close to trouble, and that is
the point of computing it: you want to know *how much* headroom you have, so that when a later
change halves it you notice.

Do that subtraction whenever the program grows a call level or a handler, and write the answer
somewhere the next reader will find it. It is the kind of calculation that is done once, believed
for a year, and quietly falsified by the third feature nobody re-checked.

---

## C.5 The stack pointer is a register you may load
Everything above treats `SP` as something the hardware moves. It is also an ordinary pair of I/O
registers, and you may read it and write it like any other.

That is worth saying plainly, because
[L01 D.6](../../L01/appendix/d_first_subroutine.md#d6-the-program) writes `SP` once, at reset, and
then explains that the hardware had already done it, which leaves
the impression that touching `SP` is ceremonial. It is not. It is the only way to answer two
questions this appendix has been asking on paper.

**Reading it: how deep did I actually go?**

```asm
    in   r24, SPL
    in   r25, SPH          ; r25:r24 = SP, and RAMEND - SP is the depth
```

**Writing it: high byte first.**

```asm
    out  SPH, r25
    out  SPL, r24
```

The order matters and only in one direction. `SP` has no shadow register, and unlike `OCR1A` both
halves are directly writable, so the hazard is not a latch, it is the moment in between. Write
`SPL` first and there is one instruction during which the low half is new and the high half is
old: `SP` points somewhere neither value describes, and an interrupt arriving in that instruction
pushes two bytes there. Writing `SPH` first leaves the intermediate value inside the *new* region
rather than in an arbitrary one. Interrupts being off makes the question moot, and writing them in
the safe order costs nothing, so the rule is worth following rather than reasoning about.

**These are I/O addresses, and this appendix has been quoting the other kind.** `SPL` is data space
`0x5D` and I/O `0x3D`; `SPH` is `0x5E` and `0x3E`. `in` and `out` take the I/O numbers, and
`m328Pdef.inc` gives you the names, so `in r24, SPL` is what you write
([L01 A.5](../../L01/appendix/a_avr_core.md#a5-the-io-window-two-names-for-one-register)). Reaching
them with `lds` and `sts` works too and costs a cycle more each.

**What this is for.** Nothing in this course needs it: the drivers you are writing never move `SP`,
and the depth figures in C.2 are computed rather than read out of the machine. It is here because
of what the four instructions above become when you write them in the other order. Save every
register on the stack you are on, store `SP` somewhere, load `SP` from somewhere else, restore
every register from *that* stack, and `ret`, and you have returned onto a stack you were not
called on. That is a context switch, it is about forty lines, and the two instruction pairs in this
section are the two that make it a switch rather than a subroutine.

---
