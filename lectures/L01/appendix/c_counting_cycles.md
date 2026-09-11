# Appendix C - Counting Cycles

## C.1 Why bother
On most machines you cannot say what a routine costs. Caches, branch prediction and out-of-order
execution mean the same code takes different times on different runs, and the honest answer to
"how long does this take" is "measure it, repeatedly, and take a distribution".

The ATmega328P has none of those. Every instruction takes a fixed number of cycles, the number is
in a table, and it is the same number every time. So "how long does this take" has an exact answer
you can work out on paper before the code exists, and that changes what is worth doing:

* You can decide between two implementations without writing either.
* You can tell whether a delay loop will meet its deadline without a scope.
* When a measurement disagrees with your count, one of you is wrong about the code, and finding
  out which is a productive afternoon rather than a guess about the hardware.

This appendix is that table, and the arithmetic on top of it.

---

## C.2 What each instruction costs
Every figure here comes from the AVR Instruction Set Manual for this core, and every one was
confirmed by running that instruction in the simulator and subtracting the `ret` around it. Where
the two had disagreed, the disagreement would be written down here. They did not.

| Cycles | Instructions |
|---|---|
| 1 | `ldi` `mov` `movw` `add` `adc` `sub` `subi` `and` `andi` `or` `ori` `eor` `com` `neg` `cp` `cpc` `cpi` `lsl` `lsr` `rol` `ror` `asr` `inc` `dec` `nop` `in` `out` `sei` `cli` |
| 2 | `rjmp` `lds` `sts` `ld` `ldd` `st` `std` `push` `pop` `adiw` `sbiw` `sbi` `cbi` |
| 3 | `rcall` `lpm` |
| 4 | `ret` `reti` |
| 1 or 2 | `breq` `brne` `brlo` `brsh` `brcc` `brcs` and the other conditional branches |

Three rows in that table are worth more attention than the rest.

**`ret` costs four cycles and `rcall` costs three.** Calling a subroutine that does nothing at all
costs seven cycles, which is more than most loops' bodies. That is not an argument against
subroutines; it is the reason a driver's cost is never just the cost of its body, and the reason
[Appendix E](./e_exercises.md)'s cross-check comes out the way it does.

**`sbi` and `cbi` cost two cycles, not one.** They look like single-bit versions of `out`, and
they are not: they read the register, modify one bit, and write it back. Worth remembering when
you are counting a routine that sets several bits one at a time and wondering where the cycles
went.

**A memory access costs twice what a register operation does.** `lds` is two cycles and `mov` is
one, which is the whole argument for keeping working values in registers. On a machine with 32 of
them that is usually possible, and arranging for it is most of what makes assembly fast.

---

## C.3 A branch costs more when it branches
A conditional branch takes **one cycle if it falls through and two if it is taken**. The reason is
that a taken branch changes the program counter, and the instruction already being fetched has to
be thrown away.

This is the single most common source of an off-by-a-few cycle count, because it means a loop's
cost is not the number of iterations times the body.

Take a loop with its test at the top, which is the shape the subroutine in
[Appendix D](./d_first_subroutine.md) needs: compare a running count against the argument, branch
out of the loop when they are equal, do the work, add one to the count, and jump back to the top.

| Step | Cycles | Times it runs |
|---|---|---|
| compare the count against the argument | 1 | `n + 1` |
| branch out when they are equal | 1 falling through, 2 taken | `n + 1` |
| the work, one instruction here | 1 | `n` |
| add one to the count | 1 | `n` |
| jump back to the top | 2 | `n` |

A loop running `n` times executes the branch **`n + 1` times**: `n` of them fall through into the
body, and one is taken to leave. So the branch contributes `n × 1 + 1 × 2 = n + 2` cycles, not
`n + 1` and not `2n`.

Everything else in the loop runs exactly `n` times, except the comparison, which also runs on the
final pass that leaves the loop and so runs `n + 1` times as well. That extra comparison is the
one people forget, and it is why the answer comes out ten rather than nine when `n` is zero.

---

## C.4 Counting a routine on paper
The table in C.3 is the method, and it is worth stating as a method because you will use it in
every lecture of this course.

**One row per instruction, not per line executed.** Write the instruction, its cost from C.2, and
how many times it runs. Multiply and sum. A branch gets two rows, because it costs differently on
the passes that fall through and on the one that is taken.

For `shift_bits` with an argument of `n`:

| Instruction | Cycles | Times | Total |
|---|---|---|---|
| `ldi` × 2 | 1 | 2 | 2 |
| `cp` | 1 | `n + 1` | `n + 1` |
| `breq`, falling through | 1 | `n` | `n` |
| `breq`, taken | 2 | 1 | 2 |
| `lsl` | 1 | `n` | `n` |
| `inc` | 1 | `n` | `n` |
| `rjmp` | 2 | `n` | `2n` |
| `mov` | 1 | 1 | 1 |
| `ret` | 4 | 1 | 4 |

which adds to `6n + 10`.

**Order does not matter and that is not a simplification.** Cost is a sum, so a table that tracked
which instruction ran when would be carrying weight for nothing. What the method does require is
that you have already worked out **how many times each line runs**, and that is the part that is
actually hard. C.3 is about exactly that, and the `n + 1` on the comparison is where most wrong
answers come from.

---

## C.5 What a hand count is blind to
It is worth being explicit, because a method that quietly stops being right is worse than no
method.

**It does not know about the `rcall` that reached the routine.** Your table is the body. The three
cycles of getting there, and the instructions that set up the arguments, belong to the caller, and
counting them is the caller's table's job.

**It does not know about interrupts.** An interrupt arriving mid-routine adds the handler's cost
plus six to nine cycles of entry and four of `reti`, at a moment nothing in this model can predict.
From L03 onwards that is a real effect and a hand count will simply be wrong about it, by an amount
that depends on what else is running. Where that matters, the answer is to measure.

**It does not know whether your table matches your code.** Nothing checks that the rows you wrote
describe the routine you assembled. Two things guard against that: the simulator, which costs the
real thing, and the discipline of writing the table from the source rather than from memory. When
they disagree, the table is usually the one that is wrong, because it was written by a human who
was thinking about something else.

**It says nothing about correctness.** A routine can cost exactly what you predicted and return
entirely the wrong answer. Cycle counting tells you whether something fits in the time available,
and nothing whatever about whether it should be running at all.

---
