# L03 - Interrupts

## Agenda
* The interrupt vector table, and why a vector holds a jump rather than a handler.
* What the hardware saves when an interrupt fires, which is less than you would like.
* `reti` against `ret`, and the global interrupt enable that sits in SREG.
* Pin change interrupts: one vector per port, eight pins sharing it, and no way to tell which.
* The ISR contract: saving SREG, saving what you use, and why the order matters.
* Atomicity: a sixteen-bit value that is briefly neither of its two correct values.
* The button driver, and the first bug in this course that only appears sometimes.

---

## Lecture plan
Worked in this order:
1. **The table, before any handler.** Twenty-six slots, two words each, and one of them is where
   the machine starts. Read [Appendix A](./appendix/a_interrupts.md) and work out what `.org`
   number a PCINT0 handler needs before you are told.
2. **What happens, cycle by cycle.** The hardware pushes a program counter and clears one flag,
   and everything else is yours to do. This is also where the simulator stops being the
   authority, which is worth knowing about before you trust a measurement.
3. **One vector, eight pins.** Pin change interrupts do not tell you which pin changed, or which
   way it went. The driver has to work both out, and the second one it cannot.
4. **The shared variable.** A counter written by a handler and read by the main loop, and the
   window in which it holds a value it never held.
5. **The driver.** Six subroutines, a structure that is the LED's plus two fields, and a handler
   that composes it with L02's LED driver.

Two predictions worth making before anything runs:
* how long your handler will keep interrupts disabled.
* whether that number is the same each time it runs.

The second is this lecture's cross-check, and the answer is no, twice over.

---

## Before the lecture
* Finish L02. The button driver's structure is the LED's with two fields added, and the handler
  calls `led_toggle`.
* Read [Appendix A](./appendix/a_interrupts.md) and [Appendix B](./appendix/b_isr_contract.md).

---

## After the lecture
* Read [Appendix C](./appendix/c_button_driver.md), which specifies what to write.
* Work through [Appendix D](./appendix/d_exercises.md). Solutions will be published after the
  lecture.

---

## What you should be able to do afterwards
* Turn a vector name into the `.org` directive that puts a handler at it, in both word and byte
  addresses, and say which of the two `.org` wants and which the simulator reports.
* Say what the hardware saves on entry to a handler and what it does not, and write the prologue
  and epilogue that make up the difference.
* Explain why SREG has to be saved before anything that writes flags, and restored after.
* Configure a pin change interrupt, and say what it tells you and what it cannot.
* Identify a variable shared between a handler and the main loop, say how wide the window is in
  cycles, and close it.
* Predict how long your own handler blocks interrupts, and check the prediction.
* Say which parts of interrupt timing this course's simulator models faithfully and which it does
  not, and what you would use instead for the parts it does not.

---

## Questions to test yourself
* PCINT0 is vector 3. What goes after `.org`, and what would the same line have to say if
  this course used `avr-gcc`?
* An interrupt fires while a `ret` is executing. How many cycles pass before the handler's first
  instruction, at the earliest and at the latest?
* Your handler does `inc r24` and nothing else. Name two things wrong with it.
* Two buttons are on port B. One of them is pressed. Which vector fires, and how does the handler
  find out which button it was?
* A handler increments a 16-bit counter and the main loop reads it with two `lds` instructions.
  Give a value the main loop can read that the counter has never held, and say how many cycles
  wide the window is.
* Your handler measures 104 cycles. For how long are interrupts disabled, and why is the answer
  larger than 104?

---

## Reference
* [Appendix A](./appendix/a_interrupts.md): the vector table and the interrupt sequence.
* [Appendix B](./appendix/b_isr_contract.md): the ISR contract, and atomicity.
* [Appendix C](./appendix/c_button_driver.md): the `btn.asm` specification.
* [Appendix D](./appendix/d_exercises.md): the exercises.
* Appendix E: the worked solutions, published after the lecture rather than with it.
* [L02 Appendix A.5](../L02/appendix/a_io_ports.md#a5-a-button-and-why-pressed-reads-zero) for
  the circuit this driver reads, and why a pressed button reads zero.

---

## Next lecture
* `X`, `Y` and `Z` in earnest: three pointers, and the displacement addressing that makes a
  struct field access one instruction.
* Where the seven bytes of an LED structure should actually live, and why `RAMEND + 1` is not it.
* The stack, now that an interrupt can arrive on top of two nested calls.
* Arrays of drivers, and a subroutine that walks one.

---
