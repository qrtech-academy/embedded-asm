# Appendix C - The LED Driver

## C.1 The task
Write `drivers/source/led.asm`: five subroutines that drive one LED, told which LED to drive by a
pointer to a structure in SRAM.

The driver is the first thing in this course that is a *component* rather than a routine. Nothing
in it knows how many LEDs exist, which port they are on, or which bit; all of that is in the
structure it is handed. That is the whole design, and it is why the same five subroutines serve
fourteen pins across two ports.

Creating `drivers/source/led.asm` is all it takes to switch its tests on.

---

## C.2 The structure
Seven bytes, laid out as [`drivers/include/led.inc`](../../../drivers/include/led.inc) declares.
The offsets are given rather than chosen, because the test suite reads your structure out of SRAM
at these offsets to check that `led_init` built it correctly.

| Offset | Field | Size | Holds |
|---|---|---|---|
| 0 | `LED_PIN_REG` | 2 | Data space address of `PINx`, low byte first |
| 2 | `LED_DIR_REG` | 2 | Data space address of `DDRx` |
| 4 | `LED_PORT_REG` | 2 | Data space address of `PORTx` |
| 6 | `LED_PIN` | 1 | Bit number within the port, 0 to 7 |
| | `LED_SIZE` | 7 | Total |

Two things to notice. The order is the hardware's own, `PINx` then `DDRx` then `PORTx` one byte
apart, so a driver that has the first can reach the others by adding one and two and never has to
know which port it is on. And the last field is the **bit number**, not the Arduino pin number:
the translation happens once, in `led_init`, and everything afterwards works in bits.

Include it with `.include "led.inc"`; `make build` puts `drivers/include` on the include path.

---

## C.3 `led_init`
Fill in the structure and configure the hardware.

**Arguments:** `r25:r24` is the address of the structure. `r22` is the Arduino pin number.
**Returns:** `r24` is 0 on success, 1 if the pin number is not one this driver accepts.

Write it in this order:

1. **Copy the structure pointer into `Z`**, with `movw`. Everything after this is `std` and `ldd`
   against `Z`, and `Z` survives the calls to `shift_bits`
   ([B.4](./b_subroutines.md#b4-calling-a-subroutine-from-a-subroutine)).
2. **Validate and choose the port.** Below 8 is port D. Below 14 is port B, and **subtract 8**
   from the pin number so that it becomes a bit number. Anything else returns 1 immediately,
   before writing anything at all.
3. **Store the bit number and the three addresses.** Load the port's `PINx` address into `X`,
   store it at offset 0, `adiw X, 1` and store at offset 2, `adiw X, 1` again and store at offset
   4. Use `PINB` and `PIND` from `m328Pdef.inc`, adding `0x20` to reach the data space
   ([L01 A.5](../../L01/appendix/a_avr_core.md#a5-the-io-window-two-names-for-one-register)).
4. **Make the pin an output.** Call `shift_bits` with the bit number, then read `DDRx`, `or` the
   mask in, and write it back.
5. **Leave the LED off.** Call `shift_bits_inverted` with the bit number, then read `PORTx`,
   `and` the mask in, and write it back.
6. **Return 0.**

### Pinned details
**Validate before writing.** A rejected pin must leave the structure untouched, so the range check
comes before the first `std`. A driver that fills the structure and then discovers the pin is
invalid has already half-configured something.

**Read the port register *after* calling `shift_bits`, not before.** `shift_bits` destroys `r18`,
`r19` and `r24`, so a driver that loads `DDRx` into `r18` and then calls it gets the mask in `r18`
and the port contents nowhere. This is the single most likely way to get a driver that assembles,
runs, and does nothing.

**Read, modify, write.** Never assign to a port register
([A.7](./a_io_ports.md#a7-reading-modifying-writing)). Seven other pins share it.

**Subtract 8 for port B.** Pin 8 is bit 0. Forgetting produces a mask of zero and an LED that
never lights ([A.6](./a_io_ports.md#a6-arduino-pin-numbers-are-not-port-bits)).

---

## C.4 `led_on`, `led_off` and `led_toggle`
All three take the structure address in `r25:r24` and return nothing.

**`led_on`** reads the bit number from the structure, calls `shift_bits`, then reads `PORTx`, ORs
the mask in, and writes it back.

**`led_off`** is the same with `shift_bits_inverted` and an `and` instead of an `or`. Note that
this is why `shift_bits_inverted` was written as its own loop in L01 rather than as `shift_bits`
followed by `com`: it is called here on the hot path, and the extra `rcall`, `ret` and `com` would
have cost more than the one `inc` per trip that it costs instead.

**`led_toggle`** calls `shift_bits` and then writes the mask to `PINx` and nothing else
([A.3](./a_io_ports.md#a3-writing-to-pinx-toggles-the-output)). No read, no OR, no write-back:
one `st`. It is the shortest of the three and the only one that cannot be interrupted halfway.

---

## C.5 `led_enabled`
**Arguments:** `r25:r24` is the structure address.
**Returns:** `r24` is 1 if the LED is on, 0 if it is off.

Read `PINx`, not `PORTx`. For an output pin the two agree, so it makes no difference here, and it
makes every difference the moment somebody hands this subroutine a pin that is an input: `PORTx`
would report the pull-up setting and `PINx` reports the world.

Mask the value with the bit, and return 1 if the result is non-zero. The natural way to write that
ends with a conditional branch, and **that branch is why this subroutine costs one cycle more when
the answer is yes** ([C.6](#c6-what-it-should-cost)). Do not try to avoid it; notice it.

---

## C.6 What it should cost
Every figure below is measured. You are asked to predict some of them in
[Appendix E](./e_exercises.md) before you look.

The shape of all five subroutines is the same: a fixed part that reads the structure and writes a
register, plus one call to a shift routine whose cost depends on the bit number. So each of them
costs `slope × bit + constant`, and the slope is the interesting half.

| Subroutine | Slope, cycles per bit | Why |
|---|---|---|
| `led_on` | 6 | one `shift_bits` |
| `led_off` | 7 | one `shift_bits_inverted`, which has one more `inc` per trip |
| `led_toggle` | 6 | one `shift_bits` |
| `led_enabled` | 6 | one `shift_bits` |
| `led_init` | 13 | one of each |

**The test suite checks two of these slopes, `led_on`'s and `led_off`'s, and none of the
constants.** It also checks that `led_enabled` costs one cycle more when the answer is yes. That
is a deliberate change from L01, where the specification gave `shift_bits` instruction by
instruction and the test asserted its cost exactly. A driver is a bigger thing with more than one
reasonable shape, and the slope is the part that follows from what it has to do rather than from
how you chose to write it.

The one absolute figure worth having in mind: on the reference implementation `led_on` costs **59
cycles for Arduino pin 13 and 29 for pin 8**, which is 3.7 µs against 1.8 µs at 16 MHz.

---

## C.7 What this driver does not do
**It does not debounce.** Nothing here is about buttons yet, but the same will be true of the
button driver in L03, and it is worth saying once: a driver that reports the state of a pin
reports the state of the pin, bounces included.

**It does not remember anything.** `led_enabled` reads the hardware rather than a flag, which
means it stays right if something else changes the port behind its back, and it also means it
cannot tell you whether the LED is *meant* to be on.

**It does not check that the pin is an output.** `led_on` on a pin that something else has made an
input would enable a pull-up rather than lighting anything. There is no type system here;
the structure is seven bytes and any subroutine will operate on any seven bytes it is given.

**It does not protect one LED from another.** Two structures pointing at the same bit of the same
port both work, and they fight. Nothing detects it.

---
