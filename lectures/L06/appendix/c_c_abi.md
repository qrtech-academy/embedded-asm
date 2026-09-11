# Appendix C - The C ABI

## C.1 The other party
Since L01 you have been following a calling convention
([L02 B.3](../../L02/appendix/b_subroutines.md#b3-the-calling-contract)): arguments in `r24` and
`r22`, results in `r24`, `r18` to `r27` and `r30`, `r31` free to destroy, `r2` to `r17` and `r28`,
`r29` to be given back.

Up to now that convention has had one party. Every caller of your subroutines was code you wrote,
so following the rules was a discipline rather than a requirement, and breaking them would only
ever have surprised you.

This appendix is the other party arriving. The C compiler follows the same convention, so a
function it generates can call a subroutine you wrote, and vice versa, with no glue and no
declaration beyond a prototype. **Everything you have been doing since L01 was for this.**

---

## C.2 The convention, exactly
![The 32 registers coloured by role, with r18 to r27 and r30 to r31 call-clobbered, r2 to r17 and r28 to r29 call-saved, and r24, r25, r22 and r23 marked as the argument and return registers](./images/register_contract.png)

**Arguments go in `r25` downwards, in pairs, left to right.** The first argument takes `r25:r24`,
the second `r23:r22`, the third `r21:r20`, and so on down to `r8`. An 8-bit argument takes only
the lower register of its pair, so the first is `r24`, the second `r22`, the third `r20`, and the
odd-numbered ones are simply not used.

That is worth stating plainly because it is the rule people guess wrong: a byte argument does
**not** move up to fill the gap. Three byte arguments arrive in `r24`, `r22` and `r20`.

**Results come back the same way.** A byte in `r24`, a 16-bit value in `r25:r24`, a 32-bit value
in `r25:r22`.

**Anything larger than fits in the registers goes on the stack**, and so does any argument past
the last pair. Allocation runs from `r25` down to `r8`, which is eighteen registers and therefore
**nine pairs**: `r25:r24`, `r23:r22`, `r21:r20`, `r19:r18`, `r17:r16`, `r15:r14`, `r13:r12`,
`r11:r10`, `r9:r8`. A byte argument takes a pair and wastes the odd half rather than closing the
gap, so six `uint8_t` arguments land in `r24`, `r22`, `r20`, `r18`, `r16` and `r14`. This course
never comes close; a kernel's `task_init` does.

**`r1` is assumed to hold zero.** The compiler relies on it constantly and never checks. A
subroutine that uses `r1` as scratch and does not clear it before returning breaks C code that
had nothing to do with it, at a distance, in a way that looks like a compiler bug. If you use
`mul`, whose result lands in `r1:r0`, clear `r1` afterwards
([L04 B.2](../../L04/appendix/b_structures.md#b2-an-array-is-a-stride)).

**`r0` is scratch for everybody** and nobody expects it preserved.

---

## C.3 Calling your assembly from C
Two things are needed, and neither is a wrapper.

On the assembly side, the subroutine has to be visible to a linker. Everywhere else in this
course that is free, because `avra` makes every label global
([L01 B.2](../../L01/appendix/b_toolchain.md#b2-avra-as-an-assembler)). **Here it is not**, and
that is the first of two reasons this lecture is the one place the course uses a second
assembler.

On the C side, a prototype whose types match what the subroutine actually expects:

```c
extern uint8_t shift_bits(uint8_t shifts);
```

That is all. The compiler puts the argument in `r24` because the prototype says it is a byte, and
reads the result from `r24` for the same reason, and your subroutine has been doing exactly that
since L01.

**The prototype is a promise nothing checks.** Declare the argument as `uint16_t` and the compiler
will pass it in `r25:r24` and your subroutine will read `r24` and ignore `r25`. That gives the same
answers as before, because C would have cut the argument to its low byte anyway, and it is the
dangerous kind of wrong: nothing changes, so nothing tells you. Declare the result as `uint16_t`
too and it stops being harmless. The caller reads `r25:r24`, `r25` still holds the argument's high
byte because your subroutine never touched it, and `shift_bits(300)` comes back as 256. There is
no header, no name mangling and no link-time type check; the linker matches a name to a name.

### The one place this course uses two assemblers
`avr-gcc` drives GNU `as`, and GNU `as` does not read AVRASM2. It cannot assemble
`drivers/source/utils.asm`, and no flag makes it: the two are different languages describing the
same machine. `avra`, for its part, has no linker and cannot combine anything with a compiled
object file.

So for this appendix, and for nothing else in the course, you translate your own `shift_bits`
into GNU `as` and save it as `drivers/source/utils_gnu.S`. The instructions do not change; only
the directives around them do:

| Your `utils.asm` | `utils_gnu.S` |
|---|---|
| `.include "m328Pdef.inc"` | `#include <avr/io.h>` |
| *(nothing; `avra` exports every label)* | `.global shift_bits` |
| `.equ NAME = value` | `.equ NAME, value` |
| `out PORTB, r16` | `out _SFR_IO_ADDR(PORTB), r16` |
| `sts PORTB + 0x20, r16` | `sts PORTB, r16` |
| `.org 0x0006` (words) | `.org 0x000C` (bytes) |

`shift_bits` touches no port, defines no constant and sits in no vector slot, so in practice the
translation is: change the include, add one `.global` line, and copy the body across unchanged.
**The file must be `.S` and not `.s`**, because the capital is what runs the preprocessor that
makes `#include` work.

### The same program, twice
Here is a program that exercises every row of that table at once. It is not one of the course's
exercises; it exists to be read side by side. In AVRASM2, which is what you have been writing:

```asm
.include "m328Pdef.inc"

.equ LED_BIT = 5

.cseg
.org 0x0000
    rjmp reset
.org PCI0addr                   ; 0x0006, a WORD address
    rjmp on_pin_change

.org 0x0034                     ; past the whole table: 26 vectors of 2 words each
reset:                          ; global already; avra exports every label
    ldi r16, (1 << LED_BIT)
    out DDRB, r16               ; DDRB is 0x04, an I/O address
    sts TCCR1B, r16             ; TCCR1B is 0x81, already a data space address
loop:
    rjmp loop

on_pin_change:
    in  r16, PINB               ; PINB is 0x03, an I/O address
    reti
```

And the same program for `avr-gcc`, which is the dialect nearly all published AVR assembly is
written in:

```asm
#include <avr/io.h>

.equ LED_BIT, 5                 /* comma, not = */

.section .text
.org 0x0000
    rjmp reset
.org 0x000C                     /* 0x0006 doubled: .org counts BYTES here */
    rjmp on_pin_change

.org 0x0068                     /* 0x0034 doubled, for the same reason */
.global reset                   /* without this, nothing outside can call it */
reset:
    ldi r16, (1 << LED_BIT)
    out _SFR_IO_ADDR(DDRB), r16 /* DDRB is 0x24 here; the macro takes 0x20 back off */
    sts TCCR1B, r16             /* unchanged: above the I/O window, both call it 0x81 */
loop:
    rjmp loop

.global on_pin_change
on_pin_change:
    in  r16, _SFR_IO_ADDR(PINB)
    reti
```

**Every instruction is identical, and so is every byte.** Assemble both and disassemble the
results:

```text
   0:   33 c0           rjmp    .+102           ; to 0x68
   c:   32 c0           rjmp    .+100           ; to 0x72
        ...                                     ; the rest of the vector table
  68:   00 e2           ldi     r16, 0x20
  6a:   04 b9           out     0x04, r16
  6c:   00 93 81 00     sts     0x0081, r16
  70:   ff cf           rjmp    .-2
  72:   03 b1           in      r16, 0x03
  74:   18 95           reti
```

**The `.org 0x0034` is not padding.** Without it `reset:` starts at word `0x07`, which is the
second word of PCINT0's slot, and the body runs straight through the slots for PCINT1, PCINT2 and
the watchdog. The program still works right up to the moment one of those interrupts is enabled,
and then the vector jumps into the middle of your setup code. Twenty-six vectors of two words each
end at word `0x33`, so `0x34` is the first word that is yours
([L03 A.2](../../L03/appendix/a_interrupts.md#a2-the-vector-table)).

That listing came out of both files. Nothing in the two columns above is a difference of
*machine*; every one of them is a difference of *notation*, and the assembler resolves all of it
before a single byte is emitted. `out DDRB, r16` and `out _SFR_IO_ADDR(DDRB), r16` are two ways
of writing `b9 04`, and the chip has never heard of either.

Three of those rows are worth dwelling on:

* **`.org PCI0addr` against `.org 0x000C`.** The same vector slot. AVRASM2 counts words as the
  datasheet does, GNU `as` counts bytes, and the factor of two between them is the single most
  productive source of wrong-looking interrupt behaviour when code moves between the dialects
  ([L03 A.2](../../L03/appendix/a_interrupts.md)).
* **`DDRB` against `_SFR_IO_ADDR(DDRB)`.** Also the same register. `m328Pdef.inc` calls it `0x04`
  and `<avr/io.h>` calls it `0x24`, and the macro subtracts the `0x20` back off so that `out` can
  reach it
  ([L01 A.5](../../L01/appendix/a_avr_core.md#a5-the-io-window-two-names-for-one-register)).
* **`sts TCCR1B, r16`, which did not change at all.** `TCCR1B` lives above the I/O window, so both
  dialects give it the same data space address and neither can reach it with `out`. The registers
  that need translating are exactly the ones `out` can touch.

Doing this once by hand is the point. That is the whole of the difference between the dialect this
course writes and the dialect most published AVR assembly is written in, and you now have a reason
to read it properly
([L01 B.7](../../L01/appendix/b_toolchain.md#b7-opening-this-course-in-microchip-studio)).

### Building the two together
Hand both files to `avr-gcc`, which recognises `.S` and `.c` and does the right thing with each:

```bash
avr-gcc -mmcu=atmega328p -Os drivers/app/main.c drivers/source/utils_gnu.S -o drivers/build/mixed.elf
```

Note that this is a *different* build from the rest of the course, which assembled one unit with
`avra` and never involved a linker at all
([L01 B.2](../../L01/appendix/b_toolchain.md#b2-avra-as-an-assembler)).
A C program needs the startup code: it is what sets up the stack pointer, clears `.bss`, sets `r1`
to zero, and calls `main`. All the things your `main.asm` had to do by hand.

---

## C.4 Calling C from your assembly
The same convention read backwards. Put the arguments in `r25:r24` and `r23:r22`, `rcall` the
function's name, and take the result from `r24`.

What changes is whose problem the registers are. **A C function will destroy `r18` to `r27` and
`r30`, `r31`**, because the convention says it may, and the compiler takes full advantage. Assembly
that calls C and expects `Z` to survive is relying on nothing.

And **the C function assumes `r1` is zero on entry**, so if your assembly has been using it, put
it back before the call and not merely before the return.

---

## C.5 Reading what the compiler produces
`avr-gcc -S` writes assembly instead of an object file, and it is worth doing at least once with
your own code beside it.

```bash
avr-gcc -mmcu=atmega328p -Os -S drivers/app/main.c -o -
```

Two things are usually surprising the first time.

**The compiler is better at some things than you expect.** A function whose last act is to call
another becomes a `jmp` rather than a `call` and a `ret`. On this part the compiler writes `call`
and `jmp`, because 32 KB of flash is further than `rcall` and `rjmp` reach: the `call` and `ret` it
removes cost eight cycles between them and the `jmp` that replaces them costs three, so the saving
is five cycles and two bytes of stack; that is the tail call from
[L03's driver specification](../../L03/appendix/c_button_driver.md#c5-the-four-interrupt-subroutines),
applied automatically and everywhere.

**And worse at others.** It does not know that a value fits in a byte when the C types say
`int`, it will not use a register you know is free, and it cannot make the arithmetic decisions
you made in L05. [Appendix E](./e_exercises.md)'s cross-check compares the compiler's `shift_bits`
against yours, and the result is not the flattering one you might expect in either direction.

**Read `-Os` output, not `-O0`.** Unoptimised AVR code spills everything to the stack and is not
representative of anything anybody ships.

---

## C.6 What the ABI does not give you
**It does not check anything.** The prototype is a promise, the linker matches names, and a
mismatch is a program that runs and is wrong.

**It does not make your assembly portable.** The convention is `avr-gcc`'s. Another compiler for
the same chip may differ, and the same compiler for a different AVR family does differ in the
details of where large values go.

**And it does not make mixed code easy to reason about.** Every call is a boundary where one side
knows what it destroyed and the other knows what it needed, and neither can see the other. That is
the price of the arrangement, and the reason the convention is worth following from the first
subroutine you write rather than from the first one that C calls.

---

## C.7 Reading a C variable from assembly
Everything so far has been about *calls*: C hands your subroutine registers, your subroutine hands
them back. There is a second half to the boundary and this course has not needed it once, because
every driver here is handed the address of everything it touches. `led_on` gets a pointer in
`r25:r24`; it never looks anything up by name.

Code that shares *state* with C rather than being called by it does look things up by name, and it
is worth doing on paper before you need it.

Given, in some C file:

```c
volatile uint8_t  ticks;
volatile uint16_t deadline;
```

the assembly is:

```asm
    lds  r24, ticks             ; one byte, one instruction
    inc  r24
    sts  ticks, r24

    lds  r24, deadline          ; two bytes, low first, two instructions
    lds  r25, deadline + 1
```

Three things in that are worth stating outright.

**A C global is a data space address, and the linker supplies it.** `ticks` is a name for a byte in
SRAM, somewhere above `0x0100`, chosen when the program was linked. That is why it is `lds` and
`sts` and never `in` and `out`: `in` and `out` reach the first 64 I/O registers and nothing else,
and no C variable ever lives there
([L01 A.5](../../L01/appendix/a_avr_core.md#a5-the-io-window-two-names-for-one-register)). The
mistake reads well and assembles cleanly, and the linker only warns: it cuts the address down to
the six bits `in` has room for and builds the program anyway, so `in r24, ticks` reads whichever
I/O register that lands on and never your variable.

**A 16-bit variable is two loads and the low byte is first.** Which means the same tearing L03
warned about ([L03 B.4](../../L03/appendix/b_isr_contract.md#b4-the-shared-variable)), on the same
terms: two instructions with a gap, and an interrupt that writes `deadline` can land in it.

**A pointer costs one more load than you think.** If C declares `struct thing* current`, then
`current` is a *pointer variable*: two bytes in SRAM holding the address of the structure. Reading
the structure's first field is two loads and then a third:

```asm
    lds  r30, current           ; Z = the pointer's value, not the pointer's address
    lds  r31, current + 1
    ld   r24, Z                 ; and now the field
```

Loading `Z` with the address *of* `current` and dereferencing that gives you the pointer's own
bytes, interpreted as data, which is a plausible-looking small number rather than an error. It is
the single most common way this boundary is got wrong, and the reason is that C hides the
difference: `current->field` is one arrow and two dereferences.

**There is no AVRASM2 half of this section**, and that is the point rather than an omission.
`avra` has no linker ([L01 B.2](../../L01/appendix/b_toolchain.md#b2-avra-as-an-assembler)), so
there is nothing to supply an address that some other file chose; a name in a `.asm` file has to
have been defined in the unit being assembled. Sharing a variable with C is a thing you can only
do in a build that links, which is this lecture's build and no earlier one.

**Where this goes next.** A kernel is exactly the code that shares state with C rather than being
called by it. Its context switch is assembly, its scheduler is C, and the two meet across a single
`struct tcb*` that the C half assigns and the assembly half reads, dereferences and writes back:
the three instructions above, in that order, plus the stack pointer of
[L04 C.5](../../L04/appendix/c_stack.md#c5-the-stack-pointer-is-a-register-you-may-load).

---
