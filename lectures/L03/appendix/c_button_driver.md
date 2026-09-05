# Appendix C - The Button Driver

## C.1 The task
Write `drivers/source/button.asm`, extend `drivers/app/main.asm` with a handler, and write
`avr::interrupt::Vectors`.

The button driver is the LED driver's mirror image for its first half and something new for its
second. Both are handed an Arduino pin number and build a structure of register addresses; where
`led_init` makes the pin an output, `button_init` makes it an input and switches its pull-up on.
`button_pressed` is `led_enabled` with its answer inverted. The new part is the four subroutines
that turn a pin change interrupt on and off for one pin without disturbing the other seven that
share its vector.

---

## C.2 The structure
Ten bytes, as [`drivers/include/btn.inc`](../../../drivers/include/btn.inc) declares.

| Offset | Field | Size | Holds |
|---|---|---|---|
| 0 | `BTN_PIN_REG` | 2 | Data space address of `PINx` |
| 2 | `BTN_DIR_REG` | 2 | Data space address of `DDRx` |
| 4 | `BTN_PORT_REG` | 2 | Data space address of `PORTx` |
| 6 | `BTN_PCMSK_REG` | 2 | `PCMSK0` for port B, `PCMSK2` for port D |
| 8 | `BTN_PCIE_BIT` | 1 | `PCIE0` for port B, `PCIE2` for port D |
| 9 | `BTN_PIN` | 1 | Bit number within the port, 0 to 7 |
| | `BTN_SIZE` | 10 | Total |

The first three fields are the LED's three, at the same offsets and in the same order. That is
deliberate: a button is an LED's three register pointers plus what it takes to raise an interrupt.

It is also a trap worth naming now, because nothing prevents you passing a button structure to
`led_on`. **Six** bytes at the front are laid out identically, the three pointers, and the
seventh is not: offset 6 is `LED_PIN` in one structure and the low byte of `BTN_PCMSK_REG` in
the other. So `led_on` finds three valid port registers and then a pin number of `0x6B` or `0x6D`,
which is the same failure as reaching for the wrong field within one structure (C.5): `shift_bits`
returns 0 for any argument of 8 or more, the mask is zero, and the subroutine writes nothing at
all and reports success.

---

## C.3 `button_init`
**Arguments:** `r25:r24` is the structure address, `r22` the Arduino pin number.
**Returns:** `r24` is 0 on success, 1 if the pin is not one this driver accepts.

The same shape as `led_init` ([L02 C.3](../../L02/appendix/c_led_driver.md#c3-led_init)), with two
more fields to fill and the direction reversed:

1. Copy the structure pointer into `Z`.
2. Validate, choose the port, and subtract 8 for port B. Reject before writing anything.
3. Store the bit number, the three port register addresses, **the mask register address**
   (`PCMSK0` or `PCMSK2`) and **the PCICR bit number** (`PCIE0` or `PCIE2`).
4. Make the pin an **input**: call `shift_bits_inverted`, then read `DDRx`, `and` the mask, write
   it back.
5. Switch the **pull-up** on: call `shift_bits`, then read `PORTx`, `or` the mask, write it back.
6. Return 0.

### Pinned details
**Store the PCICR bit number before you call anything.** Whatever register you loaded it into is
call-clobbered, and `shift_bits` will take it
([L02 B.4](../../L02/appendix/b_subroutines.md#b4-calling-a-subroutine-from-a-subroutine)). The
same applies to the mask register address. Fill the structure first, then configure the hardware.

**Steps 4 and 5 are `led_init`'s two steps with the masks swapped.** The LED clears `PORTx` and
sets `DDRx`; the button clears `DDRx` and sets `PORTx`. If you find yourself writing something
structurally different, one of the two is wrong.

**`PCMSK0` and `PCMSK2` are at `0x6B` and `0x6D`**, which is extended I/O, so nothing here can use
`in` or `out` ([A.5](./a_interrupts.md#a5-pin-change-interrupts)).

---

## C.4 `button_pressed`
**Arguments:** `r25:r24` is the structure address.
**Returns:** `r24` is 1 if the button is down, 0 if it is up.

The same shape as `led_enabled`
([L02 C.5](../../L02/appendix/c_led_driver.md#c5-led_enabled)), with one difference that is the
whole reason the subroutine exists:

1. Copy the structure pointer into `Z`.
2. Read the pin number from `BTN_PIN` and call `shift_bits` to turn it into a mask.
3. Read `PINx` through the address in `BTN_PIN_REG`.
4. Mask the two together, and return **1 when the result is zero**.

**Step 4 is inverted, and the inversion is the point.** The pull-up holds the pin high until the
button shorts it to ground, so `PINx` reads 0 when the button is down
([L02 A.5](../../L02/appendix/a_io_ports.md#a5-a-button-and-why-pressed-reads-zero)). Every other
"is it on" subroutine in this library returns 1 for a set bit. This one returns 1 for a clear one,
and writing it the other way round produces a program that is exactly and reliably backwards.

### Pinned details
**Read `PINx`, never `PORTx`.** On an input pin `PORTx` is the pull-up switch, so reading it would
report what you configured rather than what the world is doing, and it would give the same answer
pressed and unpressed. This is `led_enabled`'s rule with the stakes raised: there, the two
registers agree because the pin is an output; here they never agree.

**The branch costs a cycle on one path.** As in `led_enabled`, the natural implementation ends in a
conditional branch, so this subroutine costs one cycle more on one of its two answers. Here it is
the **unpressed** path that is dearer, because pressed is the case that falls through. Notice it
rather than avoiding it: [Appendix D](./d_exercises.md)'s cross-check asks you to account for that
cycle.

**It reports the pin, not the press.** A mechanical button bounces, and this subroutine has no
memory and no timer, so two calls a millisecond apart during a bounce legitimately disagree
([L02 A.5](../../L02/appendix/a_io_ports.md#a5-a-button-and-why-pressed-reads-zero)). What it
reports is the pin, now, and that is all it promises.

---

## C.5 The four interrupt subroutines
All four take the structure address in `r25:r24`.

**`button_enable_interrupt`** sets the port's bit in `PCICR` and the pin's bit in the structure's
mask register. Both are read-modify-write.

**`button_disable_interrupt`** clears the pin's bit in the mask register **and leaves `PCICR`
alone**. `PCICR` enables a whole port's vector and other buttons on that port may still want it;
clearing it here would silently switch off every one of them.

**`button_interrupt_enabled`** returns 1 if the pin's bit in the mask register is set, else 0.

**`button_toggle_interrupt`** calls `button_interrupt_enabled` and then one of the other two.

### Pinned details
**The driver does not touch the global interrupt flag.** No `sei`, no `cli`, anywhere in this
file. You will find AVR drivers that run `sei` at the end of their enable function, and it is
convenient and it is rude: it decides on your behalf that the whole program is now ready to be
interrupted, at a moment chosen by whoever happened to configure a button last. `sei` belongs in
your setup code, once, after everything is configured.

**`button_interrupt_enabled` must return 1 for enabled and 0 for disabled**, and that sentence is
here because the classic mistake is to return them the wrong way round. Nothing about such code
looks wrong: the branch is there, both constants are there, and they are swapped. Every caller
then does the opposite of what it meant, and `button_toggle_interrupt` stops toggling and starts
latching, which is a symptom two steps removed from its cause.

**`button_disable_interrupt` shifts by the pin number**, field at offset 9, not by anything at
offset 0. Reaching for the wrong field gives a shift count of `0x23`, which produces a mask of
zero, which clears nothing; with one button, "nothing happened" and "the right thing happened"
look identical from outside. The test with two buttons is the one that can tell.

**Preserve the structure pointer across the nested call in `toggle`.** `button_interrupt_enabled`
sets `Z` to the same value `toggle` had, so `Z` survives by coincidence, and relying on that is a
decision rather than a fact about the contract. Pushing `r25:r24` and popping them after is two
instructions and four cycles and needs no footnote. Then jump to the enable or disable subroutine
with `rjmp` rather than calling it: it is the last thing you do, so its `ret` can be yours.

---

## C.6 The handler
Add to `drivers/app/main.asm`:

**A vector entry.** `.org` the word address of PCINT0, writing `.org PCI0addr` so that the device
file supplies it, then `rjmp` to your handler
([A.2](./a_interrupts.md#a2-the-vector-table)). AVRASM2 counts `.org` in words, so the datasheet's
`0x0006` is the number you write; `0x000C` is the byte
address and lands you in the watchdog's slot.

**A handler** that saves what it uses, asks the button whether it is pressed, toggles the LED if
it is, restores, and executes `reti`. Its shape is the prologue and epilogue from
[B.2](./b_isr_contract.md#b2-sreg-first-and-sreg-last), with three instructions in the middle.
**Call it `isr_pcint0`**, exactly, because two things outside your program
look for it by that name: the measurement command in [Appendix D](./d_exercises.md), and the test
suite.

**Setup** that initialises the LED on pin 13 and the button on pin 12, enables the button's
interrupt, and then runs `sei` **once**, after everything else. Then a main loop that does nothing.

### Pinned details
**Save `r24`, `r25`, `r18` and `r19` as well as SREG: five things.** The handler passes a pointer
in `r25:r24` and calls subroutines that clobber both, plus `r18` and `r19` inside `shift_bits`.
Every one of those has to be saved, because the interrupted code agreed to nothing. Saving three
and leaving `r18` and `r19` is the mistake that costs you eight cycles less and a bug that appears
only when the main loop happens to be using them.

**The LED and the button must be on different pins.** Putting both on 13 means `button_init` makes
the pin an input after `led_init` made it an output, and the LED stops working in a way that looks
like the handler never runs.

**`sei` goes last, in setup, once.** Not in the driver, and not before the structures are built:
an interrupt arriving before `button_init` has finished would run your handler against a structure
that is half zeros.

**This is the only part of the course a unit test cannot reach.** Everything else you have written
is a subroutine, and a test can call a subroutine; an interrupt has to arrive. So the suite's
`app_test.cpp` loads the whole program, runs it, and changes the pin from outside, which is the
only way to find out whether the vector entry points at your handler, whether `sei` ran, and
whether the handler ends with `reti`. It checks no cycle counts: what your handler costs depends
on what your handler saves, and measuring that is exercise 6's job rather than the suite's.

---

## C.7 What this driver does not do
**It does not debounce.** A press produces several interrupts, a few milliseconds apart, and the
handler runs for every one. An LED toggled by this driver will appear to respond to about half of
your presses, and that is the driver working correctly.

**It does not tell you which way the pin went.** The interrupt fires on press and on release, and
by the time the handler reads the pin it is reading the present, not the edge. Comparing against a
remembered previous state is the usual answer, and it needs a variable shared with the handler
([B.4](./b_isr_contract.md#b4-the-shared-variable)).

**It does not tell you which pin.** One vector serves eight, so a handler with two buttons on one
port has to ask both.

**It does not stop you enabling an interrupt with no handler behind it.** The vector then contains
whatever was there, which for an unwritten slot is `0xFFFF`, and the machine executes off into
unprogrammed flash and eventually restarts
(L01 F.6, exercise 6).

---
