# L02 - I/O Ports and Subroutines

## Agenda
* `DDRx`, `PORTx` and `PINx`: three registers per port, and what each of the three actually does,
  which is more than L01's two `sbi` instructions had to know.
* The internal pull-up, which is a resistor you did not fit and cannot see.
* Writing a one to `PINx`, which toggles the output and is not what the name suggests at all.
* Arduino pin numbers against port bits, and why that translation is your driver's first job.
* `rcall` and `ret`: what goes on the stack, what comes back off it, and what it costs.
* The calling contract: which registers a subroutine may destroy and which it must give back.
* The LED driver: five subroutines, a structure in SRAM, and a cost that depends on the pin.

---

## Lecture plan
Worked in this order:
1. **One pin, four states.** `DDRx` and `PORTx` are two bits, so there are four combinations, and
   each of them does something different. Read [Appendix A](./appendix/a_io_ports.md) and predict
   what a floating input reads before you are told.
2. **The pull-up, and the button that reads backwards.** A pressed button reads zero. That is not
   a convention anybody chose; it falls out of the circuit, and the circuit is drawn.
3. **The translation.** Arduino pin 13 is bit 5 of port B. Derive the mapping from the rule rather
   than reading it off the table.
4. **Subroutines, properly.** What `rcall` pushes, what `ret` does not undo, and the register
   contract that makes a subroutine safe to call from code you did not write.
5. **The driver.** Five subroutines over a structure in SRAM, so that two LEDs can exist without
   the driver knowing there are two.

Two predictions worth making before anything runs:
* what `led_on` costs for Arduino pin 13, given what you already know `shift_bits` costs.
* whether `led_enabled` takes the same time whether the LED is on or off.

The second is this lecture's cross-check, and the answer is no.

---

## Before the lecture
* Finish L01. This lecture calls `shift_bits`, and the LED driver does not work without it.
* Read [Appendix A](./appendix/a_io_ports.md) and [Appendix B](./appendix/b_subroutines.md).

---

## After the lecture
* Read [Appendix C](./appendix/c_led_driver.md), which specifies what to write.
* Work through [Appendix E](./appendix/e_exercises.md). Solutions will be published after the
  lecture.
* Optional: [Appendix D](./appendix/d_hardware.md) puts it on a real board. Nothing needs it.

---

## What you should be able to do afterwards
* Say what each of `DDRx`, `PORTx` and `PINx` does, and give the four states of a pin.
* Configure a pin as an input with its pull-up on, and say what it reads with nothing connected.
* Explain why writing a one to `PINx` toggles an output, and why writing a zero does nothing.
* Translate an Arduino pin number into a port, a bit, a mask and three register addresses.
* Say exactly what `rcall` pushes, in what order, and what `ret` leaves behind.
* Say which registers a subroutine may clobber, and what breaks when it clobbers the others.
* Write a driver that reads, modifies and writes a port register rather than assigning to it, and
  say what goes wrong when it assigns.
* Predict how a driver's cost varies with the pin it was given, and check the prediction.

---

## Questions to test yourself
* `DDRx` bit is 0 and `PORTx` bit is 1. Is that pin an input or an output, and what does it read?
* You want to turn one LED on without disturbing the seven other bits of its port. Write the
  three-instruction sequence, and say why a single `sts` will not do.
* A button is wired from a pin to ground with the internal pull-up on. `btn_pressed` should
  return 1 when it is pressed. What does `PINx` read at that moment, and what must the driver do
  about it?
* `rcall` pushes two bytes. Are they the byte address of the next instruction or its word
  address, and which byte goes at the higher address?
* Your subroutine uses `r16` as scratch and does not restore it. Nothing in this course breaks.
  Give the situation in which something does.
* `led_on` costs 59 cycles for Arduino pin 13 and 29 for pin 8. Where do the 30 cycles go, and
  what does that tell you about wiring an LED to a low-numbered pin?

---

## Reference
* [Appendix A](./appendix/a_io_ports.md): the three port registers, the pull-up, and the pin map.
* [Appendix B](./appendix/b_subroutines.md): `rcall`, `ret`, the stack, and the register contract.
* [Appendix C](./appendix/c_led_driver.md): the `led.asm` specification.
* [Appendix D](./appendix/d_hardware.md): flashing a real Arduino Uno. Entirely optional.
* [Appendix E](./appendix/e_exercises.md): the exercises.
* Appendix F: the worked solutions, published after the lecture rather than with it.
* [L01 Appendix D](../L01/appendix/d_first_subroutine.md) for `shift_bits`, which every
  subroutine in this lecture calls.

---

## Next lecture
* Code that runs when you are not looking: the interrupt vector table, and why a vector holds a
  jump rather than a handler.
* What the hardware saves when an interrupt fires, which is less than you would like.
* Pin change interrupts, and one handler serving eight pins.
* The button driver, and the first bug in this course that only appears sometimes.

---
