# Embedded Assembly for the ATmega328P
Repository for the course **Embedded Assembly for the ATmega328P**.

This course consists of six lectures and is intended for embedded engineers who write C or C++
for microcontrollers and have never written assembly, or have read some and never produced any.
It takes you from your first `ldi` to a driver library with interrupts, timers and a watchdog,
written entirely in AVR assembly and verified by tests that run on your laptop.

**The subject is the machine.** Assembly is how you get at it; it is not being taught here as a
way to write applications, and this course will not tell you it is faster than your compiler.
What it is good for is narrower and more durable:
* Reading a disassembly and knowing what you are looking at.
* Writing the handful of things C genuinely cannot express.
* Understanding what your compiler was doing all along. 

See [Prerequisites](./info/README.md#prerequisites) for what is assumed.

---

## About the Course
The course covers writing, assembling and verifying AVR assembly for the ATmega328P: the register
file and the three memory spaces, I/O ports, the subroutine calling contract, interrupts, pointer
registers and data structures in SRAM, timers, and the watchdog, each reasoned about as machine
behaviour first and then written.

Topics include:
* The AVR core: 32 registers, SREG, and the Harvard split between flash, SRAM and EEPROM.
* I/O ports, and why writing to `PINx` toggles rather than reads.
* Subroutines: the calling contract, and what happens to the stack when it is ignored.
* Interrupts: the vector table, what the hardware does not save, and the atomicity bugs that
  follow from the difference.
* `X`, `Y` and `Z`, and building C-like structs in SRAM without a compiler.
* Timers, the watchdog, sleep, and the C ABI in both directions.

**One body of code is built across the course, and it is yours to write:** an AVR assembly driver
library (`drivers/`), grown one lecture at a time. `led.asm`, `btn.asm`, `led_array.asm`,
`timer.asm`, `watchdog.asm` and the utilities under them, plus an application program that
composes them.

There is no second language to learn on the way. The only C++ that ships is
[`device/`](./device/README.md), three headers of pinned ATmega328P constants, and it is there so
the test suite can check your assembly against the datasheet rather than against itself. If you
want a host-side library that computes the numbers this course quotes, that is a good exercise and
[`device/README.md`](./device/README.md) says which numbers are worth it; nothing here ships a
contract for it, and nothing checks it.

---

## How Verification Works
Every quantitative claim in this course is checked twice, and the whole method is built on the two
not always agreeing:
* **By hand.** You compute the number from the instruction set summary and the datasheet, before
  any code exists. Nothing automated checks this step, deliberately, and that is the point of it.
* **In the simulator.** The assembly you wrote is assembled, loaded into
  [simavr](https://github.com/buserror/simavr) by a harness this repo provides, and measured:
  cycles consumed, pins driven, SRAM written, interrupts taken.

Where the two disagree, the reconciliation is the lesson, and every lecture has one exercise that
is exactly this. Your hand count of `shift_bits` and the figure the simulator reports at a call
site differ by a fixed amount, and the difference is the `ldi` that set the argument up and the
`rcall` that got you there. Your timer's requested 1000 Hz and its actual 1000.0 Hz agree, and
then at 3 kHz they do not, and the gap is not rounding noise but the distance to the nearest
frequency a whole number of ticks can express.

And once, in L03, they disagree because the **simulator** is wrong: simavr reports a flat
four-cycle interrupt entry where the datasheet says six to nine. Knowing which of your two
instruments to believe, and why, is the skill this arrangement exists to build.

**No exercise in this course needs hardware.** Everything is written, assembled, simulated and
verified on an ordinary laptop. If you own an Arduino Uno or Nano with an ATmega328p processor and
want to watch a real LED, [the flashing appendix](./lectures/L02/appendix/d_hardware.md) covers
`avrdude`; nothing depends on it.

---

## Learning Outcomes
After completing the course, participants should be able to:
* Read an AVR disassembly and say what each instruction does to the register file and to SREG.
* Write a subroutine that obeys the calling contract, and an interrupt handler that obeys the
  stricter one, naming the shared state that makes a main-loop read of it unsafe.
* Build and traverse structured data in SRAM with `X`, `Y` and `Z`.
* Configure a timer for a wanted period, and state the error between what was asked for and what
  the hardware can produce.
* Count the cycles a piece of assembly takes, and then say why the measured figure is higher.
* Call assembly from C and C from assembly, and say what the watchdog does not protect against.

---

## Written Examinations
Nothing in this course is marked. Assessment is the exercises after every lecture, the test suite
each one ships, and the hand calculation you make before running anything.

[`exam/`](./exam/README.md) holds two three-hour papers with worked solutions, and they check
something else: **your own skills and knowledge, on paper, with nothing in front of you.** Six
questions each, one per lecture, mixing theory with instructions you assemble by hand, cycle
counts you work out from a listing, and routines that assemble cleanly and are wrong anyway.

**They are there for you to test yourself with after the course, and nothing more.** They gate
nothing, they are not a qualification, and no part of the course requires them.

---

## Structure

```text
Makefile     Entry point for the checks below; run `make help` for the target list.
ci/          Check scripts: assembly build, test suites, course conventions, links, formatting.
info/        Course info: prerequisites, instructor, course plan, per-lecture topic breakdown.
lectures/    Per lecture: README, appendix/ carrying the material, and a test suite.
drivers/     Your AVR assembly library. Ships the contracts and the build; the bodies are yours.
device/      The pinned ATmega328P constants the test suites check your drivers against.
tools/avrsim The simavr harness the suites run your assembly on, as a git submodule.
libs/test/   The QAcademy Test framework, as a git submodule.
diagrams/    Python sources for the generated figures.
exam/        Two written papers and their solutions. Optional, and marked by nobody here.
```

---

## Building

```bash
make help                # List every target.
make build               # Assemble the drivers and build the simulator harness.
make test                # Build and run every lecture test suite.
make lint                # Conventions, Markdown links, line width, and formatting.
make clean               # Remove everything the build generates.
```

Every one of those runs from the very first commit, when almost nothing exists, and reports what
it could not do by name. A check that silently did not run must never read like one that passed,
so `make build` on a fresh clone builds the two things that ship, prints a `SKIP` line for the
drivers you have not written, and exits 0. That is the truth about a repo where you have not
written anything yet.

The toolchain, on WSL/Ubuntu:

```bash
git clone --recursive https://github.com/qrtech-academy/embedded-asm.git
sudo apt -y update
sudo apt -y install git make g++ avra binutils-avr simavr libsimavr-dev libelf-dev clang-format
sudo apt -y install gcc-avr avr-libc  # L06 only; see below.
avra --version                        # 1.4.2 or newer.
```

Cloned without `--recursive`? `git submodule update --init` fetches the two submodules: the test
framework the suites are written against, and
[avrsim](https://github.com/qrtech-academy/avrsim), the harness they run your assembly on. Both
are ours and neither is coursework; nothing asks you to change either. The kernel course that
follows this one uses the same two, which is most of why they are separate repositories.

`avra` is the assembler, and it is AVRASM2 rather than GNU `as`. That is a deliberate choice: the
source you write here opens unchanged in Microchip Studio, so the register views and the
single-stepping in that debugger apply to your own code rather than to a translation of it. The
device definitions come with the package, in `/usr/share/avra/m328Pdef.inc`.

`libelf-dev` is the one nothing tells you about. It is not this course's dependency: the harness
links `-lelf` to read the symbol table out of an ELF, and the package is so often already present
that its absence only shows up on a clean machine, as `cannot find -lelf` from the linker.

`libsimavr-dev` is the one people miss. `simavr` alone gives you the command-line simulator, and
the test suites do not use it; they link against the library and drive the core themselves, which
is what lets a test call one of your subroutines and read the registers afterwards.

`binutils-avr` is on the first line and not the second, because `avr-objdump` is L01 material:
disassembling your own hex and reading it against what you typed is
[Appendix B.3](./lectures/L01/appendix/b_toolchain.md#b3-reading-a-disassembly) and one of L01's
exercises. It is the assembler's output you disassemble, not a compiler's, so it is needed from the
first lecture even though nothing compiles anything until the last.

`avr-gcc` and `avr-libc` are needed by **L06 alone**, where a C program calls your assembly and the
two are linked together. Nothing in the first five lectures touches them, and skipping them costs
you one appendix rather than the course.

`python3` is needed only to redraw the figures, which are committed as PNGs. See
[diagrams/README.md](./diagrams/README.md) for that one-time setup.

---

## What Comes After
**Real-Time Kernel Design** is the sequel: the same ATmega328P, the same simavr harness and test
framework, and eight lectures spent taking a context switch apart and putting it back together.

It takes this course as a prerequisite in full, and L06 in particular, because the C ABI is the
contract the two halves of a kernel meet across. L03's interrupt material, L04's stack arithmetic
and L05's timer arithmetic are used there directly rather than recapped, which is the other half
of why 2048 bytes and one core are still the right machine to learn this on.

---
