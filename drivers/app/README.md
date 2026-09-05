# Your Program
`main.asm`: the vector table, the stack pointer, the setup, and the main loop. This is the file
that turns a pile of subroutines into something that runs on its own, and it is what L03's
integration test loads, because an interrupt cannot be called from a test; it has to arrive.

Put a program here and that test switches itself on, the same way writing a driver switches its
own tests on.

It grows with the course. In L01 it initialises the stack pointer and calls a subroutine. By L06
it has a vector table with a reset vector and two handlers in it: `PCINT0` from L03 and
`TIMER1_COMPA` from L05.

Nothing here is committed. See [the driver library README](../README.md).

---
