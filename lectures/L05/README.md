# L05 - Timers

## Agenda
* Why a timer, and what is wrong with a loop that counts.
* The prescaler: five ratios, and the two places the ladder stops doubling by eight.
* CTC mode, and why the period is `OCR1A + 1` ticks rather than `OCR1A`.
* Turning a frequency you want into a prescaler and a compare value, and the error left over.
* Frequencies no timer on this device can reach, in both directions.
* Extending a timer in software, so one interrupt can drive several rates.
* A blinker that keeps time while the processor is doing something else.

---

## Lecture plan
Worked in this order:
1. **The counting loop, and its problem.** L02 ended with an LED toggling at about 127 kHz
   because nothing was slowing it down. The fix is not a delay loop, and
   [Appendix A](./appendix/a_timers.md) is about why.
2. **The hardware, once.** A counter, a prescaler, a compare register and a flag. Five paragraphs
   of datasheet, and then it is arithmetic for the rest of the lecture.
3. **The arithmetic.** Given a frequency, which prescaler and which compare value, and how far
   off do you land. Work the table out rather than reading it; the rule is short and the boundary
   cases are where it lives.
4. **What cannot be reached.** An 8-bit timer at 16 MHz cannot produce 1 Hz. Not badly: at all.
5. **Counting the interrupts.** The software timer that fixes it, and that lets one hardware
   timer drive four events at four rates.

Two predictions worth making before anything runs:
* what compare value gives exactly 1 kHz, and whether "exactly" is really exact.
* whether two consecutive interrupts are the same number of cycles apart.

The second is this lecture's cross-check, and the answer is: sometimes.

---

## Before the lecture
* Finish L04. The timer's compare match is an interrupt like any other and its handler needs the
  same prologue, and its software timers are structures in SRAM, laid out and reached the way L04's
  were.
* Read [Appendix A](./appendix/a_timers.md) and [Appendix B](./appendix/b_frequency.md).

---

## After the lecture
* Read [Appendix C](./appendix/c_what_to_build.md), which specifies what to write.
* Work through [Appendix D](./appendix/d_exercises.md). Solutions will be published after the
  lecture.

---

## What you should be able to do afterwards
* Say what a prescaler does, name the five ratios, and say which steps between them are not a
  factor of eight.
* Configure Timer1 for CTC mode at a chosen prescaler, from the datasheet's bit names.
* Turn a wanted frequency into a prescaler and a compare value, by hand and in code.
* Say why the compare value is one less than the tick count, and what going wrong there costs.
* State the fastest and slowest frequencies a given timer can reach, and say what to do about a
  frequency below the slowest.
* Explain why an 8-bit timer is so much worse at hitting a frequency exactly than a 16-bit one,
  in terms of ticks rather than of bits.
* Extend a timer in software so that one interrupt drives several events at different rates.
* Predict the number of cycles between two compare-match interrupts, and say when that number is
  the same every time and when it is not.

---

## Questions to test yourself
* Why is a delay loop a worse way to wait than a timer, given that both work?
* The prescaler ratios are 1, 8, 64, 256 and 1024. Which steps are the odd ones, and what does
  that mean when a frequency does not fit at one prescaler?
* You want 1 kHz from Timer1 at 16 MHz. Give the prescaler and the compare value, and say whether
  the result is exact.
* You want the same 1 kHz from Timer0. Give the prescaler and compare value, and say why they are
  different numbers for the same frequency.
* An 8-bit timer at 16 MHz cannot produce 1 Hz. Say why, in one sentence, and say what you would
  do instead.
* Two compare-match interrupts are 5333 cycles apart on average, but no individual gap is 5333.
  What is going on, and is the timer at fault?

---

## Reference
* [Appendix A](./appendix/a_timers.md): the hardware, and why a timer beats a loop.
* [Appendix B](./appendix/b_frequency.md): the arithmetic, and the frequencies you cannot have.
* [Appendix C](./appendix/c_what_to_build.md): the `Timer` and `timer.asm` specifications.
* [Appendix D](./appendix/d_exercises.md): the exercises.
* Appendix E: the worked solutions, published after the lecture rather than with it.
* [L03 Appendix B](../L03/appendix/b_isr_contract.md) for the handler contract, which a
  compare-match handler obeys exactly like a pin change one.

---

## Next lecture
* The watchdog: a timer whose job is to notice that your program has stopped.
* Timed write sequences, and hardware that refuses to be configured carelessly.
* Sleep modes, and what is still running in each.
* Calling your assembly from C, and C from your assembly, which is where the calling contract
  you have been following since L02 finally has another party to it.

---
