# Course Information

## Instructor
Erik Pihl ([erik.axel.pihl@gmail.com](mailto:erik.axel.pihl@gmail.com))

---

## Prerequisites
The subject of this course is **AVR assembly and the machine underneath it**, not embedded
programming in general. Participants are expected to arrive already comfortable with:
* C or C++ for microcontrollers: pointers, structs, bitwise operators, `volatile`.
* Binary and hexadecimal, two's complement, and reading a bit mask such as `(1 << 5)`.
* What a microcontroller peripheral is, and the idea that a register write configures hardware.
* Reading a datasheet section: finding a register, its bit fields, and their meanings.

None of that is taught from scratch. What the course does teach from nothing is the instruction
set, the register file, the calling contract, the vector table, and the toolchain: `avra` as
an assembler, its listing and map files, and simavr as the thing that tells you whether you
were right.

**No assembly experience of any kind is assumed**, on the AVR or anywhere else. If you have
written x86 or ARM assembly, L01 will be short work and the rest will not be: the AVR's
16-bit-pointer-in-three-register-pairs arrangement, its separate program and data address spaces,
and its I/O register window are all different enough to be worth reading rather than skimming.

The course writes AVRASM2 throughout, which is the syntax Microchip Studio assembles, and never
GNU `as`. Nothing is assumed about either.
[L01 Appendix B.7](../lectures/L01/appendix/b_toolchain.md#b7-opening-this-course-in-microchip-studio)
is for readers who want Studio open beside the course, and
[L06 Appendix C.3](../lectures/L06/appendix/c_c_abi.md#c3-calling-your-assembly-from-c) is where the
two dialects are put side by side, because that is the one lecture that needs both.

---

# Course Plan - Embedded Assembly for the ATmega328P

| Week | Lecture | Topic |
|------|---------|------|
| 1 | L01 | The AVR core and the toolchain |
| 3 | L02 | I/O ports and subroutines |
| 5 | L03 | Interrupts |
| 7 | L04 | Pointers, arrays and structs in SRAM |
| 9 | L05 | Timers |
| 11 | L06 | Watchdog, sleep, and the C ABI |

---

## Lecture Content

### L01 - The AVR Core and the Toolchain
What the machine is, and how to make it run something.

Topics include:
* The register file: 32 registers, why `ldi` reaches only half, and what SREG records
* The Harvard architecture: flash, SRAM and EEPROM as three separate address spaces
* The I/O register window, and the difference between `in`/`out` and `lds`/`sts`
* Instruction encoding, and reading a disassembly against the source that produced it
* Cycle counts from the instruction set summary, and your first loop costed by hand
* The toolchain: `avra`, its listing and map files, and simavr
* A first program: a reset vector, a stack pointer, and an LED lit with two `sbi` instructions

---

### L02 - I/O Ports and Subroutines
The first driver, and the contract that makes a subroutine reusable.

Topics include:
* `DDRx`, `PORTx` and `PINx`, and what each of the three actually does
* The internal pull-up, and writing to `PINx` to toggle, which behaves like nothing else
* Arduino Uno pin numbers and the port bits behind them
* `rcall` and `ret`: what goes on the stack, and what it costs in cycles
* The AVR calling contract, and what breaks when a subroutine ignores it
* The `led` driver: `led_init`, `led_on`, `led_off`, `led_toggle`, `led_enabled`

---

### L03 - Interrupts
Code that runs when you are not looking, and everything that follows from that.

Topics include:
* The vector table, `.org`, and why a vector holds a jump rather than a handler
* What the hardware saves on entry (the program counter, and nothing else) and what it does not
* Pin change interrupts: `PCICR`, `PCMSK0..2`, and one handler for eight pins
* Saving and restoring SREG inside a handler, and why `push`/`pop` order matters
* Atomicity: a multi-byte variable shared between a handler and the main loop
* Interrupt latency, computed from the datasheet, and why the simulator is the wrong authority

---

### L04 - Pointers, Arrays and Structs in SRAM
Data structures with no compiler to lay them out for you.

Topics include:
* `X`, `Y` and `Z`: three 16-bit pointers made from six registers, and their increment forms
* `ldd` and `std`: displacement addressing, and why `Z` and `Y` have it and `X` does not
* `lpm` and the program memory space, which ordinary loads cannot reach
* Laying out a struct by hand: offsets, sizes, and passing one by reference
* The stack: how `push`, `rcall` and an interrupt all use the same pointer
* An array of LED structures, walked at the structure's stride

---

### L05 - Timers
Counting time in hardware, and the arithmetic of not quite being able to.

Topics include:
* Timer0, Timer1 and Timer2, and what makes the 16-bit one different
* Prescalers, and the five ratios you actually get
* Normal mode and CTC mode; `TCNT`, `OCR`, the compare match, and the flags behind it
* Turning a wanted period into a prescaler and a compare value, and the error left over
* Software-extending a timer to reach periods the hardware cannot
* The `timer` driver, and an interrupt-driven blinker that keeps real time

---

### L06 - Watchdog, Sleep, and the C ABI
Finishing the library, and connecting it to the language everything else is written in.

Topics include:
* The watchdog timer, its prescaler, and its two modes: reset and interrupt
* The timed write sequence, why the hardware demands one, and why `cli` around it is not optional
* `MCUSR` and `WDRF`, and the far longer list of what a watchdog does not protect against
* Sleep modes, `sleep`, the wake-up sources that survive each, and what waking up costs
* The AVR C ABI in full, and reading a C variable from assembly
* Calling in both directions, and reading `avr-gcc -S`: what the compiler was doing all along

---

## Course Material

### Literature
The course material consists of:
* Lecture notes and theory appendices, which carry the material
* Prose specifications of every subroutine you are asked to write
* Exercises completed after each lecture, with worked solutions published once it has been given
* A test suite per lecture, cumulative, run against your own work with `make test`

The primary external reference is the
[ATmega328P datasheet](https://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-7810-Automotive-Microcontrollers-ATmega328P_Datasheet.pdf)
and the
[AVR Instruction Set Manual](https://ww1.microchip.com/downloads/en/devicedoc/atmel-0856-avr-instruction-set-manual.pdf).
Every register and every cycle count the course quotes comes from one of those two, and the
appendices say which.

---

### Software
**What each participant needs**, on an ordinary laptop, with no hardware of any kind:

```bash
sudo apt -y update
sudo apt -y install git make g++ avra binutils-avr simavr libsimavr-dev libelf-dev clang-format
sudo apt -y install gcc-avr avr-libc                   # L06 only
```

* **avra** - AVRASM2-compatible assembler, and the one this course uses throughout. It brings
  `m328Pdef.inc` with it, and the syntax it takes is the syntax Microchip Studio takes, so a
  source file from this course opens and single-steps there unchanged.
* **[binutils-avr](https://gcc.gnu.org/wiki/avr-gcc)** - Needed from **L01**, for `avr-objdump`
  alone. Disassembling your own hex and reading it against what you typed is core L01 material and
  one of its exercises, and the assembler's output is what you disassemble
* **[avr-gcc, avr-libc](https://gcc.gnu.org/wiki/avr-gcc)** - The GNU AVR compiler, needed by
  **L06 alone**, where a C program calls your assembly and the two are linked together. Nothing in
  the first five lectures uses either
* **[simavr](https://github.com/buserror/simavr)** - Free, open-source AVR simulator. The test
  suites do not run the `simavr` command; they link against `libsimavr` and drive the core
  directly, which is what lets a test call one of your subroutines and inspect the machine
  afterwards. `libsimavr-dev` is therefore required, not optional
* **libelf-dev** - Not this course's dependency but the harness's: it links `-lelf` to read an
  ELF's symbol table. Usually already installed, never installed on a clean machine, and its
  absence appears as `cannot find -lelf` from the linker rather than as anything about AVR
* **[clang-format](https://clang.llvm.org/docs/ClangFormat.html)** - Formats every C and C++
  source in the repository, the device headers and L06's capstone alike, against the
  `.clang-format` at the repository root. The assembly gets a lighter pass: trailing whitespace
  and hard tabs only

**Optional, for watching a real LED**: an **Arduino Uno** (or any ATmega328P board) and
`avrdude`, which is a separate package the lists above deliberately leave out:

```bash
sudo apt -y install avrdude
```

Flashing is covered in an appendix to L02, the lecture where an LED first lights up. No exercise
in this course requires it, and no test suite knows whether you own a board.

**Not needed**: Microchip Studio, Atmel Studio, the Arduino IDE, or Windows.

---
