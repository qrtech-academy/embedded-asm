# Appendix B - The Frequency You Asked For

## B.1 The arithmetic
Given a clock, a prescaler and a frequency you want, the number of ticks in one period is:

```math
\text{ticks} = \frac{f_{\mathrm{clk}}}{N \times f}
```

and the compare value is one less than that, because the counter starts at zero
([A.4](./a_timers.md#a4-ctc-mode)).

At 16 MHz, 1 kHz and a prescaler of 1: `16000000 / 1000 = 16000` ticks, so `OCR1A = 15999`. That
is exact, and `16000000 / 16000` is exactly 1000 Hz.

Most frequencies are not like that.

---

## B.2 Ticks are whole numbers
At 16 MHz and a prescaler of 1, 3 kHz needs `16000000 / 3000 = 5333.33` ticks. The counter cannot
count a third of a tick, so you get 5333 or 5334 and nothing in between.

Take 5333, so `OCR1A = 5332`. The frequency you actually get is:

```math
\frac{16000000}{1 \times 5333} = 3000.1875 \text{ Hz}
```

which is **0.0063% high**. That is the error, and it is not a rounding artefact of your
arithmetic; it is the closest frequency the hardware can produce.

**More ticks means less error.** The gap between two adjacent achievable frequencies is roughly
`f / ticks`, so a period of 5333 ticks lands you within about 0.02% and a period of 83 ticks
within about 1.2%. That single sentence is the whole reason to prefer a small prescaler and a
wide counter.

---

## B.3 Choosing the prescaler
The rule is: **the smallest prescaler whose tick count still fits in the counter.**

Smallest, because a smaller prescaler means more ticks per period, and more ticks means finer
resolution. You move up only when forced, and you are forced when the ticks no longer fit.

Worked at 16 MHz for 1 kHz:

| Prescaler | Ticks | Fits in 16 bits? | Fits in 8 bits? |
|---|---|---|---|
| 1 | 16000 | yes | no |
| 8 | 2000 | yes | no |
| 64 | 250 | yes | **yes** |
| 256 | 62.5 | yes | yes |
| 1024 | 15.6 | yes | yes |

So Timer1 takes prescaler 1 with `OCR1A = 15999`, and Timer0 takes prescaler 64 with
`OCR0A = 249`. **Same frequency, different numbers**, because the counters are different widths;
both are exact here, and that is luck rather than design.

---

## B.4 What you actually get
Build this table before reading it. Every row is the same three steps, and doing them by hand
four times is what turns the rule into something you can apply to a frequency that is not here.

| Wanted | Timer1, 16-bit | Timer0, 8-bit |
|---|---|---|
| 1 Hz | `/256`, `OCR = 62499`, exact | **not reachable** |
| 2 Hz | `/256`, `OCR = 31249`, exact | **not reachable** |
| 10 Hz | `/64`, `OCR = 24999`, exact | **not reachable** |
| 1 kHz | `/1`, `OCR = 15999`, exact | `/64`, `OCR = 249`, exact |
| 3 kHz | `/1`, `OCR = 5332`, `+0.0063%` | `/64`, `OCR = 82`, `+0.40%` |
| 100 kHz | `/1`, `OCR = 159`, exact | `/1`, `OCR = 159`, exact |
| 3 MHz | `/1`, `OCR = 4`, `+6.67%` | `/1`, `OCR = 4`, `+6.67%` |

Three things in that table are worth stopping on.

**3 kHz misses by sixty times more on the 8-bit timer.** Same clock, same frequency, same
arithmetic; the only difference is that one has 5333 ticks to work with and the other 83.

**At 3 MHz both are equally bad.** With only five ticks in a period, the width of the counter
stops mattering: you are choosing between 3.2 MHz and 2.67 MHz and nothing between. High
frequencies are where a timer stops being a precision instrument, whatever hardware you have.

**Several rows are exact.** That is not an accident of these examples: 16 MHz divided by a power
of two is a whole number, and the prescalers are powers of two, so frequencies that divide the
clock cleanly come out exactly. It is worth knowing which of your frequencies are the lucky ones.

---

## B.5 Frequencies you cannot have
Two limits, and they are limits of different kinds.

**Too fast: above the clock.** The shortest period is one tick at a prescaler of 1, so the fastest
compare rate is the clock itself, 16 MHz. Anything above that is not "approximated badly", it is
unreachable, and asking for it should be an error rather than a number.

**Too slow: past a full counter at the largest prescaler.**

```math
f_{\min} = \frac{f_{\mathrm{clk}}}{1024 \times \text{counter values}}
```

At 16 MHz that is **0.238 Hz** for a 16-bit counter and **61.04 Hz** for an 8-bit one.

**So an 8-bit timer at 16 MHz cannot produce 1 Hz.** Not badly; at all. There is no prescaler that
gets sixteen million cycles into 256 ticks, and no value of `OCR0A` helps, because the problem is
that the counter runs out of values rather than that you chose the wrong one.

That is a real constraint on real projects, and the answer to it is not a bigger register. It is
to accept an interrupt rate the hardware *can* reach and count those interrupts yourself, which
is [C.4](./c_what_to_build.md#c4-what-to-build-in-assembly-driverssourcetimerasm) and the reason
this lecture has an assembly half at all.

---

## B.6 Rounding is a decision
`16000000 / (1 × 3000)` is 5333.33, and 5333 is nearer than 5334, so round to nearest.

That is a choice, and it should be made deliberately rather than by whichever way the language
happens to truncate. Truncating always rounds down, so it always produces a period that is too
short and a frequency that is too high, systematically, in every calculation you ever do with it.
Rounding to nearest is wrong half the time by half as much.

**Round to nearest, with a half rounding up**, and use that rule everywhere rather than choosing
per calculation: one rule everywhere is one rule to check.

And note what rounding does *not* do. It does not make the answer exact, and it does not make the
error small; it makes it as small as this prescaler allows. If that is not small enough, the fix
is a different prescaler, a different timer, or a different clock crystal, and
[Appendix D](./d_exercises.md) asks you to work out which.

---

## B.7 Why the gaps alternate
Everything above is about the period the timer produces. This is about the period you can
*observe*, and the two are not the same number even when the timer is exact.

Ask for 3 kHz, get `OCR1A = 5332` and a period of 5333 cycles, then measure the gaps between
successive handler entries. They come out **5332, 5334, 5332, 5334** and not one of them is 5333.

Nothing is broken. The compare match really does happen every 5333 cycles; what is quantised is
the *handler's first instruction*, because an interrupt is taken at an instruction boundary and
not in the middle of one ([L03 A.4](../../L03/appendix/a_interrupts.md#a4-what-happens-in-order)).
A main loop of `rjmp` offers a boundary every two cycles. A period of 5333 is odd. So each match
falls on the other side of a boundary from the last one, and the instant you can observe alternates
by a cycle either way.

Three things follow, and the third is the useful one.

**The average is exact.** `(5332 + 5334) / 2 = 5333`. Over any even number of periods the total is
right, so nothing drifts. Jitter and drift are different failures and this is only the first.

**An even period does not alternate.** `OCR1A = 5331` gives a period of 5332 and four measured
gaps of 5332. That is the prediction the explanation makes, and it is worth making before
measuring rather than after.

**And it is not the period alone that decides it.** The handler is what determines where the main
loop resumes, and therefore where the next boundary falls, so its cost is a term too:

> **The gaps alternate when `period + handler round trip` is odd, and are steady when it is
> even.** Against a two-cycle main loop, nothing else about either number matters.

Which means you can invert the whole table by adding a single `nop` to the handler. An even period
that was steady starts alternating, and the odd one goes quiet. That is a strange result to arrive
at from first principles and an obvious one afterwards, and it is the clearest example this course
has of a measurement that is telling you about the code being interrupted rather than about the
thing you were measuring.

[Appendix D](./d_exercises.md) has you reproduce all three, and the kernel course that follows this
one meets the same rule again with the scheduler's own round trip added to the sum.

---
