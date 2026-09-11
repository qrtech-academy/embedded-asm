# Appendix E - Exercises

> **How to check your work.** Exercise 5 is checked by this lecture's test suite: write the file
> at the path the specification gives, then run `make test`. The suite is
> cumulative, so it runs L01's `shift_bits` tests too; if something you write here breaks it, this
> is where it shows up. See [the suite's README](../exercises/test/README.md).
>
> The rest are checked by Appendix F, the worked solutions, published after the lecture. Work each
> one before you read it.
>
> **No hardware is needed for any of this.** [Appendix D](./d_hardware.md) is optional and nothing
> depends on it.

Each exercise is labelled with its kind. There is exactly one **Cross-check**, and here it is
exercise 8.

---

## 1. Four states
**Recall.**

**a)** Give the four combinations of `DDRx` and `PORTx` for a single pin, and say what each one
does to that pin.

**b)** Which of the four is a mistake rather than a choice? Say what a program reading it gets.

**c)** `PINx` is not in that table. Give both of the things it does, and say why neither of them
is what its name suggests.

**d)** You want to toggle one output pin. Give the one-instruction way and the three-instruction
way, and one reason to prefer the short one that is not about speed.

---

## 2. Wiring a button
**Design.**

A button is wired between an ATmega328P pin and ground, with nothing else attached.

**a)** Give the values of `DDRx` and `PORTx` for that pin, and say what each one is doing.

**b)** What does `PINx` read when the button is not pressed? When it is?

**c)** A driver subroutine `btn_pressed` should return 1 when the button is down. Write, in
words, what it has to do to the bit it read, and say why.

**d)** Somebody proposes leaving `PORTx` at 0 and fitting an external pull-down resistor to
ground, wiring the button to 5 V instead. Their polarity is now the intuitive one. Give one real
advantage of their scheme and two reasons nobody does it.

**e)** Your driver reads the pin every millisecond and counts a press each time it sees a 1 then a
0. Presses are being counted several times each. Explain, without using the word "software".

---

## 3. Translating pin numbers
**Hand calculation.**

For Arduino pins **3**, **8** and **13**, give the port, the bit number, the mask, and the data
space addresses of the three port registers. Do this from
[A.6](./a_io_ports.md#a6-arduino-pin-numbers-are-not-port-bits) and
[L01 A.5](../../L01/appendix/a_avr_core.md#a5-the-io-window-two-names-for-one-register), not from
a table you have already been shown.

**a)** Fill in the three rows.

**b)** What is the mask for pin 8, and what would it be if you forgot to subtract 8 first? Say what
the LED does in each case.

**c)** Arduino pins stop at 13. Port B has eight bits. What are the other two, and why can you not
use them?

**Check yourself:** the port and bit for every pin are in
[A.6](./a_io_ports.md#a6-arduino-pin-numbers-are-not-port-bits), and deriving a row is quicker
than looking it up.

---

## 4. What a call leaves behind
**Recall.**

**a)** An `rcall` at byte address `0x0A` calls a subroutine. What two things does the instruction
do, in order?

**b)** Exactly what value goes on the stack? Say whether it is a byte address or a word address,
and give the number.

**c)** Which byte of it ends up at the higher address?

**d)** `SP` was `0x08FF`. What is it inside the subroutine, and what is it after `ret`?

**e)** After the `ret`, what is stored at `0x08FF`?

**f)** A subroutine does one `push` and no `pop`, then `ret`. Describe what happens, and say why
there is no error message.

---

## 5. The LED driver
**Code.**

Write `drivers/source/led.asm` to the specification in [Appendix C](./c_led_driver.md).

**a)** Write all five subroutines. `.include "led.inc"` for the field offsets.

**b)** Run `make test`.

**c)** Disassemble your `led_init` and count how many instructions run in the case where the pin
number is rejected. Compare it against the case where it is accepted.

**d)** Deliberately move the range check to *after* the structure is filled in, rebuild, and say
which test catches it. Then put it back.

---

## 6. Read, modify, write
**Design.**

**a)** Write the three-instruction sequence that sets one bit of a port register, given the mask
in `r24` and the register's address in `X`.

**b)** Somebody replaces it with a single `st X, r24`. Their LED works. Describe precisely what
else on that port stops working, and say why their own test did not catch it.

**c)** Which test in this lecture's suite does catch it? Look it up.

**d)** `led_toggle` needs no read-modify-write at all. Say why, and give the one property that
gives it besides being shorter.

**e)** The AVR has `sbi` and `cbi`, which set and clear one bit of a low I/O register in a single
instruction. Give the reason this driver cannot use them, and note that it has nothing to do with
speed.

---

## 7. Predicting the driver's cost
**Hand calculation.**

You know from L01 that `shift_bits` costs `6n + 10` cycles and `shift_bits_inverted` costs
`7n + 10`, where `n` is the number of shifts.

**a)** Without counting the rest of `led_on`, say how much more it must cost for Arduino pin 13
than for pin 8, and show why.

**b)** Do the same for `led_off`.

**c)** `led_init` calls both shift routines once each. How much more does it cost for pin 13 than
for pin 8?

**d)** Which of the five subroutines is the cheapest for a given pin, and why?

**e)** Explain why you can answer all of the above without knowing how the rest of each subroutine
is written.

---

## 8. Cross-check: a driver whose cost depends on its argument
**Cross-check.** *Compute it by hand, measure it, reconcile.*

Do the parts in order and write each answer down before starting the next.

**a) By hand.** From exercise 7, predict the difference in cycles between `led_on` for Arduino pin
13 and `led_on` for pin 8. Convert it to microseconds at 16 MHz.

**b) In full, on paper.** Write the count out in the shape
[L01 C.4](../../L01/appendix/c_counting_cycles.md#c4-counting-a-routine-on-paper) gives, once for
bit 0 and once for bit 5. Your table has to include the nested call, so it needs a row for the
`rcall` and then every row of `shift_bits` itself. Do this before (c).

**c) By measurement.**

```bash
make measure CALLS="led_init:0x0200:8 led_on:0x0200"
make measure CALLS="led_init:0x0200:13 led_on:0x0200"
```

Two calls, because `led_on` needs a structure that `led_init` had to build first.

**d) Reconcile.** The **difference** between the two pins should come out the same in both. If
your absolute figures disagree while the difference agrees, say what that tells you about where
the error is, and find it: a constant offset is a row you left out of the table, and it is the
same row for both pins.

**e) Now the asymmetry.** Predict whether `led_enabled` takes the same number of cycles when the
LED is on as when it is off. Write the prediction down, then measure both:

```bash
make measure CALLS="led_init:0x0200:13 led_on:0x0200 led_enabled:0x0200"
make measure CALLS="led_init:0x0200:13 led_off:0x0200 led_enabled:0x0200"
```

**f) The discrepancy.** State the difference in cycles and explain it in one sentence. Then say
what it would take to write a version of `led_enabled` whose cost did **not** depend on the answer,
and whether you think it is worth doing.

**g) What it means.** You are bit-banging a protocol that needs a pulse held for exactly 5 µs, and
you are using this driver. Say which of the five subroutines you could use inside that pulse and
which you could not, and give the one change to the *wiring* that would make the problem smaller.

---

## 9. A program that blinks
**Code.**

Extend `drivers/app/main.asm` so that it initialises the LED on pin 13 and toggles it forever.

**a)** Write it. There is no delay routine yet, so it will toggle as fast as the loop runs.

**b)** Work out how fast that is, in cycles per toggle, from your `led_toggle` cost and the loop's
own `rjmp`. Convert it to a frequency.

**c)** An LED toggling at that frequency does not look like it is blinking. Say what it looks like
and why, and what would have to change for it to blink visibly. L05 is where you fix it properly.

**d)** `make build` should report that it built `app.hex`. If you own a board,
[Appendix D](./d_hardware.md) will put it on one.

---
