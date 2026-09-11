# L06 - Watchdog, Sleep, and the C ABI

## Agenda
* What a watchdog protects against, and the much longer list of what it does not.
* The timed write sequence: hardware that refuses to be configured carelessly, and why.
* The one typo in this lecture that leaves a device resetting every sixteen milliseconds.
* Sleep modes, and which of them a timer can wake you from. It is fewer than you would like.
* The AVR C ABI in full, and where you have been following it since L01 without a second party.
* Calling your assembly from C, and reading what the compiler generates for the same job.

---

## Lecture plan
Worked in this order:
1. **What a watchdog is for.** Read [Appendix A](./appendix/a_watchdog.md) and decide, before you
   are told, which of five failures a watchdog would catch. The answer is two of them, and a third
   eventually.
2. **The timed sequence.** Two writes, four cycles apart at most. Get it wrong and the register
   holds a value that is not merely wrong but specifically dangerous.
3. **Sleeping.** What stops in each mode, and the two things that can always wake you.
4. **The other party to the contract.** [Appendix C](./appendix/c_c_abi.md) is the one place in
   this course where somebody else's code has to agree with yours about registers, and it turns
   out you have been getting it right since L01.
5. **The capstone.** Call `shift_bits`, unchanged from L01, from a C program. Then read what the
   compiler produces for the same job and compare.

Two predictions worth making before anything runs:
* whether a watchdog would have caught the atomicity bug from L03.
* how many instructions the compiler needs for `shift_bits` against your nine, and what its cost
  comes to against your 6n + 10.

The second is this lecture's cross-check, and the honest answer is not the flattering one.

---

## Before the lecture
* Finish L05. The watchdog is configured from a table of scattered bits, in the same way the
  timer was configured from a prescaler and a compare value.
* Read [Appendix A](./appendix/a_watchdog.md) and [Appendix B](./appendix/b_sleep.md).

---

## After the lecture
* Read [Appendix C](./appendix/c_c_abi.md) and [Appendix D](./appendix/d_what_to_build.md).
* Work through [Appendix E](./appendix/e_exercises.md). Solutions will be published after the
  lecture.

---

## What you should be able to do afterwards
* Say what a watchdog detects, and name three failures it does not.
* Write the timed sequence correctly, and say what the hardware does when you do not.
* Choose a timeout from a worst-case loop time, and say why the choice is not obvious in either
  direction.
* Explain why `WDRF` must be cleared before `WDE` can be, and what goes wrong on the second run
  of a program that forgets.
* Choose a sleep mode from what the program needs left running, and name the two wake sources
  that survive every mode.
* State the AVR C calling convention: argument registers, return registers, call-saved registers,
  and the register the compiler keeps at zero.
* Call an assembly subroutine from C, and a C function from assembly, and say what each side is
  promising the other.
* Read `avr-gcc -S` output and compare it against assembly you wrote for the same job.

---

## Questions to test yourself
* Your program deadlocks waiting for an interrupt that never comes. Does the watchdog help? What
  if instead it computes a wrong answer very quickly?
* The two writes of the timed sequence must be within four cycles. Why is `cli` before them not
  optional?
* You write the byte `0x08` into `WDTCSR` meaning "the four second timeout". What did you
  actually ask for, and what happens next?
* A program is reset by the watchdog, restarts, and tries to switch the watchdog off. Why might
  it fail, and what has to happen first?
* You put the device into power-down and expect Timer1 to wake it in a second. What actually
  happens?
* You pass a 16-bit value to an assembly subroutine from C. Which registers does it arrive in,
  and which half is in the lower-numbered one?

---

## Reference
* [Appendix A](./appendix/a_watchdog.md): the watchdog, and the timed sequence.
* [Appendix B](./appendix/b_sleep.md): sleep modes and wake sources.
* [Appendix C](./appendix/c_c_abi.md): the C ABI, and calling in both directions.
* [Appendix D](./appendix/d_what_to_build.md): the `watchdog.asm` specification and the C
  interoperation task.
* [Appendix E](./appendix/e_exercises.md): the exercises.
* Appendix F: the worked solutions, published after the lecture rather than with it.
* [L02 Appendix B.3](../L02/appendix/b_subroutines.md#b3-the-calling-contract) for the contract
  this lecture finally introduces you to the other side of.

---

## After the course
This is the last lecture. What you have built is a driver library in assembly, and the habit that
goes with it: **compute the number first, then measure it, and take the disagreement seriously.**

The two written papers in [`exam/`](../../exam/README.md) are there if you want to test yourself
on paper. They gate nothing and no part of the course requires them.

**Real-Time Kernel Design** is the course that follows this one: the same part, the same harness,
the same check by hand and by measurement, building a preemptive kernel one context switch at a
time. It names this course a prerequisite and it means it. L03's ISR contract, L04's stack
arithmetic and C.5's loadable stack pointer, L05's timer arithmetic, and this lecture's C ABI in
both directions are used there rather than recapped. The half of a kernel that must be assembly is
about two files out of a dozen, and knowing *which* two is most of what that course is for.

---
