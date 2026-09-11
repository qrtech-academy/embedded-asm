# Appendix E - Exercises

> **How to check your work.** Exercise 5 is checked by this lecture's test suite: write the file
> at the path the specification gives, then run `make test`. The suite is cumulative and runs L01
> to L05's tests too. Exercise 6 is the C capstone, which no test covers: it needs the C runtime
> and is built by hand, as [the suite's README](../exercises/test/README.md) describes.
>
> The rest are checked by Appendix F, the worked solutions, published after the lecture.
>
> **No hardware is needed for any of this.**

Each exercise is labelled with its kind. There is exactly one **Cross-check**, and here it is
exercise 8. It is the last one in the course.

---

## 1. What it catches
**Recall.**

**a)** State, in one sentence, the only thing a watchdog detects.

**b)** For each of the following, say whether a watchdog would catch it:
* a loop that never exits;
* a driver writing to the wrong port register;
* the torn 16-bit read from L03;
* a program waiting for an interrupt that will never arrive;
* a stack that has grown into the variables.

**c)** One of those five is "sometimes, eventually". Which, and what has to happen first?

**d)** Give the two modes a timeout can produce, and say which of them is a safety mechanism.

---

## 2. Where to pet it
**Design.**

**a)** A program has a main loop and a timer interrupt firing every millisecond. Somebody puts
`watchdog_reset` in the timer handler, because it is called reliably. Explain precisely what that
achieves and what it destroys.

**b)** Where should it go instead, and what property does that location need?

**c)** The main loop has two branches, one of which runs rarely. Where do you pet the watchdog so
that a fault in the rare branch is still caught?

**d)** A program pets the watchdog in three different places. Say what has probably gone wrong
with its design.

---

## 3. Control bytes
**Hand calculation.**

Using [A.3](./a_watchdog.md#a3-the-registers), and without running anything:

**a)** Give the byte for a 1 second timeout in system reset mode.

**b)** Give the byte for an 8 second timeout in interrupt mode.

**c)** Give the byte for a 250 ms timeout in interrupt-and-reset mode.

**d)** Somebody wants four seconds and writes `0x08`. Say exactly what they asked for instead, and
describe what the device does from that moment on.

**e)** Why is their mistake so much worse than, say, asking for 2 seconds and getting 250 ms?

**Check yourself:** the timeout table is in
[A.3](./a_watchdog.md#a3-the-registers), and the four
selector bits are not contiguous, so no control byte is ever the timeout number.

---

## 4. The timed sequence
**Recall.**

**a)** Give the two writes, in order, and the constraint between them.

**b)** Four cycles is the limit. Roughly how many cycles would an interrupt take if one landed
between the two writes? Say why `cli` is therefore not optional.

**c)** On a device fresh from reset, what is in `WDTCSR` if the second write arrives too late? Say
why that particular value is the worst possible outcome.

**d)** Why must `WDRF` be cleared before `WDE` can be? Give the reason the hardware behaves that
way, and the consequence for a driver that forgets.

**e)** The sequence begins with `wdr`. What would go wrong without it?

---

## 5. The watchdog driver
**Code.**

Write `drivers/source/watchdog.asm` to the specification in
[D.2](./d_what_to_build.md#d2-what-to-build-in-assembly-driverssourcewatchdogasm).

**a)** Write all four subroutines.

**b)** Run `make test`.

**c)** Insert four `nop` instructions between the two writes of the sequence, rebuild, and note
what `WatchdogDriver.InitWritesTheByteAsked` reports. Say what that value means, then remove them.

**d)** Replace the save-and-restore of `SREG` with a plain `cli` and `sei`. Note which test fails
and describe the bug it is protecting you from.

---

## 6. Calling it from C
**Code.**

Write `drivers/app/main.c` to the specification in
[D.3](./d_what_to_build.md#d3-the-capstone-call-it-from-c).

**a)** Write a C program that calls `shift_bits` and does something with the result. Change
nothing in `utils.asm`; the `utils_gnu.S` you translate from it is a
transcription, not a redesign.

**b)** Translate `utils.asm` into `drivers/source/utils_gnu.S` using the table in
[C.3](./c_c_abi.md#the-one-place-this-course-uses-two-assemblers), then build with `avr-gcc`,
giving it both the `.c` and the `.S`. This build shares no flag with the course's usual one: say
what `-mmcu=atmega328p` is deciding that `avra` decided some other way, and say what the startup
code does that your `main.asm` used to do by hand.

**c)** Declare the prototype's argument as `uint16_t` instead, rebuild, and say what now happens
for an argument of 5 and for an argument of 300. Then declare the result as `uint16_t` as well and
answer the same question. Then put both back.

**d)** Write a C function and call it from your assembly. Say which registers you had to assume it
would destroy.

---

## 7. Sleeping
**Design.**

**a)** For each of idle, power-down and power-save, say what is still running.

**b)** A program sleeps in power-down and expects Timer1 to wake it after one second. Describe
what actually happens, and how long it lasts.

**c)** Name the two wake sources that survive every sleep mode, and say why each of them does.

**d)** Design, in words, a device that does something once every eight seconds and spends the rest
of its life drawing microamps. Say which peripheral wakes it and in which mode.

**e)** A device refuses to stay asleep: it wakes immediately, every time. Give two plausible
causes.

---

## 8. Cross-check: your assembly against the compiler's
**Cross-check.** *Compute it by hand, measure it, reconcile.*

The last cross-check in the course, and the only one where the thing you are checking against is
somebody else's work.

**a) By hand.** From L01, your `shift_bits` costs `6n + 10` cycles. Write that down.

**b) Write the same thing in C.** A function taking a byte, returning `1` shifted left that many
times, using a loop. **Call it `c_shift_bits`**, so that both live in one ELF without colliding.
Compile it at `-Os` and read the assembly with `avr-gcc -S`. Count the instructions and predict
its cost as a formula in `n`, before measuring.

**c) By measurement.** `drivers/build/drivers.hex` holds no C, so build one image that holds both,
the same hand build the capstone uses, and point `make measure` at it:

```bash
avr-gcc -mmcu=atmega328p -Os drivers/app/main.c drivers/source/utils_gnu.S -o drivers/build/mixed.elf
make measure IMAGE=mixed CALLS="shift_bits:0 c_shift_bits:0 shift_bits:8 c_shift_bits:8"
```

`IMAGE` names the stem and not the extension, so the same variable reaches `drivers.hex` and this
`mixed.elf`; `ci/measure.sh` takes whichever of the two exists.

**d) Reconcile.** Give both formulas. They are not the same shape, and one of them wins at some
arguments and loses at others: say where they cross.

**e) The surprise.** At one specific argument the compiler's version is **faster** than yours.
Which argument, by how much, and what did the compiler do that you did not? Look at the
instruction it used and say what it does.

**f) Code size.** Count the instructions in each. Now say which version you would ship, and note
that "the hand-written one is smaller and faster" is not the answer the numbers support.

**g) What this is evidence for.** In one paragraph, say what this comparison does and does not
establish about writing assembly by hand. Be specific about the size of the win and about what it
cost you to get it.

---

## 9. What you would actually reach for
**Design.**

The course is over. For each of the following, say whether you would write assembly, write C, or
do something else entirely, and why.

**a)** A driver for a new sensor on the SPI bus.

**b)** An interrupt handler that must respond within two microseconds.

**c)** A routine that toggles a pin for a fixed 3 microseconds, exactly, every time.

**d)** The main loop of a battery-powered logger.

**e)** Working out why a program that worked yesterday now resets every few seconds.

**f)** One of the five answers above is the one this course was really for. Say which.

---
