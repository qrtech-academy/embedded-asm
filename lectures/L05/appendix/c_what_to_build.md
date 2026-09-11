# Appendix C - What To Build

## C.1 The task
Two things: `drivers/source/timer.asm`, which counts interrupts so that one hardware timer can
drive several rates; and the hardware setup in `drivers/app/main.asm`, which uses the prescaler
and compare value you worked out by hand in [Appendix B](./b_frequency.md).

---

## C.2 The structure the driver uses
Five bytes, as [`drivers/include/timer.inc`](../../../drivers/include/timer.inc) declares.

| Offset | Field | Size | Holds |
|---|---|---|---|
| 0 | `TIMER_TARGET` | 2 | Interrupts that make one event. Never 0 |
| 2 | `TIMER_COUNT` | 2 | Interrupts counted since the last event |
| 4 | `TIMER_RUNNING` | 1 | 0 or 1 |
| | `TIMER_SIZE` | 5 | Total |

**Both counters are sixteen bits**, because a target of 1000 is one second at a 1 kHz interrupt
and that is an ordinary thing to want. A driver that keeps them in one byte works perfectly up to
255 and then silently does something else.

---

## C.3 The idea: count the interrupts
An 8-bit timer at 16 MHz cannot reach 1 Hz
([B.5](./b_frequency.md#b5-frequencies-you-cannot-have)), and even a 16-bit one has to use its
largest prescaler and most of its range to get near it. Meanwhile a program usually wants several
different rates at once, and there are only three timers.

Both problems have the same answer. Set the hardware to a rate it reaches comfortably and
accurately, say 1 kHz, and then **count those interrupts in software**. A target of 1000 gives an
event every second; a target of 500 gives two a second; and both can exist at the same time, from
the same interrupt, because each has its own structure.

What you give up is resolution: every event lands on a 1 kHz boundary, so the finest interval you
can express is one millisecond. What you get is any multiple of that, from one millisecond to just
over a minute, from one timer, with no extra hardware.

---

## C.4 What to build in assembly: `drivers/source/timer.asm`
Five subroutines.

**`timer_init`** takes the structure address in `r25:r24` and the target in `r23:r22`. It stores
the target, clears the count, leaves the timer **off**, and returns 0 in `r24`; or returns 1
without storing anything if the target is zero.

**`timer_on`** and **`timer_off`** take the structure address and switch it. `timer_off` also
**clears the count**.

**`timer_enabled`** returns 1 if it is on, else 0.

**`timer_tick`** takes the structure address, and is what your compare-match handler calls. If
the timer is off it does nothing and returns 0. Otherwise it adds one to the count; if the count
has reached the target it clears the count and returns 1, and otherwise it stores the count and
returns 0.

### Details that are pinned rather than up to you
**A target of zero is refused.** A count that starts at zero and is compared against zero either
fires on every interrupt or never fires, depending on where in the subroutine you compare, and
neither is obviously wrong from outside. Reject the value instead of picking one.

**`timer_init` leaves it off.** A timer that starts running the moment it is created begins
counting before the rest of the program is ready, and the first event arrives at a moment nobody
chose.

**`timer_off` clears the count**, so switching a timer off and on again starts a whole period
rather than finishing the one that was interrupted.

**Fire on the target-th call, not the one before or after.** With a target of 4, the fourth call
returns 1 and the three before it return 0. Increment first, then compare; the other order is off
by one, and shows up as every period one interrupt long, a rate 20% slow at a target of 4 and 0.1%
slow at 1000, rather than as anything obviously broken.

**Clear the count *after* firing, to zero and not to one.** Otherwise every period after the first
is one interrupt short.

**Compare both bytes.** `cp` then `cpc` on the high bytes, and note the order: the low bytes are
compared first, and the carry from that comparison feeds the second. A driver that compares only
the low byte fires 256 times too often for any target above 255, and passes every test with a
small target in it.

**There is no `adiw` for `r19:r18`.** It only works on `r24`, `r26`, `r28` and `r30`
([L04 A.5](../../L04/appendix/a_pointers.md#a5-what-a-pointer-costs)). Adding one to an ordinary
pair is `subi` with `low(-1)` and `sbci` with `high(-1)`, which is subtracting minus one, and reads
strangely exactly once.

---

## C.5 The hardware setup
In `drivers/app/main.asm`, add to your existing setup:

1. **Zero `TCCR1A`.** No pin output, no waveform generation bits from this half.
2. **Write `OCR1A`**, high byte first ([A.5](./a_timers.md#a5-the-registers)).
3. **Set `OCIE1A` in `TIMSK1`.**
4. **Set `TCCR1B`** to `WGM12` for CTC plus the clock select bits for your prescaler.
5. Leave `sei` where it is, at the end, once.

**`TCCR1B` goes last, and the order is the point.** Writing the clock select bits is what starts
the counter ([A.5](./a_timers.md#a5-the-registers)), so anything written after it is written to a
timer that is already running. Set the compare value first and the timer counts from zero to a
value that was already there; set it afterwards and the first period is whatever `OCR1A` happened
to hold, which after reset is `0x0000`: a compare match on every tick until your write lands.

And add a handler at the `TIMER1_COMPA` vector, which is vector 11, so `.org 0x16`, or
`.org OC1Aaddr`, which is the same number out of the device file
([L03 A.2](../../L03/appendix/a_interrupts.md#a2-the-vector-table)). It has
the same shape as L03's: save what you use and SREG, call `timer_tick` on each software timer,
act on the ones that returned 1, restore, `reti`.

**Blink a second LED, not L03's.** Put it on Arduino pin 8 and leave the one on pin 13 to the
button: L03's integration tests run in this suite too, and one of them watches pin 13 for eight
million cycles and expects nothing to change it.

**Use the numbers you worked out.** Work out the prescaler and compare value for 1 kHz on a
16-bit counter by hand, by the rule in [B.3](./b_frequency.md#b3-choosing-the-prescaler), and
write those in.

**All four registers need `lds` and `sts`.** They are in extended I/O and `out` cannot reach them.

---

## C.6 What this does not do
**It does not make the handler punctual**, only regular. The compare match is exact to the cycle;
when your code actually runs depends on what it interrupted
([Appendix D](./d_exercises.md)'s cross-check).

**It does not survive a handler that is too slow.** If your handler takes longer than the period,
the next match arrives while you are still in the previous one, and the flag is a single bit: you
lose interrupts, silently, and the software timers run slow. At 1 kHz you have 16000 cycles, which
is a great deal; at 100 kHz you have 160, which is not.

**And it does not know about the hardware at all.** `timer_tick` counts calls. Calling it twice
in one interrupt, or forgetting to call it, changes the rate and nothing detects either.

---
