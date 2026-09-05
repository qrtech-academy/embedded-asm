# Paper 1 - The Core, the Cost, and the Contract
**Three hours. 100 marks.** Answer all six questions. One question comes from each lecture, and
they carry roughly equal weight; the marks in brackets say how much detail an answer needs.

You may use the [reference sheet](#reference-sheet) at the end of this paper. You may not use a
simulator, an assembler, or a datasheet: every number you need is either on the reference sheet or
is something the course expects you to know.

One of the listings below is wrong. It assembles without a warning.

---

## Question 1 - The core and an instruction (16 marks)
**a)** Assemble `ldi r20, 0x3F` by hand into its sixteen bits. Show the field split, and give the
result as a hexadecimal word. **[4]**

**b)** `ldi r4, 0x3F` does not assemble. Say why, and say what you write instead when the value
really does have to end up in `r4`. **[3]**

**c)** The address `0x0060` names a different byte in each of the three address spaces. Say what
lives there in each, and name the instruction you would use to reach it. **[4]**

**d)** A program executes, in order:

```
    ldi   r16, 0x10
    subi  r16, 0x20
```

Give the value left in `r16`, and the state of the `C`, `Z`, `N`, `V` and `S` flags afterwards.
For each flag, say in a few words why it has that value. **[5]**

---

## Question 2 - A pin, a port, and a cost (18 marks)
A colleague writes this to produce a short pulse on PB3.

```
pulse:
    sbi   DDRB, 3
    sbi   PORTB, 3
    ldi   r18, 8
spin:
    dec   r18
    brne  spin
    cbi   PORTB, 3
    ret
```

**a)** Count the cycles this routine costs, from the first `sbi` to the `ret` inclusive. Show the
loop arithmetic rather than only the total. **[6]**

**b)** How long is that at 16 MHz? **[2]**

**c)** The colleague wants a longer pulse and changes the `ldi` to `ldi r18, 0`. Say what the loop
now does, how many cycles the routine costs, and what that says about `dec` and `brne`. **[4]**

**d)** They then decide that 1 ms is what they actually wanted. Say why this routine cannot be
stretched to give it, and give the two things you would change. **[3]**

**e)** Someone editing this file changes the second line to `sbi PINB, 3`. The pulse still appears
on the pin, on every call. Say what that instruction does, why it still works here, and give a
circumstance in which the same routine would then produce an upside-down pulse. **[3]**

---

## Question 3 - A handler that assembles and is wrong (18 marks)
A pin change on PB4 is meant to count button presses. The vector table holds `rjmp` instructions.

```
tick:
    push  r24
    lds   r24, count
    inc   r24
    sts   count, r24
    pop   r24
    reti
```

**a)** Count the cycles the handler costs, `reti` included. **[3]**

**b)** Using the course's model, give the response time from the flag being set to the handler's
first instruction, in the best case and in the worst case, and say what makes the difference.
**[4]**

**c)** The handler has one fault. Name it, and say exactly which instruction in the listing
introduces it. **[4]**

**d)** Describe a run in which that fault produces a visibly wrong result. Name the interrupted
instruction, say what the main program then does, and say why the bug is intermittent. **[4]**

**e)** `count` is later widened to sixteen bits, the handler is corrected, and the main loop reads
the pair with two `lds` instructions. Give the interleaving that returns a value the counter never
held, and give two different fixes. **[3]**

---

## Question 4 - Structures, pointers, and the stack (16 marks)
A driver keeps this structure in SRAM, laid out by hand in this order:

```text
    count    2 bytes
    target   2 bytes
    enabled  1 byte
```

An array of four of them starts at `0x0140`.

**a)** Give the size of one structure, the stride of the array, and the data space address of the
`target` field of element 2, counting from zero. **[4]**

**b)** `Z` points at the base of one element. Give the instruction that loads `enabled` into `r24`
in one instruction, and say why the same thing cannot be done with `X`. **[4]**

**c)** The equivalent C structure on this device is also five bytes, and on a desktop it would
very likely be more. Say what the desktop compiler is doing and why this device's compiler does
not. **[2]**

**d)** `main` calls `outer`, which calls `inner`. `inner` pushes four registers. While `inner` is
running, a pin change interrupt is taken, and its handler pushes three registers. Give the total
number of bytes in use below `RAMEND` at the deepest point, the value in `SP` there, and the
address of the lowest byte actually written. **[6]**

---

## Question 5 - Timers (16 marks)
The clock is 16 MHz throughout. Timer1 is in CTC mode with `OCR1A` as the top.

**a)** You want a compare match at exactly 1 kHz. Give every prescaler and compare value that
produces it exactly, then choose one and justify the choice in one sentence. **[6]**

**b)** You want 3 kHz. Give the best prescaler and compare value, the frequency you actually get,
and the error as a percentage. **[5]**

**c)** A handler toggles PB0 on every compare match, and the main program is a two-cycle wait
loop. The measured gaps between edges alternate between 16001 and 15999 cycles, with an average of
exactly 16000. Explain the alternation, and say what single change to the handler would remove it
without changing the average. **[3]**

**d)** Give the lowest frequency Timer1 can produce on its own at this clock, and say how you
would produce one below it. **[2]**

---

## Question 6 - Watchdog, sleep, and the C ABI (16 marks)
**a)** Give the byte to write to `WDTCSR` for each of: a 1 second timeout that raises an interrupt
and does not reset; a 2 second timeout that resets. Show how you built each byte. **[4]**

**b)** Write out the timed sequence that changes the watchdog configuration, in order, and say
what the four-cycle window means for the interrupt flag. **[4]**

**c)** A colleague's sequence is correct except that one instruction was added between its two
writes. `WDTCSR` afterwards holds `0x08`. Say what that value means, why it is worse than an
ordinary wrong timeout, and what it does to your ability to reprogram the board. **[3]**

**d)** A C header declares:

```c
uint16_t blend(uint8_t weight, uint16_t value, uint8_t offset);
```

You are writing `blend` in assembly. Say which registers hold each argument, which hold the
result, and which registers you may destroy without saving them. **[5]**

---

## Reference sheet
**SREG**, bit 7 down to bit 0: `I T H S V N Z C`.

**Instruction encodings**

```text
ldi   1110 KKKK dddd KKKK      d is the register number minus 16
subi  0101 KKKK dddd KKKK
sbi   1001 1010 AAAAA bbb      A is an I/O address, 0 to 31 only
cbi   1001 1000 AAAAA bbb
in    1011 0AAd dddd AAAA      A is an I/O address, 0 to 63
```

**Cycle costs**

```text
ldi, dec, inc, mov, movw, add, sub, cpi, andi, in, out, nop   1
sbi, cbi, push, pop, lds, sts, ld, st, adiw, sbiw             2
lpm, rcall, jmp                                               3
ret, reti, call                                               4
rjmp                                                          2
brne and friends: 2 when taken, 1 when not
```

**Addresses**, in the data space

```text
PINB 0x23   DDRB 0x24   PORTB 0x25      I/O addresses are these minus 0x20
SPL  0x5D   SPH  0x5E   SREG  0x5F
WDTCSR 0x60   MCUSR 0x54   SMCR 0x53
RAMEND 0x08FF
```

**Timer1**: the compare match period is `N * (1 + OCR1A)` clock cycles, `OCR1A` is sixteen bits,
and the prescalers `N` are 1, 8, 64, 256 and 1024.

**Watchdog**: the timeout selector is a four-bit number, 0 for 16 ms and each step after that
doubling, so 6 is 1 s and 9 is 8 s. Its low three bits sit at bits 2 to 0 of `WDTCSR`, and its top
bit sits at **bit 5**. `WDE` is bit 3, `WDCE` is bit 4, `WDIE` is bit 6.

**Interrupts**: response is `4 + whatever is left of the instruction in progress + the vector
jump`, where `rjmp` costs 2 and `jmp` costs 3.

**The C ABI**: arguments are allocated from `r25` downwards, each rounded up to an even number of
registers, so the first byte argument arrives in `r24`. Returns are in `r24` or `r25:r24`.
`r18` to `r27`, `r30` and `r31` are call-clobbered; `r2` to `r17`, `r28` and `r29` are call-saved;
`r1` is zero.

---
