# Appendix E - Exercises
> **How to check your work.** Exercises 5 to 8 are checked by this lecture's test suite: write the
> file at the path the specification gives, then run `make test` from the repository root. Nothing
> has to be registered; creating the file is what switches its tests on. See
> [the suite's README](../exercises/test/README.md).
>
> The rest are checked by Appendix F, the worked solutions, published after the lecture. Work each
> one before you read it. Where an exercise has a plausible wrong answer, F gives that too, and
> says why it is wrong, because being told the right answer teaches you less than being shown the
> one you nearly gave.
>
> **No hardware is needed for any of this.** Everything is written, assembled, simulated and
> measured on your laptop.

Each exercise is labelled with its kind. There is exactly one **Cross-check** per lecture, and in
this one it is exercise 8.

---

## 1. The upper half
**Recall.**

**a)** State which registers `ldi` can name, and which it cannot.

**b)** Explain *why*, from the instruction's encoding rather than from the datasheet's table. Your
answer should mention a specific number of bits.

**c)** You are writing a routine that needs six working registers, and you have used `r16` to
`r21`. A seventh value is a constant you need to load. Somebody suggests `r10`, which is free.
What does that cost you, in instructions and in cycles, every time you set it up?

**d)** Name two instructions other than `ldi` that have the same restriction, and one instruction
that does not.

---

## 2. Assembling three instructions by hand
**Hand calculation.**

Using the encoding in [A.6](./a_avr_core.md#a6-what-an-instruction-is), and nothing else, work out
the 16-bit word each of these assembles to. Show the four nibbles for at least the first one.

**a)** `ldi r16, 0x2A`

**b)** `ldi r24, 0x2A`

**c)** `ldi r31, 0xFF`

**d)** `ldi r20, 0x03`

**e)** One of these is not a legal instruction: `ldi r15, 0x2A`. Say what the assembler does with
it, and what would go wrong if it silently produced a word anyway.

**Check yourself:** the encoding is `1110 KKKK dddd KKKK` with `d = Rd - 16`, and the assembler
will settle it. Put the instructions in a `.asm` file, assemble it, and run
`avr-objdump -D -m avr:5 -b ihex` over the hex; the bytes come out reversed, for the reason in
[B.3](./b_toolchain.md#b3-reading-a-disassembly).

---

## 3. Which space, which instruction
**Recall.**

For each of the following, say which address space it names, what is stored there, and which
instruction or instructions can reach it.

**a)** Data space `0x0005`

**b)** Data space `0x0025`

**c)** I/O address `0x05`

**d)** Data space `0x0100`

**e)** Program word address `0x0006`

**f)** EEPROM address `0x0000`

**g)** Two of the above name the same physical register. Which two, and what happens if you use
one of the two numbers with an instruction expecting the other?

---

## 4. Choosing the branch
**Design.**

`r19` holds a loop counter and `r24` holds a limit. Both are unsigned.

**a)** You want to leave the loop when the counter has reached the limit. Write the two
instructions, and say which flag the second one reads.

**b)** You want to stay in the loop while the counter is strictly below the limit. Write the two
instructions.

**c)** Somebody inserts an `inc r19` between the comparison and the branch. Explain what breaks,
and why the symptom is a branch that goes the wrong way rather than an assembler error.

**d)** Somebody inserts a `mov r20, r19` in the same place instead. Explain why this one is
harmless, and say where you would look it up rather than guessing.

---

## 5. Your first subroutines
**Code.**

Write `shift_bits` and `shift_bits_inverted` in `drivers/source/utils.asm`, to the specification in
[Appendix D](./d_first_subroutine.md).

**a)** Write both. Use `r18` and `r19` as scratch, for the reason in
[D.5](./d_first_subroutine.md#d5-why-r18-and-r19).

**b)** Assemble with `make build`, then disassemble your own routine with
`avr-objdump -D -m avr:5 -b ihex drivers/build/drivers.hex` and read it against what you wrote.
Both flags are required, for the reason in [B.3](./b_toolchain.md#b3-reading-a-disassembly): a hex
file says nothing about its own architecture. At least one line will have come back as a different
instruction than you typed. Say which, and why that is not a mistake.

**c)** Run `make test`.

**d)** Before running anything else: predict what `shift_bits` returns for an argument of 8, and
say what a reader thinking in C would predict instead.

---

## 6. A program that runs on its own
**Code.**

Write `drivers/app/main.asm` to the specification in
[D.6](./d_first_subroutine.md#d6-the-program).

**a)** Write the reset vector, the stack pointer initialisation, a call to `shift_bits`, the two
instructions that light PB5, and the final loop.

**b)** `make build` should now report that it built `app.hex` as well as `drivers.hex`, and
`make test` should report two more passing tests than it did before.

**c)** The hardware sets `SP` to `RAMEND` at reset by itself, so on a cold start your four
instructions change nothing. Give the case where they do change something, and say what would go
wrong without them.

**d)** Remove the final loop and describe, without running it, what the machine does when it
reaches the end of your code. What is in flash after your last instruction?

**e)** Swap the two `sbi` instructions, so that `PORTB` is written before `DDRB`. The LED still
ends up lit. Say what the pin is doing during the one instruction in between, and why that is not
the same thing as being an output that happens to be low.

**f)** You wrote `sbi DDRB, 5`, and the test that checks it reads data space address `0x24`. Both
numbers are right. Explain, and give the one instruction that would write the same register using
`0x24` directly.

---

## 7. Counting by hand
**Hand calculation.**

Using only the table in [C.2](./c_counting_cycles.md#c2-what-each-instruction-costs) and the rule
in [C.3](./c_counting_cycles.md#c3-a-branch-costs-more-when-it-branches), and without running
anything:

**a)** Count the cycles `shift_bits` takes for an argument of 0. Show your working as a line per
instruction, with how many times each one runs.

**b)** Do the same for an argument of 7.

**c)** From those two, write down the general formula in terms of `n`.

**d)** How many times does the `cp` execute when `n` is 3? How many times does the `breq`? How
many of those `breq` executions are taken? These three numbers are not the same, and getting them
confused is the usual reason a hand count comes out wrong.

**e)** Do the same for `shift_bits_inverted`, and state the difference between the two formulas in
one sentence about a single instruction.

---

## 8. Cross-check: what a subroutine costs
**Cross-check.** *Compute it by hand, measure it, reconcile.*

This is the exercise the lecture exists for. Do the parts in order, and write each answer down
before starting the next; the point is lost if you look at the measurement first.

**a) By hand.** From the exercise above, you have a formula. Evaluate it for `n = 0` and for
`n = 7`, and convert both to microseconds at 16 MHz. One cycle is 62.5 nanoseconds, and doing that
conversion in your head once is worth more than a function that does it for you.

**b) The table, in full.** Write out the count for `n = 7` in the shape
[C.4](./c_counting_cycles.md#c4-counting-a-routine-on-paper) gives: one row per instruction, its
cost, how many times it runs, and the product. You will need it in (f), and a formula you cannot
decompose is a formula you cannot find the mistake in.

**c) By measurement.**

```bash
make measure SYMBOL=shift_bits ARG=0
make measure SYMBOL=shift_bits ARG=7
```

**d) Reconcile the two.** They should agree exactly. If they do not, the table is more likely
wrong than the simulator, and the row to check first is the `cp`, which runs `n + 1` times rather
than `n`. Find the mistake before continuing rather than adjusting the formula until it matches.

**e) Now the call site.** Your `main.asm` does not just execute `shift_bits`; it loads an argument
and calls it. Count, by hand, the cycles of those two extra instructions, and write down what a
loop that called `shift_bits(7)` over and over would cost *per iteration*.

**f) The discrepancy.** Your answer to (e) is larger than your answer to (a). State the difference
in cycles, and state it again as a percentage of the (a) figure, once for `n = 0` and once for
`n = 7`. **The two percentages are very different.** Explain why, in one sentence, without using
the word "overhead".

**g) What it means for a driver.** L02's `led_on` calls `shift_bits` with a pin number. Using your
formula, how many times longer does `led_on` take for Arduino pin 13 than for Arduino pin 8?
(Pin 13 is bit 5 of port B; pin 8 is bit 0 of port B.) Say whether that difference would matter,
and give one situation in which it would.

**h)** `make measure` reports a figure that does not include the `rcall`. Is that a defect in the
tool? Give the case for and against, in a sentence each, and say what you would have it do
instead if you disagree with the choice.

---
