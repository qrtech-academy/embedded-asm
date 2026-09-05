# Appendix D - What To Build

## D.1 The task
Three things, and the last of them is the course's capstone: `avr::watchdog::Watchdog`, which
produces the bytes; `drivers/source/watchdog.asm`, which writes them correctly; and a C program that
calls the assembly you wrote in L01, unchanged.

---

## D.2 What to build in assembly: `drivers/source/watchdog.asm`
Four subroutines.

**`watchdog_init`** takes the control byte in `r24` and performs the timed sequence
([A.4](./a_watchdog.md#a4-the-timed-write-sequence)):

1. Save `SREG`, then `cli`.
2. `wdr`, so the timeout starts from now rather than from wherever the counter had got to.
3. Clear `WDRF` in `MCUSR`, leaving the other three cause bits alone.
4. Write `WDCE` and `WDE` together into `WDTCSR`.
5. Write `r24` into `WDTCSR`.
6. Restore `SREG`.

**`watchdog_reset`** is a single `wdr` and a `ret`. It runs in your main loop, thousands of times,
and must do exactly that one thing.

**`watchdog_disable`** is `watchdog_init` with a written value of zero.

**`watchdog_caused_reset`** returns 1 in `r24` if `WDRF` was set in `MCUSR`, else 0, and clears
`WDRF` either way, leaving the other cause bits alone.

### Details that are pinned rather than up to you
**Steps 4 and 5 must be adjacent.** Two `sts` instructions, nothing between them. Two cycles each,
so they fit the four-cycle window with room; a single instruction inserted between them is enough
to leave `WDTCSR` holding `0x08`
([A.4](./a_watchdog.md#what-a-failed-sequence-leaves-behind)).

**Save and restore `SREG`, do not just `cli` and `sei`.** The sequence must run with interrupts
off, but leaving them off on the way out is a bug: every other interrupt in the program quietly
stops, at a moment determined by whoever last configured the watchdog. This is the same discipline
as L03's atomic read ([L03 B.4](../../L03/appendix/b_isr_contract.md#b4-the-shared-variable)).

**Clear `WDRF` before the window, not after.** The hardware refuses to clear `WDE` while `WDRF` is
set, so a driver that clears it afterwards works the first time and cannot disable the watchdog
after a watchdog reset, which is exactly when it matters.

**`MCUSR` is inside the I/O window, so `in` and `out` reach it**; `WDTCSR` is not, and needs `lds`
and `sts`. The two numbers are the usual pair: `MCUSR` is data space `0x54` and I/O `0x34`, and the
name in `m328Pdef.inc` is the I/O one, so `in r24, MCUSR` is what you write
([L01 A.5](../../L01/appendix/a_avr_core.md#a5-the-io-window-two-names-for-one-register)). `WDTCSR`
is `0x60` in both, because above the window there is only one. Two registers, two addressings, one
subroutine.

**Leave the other reset causes alone.** `MCUSR` records four different reasons in four bits, and
clearing all of them because you cared about one destroys information nothing can recover.

---

## D.3 The capstone: call it from C
Write `drivers/app/main.c`, a C program that calls `shift_bits` from L01 and uses the result.

**Change nothing in `utils.asm`.** That is the point. It has followed the calling convention since
L01, so a C prototype is the whole of the interface
([C.3](./c_c_abi.md#c3-calling-your-assembly-from-c)).

Build it with a normal `avr-gcc` invocation rather than the course's usual one: a C program needs
the startup code that sets the stack pointer, zeroes `.bss` and `r1`, and calls `main`, all the
things your `main.asm` did by hand.

Then generate the compiler's own version of the same job with `-S`, and compare it against what
you wrote ([Appendix E](./e_exercises.md)'s cross-check).

### Details that are pinned rather than up to you
**The prototype's types must match.** `uint8_t shift_bits(uint8_t)`. Declaring the argument wider
passes it in `r25:r24` and your subroutine reads only `r24`, which works for small values and is
still wrong.

**Do not add `extern "C"`.** This is C, not C++, and there is no name mangling to suppress.

---

## D.4 What none of this does
**The watchdog class does not touch hardware.** It computes bytes. Writing them correctly is the
assembly's job, and writing them at all is your program's.

**The driver does not decide when to pet.** Where `watchdog_reset` is called from is the entire
difference between a watchdog that works and one that is decoration
([A.1](./a_watchdog.md#a1-what-it-actually-detects)), and nothing in the driver can help.

**And none of it is tested against sleep.** The interaction between sleep modes and wake sources
is specified by the datasheet and approximated by the simulator, so this course teaches it and
does not check it ([B.5](./b_sleep.md#b5-what-sleep-does-not-do)).

---
