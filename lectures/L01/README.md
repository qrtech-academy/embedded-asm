# L01 - The AVR Core and the Toolchain

## Agenda
* What kind of machine an ATmega328P is, and which of your C intuitions survive contact with it.
* The 32 registers, and why only half of them can be loaded with a constant.
* SREG: the flags every arithmetic instruction writes and every branch reads.
* Three separate address spaces, and why address `0x0060` names three different bytes.
* What an instruction *is*: `ldi r16, 0x2A` taken apart into the sixteen bits it assembles to.
* The toolchain: `avra` as an assembler, its listing and map files, and a simulator that runs
  your code and counts its cycles.
* Your first subroutine, `shift_bits`, costed on paper before it is run.
* A program that lights an LED in two instructions, which is as far as one pin gets you.

---

## Lecture plan
Worked in this order:
1. **The machine, before any code.** Registers, flags, and the three address spaces, read off
   the figures in [Appendix A](./appendix/a_avr_core.md). Nothing runs yet; the point is to know
   what you are writing *for*.
2. **One instruction, taken apart.** `ldi r16, 0x2A` is sixteen bits, and every one of them is
   accounted for. Predict the word before you look at it, then assemble the instruction and
   check it against the listing `avra` writes.
3. **The toolchain, end to end.** One `.asm` file through `avra` to a hex, then the same hex
   into a disassembler and into a simulator. Three views of one artifact.
4. **Counting cycles.** The cost of every instruction you will use, why a branch costs more when
   it branches, and the arithmetic that turns a routine into a number of microseconds.
5. **Writing something.** `shift_bits`, in assembly, costed on paper before it is run, and a
   program that lights an LED so that the lecture ends with something you can see.

Two predictions worth making before anything runs:
* what `ldi r16, 0x2A` assembles to, from the encoding alone.
* how many cycles `shift_bits` takes for an argument of 5, from the instruction table alone.

You will check both, and one of them is the subject of this lecture's cross-check exercise.

---

## Before the lecture
* Install the toolchain, as described in [the course README](../../README.md#building).
* Read [Appendix A](./appendix/a_avr_core.md) and [Appendix B](./appendix/b_toolchain.md).

---

## After the lecture
* Read [Appendix C](./appendix/c_counting_cycles.md) and
  [Appendix D](./appendix/d_first_subroutine.md), which specify what you are asked to write.
* Work through [Appendix E](./appendix/e_exercises.md). Solutions will be published after the
  lecture.

---

## What you should be able to do afterwards
* Say what the 32 registers are, which sixteen an immediate instruction can name, and why the
  other sixteen cannot be named that way.
* Read a line of SREG's contents and say which branch would be taken next.
* Given an address, say which of the three address spaces it belongs to and which instruction
  reaches it; and say why `in`, `lds` and `lpm` are three different instructions rather than one.
* Encode an `ldi` by hand and confirm it against a disassembly.
* Assemble a `.asm` file, disassemble the result, and run it in the simulator.
* Count the cycles of a straight-line routine and of a loop, from the instruction set summary,
  and say why a measured figure at a call site comes out higher than your count of the body.
* Write a subroutine that takes an argument in `r24`, returns a value in `r24`, and returns.
* Write a program that runs on its own: a reset vector, a stack pointer, an LED lit through
  `DDRB` and `PORTB`, and a loop to stop in.

---

## Questions to test yourself
* Why can `ldi` name `r16` but not `r15`, and what does that cost you when you run out of
  registers in the upper half?
* Data space address `0x0025` and I/O address `0x05` are the same register. Which instructions
  take which of the two numbers, and what happens if you give one the other's?
* The register file is addressable as data at `0x0000` to `0x001F`. What could you do with that,
  and why does essentially no program do it?
* A conditional branch costs one cycle when it falls through and two when it branches. A loop
  running `n` times executes its exit branch `n + 1` times. How many of those are taken?
* Your hand count of a subroutine says 40 cycles and the simulator agrees, yet the *call* costs 44
  and the loop around it costs 46 per iteration. Where are the other four, and the two after that,
  without looking anything up?
* Why does `shift_bits(7)` cost more than five times what `shift_bits(0)` costs, and what does
  that imply about a driver that calls it with a pin number?
* Your program writes `DDRB` at I/O address `0x04`, and the test that checks it reads data space
  address `0x24`. Both are right. Which instructions take which of the two numbers?
* You light an LED with `sbi PORTB, 5` and it works. Why can a driver that has to light *any* LED
  not be written that way at all?

---

## Reference
* [Appendix A](./appendix/a_avr_core.md): the machine.
* [Appendix B](./appendix/b_toolchain.md): the tools, including the AVRASM2 mapping if you are
  arriving from Microchip Studio.
* [Appendix C](./appendix/c_counting_cycles.md): cycle counting on paper.
* [Appendix D](./appendix/d_first_subroutine.md): the `utils.asm` specification.
* [Appendix E](./appendix/e_exercises.md): the exercises.
* The two primary documents. Every number this lecture quotes comes from one of them, and the
  appendix says which:
  * [ATmega328P datasheet](https://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-7810-Automotive-Microcontrollers-ATmega328P_Datasheet.pdf)
  * [AVR Instruction Set Manual](https://ww1.microchip.com/downloads/en/devicedoc/atmel-0856-avr-instruction-set-manual.pdf)

---

## Next lecture
* `DDRx`, `PORTx` and `PINx`: three registers per port, and what each of the three actually does,
  which is more than the two `sbi` instructions at the end of this lecture needed to know.
* Why writing a one to `PINx` toggles an output, which is not what the name suggests at all.
* The calling contract: which registers a subroutine may destroy, and which it must give back.
* The LED driver: the same LED, lit by something that can be told which LED to light.

---
