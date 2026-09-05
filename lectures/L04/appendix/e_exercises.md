# Appendix E - Exercises

> **How to check your work.** Exercises 5 and 6 are checked by this lecture's test suite: write
> the file at the path the specification gives, then run `make test`. The suite is cumulative and
> runs L01 to L03's tests too. See [the suite's README](../exercises/test/README.md).
>
> The rest are checked by Appendix F, the worked solutions, published after the lecture. Work each
> one before you read it.
>
> **No hardware is needed for any of this.**

Each exercise is labelled with its kind. There is exactly one **Cross-check**, and here it is
exercise 8.

---

## 1. Three pointers
**Recall.**

**a)** Name the three pointer register pairs and the registers each is made of, and say which
register of a pair holds the high byte.

**b)** Which of the three has no displacement form, and which one does compiled C reserve?

**c)** `movw r30, r24` copies a pointer in one instruction. Say why one instruction is enough,
and what would be needed if the two pairs did not agree about byte order.

**d)** Nothing stops you putting a loop counter in `r30`. Give the situation in which that turns
out to be expensive.

---

## 2. Four ways to read a byte
**Hand calculation.**

`Z` holds `0x0204`. The bytes at `0x0202` to `0x0208` are, in order:
`11 22 33 44 55 66 77`.

For each of the following, give the value loaded into `r16` and the value of `Z` afterwards:

**a)** `ld r16, Z`

**b)** `ld r16, Z+`

**c)** `ld r16, -Z`

**d)** `ldd r16, Z+3`

**e)** Two of the four leave `Z` unchanged. Which, and why is that the property that makes
structures cheap?

**f)** All four cost the same. How many cycles, and what does that say about choosing between
them?

---

## 3. Which pointer to use
**Design.**

**a)** A subroutine walks a buffer forwards, one byte at a time, and also has to read fields of a
structure at known offsets. How many pointer registers does it need, which would you choose, and
why not the third?

**b)** A colleague's subroutine uses `Y` and does not save it. Say what breaks, when, and why the
symptom appears in their caller rather than in their subroutine.

**c)** Write down, in words, the four instructions a subroutine using `Y` has to add, and give
their total cost in cycles.

**d)** `ldd` cannot reach a displacement of 70. Give two ways to read that byte anyway, and say
what each costs.

---

## 4. Array arithmetic
**Hand calculation.**

An array of LED structures begins at `0x0300`.

**a)** Give the address of entries 0, 1, 2 and 5.

**b)** What is the stride, and where is it declared?

**c)** A colleague advances the pointer by 6 instead. Give the address their code computes for
entry 2, say which byte of which real entry that is, and describe what the driver would then read
as a port register address.

**d)** Their code produces no error and their first LED works. Explain both.

**e)** An array of *button* structures begins at the same address. Where is entry 3, and why is
the answer different?

**f)** How many LED structures fit in the ATmega328P's SRAM if nothing else used any of it? How
many buttons? Say why neither number is the real limit on how many drivers a program can have.

---

## 5. The LED array
**Code.**

Write `drivers/source/led_array.asm` to the specification in
[Appendix D](./d_what_to_build.md).

**a)** Write all four subroutines.

**b)** Run `make test`.

**c)** Change your stride from `LED_SIZE` to 6, rebuild, and note which tests fail and which still
pass. Then put it back.

**d)** Move the count test in one of the walks from the top of the loop to the bottom, rebuild,
and note which single test catches it. Explain why no other test could.

---

## 6. Where to put things
**Design.**

**a)** For each of `0x0005`, `0x0025`, `0x0068`, `0x0200`, `0x08FF` and `0x0900`, say what is
there and whether a driver structure may live at it.

**b)** A widely copied piece of AVR code allocates its structures at `RAMEND + 1`. Say what that
address is on an ATmega328P, what a store to it does, and what the driver appears to do as a
result.

**c)** The same code on a different AVR, one with external RAM fitted, works. Explain.

**d)** Give two ways to choose an address for a structure, and one advantage of each.

**e)** Your program has one LED structure, one button structure, and an array of six LEDs. How
many bytes of SRAM is that? What fraction of the total?

---

## 7. How deep does it go
**Hand calculation.**

Use the rule in [C.2](./c_stack.md#c2-counting-the-worst-case).

**a)** A program with no interrupts, whose deepest path is a main loop calling a driver which
calls `shift_bits`. How many bytes of stack?

**b)** L03's program: the same main loop, plus an interrupt whose handler saves five registers
and calls `btn_pressed`, which itself calls `shift_bits`. How many bytes?

**c)** Where does the stack pointer end up, and what is the lowest byte actually occupied? These
are not the same number.

**d)** A handler that is nothing but `reti` still costs stack. How much, and why?

**e)** You add the LED array from exercise 5, and the main loop now calls `led_array_all_on`,
which calls `led_on`, which calls `shift_bits`. Redo (b).

**f)** A structure is placed at `0x08F0`. Using your answer to (b), is it safe? Show the
comparison.

---

## 8. Cross-check: how deep the stack really goes
**Cross-check.** *Compute it by hand, compute it with your own code, measure it, reconcile.*

**a) By hand.** Your answer to exercise 7(b).

**b) The lowest byte.** Turn that depth into an address: `SP` points at the next free byte, so
the lowest byte the stack occupies is `RAMEND - depth + 1`. Do this before (c).

**c) By measurement.** Let the program run, press the button, and read the low-water mark:

```bash
make measure IMAGE=app CALLS="--run 4000 --drive B4=0 --run 300 --drive B4=1 --run 300"
```

`--run` lets the program run on its own, which is the only way to reach a handler: an interrupt
cannot be called, it has to arrive. The last line reports how far down the stack pointer went.

**d) Reconcile.** The byte count should agree with (a) and (b). The stack pointer's own value will
be one below the lowest byte you computed, and that is not a disagreement; say why.

**e) Now run it without pressing anything.**

```bash
make measure IMAGE=app CALLS="--run 4000"
```

The measured depth is much smaller. Say what number you get, why it is smaller, and then answer
the question this exercise is really about: **which of your three answers is now wrong, and which
would you ship?**

**f) The rule.** Write down, in one sentence, when a measurement of stack depth is worth more
than the arithmetic and when it is worth less. Then say what a measured depth *larger* than your
computed one would mean, and which of the two you would go and check first.

**g) The margin.** Take your worst-case depth and your structures from exercise 6(e). How many
bytes are free? If a later change added one more level of nesting inside the handler, how much
would that cost, and would you notice?

---

## 9. When it goes wrong
**Design.**

**a)** A wrong stride and an off-by-one loop bound are the two characteristic array bugs. For
each, describe what memory looks like afterwards.

**b)** Neither produces an error. Say what you would actually observe in a program with six LEDs
and a wrong stride.

**c)** The test suite catches both. Say what a test has to do that a program does not, in order to
notice.

**d)** A structure at `0x08F8` and a stack that reaches 15 bytes down. Nothing fails for a week,
and then it does. Give a plausible account of what changed.

**e)** Name one thing you could add to the *program* that would make a stack overflow noticeable
rather than silent, and say what it would cost.

---
