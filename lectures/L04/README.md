# L04 - Pointers, Arrays and Structs in SRAM

## Agenda
* `X`, `Y` and `Z`: three 16-bit pointers made out of six 8-bit registers.
* `ld`, `st`, and the post-increment and pre-decrement forms that make a walk one instruction.
* `ldd` and `std`: displacement addressing, and why `X` does not have it.
* `lpm`, and the address space no ordinary load can reach.
* Laying a structure out by hand: offsets, size, and what "passing by reference" costs.
* Arrays of structures, and the stride that is not one byte.
* Where in SRAM your structures should actually live, and why `RAMEND + 1` is not it.
* The stack, now that an interrupt can land on top of two nested calls.

---

## Lecture plan
Worked in this order:
1. **Six registers, three pointers.** Read [Appendix A](./appendix/a_pointers.md) and work out,
   before you are told, what distinguishes `ld r16, Z` from `ld r16, Z+` in the value it returns.
   The answer is nothing, and that is the point.
2. **A structure is seven bytes.** Not a type, not a record: seven bytes at an address, and the
   only thing that makes them a structure is that you and your code agree on the offsets.
3. **An array is a stride.** Walking one means adding the *structure's* size to a pointer, which
   is not one and is not a power of two, and that turns out to matter.
4. **Where to put it.** SRAM is 2048 bytes shared between your variables and the stack, and
   nothing on the device notices when they meet.
5. **How deep the stack goes.** A number you can compute in advance, and this lecture's
   cross-check is computing it and then measuring it.

Two predictions worth making before anything runs:
* how many bytes of stack L03's program uses at its worst moment.
* what happens if you store a structure at `RAMEND + 1`.

The first is the cross-check. The second is a trap that a great deal of published AVR code
falls into.

---

## Before the lecture
* Finish L03. This lecture's array is an array of the LED structures L02 defined, and the stack
  arithmetic counts L03's handler.
* Read [Appendix A](./appendix/a_pointers.md) and [Appendix B](./appendix/b_structures.md).

---

## After the lecture
* Read [Appendix C](./appendix/c_stack.md) and [Appendix D](./appendix/d_what_to_build.md).
* Work through [Appendix E](./appendix/e_exercises.md). Solutions will be published after the
  lecture.

---

## What you should be able to do afterwards
* Name the three pointer register pairs and say which registers each is made of.
* Choose between `ld`, `ld Z+`, `ld -Z` and `ldd Z+q` for a given job, and say what each leaves
  the pointer holding.
* Say why `ldd` exists, why it is limited to a displacement of 63, and why `X` cannot do it.
* Read a byte from program memory, and say why it takes a different instruction and a different
  kind of address.
* Lay out a structure by hand and reach any field of it in one instruction.
* Walk an array of structures, and say what the stride is and why it is not the field size.
* Say which addresses in the data space a structure may occupy, and which look usable and are not.
* Compute the deepest the stack will reach in a program with interrupts, and check that it does
  not meet your variables.

---

## Questions to test yourself
* `Z` is `r31:r30`. Which is the high byte, and what does that mean for `movw r30, r24`?
* `ld r16, Z+` and `ldd r16, Z+0` both read the byte `Z` points at. Give two differences.
* Why can `ldd` reach `Z+63` but not `Z+64`, and why is there no `ldd` for `X` at all?
* An array of LED structures starts at `0x0300`. Where does the fourth one start, and what is the
  arithmetic you would write to get there from the first?
* A great deal of AVR code allocates driver structures at `RAMEND + 1`. What is at that address on
  an ATmega328P, and what happens when you store there?
* Your program is two calls deep when an interrupt arrives, and the handler saves five registers
  and makes two more calls. How many bytes of stack are in use at the deepest moment?

---

## Reference
* [Appendix A](./appendix/a_pointers.md): the pointer registers and the addressing modes.
* [Appendix B](./appendix/b_structures.md): structures, arrays, and where they live.
* [Appendix C](./appendix/c_stack.md): the stack, and how deep it goes.
* [Appendix D](./appendix/d_what_to_build.md): the `led_array.asm` specification.
* [Appendix E](./appendix/e_exercises.md): the exercises.
* Appendix F: the worked solutions, published after the lecture rather than with it.
* [L02 Appendix C.2](../L02/appendix/c_led_driver.md#c2-the-structure) for the structure this
  lecture builds arrays of.

---

## Next lecture
* Counting time in hardware instead of in a loop that does nothing else.
* Prescalers, and the five ratios you actually get.
* Turning a period you want into a register value that cannot represent it exactly, and saying
  by how much you missed.
* A blinker that keeps time while the processor does something else.

---
