# Paper 2 - Addresses, Vectors, and What Is Still Running
**Three hours. 100 marks.** Answer all six questions. One question comes from each lecture, and
they carry roughly equal weight; the marks in brackets say how much detail an answer needs.

You may use the [reference sheet](#reference-sheet) at the end of this paper. You may not use a
simulator, an assembler, or a datasheet: every number you need is either on the reference sheet or
is something the course expects you to know.

Two of the listings below are wrong. Both assemble without a warning.

---

## Question 1 - Encodings, registers, and flags (16 marks)
**a)** Assemble `sbi PORTB, 5` by hand into its sixteen bits. Show the field split, and give the
result as a hexadecimal word. **[4]**

**b)** The same instruction cannot be used to set a bit in `TIMSK1`. Say why, and give the
instructions you would write instead. **[4]**

**c)** `r0` and `r1` each carry a convention rather than a hardware rule. Give both conventions,
say who imposes them, and say what breaks if you ignore each one. **[4]**

**d)** A program executes, in order:

```
    ldi   r16, 0x70
    ldi   r17, 0x20
    add   r16, r17
```

Give the value left in `r16` and the state of `C`, `Z`, `N`, `V` and `S`. Then explain in one
sentence why `S` is zero although the result has its top bit set. **[4]**

---

## Question 2 - The port trio and an address trap (18 marks)
A colleague intends to read a switch on PB4.

```
read_switch:
    in    r24, 0x25
    andi  r24, 0x10
    ret
```

**a)** Say which register that `in` actually reads, and explain the mistake in one sentence about
address spaces. **[4]**

**b)** Give the corrected instruction, and one alternative instruction that also works. **[2]**

**c)** Corrected, the routine returns `0x10` when the switch is **not** pressed and `0x00` when it
is. Say what `DDRB` and `PORTB` must hold for that to be true, name the component that makes it
so and say who fitted it, and say what the routine has to do to report a press as non-zero. **[5]**

**d)** The switch is described in the schematic as being on Arduino pin 8. Give the port and bit,
and say in one sentence why the translation is your driver's job rather than the hardware's. **[3]**

**e)** Compare `sbi PORTB, 5` with the sequence `lds`, `ori`, `sts` that has the same effect. Give
both cycle costs, and give the difference that matters more than the cycles. **[4]**

---

## Question 3 - Vectors, and a handler that returns wrongly (18 marks)
**a)** `PCINT0` is the fourth entry in the vector table, and its vector is at word address `0x06`
rather than `0x03`. Explain, and give the word address of the `TIMER1_COMPA` vector, which is the
twelfth entry. **[5]**

**b)** A handler is correct in every respect except that it ends with `ret` instead of `reti`.
Say what still works, what stops working, and roughly when in testing you would notice. **[5]**

**c)** Eight pins share the `PCINT0` vector, and the hardware does not say which one changed. Say
what your driver must keep in order to work it out, and give one thing it can never recover no
matter what it keeps. **[4]**

**d)** Your handler costs 19 cycles including its `reti`, and the vector table holds `jmp`. Give
the length of the window in which interrupts are disabled, show how it is made up, and say what it
means for a second interrupt that arrives during it. **[4]**

---

## Question 4 - A table in flash, and one instruction of difference (16 marks)
Two routines are identical except for one instruction. `table` is eight bytes, `1, 2, 4, 8, 16,
32, 64, 128`, placed in flash at the start of the program.

```
mask_of:                        mask_of_sram:
    ldi   r30, low(table*2)         ldi   r30, low(table*2)
    ldi   r31, high(table*2)        ldi   r31, high(table*2)
    add   r30, r24                  add   r30, r24
    adc   r31, r1                   adc   r31, r1
    lpm   r24, Z                    ld    r24, Z
    ret                             ret
```

**a)** Give what each returns when called with 3, and explain what the second one actually read.
**[6]**

**b)** Give the cycle cost of each, and say where the difference comes from. **[2]**

**c)** The table is bytes, and the index needed no scaling. Say what changes if the table holds
sixteen-bit values instead, and give the instruction sequence you would use to walk it. **[4]**

**d)** A colleague avoids all of this by reserving the table in the data segment, with `.dseg` and
`.byte`, and reading it with `ld`. Say what their table contains at run time and why. **[4]**

---

## Question 5 - Timers (16 marks)
The clock is 16 MHz throughout, and Timer1 is in CTC mode.

**a)** You want a compare match at exactly 50 Hz. Give every prescaler and compare value that
produces it exactly, and say why prescaler 1 is not among them. **[6]**

**b)** You now want 0.1 Hz. Show that Timer1 cannot produce it alone, then give a scheme that
produces it exactly, with the prescaler, the compare value, and the count your software keeps.
**[5]**

**c)** The prescaler steps are 1, 8, 64, 256, 1024. Say what is odd about that sequence and what
it means for the advice "if it does not fit, use the next prescaler up". **[3]**

**d)** Give the highest compare match rate Timer1 can be asked for, and say why a rate near it is
useless in a program that has a handler. **[2]**

---

## Question 6 - Sleep, waking, and a prototype that lies (16 marks)
**a)** Give the byte to write to `SMCR` to select power-down and allow sleeping, and the byte for
idle. Show how you built each. **[4]**

**b)** A device configures Timer1 for a compare match every second, sets power-down, and sleeps at
the bottom of its main loop. Say what happens, and give two wake sources that would have worked.
**[4]**

**c)** You choose the watchdog as the wake source. Say which watchdog mode you must use, and say
what `MCUSR` reads in the main loop after a wake. **[3]**

**d)** Your `shift_bits` takes one byte in `r24` and returns a byte in `r24`. A colleague's header
declares it as `uint16_t shift_bits(uint16_t)`. Their code calls it with 5, and later with 300.
Say what each call returns and why, and say why neither the compiler nor the linker complains.
**[5]**

---

## Reference sheet
**SREG**, bit 7 down to bit 0: `I T H S V N Z C`.

**Instruction encodings**

```text
ldi   1110 KKKK dddd KKKK      d is the register number minus 16
sbi   1001 1010 AAAAA bbb      A is an I/O address, 0 to 31 only
cbi   1001 1000 AAAAA bbb
in    1011 0AAd dddd AAAA      A is an I/O address, 0 to 63
```

**Cycle costs**

```text
ldi, dec, inc, mov, movw, add, adc, sub, cpi, andi, ori, in, out, nop   1
sbi, cbi, push, pop, lds, sts, ld, st, adiw, sbiw                       2
lpm, rcall, jmp                                                         3
ret, reti, call                                                         4
rjmp                                                                    2
brne and friends: 2 when taken, 1 when not
```

**Addresses**, in the data space

```text
PINB 0x23   DDRB 0x24   PORTB 0x25      I/O addresses are these minus 0x20
SPL  0x5D   SPH  0x5E   SREG  0x5F
TIMSK1 0x6F   TCCR1B 0x81   OCR1A 0x88
WDTCSR 0x60   MCUSR 0x54   SMCR 0x53
RAMEND 0x08FF
```

`in` and `out` reach I/O addresses `0x00` to `0x3F`, which is data space `0x20` to `0x5F`.

**Timer1**: the compare match period is `N * (1 + OCR1A)` clock cycles, `OCR1A` is sixteen bits,
and the prescalers `N` are 1, 8, 64, 256 and 1024.

**Vectors**: the table holds 26 vectors, each **two words** wide, and the application section
begins at word `0x0034`.

**Interrupts**: response is `4 + whatever is left of the instruction in progress + the vector
jump`, where `rjmp` costs 2 and `jmp` costs 3. The global enable is cleared by the hardware before
the return address is pushed, and set again by `reti`.

**SMCR**: `SE` is bit 0. The sleep mode selector `SM2 SM1 SM0` sits at bits 3 to 1, with idle
`000`, ADC noise reduction `001`, power-down `010`, power-save `011`.

**The Arduino Uno**: pins 0 to 7 are `PD0` to `PD7`, pins 8 to 13 are `PB0` to `PB5`, and the
built-in LED is pin 13.

**The C ABI**: arguments are allocated from `r25` downwards, each rounded up to an even number of
registers. Returns are in `r24` or `r25:r24`. `r18` to `r27`, `r30` and `r31` are call-clobbered;
`r2` to `r17`, `r28` and `r29` are call-saved; `r1` is zero and `r0` is scratch.

---
