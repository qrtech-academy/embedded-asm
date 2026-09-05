# Paper 2 - Solutions
Full answers to [Paper 2](./paper_2.md), with the marks, and with the wrong answers that are worth
predicting. Every cycle count and every measured figure here was checked in the simulator.

---

## Question 1 - Encodings, registers, and flags
**a) [4]** `sbi` is `1001 1010 AAAAA bbb`. `PORTB` is data space `0x25`, so its I/O address is
`0x25 - 0x20 = 0x05`, which is `00101`. The bit number 5 is `101`.

```text
    1001  1010  0010  1101   =  0x9A2D
```

The common wrong answer is **`0x9B2D`**, from putting the data space address `0x25` into the
five-bit field: `0x25` is `100101`, six bits, so the extra one does not vanish; it lands in the
bit above the field and changes the opcode's own low bit, turning `9A` into `9B`. `sbi` speaks I/O
addresses only, and this is the same confusion Question 2 is built on.

**b) [4]** `TIMSK1` is at data space `0x6F`, in extended I/O. `sbi` reaches I/O addresses `0x00` to
`0x1F` only, which is data space `0x20` to `0x3F`; even `in` and `out` stop at data space `0x5F`.
So there is no bit instruction and no I/O instruction that can touch it. You write:

```text
    lds   r24, 0x6F
    ori   r24, (1 << 1)
    sts   0x6F, r24
```

Five cycles instead of two, and no longer a single instruction, which matters for the reason in
Question 2(e).

**c) [4]**

* **`r0` is the scratch register.** It is call-clobbered, and `lpm` writes it when you give no
  destination. Nothing you leave in `r0` survives a call, or a `lpm` you had forgotten about.
* **`r1` is the zero register.** The compiler assumes it holds zero at all times and emits code
  that uses it as a zero operand, `adc r25, r1` for instance.

Both are imposed by the **C ABI**, which is to say by `avr-gcc`, not by the hardware. In assembly
that never meets C, both registers are ordinary. The moment C is linked in, leaving a non-zero
value in `r1` corrupts arithmetic in code you did not write and cannot see. The classic way to do
it by accident is `mul`, which writes its result into `r1:r0`; you must `clr r1` afterwards.

**d) [4]** `0x70 + 0x20 = 0x90`, and `SREG` reads `0x0C`.

| Flag | Value | Why |
|---|---|---|
| `C` | 0 | `0x90` fits in eight bits, nothing carried out |
| `Z` | 0 | The result is not zero |
| `N` | 1 | Bit 7 of the result is set |
| `V` | 1 | Signed, `+112 + 32 = +144`, which does not fit in a signed byte |
| `S` | 0 | `S` is `N` exclusive-or `V` |

`S` is zero because the true signed result is **positive**; the addition overflowed, so bit 7 is
lying about the sign, and `S` is the sign after correcting for that. `N` reports the bit, `V`
reports whether the bit can be believed, and `S` is the answer you actually want. Branching on `N`
here sends you the wrong way; branching on `S` does not.

---

## Question 2 - The port trio and an address trap
**a) [4]** It reads **`TCCR0B`**, Timer0's control register.

`in` takes an **I/O address**, and `0x25` is `PORTB`'s **data space** address. As an I/O address
`0x25` means data space `0x25 + 0x20 = 0x45`, which is `TCCR0B`. The routine reads a timer
configuration byte, masks bit 4, and returns something that has nothing to do with any switch. It
assembles, it runs, and it is stable, which is worse than a crash.

**b) [2]** `in r24, 0x03`, since `PINB` is data space `0x23` and therefore I/O `0x03`. The
alternative is `lds r24, 0x23`, which takes the data space address and costs two cycles instead of
one.

Note that even the intent was slightly wrong: reading `PORTB` would have told the colleague what
they were driving, not what the pin is doing. A switch is read from `PINx`.

**c) [5]** `DDRB` bit 4 must be **0**, making the pin an input, and `PORTB` bit 4 must be **1**.

That second write enables the **internal pull-up resistor**, which was fitted by the manufacturer
inside the chip; it is not on your board and it is not in your schematic. It is reached through the
same `PORT` bit that would drive the pin high if the pin were an output, which is why one register
appears to mean two different things.

With the switch wired to ground, not pressed reads 1 and pressed reads 0, so the routine's sense
is inverted. To report a press as non-zero it must invert the bit, and it should return a clean
`0` or `1` rather than `0x10`: `andi` leaves the bit where it was, so a caller written as
`if (read_switch() == 1)` fails on a value that is not zero.

**d) [3]** Arduino pin 8 is **`PB0`**.

The translation is your driver's job because it exists nowhere in the hardware. The numbers are
printed on the board and used by the Arduino library; the chip has ports and bits and has never
heard of pin 8. Anything that wants to accept a board pin number has to hold that map itself.

**e) [4]** `sbi PORTB, 5` costs **2 cycles**; `lds` 2 plus `ori` 1 plus `sts` 2 is **5**.

The difference that matters more is **atomicity**. `sbi` is one instruction, so an interrupt
cannot be taken part-way through it. The read-modify-write sequence can be interrupted between the
`lds` and the `sts`; if the handler changes a different bit of `PORTB`, the `sts` writes back a
byte read before that change and silently undoes it. The bug appears only when the interrupt lands
in a two-instruction window, so it is rare, real, and very hard to find.

The other difference worth a mark: `sbi` only reaches I/O `0x00` to `0x1F`, so for anything in
extended I/O the slow sequence is not a choice.

---

## Question 3 - Vectors, and a handler that returns wrongly
**a) [5]** Each slot in the table is **two words**, not one, because on a part with 16K words of
flash a `jmp` is a two-word instruction and every slot has to be able to hold one. So the entry
with index `n`, counting from zero, starts at word `2n`.

`PCINT0` is the fourth entry, index 3, so word `0x06`. `TIMER1_COMPA` is the twelfth entry, index
11, so word `22`, which is **`0x16`**. Verified against the table `avr-gcc` emits.

The wrong answer is `0x0B`, from counting entries as one word each. It is worth noticing that this
error puts every vector after the second one in the wrong place, so the symptom is not "one
interrupt does not work" but "the device jumps into the middle of an instruction".

**b) [5]** **What still works:** the return. `ret` pops the same two bytes and costs the same four
cycles, so control goes back to exactly the right instruction and everything the handler did has
been done.

**What stops working:** `reti` is what sets `I` again. The hardware cleared it on entry, so after a
`ret` the global interrupt enable stays clear for ever, and no interrupt of any kind is ever served
again.

**When you notice:** the first press works perfectly and nothing works after it. If the program has
other interrupt sources, a timer say, they all stop at the same moment, which sends you to look at
the timer rather than at the handler that broke it. This is the fault whose symptom points at the
wrong file.

**c) [4]** Keep the **previous sample of `PINB`**, masked to the pins you care about. Exclusive-or
the new sample with the old one to get the bits that changed, then store the new sample.

What you can never recover: **a change that came and went between two samples**. A pulse shorter
than your response time toggles the pin twice, sets the flag once, and reads identically to no
change at all. If two pins change before you sample, you also cannot recover which changed first.
The hardware gives you one flag for eight pins, and the flag is not a queue.

**d) [4]** The window is `4 + vector jump + handler`:

```text
    4    the hardware pushes the return address, with I already cleared
    3    the jmp in the vector
   19    your handler, its own reti included
   26 cycles
```

A second interrupt arriving inside it is **not lost**: its flag stays set and it is served once
`reti` restores `I`, plus the one guaranteed instruction of the main program that the AVR always
executes first. It is **late**, by up to 26 cycles. That number is the whole content of "keep
handlers short", and 19 of the 26 are your handler's. The vector jump is yours to choose as well:
an `rjmp` table would make it 25.

---

## Question 4 - A table in flash, and one instruction of difference
**a) [6]** `mask_of` returns **8**, the entry at index 3. `mask_of_sram` returns **0**. Measured:
8 and 0.

`low(table*2)` and `high(table*2)` gave the byte address of `table` **in flash**, and `ld` reads
the **data space**. With the table at the start of the program, `Z` ends up holding 3, and data
space address 3 is `r3`, a register in the register file. The routine read a CPU register and
returned its contents, which happened to be zero.

The `*2` is there because a label in the code segment is a **word** address to AVRASM2, and `lpm`
takes a **byte** address. It changes nothing about this question, because the table is at zero and
zero doubled is zero, and it is the difference between a routine that works at the start of a
program and one that works anywhere.

That is the reason `lpm` exists as a separate instruction: it is the only way to read flash, and
the address it takes is in a different space from every other load on the machine. The trap is
that both routines assemble, both run, and the wrong one returns a plausible value.

**b) [2]** 11 cycles and 10. `lpm` costs 3 cycles and `ld` costs 2; every other instruction is the
same. Measured, both.

**c) [4]** The index must be **doubled** before it is added, because `lpm` addresses flash in
bytes and the entries are now two bytes apart. Then each entry needs two loads:

```text
    lsl   r24                 index times two
    add   r30, r24
    adc   r31, r1
    lpm   r24, Z+             low byte
    lpm   r25, Z              high byte
```

The confusion to avoid is that the vector table and `.org` count in **words** while `lpm` counts
in **bytes**. Both are true at once, about the same memory.

**d) [4]** At run time it contains **zeros in the simulator, and whatever the SRAM happened to
hold on real hardware**.

`.byte` reserves an address and nothing else. AVRASM2 has no way to give SRAM an initial value,
because an `avra` build has nothing that runs before your code to put one there: the initialisers
it does have, `.db` and `.dw`, live in `.cseg` and put bytes in flash, which is where you started.
Measured: the first element reads 0 rather than 1.

The same fact from the other side is what L06's capstone runs into. A C program *does* get a table
in SRAM, and the thing that puts it there is the startup code `avr-gcc` links in: the same startup
code that sets the stack pointer, copies `.data` from flash, zeroes `.bss` and zeroes `r1`, all of
which the assembly programs in this course did by hand.

---

## Question 5 - Timers
**a) [6]** 50 Hz at 16 MHz needs `16000000 / 50 = 320000` cycles.

| `N` | `1 + OCR1A` | `OCR1A` | Usable? |
|---|---|---|---|
| 1 | 320000 | 319999 | **no**, `OCR1A` is sixteen bits, maximum 65535 |
| 8 | 40000 | 39999 | yes |
| 64 | 5000 | 4999 | yes |
| 256 | 1250 | 1249 | yes |
| 1024 | 312.5 | - | no, not an integer |

Prescaler 1 fails for a different reason from prescaler 1024: the arithmetic is exact, and the
number simply does not fit in the register. **That is what the prescaler is for.** It buys range at
the cost of resolution, and here it costs nothing at all because three of the five are exact.

**b) [5]** 0.1 Hz needs 160,000,000 cycles. Timer1's longest period is

```text
    1024 x 65536 = 67108864 cycles = 4.194 s, which is 0.2384 Hz
```

so 0.1 Hz is out of reach by a factor of about 2.4, and no choice of prescaler and compare value
gets there.

Exactly, in software: take `N = 1024` and `1 + OCR1A = 15625`, so `OCR1A = 15624`. The period is
`1024 x 15625 = 16000000` cycles, which is **exactly one second**. Count interrupts and act on
every tenth. The result has no error at all, because 16 MHz divides by 1024 to give exactly 15625.

**A different pair is equally right.** Taking the smallest prescaler whose ticks still fit gives
`N = 256` with `OCR1A = 62499`, and `256 x 62500` is also exactly 16000000 cycles. Both are exact
one-second ticks; neither is more correct. If your pair differs from either of these, check the
product before you assume it is wrong.

Full marks want the observation that the software count is not an approximation here: the
underlying tick is exact, so the extension is exact.

**c) [3]** The steps are **8, 8, 4, 4**: `1 -> 8` and `8 -> 64` multiply by eight, `64 -> 256` and
`256 -> 1024` by four. The sequence is not geometric. Answering that there is a single odd step,
usually `64 -> 256`, is the expected slip; there are two, and they are the top two.

So "use the next prescaler up" multiplies your reach by four in the top half of the ladder and by
eight in the bottom half, and it is not a smooth adjustment in any case: moving up divides the
required `1 + OCR1A` by
four or eight, and the result has to remain a whole number. A period that is exact at one prescaler
is often not exact at the next. 50 Hz above is exact at 8, 64 and 256, and not at 1024.

**d) [2]** `N = 1` with `OCR1A = 0` gives a compare match **every clock cycle**, 16 MHz.

It is useless because a handler takes tens of cycles. The 19-cycle handler of Question 3 costs 26
cycles from flag to `reti`, so above roughly 615 kHz the processor never leaves the handler, and
well below that the main program stops getting a useful share of the machine.

---

## Question 6 - Sleep, waking, and a prototype that lies
**a) [4]** `SE` is bit 0 and the selector `SM2 SM1 SM0` sits at bits 3 to 1.

* **Power-down** is `010`, so `SM1` is set, which is bit 2: `0x04`. With `SE`: **`0x05`**.
* **Idle** is `000`, so the selector contributes nothing. With `SE`: **`0x01`**.

Writing the mode without `SE` is the mistake worth naming: `sleep` then does nothing at all, the
loop simply runs at full speed, and from outside that is indistinguishable from waking
immediately.

**b) [4]** **Nothing happens, for ever.** Power-down stops the I/O clock, so Timer1 does not count,
the compare match never occurs, and there is nothing to wake the device. It sits there drawing
microamps. No error is reported, because from the hardware's point of view nothing has gone wrong.

Two wake sources that would have worked:

* A **pin change interrupt**, which needs no clock because the pin changing is itself the signal.
* The **watchdog**, which runs from its own oscillator and does not care what else has stopped.

Timer2 in asynchronous mode is a third, but only in **power-save**; it is stopped in power-down
too, and saying so earns the mark.

**c) [3]** **Interrupt mode**: `WDIE` set and `WDE` clear. In reset mode the timeout resets the
device instead of waking it, which is a different program entirely.

`MCUSR` reads whatever it read before the sleep, with **`WDRF` clear**, because no reset happened:
the device was woken by an interrupt and the main loop continued from the instruction after
`sleep`. That is precisely how a program tells "the watchdog woke me" from "the watchdog reset me".

**d) [5]** The prototype changes what the **caller** does; your routine is untouched and cannot
tell.

The compiler now passes the argument in `r25:r24` and reads the result from `r25:r24`.

* **`shift_bits(5)`** puts `r24 = 5` and `r25 = 0`. Your routine reads `r24`, works correctly, and
  returns 32 in `r24`. `r25` is still 0, so the caller reads 32. **The call appears to work**,
  which is the worst part of this question.
* **`shift_bits(300)`** puts `r25:r24 = 0x012C`, so `r24 = 44`. Your routine shifts a byte 44
  times and returns **0** in `r24`. It never touches `r25`, which the caller left holding 1, so
  the caller reads `r25:r24 = 0x0100`, which is **256**. Not the 0 you would predict from the low
  byte alone, and not anything else in the problem either.

Verified: compiled against a reference `shift_bits`, `avr-gcc` emits `ldi r24, 0x2C` and
`ldi r25, 0x01` for the second call, and the routine returns 0 in `r24`.

Nothing complains because C has no name mangling: the linker matches the symbol `shift_bits` to
the symbol `shift_bits` and has no types to compare. The header declaration is the only place the
two sides ever agree, and nothing checks that it is true. This is the price of the ABI being a
convention rather than a contract the tools enforce.

---
