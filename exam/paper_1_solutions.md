# Paper 1 - Solutions
Full answers to [Paper 1](./paper_1.md), with the marks, and with the wrong answers that are worth
predicting. Every cycle count and every measured figure here was checked in the simulator.

---

## Question 1 - The core and an instruction
**a) [4]** `ldi` is `1110 KKKK dddd KKKK`. The register field is four bits because `ldi` reaches
only the top half of the file, so `dddd` is `20 - 16 = 4`, which is `0100`. The constant `0x3F`
splits into `0011` and `1111`.

```text
    1110  0011  0100  1111   =  0xE34F
```

The common wrong answer is **`0xE43F`**, from writing the constant as one contiguous byte instead
of splitting it across the two `K` nibbles. It is a perfectly legal instruction and it is not the
one that was asked for: decoding `1110 0100 0011 1111` back gives `dddd` = `0011`, so `r19`, and
`K` = `0100 1111`, so `0x4F`. Both the register and the constant came out wrong, and the encoding
still assembles, which is why nothing catches it. The split is the thing to remember: `ldi`'s
eight-bit immediate is in two halves with the register field between them.

**b) [3]** The encoding has four bits for the register, so `ldi` can name only `r16` to `r31`. It
is not that `r4` is special; it is that the instruction has nowhere to put the number 4 that would
not collide with `r20`. To get a constant into `r4`:

```text
    ldi   r16, 0x3F
    mov   r4, r16
```

Two instructions and two cycles, which is the reason drivers keep their working values in the top
half of the file.

**c) [4]**

* **Data space `0x0060`**: `WDTCSR`, the first extended I/O register. Reachable only with `lds`
  and `sts`, because `in` and `out` stop at I/O address `0x3F`, which is data space `0x5F`.
* **Program memory word `0x0060`**: an instruction, in the application section. The vector table
  is 26 vectors of two words each, so it ends at word `0x0033` and the application starts at
  `0x0034`. Reachable with `lpm`, which addresses flash in bytes, so as `0x00C0` and `0x00C1`.
* **EEPROM `0x0060`**: the 97th byte of 1024. No load or store instruction reaches it at all; you
  go through `EEARH:EEARL`, `EEDR` and `EECR`.

One mark of the four is for saying that the three are different address spaces rather than three
views of one, which is the intuition C leaves you with and this device does not honour.

**d) [5]** `0x10 - 0x20` leaves **`0xF0`** in `r16`, and `SREG` reads `0x15`.

| Flag | Value | Why |
|---|---|---|
| `C` | 1 | Unsigned borrow: `0x10` is smaller than `0x20` |
| `Z` | 0 | The result is not zero |
| `N` | 1 | Bit 7 of the result is set |
| `V` | 0 | Signed, this is `+16 - 32 = -16`, which fits in a byte |
| `S` | 1 | `S` is `N` exclusive-or `V` |

The trap is answering `V = 1` because the result "looks negative". `N` reports the bit; `V`
reports whether the bit lies. Here it does not.

---

## Question 2 - A pin, a port, and a cost
**a) [6]**

```text
    sbi   DDRB, 3          2
    sbi   PORTB, 3         2
    ldi   r18, 8           1
    loop, passes 1 to 7    7 x (dec 1 + brne taken 2)   = 21
    loop, pass 8           dec 1 + brne not taken 1     =  2
    cbi   PORTB, 3         2
    ret                    4
                                                    total 34
```

The pass that leaves the loop is the cheap one, because a branch not taken costs one cycle and a
branch taken costs two. Answering `8 x 3 = 24` for the loop, and 35 overall, is the expected slip.

**b) [2]** 34 cycles at 16 MHz is **2.125 microseconds**.

**c) [4]** `dec` sets `Z` only when the result is zero, and `0 - 1` is `255`. So the loop runs
**256 times**, which is the longest it can run rather than the shortest:

```text
    5 + (255 x 3 + 2) + 2 + 4 = 778 cycles, 48.6 us
```

Measured: 778. The lesson is that an 8-bit down-counter loaded with zero is the idiom for "all of
them", and that `dec` reports zero, not sign.

**d) [3]** 1 ms at 16 MHz is 16000 cycles, and the whole routine tops out at 778. The two changes:

* **Count wider.** Nest a second counter, or use a register pair with `sbiw`, which gets you to
  65536 iterations and past 16000 cycles.
* **Stop counting.** Use Timer1, because a delay loop this long is 16000 cycles in which the
  processor is not available for anything else, and the timer costs you nothing.

Full marks need both, and the second is the answer the course wants: a millisecond is a long time.

**e) [3]** Writing a one into a bit of `PINx` **toggles** the corresponding bit of `PORTx`. It is
not a read of the pin and it is not a write to the pin; the name is simply misleading.

It works here because the routine's own `cbi` leaves `PORTB` bit 3 at zero on the way out, so
every call finds a zero and toggles it to one. It goes wrong the moment anything else leaves that
bit set. The clearest case is a pin that was an input with its pull-up enabled, since the pull-up
*is* that same `PORT` bit: the routine then toggles it to zero, holds the pin low for the loop,
and the `cbi` leaves it low. The pulse is upside down, the routine reports nothing, and the
listing still says `sbi`.

---

## Question 3 - A handler that assembles and is wrong
**a) [3]** `push 2 + lds 2 + inc 1 + sts 2 + pop 2 + reti 4` = **13 cycles**. Measured: 13. `reti`
costs the same four cycles as `ret`; measured, both give 5 for a `nop` and a return.

**b) [4]** Response is `4 + whatever is left of the instruction in progress + the vector jump`,
and the table holds `rjmp`, which is 2.

* **Best case, 6 cycles**: the flag was set on an instruction boundary.
* **Worst case, 9 cycles**: a four-cycle instruction, `ret` say, had just begun, so three cycles
  of it remain. The hardware never abandons an instruction part-way.

Two marks of the four are for the reason for the spread rather than the numbers.

**c) [4]** **`SREG` is not saved.** The instruction that introduces the fault is **`inc r24`**,
which writes `Z`, `N`, `V` and `S`. Nothing else in the listing touches a flag: `push`, `pop`,
`lds` and `sts` all leave `SREG` alone, which is exactly why the fault is easy to miss.

The fix is the standard prologue and its mirror, and it costs six cycles: `in r24, SREG` and a
second `push` on the way in, a `pop` and `out SREG, r24` on the way out. Measured, the corrected
handler is 19 cycles against 13.

**d) [4]** The main program compares and branches:

```text
    cpi   r18, 10
    brne  somewhere
```

An interrupt is taken between those two instructions. The handler increments `count` from, say,
`0x0F` to `0x10`, which is not zero, so it leaves `Z` clear. `reti` restores the program counter
and the `I` flag; it does not restore `SREG`. The `brne` now branches on the handler's result
rather than on the comparison, and the main program takes the wrong path with `r18` holding
exactly 10.

It is intermittent because the window is one instruction wide. The button press has to land in
that specific gap, so the program works for a thousand presses and misbehaves on the next one, and
the bug is not in the code that misbehaves.

**e) [3]** The interleaving, with `count` at `0x00FF`:

```text
    main    lds r24, count       reads 0xFF
    ISR     increments count     0x00FF becomes 0x0100
    main    lds r25, count+1     reads 0x01
    main    now holds 0x01FF
```

`0x01FF` is 511; the counter went from 255 to 256 and was never anywhere near it.

Two fixes:

* **Close the window.** Save `SREG`, `cli`, do both loads, restore `SREG`. Restore rather than
  `sei`, or you enable interrupts in a caller that had deliberately disabled them.
* **Read until it agrees.** Read high, low, high again, and repeat if the two high bytes differ.
  This never disables interrupts, which matters when something else in the system has a deadline.

---

## Question 4 - Structures, pointers, and the stack
**a) [4]** Size **5 bytes**, stride **5 bytes**, and element 2 begins at `0x0140 + 2 x 5 =
0x014A`, so `target` is at `0x014A + 2 = ` **`0x014C`**.

The stride is the trap. It is the size of the structure and nothing else; there is no scaling and
no alignment to make it a power of two, so indexing is a multiplication your code has to do.

**b) [4]** `enabled` is at offset 4:

```text
    ldd   r24, Z+4
```

`X` cannot do it because the instruction set provides `ldd` and `std` for `Y` and `Z` only. With
`X` you either add the offset in and take it out again, or walk with `ld r24, X+`. That is the
whole reason a driver holding a structure pointer keeps it in `Y` or `Z`, and it is worth one mark
to say so.

**c) [2]** The desktop compiler aligns: a two-byte field must start at an even address, so it
inserts padding and rounds the structure's size up. The AVR has no alignment requirement at all;
every load and store is one byte, so alignment buys nothing and the compiler packs the fields
tight. Your hand layout and the C compiler's agree here, which is not something to rely on when
you cross to another machine.

**d) [6]**

```text
    rcall outer          2 bytes of return address
    rcall inner          2
    inner pushes 4       4
    interrupt taken      2 bytes of return address
    handler pushes 3     3
                        13 bytes
```

`SP` reaches `0x08FF - 13 = ` **`0x08F2`**. The stack pointer points at the **next free byte**, so
the lowest byte actually written is **`0x08F3`**.

Measured: with exactly this arrangement the simulator reports `SP` reaching `0x08F2`, 13 bytes
below `RAMEND`.

The off-by-one between `0x08F2` and `0x08F3` is worth a mark on its own, because it is the
difference between "my variables start at `0x08F3` and are safe" and losing one of them.

---

## Question 5 - Timers
**a) [6]** The period is `N x (1 + OCR1A)` and 1 kHz at 16 MHz needs 16000 cycles.

| `N` | `1 + OCR1A` | `OCR1A` | Exact? |
|---|---|---|---|
| 1 | 16000 | 15999 | yes |
| 8 | 2000 | 1999 | yes |
| 64 | 250 | 249 | yes |
| 256 | 62.5 | - | no |
| 1024 | 15.625 | - | no |

Take `N = 1`, `OCR1A = 15999`. All three exact options give exactly 1 kHz, so accuracy does not
choose between them; resolution does. At `N = 1` a tick is 62.5 ns and the nearest other
frequencies are 999.94 and 1000.06 Hz. At `N = 64` a tick is 4 microseconds and the neighbours are
996 and 1004 Hz. The choice costs nothing today and matters the moment the target moves.

**b) [5]** 16 MHz over 3 kHz is 5333.33 cycles, which is not an integer, so 3 kHz is not exactly
reachable.

* `N = 1`, `1 + OCR1A = 5333`, so **`OCR1A = 5332`**.
* Actual frequency `16000000 / 5333 = ` **3000.1875 Hz**.
* Error `+0.1875 / 3000 = ` **+0.00625%**.

Rounding the other way, `1 + OCR1A = 5334`, gives 2999.6 Hz and an error of `-0.0125%`, twice as
far out. Any larger prescaler is worse again: `N = 8` forces `1 + OCR1A = 667` and 2998.5 Hz,
which is `-0.05%`, eight times the error, for no benefit.

**c) [3]** The compare match happens on a fixed 16000-cycle period; what moves is when the pin
gets toggled. An interrupt is only taken at an instruction boundary, and the main program is a
two-cycle `rjmp`, so the flag waits either zero or one cycle depending on the phase. Everything
from the match to the return is an **odd** number of cycles, so the phase flips every period: the
edges are alternately on time and one cycle late, giving gaps of 15999 and 16001 around a true
period of exactly 16000.

Add one cycle to the handler, a single `nop`, and the round trip becomes even, the phase stops
flipping, and every gap measures exactly 16000. Measured, both ways.

The general rule, which L05's cross-check approaches
from the opposite direction, is that **the gaps alternate when `period + handler round trip` is
odd**. There the period is odd and the handler even; here the period is even and the handler odd.
Same arithmetic, and either half will do it.

The wrong answer is that the timer is inaccurate. The timer is exact; the observation is not.

**d) [2]** The slowest is `N = 1024` with `OCR1A = 65535`:

```text
    1024 x 65536 = 67108864 cycles = 4.194 s  ->  0.2384 Hz
```

Below that you extend it in software: run the timer at a convenient rate and count interrupts, so
that one in `k` of them does the work. This is also how one timer serves several different rates
at once.

---

## Question 6 - Watchdog, sleep, and the C ABI
**a) [4]** The selector's low three bits sit at bits 2 to 0, and its top bit sits at **bit 5**.

* **1 s, interrupt, no reset.** Selector 6 is `0110`: top bit clear, low three bits `110`, so
  `0x06`. Add `WDIE` at bit 6, `0x40`. **`0x46`**, with `WDE` left clear.
* **2 s, reset.** Selector 7 is `0111`, so `0x07`. Add `WDE` at bit 3, `0x08`. **`0x0F`**.

The expected wrong answer is `0x4E` for the first, from setting `WDE` as well because "the
watchdog needs enabling". `WDIE` alone is the interrupt-only mode; `WDE` is what makes it a reset.

**b) [4]**

```text
    save SREG, then cli
    wdr                                  restart the timeout from now
    clear WDRF in MCUSR                  or WDE cannot be cleared later
    write (1<<WDCE) | (1<<WDE) to WDTCSR opens the window
    within four cycles: write the byte you want, with WDCE clear
    restore SREG
```

Four cycles is the whole reason for the `cli`. Response to an interrupt is at least six cycles
before the handler's first instruction, and the handler itself is tens of cycles; an interrupt
taken between the two writes does not delay the sequence, it destroys it. `cli` here is not
defensive style, it is a requirement.

**c) [3]** `0x08` is `WDE` set with the selector at zero: **system reset mode with the 16 ms
timeout**. It is worse than an ordinary wrong timeout because the device no longer runs. A wrong
timeout gives a program that mostly works and occasionally resets, which is a bug you can chase; a
16 ms reset loop gives a board that runs for 16 ms at a time, for ever.

Reprogramming means winning a race: the bootloader has to start and accept the upload inside a
window shorter than the watchdog's, every time.

**d) [5]** Arguments are allocated from `r25` downwards, each rounded up to an even number of
registers.

| | Register | Why |
|---|---|---|
| `weight`, `uint8_t` | **`r24`** | a byte still takes the pair `r25:r24`, and uses the low half |
| `value`, `uint16_t` | **`r23:r22`** | the next pair down, low byte in `r22` |
| `offset`, `uint8_t` | **`r20`** | the next pair again, low half used |
| return, `uint16_t` | **`r25:r24`** | |

You may destroy `r18` to `r27`, `r30` and `r31` without saving them, and `r0`, the scratch
register. You must preserve `r2` to `r17`, `r28` and `r29`, and you must leave `r1` holding zero,
because the compiler's own code assumes it without checking.

The expected wrong answer is `r22` for the third argument, from counting arguments rather than
registers. `value` is sixteen bits and takes the whole pair, so the third argument starts at `r20`.
Verified against what `avr-gcc` actually emits.

---
