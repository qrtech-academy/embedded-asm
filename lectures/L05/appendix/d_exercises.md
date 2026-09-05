# Appendix D - Exercises

> **How to check your work.** Exercises 5, 6 and 7 are checked by this lecture's test suite: write
> the file at the path the specification gives, then run `make test`. The suite is cumulative and
> runs L01 to L04's tests too. See [the suite's README](../exercises/test/README.md).
>
> The rest are checked by Appendix E, the worked solutions, published after the lecture. Work each
> one before you read it.
>
> **No hardware is needed for any of this.**

Each exercise is labelled with its kind. There is exactly one **Cross-check**, and here it is
exercise 8.

---

## 1. Why not a loop
**Recall.**

**a)** Give three reasons a counting loop is a worse way to wait than a timer. One of them is
about the processor, one about arithmetic, and one about interrupts.

**b)** Name the four pieces of hardware in the timer and say which two you choose.

**c)** What does CTC stand for, and what does the hardware do on a match that normal mode does
not?

**d)** A delay loop and a CTC timer are each one cycle out per period. After an hour, how do the
two errors compare? Say why.

---

## 2. Prescaler and compare
**Hand calculation.**

At 16 MHz, for each frequency below, give the prescaler and the compare value for a 16-bit timer
and for an 8-bit one, and the error in each case.

**a)** 500 Hz

**b)** 440 Hz

**c)** 3 kHz

**d)** For one of the three, both timers are exact. Say which and why it is not luck.

**e)** For another, the 8-bit timer is more than an order of magnitude worse. Say which, give the
ratio, and explain it in terms of ticks rather than of bits.

**Check yourself:** the worked rows are in
[B.4](./b_frequency.md#b4-what-you-actually-get), and the rule that produces them is
B.3.

---

## 3. Choosing a prescaler
**Design.**

**a)** State the rule for choosing a prescaler, and justify it in one sentence.

**b)** The ratios are 1, 8, 64, 256, 1024. A frequency needs 70000 ticks at a prescaler of 1.
Which prescaler do you end up at, how many ticks is that, and how much resolution did you lose
compared with the one that did not fit?

**c)** The four steps in that ladder are not all the same size. Say which are which, and when you
would notice.

**d)** Somebody suggests always using a prescaler of 1024 "to be safe". Give two things that goes
wrong.

---

## 4. The registers
**Recall.**

**a)** Name the four registers Timer1 needs for a CTC interrupt, and what goes in each.

**b)** All four are at `0x60` or above. What does that rule out, and is the failure loud or quiet?

**c)** `TCCR1B` holds both the mode bit and the clock select bits. Describe the bug that follows
from that, and what it looks like from outside.

**d)** The datasheet says to write a 16-bit register's high byte first. Say why, and say whether
the simulator would catch you getting it wrong.

---

## 5. The software timer
**Code.**

Write `drivers/source/timer.asm` to the specification in
[C.4](./c_what_to_build.md#c4-what-to-build-in-assembly-driverssourcetimerasm).

**a)** Write all five subroutines.

**b)** Run `make test`.

**c)** Change `timer_tick` so that it compares before incrementing rather than after. Note which
tests fail, then put it back.

**d)** Change it to compare only the low bytes of the count and the target. Note which single test
catches it, and say why every other test passes.

---

## 6. The hardware setup
**Code.**

Extend `drivers/app/main.asm` to the specification in
[C.5](./c_what_to_build.md#c5-the-hardware-setup).

**a)** Configure Timer1 for a 1 kHz compare-match interrupt, using the prescaler and compare
value your own `Timer` gave you.

**b)** Add the handler at the `TIMER1_COMPA` vector. Give the `.org` address you used and say
where the number came from.

**c)** Have the handler call `timer_tick` on a software timer with a target that blinks the LED
at a rate you can see, and say what target you chose and why.

**d)** `make build` should build `app.hex`.

---

## 7. What cannot be reached
**Hand calculation.**

**a)** Give the formula for the slowest frequency a timer can reach, and evaluate it at 16 MHz for
both counter widths.

**b)** Can a 16-bit timer produce 0.5 Hz? Give the prescaler and compare value, or say why not.

**c)** Can it produce 0.1 Hz? Same question.

**d)** An 8-bit timer cannot produce 1 Hz. Explain in one sentence why no value of `OCR0A` helps.

**e)** You need 0.1 Hz and you have a 16-bit timer. Describe the arrangement you would use, and
give one interrupt rate and one target that achieve it.

**f)** What is the fastest compare rate any of these timers can produce, and why is asking for
more not merely inaccurate?

---

## 8. Cross-check: how far apart are two interrupts
**Cross-check.** *Compute it by hand, compute it with your own code, measure it, reconcile.*

**a) By hand.** For a 1 kHz compare-match interrupt from Timer1 at 16 MHz, give the prescaler, the
compare value, and the number of CPU cycles between two interrupts.

**b) In cycles.** Turn your `OCR1A` back into a period: `prescaler x (OCR1A + 1)` cycles, and
then into microseconds. Do this before (c).

**c) By measurement.** Build a program whose handler toggles a pin, then:

```bash
make measure IMAGE=app CALLS="--watch B0 --run 200000"
```

`--watch` records every transition of a pin and reports the gaps between them, and a period is a
gap. Ignore the first gap; part (f) is about why.

**d) Reconcile.** All three should agree exactly, and they do. Say in one sentence why a timer is
the one thing in this course where that is unsurprising.

**e) Now ask for 3 kHz instead.** Compute the prescaler, compare value and period in cycles, then
measure it the same way.

**f) The discrepancy.** Your computed period is 5333 cycles. **No measured gap is 5333.** Write
down what you actually measured, then answer three questions:

* Is the timer wrong?
* Is the average right?
* What is quantising the measurement, given that the timer is exact?

**g) Test your explanation.** Whatever you decided in (f), it makes a prediction about compare
values that give an **even** period. Change `OCR1A` to 5331 and then to 5333, measure both, and
say whether your explanation survived.

**h) The first gap.** In every one of these runs the first gap is different from all the others
and is roughly twice as long. Explain it, and say whether it would still happen on real hardware.

---

## 9. When the handler is too slow
**Design.**

**a)** Your handler takes 800 cycles and the compare match happens every 16000. What fraction of
the processor is the handler using?

**b)** The same handler, with the interrupt rate raised to 100 kHz. Now what?

**c)** Describe precisely what happens when a compare match occurs while the previous handler is
still running. Is the interrupt lost or delayed?

**d)** Two matches occur during one long handler. Now what, and how does this differ from (c)?

**e)** The software timers built on that interrupt now run slow. Say by how much, in terms of the
interrupts that were missed, and say whether anything in the program could detect it.

**f)** Give two ways to make the problem visible rather than silent, and say what each costs.

---
