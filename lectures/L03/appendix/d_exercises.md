# Appendix D - Exercises

> **How to check your work.** Exercises 5 and 6 are checked by this lecture's test suite:
> write the file at the path the specification gives, then run `make test`. The suite is
> cumulative and runs L01's and L02's tests too. See
> [the suite's README](../exercises/test/README.md).
>
> The rest are checked by Appendix E, the worked solutions, published after the lecture. Work each
> one before you read it.
>
> **No hardware is needed for any of this.**

Each exercise is labelled with its kind. There is exactly one **Cross-check**, and here it is
exercise 8.

---

## 1. The table
**Recall.**

**a)** How many vectors does the ATmega328P have, how many words does each slot occupy, and how
many words of program memory does the whole table therefore take?

**b)** RESET is in the table. What follows from that about the first instruction of your program?

**c)** A slot is two words. Give the two things that can go in one, and say which this course uses.

**d)** The datasheet says PCINT1 is at `0x0008`. What do you write after `.org`, and what is the
name `m328Pdef.inc` gives that address? Assembly written for `avr-gcc` would need `.org 0x0010`
for the same vector. Where does the factor of two come from?

**e)** What is at word address `0x0007`, and why is it not a place anything may jump to?

---

## 2. Addresses and response times
**Hand calculation.**

**a)** Give the vector number, word address and byte address for PCINT0, PCINT2 and WDT.

**b)** An interrupt flag is set at the exact moment an instruction finishes, and the vector holds
an `rjmp`. How many cycles pass before the handler's first instruction? Show the terms.

**c)** The same, but the flag is set just as a four-cycle `ret` begins.

**d)** The compiler puts `jmp` in vector slots rather than `rjmp`. Redo (b) and (c) for a `jmp`
table, and say in one sentence why a compiler would choose the slower one.

**e)** Your handler measures 104 cycles including its `reti`, and the table uses `rjmp`. For how
long are interrupts disabled? The answer is not 104.

---

## 3. The prologue
**Design.**

A handler is about to be written. It calls `btn_pressed` and `led_toggle`, which between them
use `r18`, `r19`, `r24`, `X` and `Z`, and it uses `r24` and `r25` itself to pass a pointer.

**a)** List every register the handler must save, and say why the list is not "the call-saved
ones".

**b)** Write the prologue and epilogue, including SREG. Give the order precisely.

**c)** Explain why the register is pushed *before* SREG is read, and why SREG is restored *before*
the last `pop`.

**d)** Somebody writes the epilogue as `pop r24`, `pop r25`, `out SREG, r24`, `reti`. Say what is
wrong with it, and describe the symptom in the interrupted program.

**e)** How many cycles do your prologue and epilogue cost together? What fraction is that of a
handler whose useful work is a single `sts`?

---

## 4. One vector, eight pins
**Design.**

**a)** Two buttons are wired to Arduino pins 12 and 13. How many interrupt vectors are involved,
and which?

**b)** One of them is pressed. Describe exactly what the handler is told.

**c)** Write, in words, how the handler works out which button it was.

**d)** The handler wants to know whether the button was *pressed* or *released*. Explain why it
cannot find out from the pin alone, and what it would need to keep in order to know.

**e)** A third button is added on Arduino pin 3. What changes in `PCICR`, what changes in the
mask registers, and how many vectors are now involved?

---

## 5. The button driver
**Code.**

Write `drivers/source/btn.asm` to the specification in [Appendix C](./c_button_driver.md).

**a)** Write all six subroutines.

**b)** Run `make test`.

**c)** Deliberately swap the two return values in `btn_interrupt_enabled`, rebuild, and note
which tests fail. One of them is not about `btn_interrupt_enabled` at all. Explain why it
failed, then put the code back.

**d)** Deliberately make `btn_disable_interrupt` clear `PCICR` as well as the mask bit. Say
which test catches it, and why the test with two buttons does not.

---

## 6. The handler
**Code.**

Extend `drivers/app/main.asm` to the specification in [C.6](./c_button_driver.md#c6-the-handler).

**a)** Write the vector entry, the handler, the setup and the main loop. Put the LED on Arduino
pin 13 and the button on pin 12.

**b)** `make build` should build `app.hex`.

**c)** Move `sei` from the end of setup to the beginning, before the structures are built. Say
whether anything goes wrong in your program as it stands, and why. Then enable the button's
interrupt before `btn_init` as well: describe what could now go wrong, and say why testing it would
probably not show you.

**d)** Put the button on pin 13 as well, so the LED and the button share a pin. Predict what
happens before rebuilding, then check.

---

## 7. The shared counter
**Hand calculation.**

A handler increments a 16-bit counter in SRAM. The main loop reads it with two `lds`
instructions, low byte first.

**a)** The counter holds `0x00FF` and the handler runs between the two `lds`. What value does the
main loop assemble? Give it in hex and in decimal, and say what the counter actually held before
and after.

**b)** How many cycles wide is the window? At 16 MHz, with the handler firing at 1 kHz and the main
loop reading once per millisecond, roughly how often would you expect a torn read?

**c)** Write the fix, and give its cost in cycles.

**d)** The obvious fix has a bug of its own. Say what it is and write the version without it.

**e)** The same handler also sets an 8-bit flag that the main loop reads. Does that need
protecting? Say why, in one sentence about instructions.

---

## 8. Cross-check: how long is the door shut
**Cross-check.** *Compute it by hand, measure it, reconcile.*

Your handler runs with interrupts disabled. This exercise is about finding out for how long, and
about which parts of that number you can measure and which you cannot.

**a) By hand.** Count the cycles of your handler along the path where the button is **not**
pressed: prologue, the call to `btn_pressed`, the compare, the branch taken, epilogue, `reti`.
You measured `led_enabled` this way in L02, and `btn_pressed` measures the same way; if you
have not measured it yet, do that now.

**b) The whole window.** Add the entry to your handler's own cost: four cycles for the hardware's
push, two for the `rjmp` in the vector slot, then the handler, then the `reti`. **This is the one
number in the lecture you cannot check by measuring**, because simavr charges nothing for the
hardware's four-cycle push ([A.4](./a_interrupts.md#a4-what-happens-in-order)). Write it down
anyway, and expect (c) to disagree.

**c) By measurement.**

```bash
make measure IMAGE=app CALLS="led_init:0x0200:13 btn_init:0x0240:12 --drive B4=1 isr_pcint0"
```

`--drive B4=1` holds the button's pin high, which is a button that is **not** pressed. `IMAGE=app`
because a handler lives in your program, not in the driver library. This works at all because
`reti` pops a return address exactly as `ret` does.

**d) Reconcile.** The two should agree. If they do not, the most likely culprits are the branch
you charged one cycle instead of two, and forgetting that the measured figure already includes the
`reti`.

**e) Now the other path.** Predict the pressed-path cost before measuring it:

```bash
make measure IMAGE=app CALLS="led_init:0x0200:13 btn_init:0x0240:12 --drive B4=0 isr_pcint0"
```

State the difference between the two paths and account for every cycle of it. There are five
terms and two of them are negative.

**f) The part you cannot measure.** Add the response time from
[A.4](./a_interrupts.md#a4-what-happens-in-order), not forgetting the one main-program instruction
A.4 guarantees after `reti`, to get the total worst-case delay before a *second* interrupt can be
served. Then set that against what the simulator does: it finishes the
interrupted instruction as the device would, and then charges nothing at all for the push
([A.4](./a_interrupts.md#a4-what-happens-in-order)). Note that there is no measurement to make
here, because the harness offers none for this quantity, which is itself part of the answer. Say
which of your sources you believe and why, and state the general rule you would apply next time a
tool and a datasheet disagree.

**g) What it means.** A second button on the same port is pressed while your handler is running.
Is its interrupt lost or delayed? Now the *same* button bounces twice during the window. Same
question, and the answer is different. Explain both.

---

## 9. Why it responds to half your presses
**Design.**

You build the program, wire a button, and press it. The LED toggles about half the time.

**a)** Explain what is happening, in terms of the circuit rather than the code.

**b)** Roughly how many interrupts does one press generate, and over what timescale?

**c)** Why does "about half" make sense as an outcome, and what would the LED do if a press
generated an odd number of interrupts instead?

**d)** Give three ways to fix it, and say what each one costs. One of them needs something this
course has not covered yet; name the lecture.

**e)** Which of your three is wrong for a button and right for a rotary encoder? Say why.

---
