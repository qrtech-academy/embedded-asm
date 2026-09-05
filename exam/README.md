# Written Examinations
Two three-hour papers, with worked solutions, six questions each, one per lecture.

**They are there for you to test yourself with after the course, and nothing more.** They gate
nothing, they are not a qualification, and no part of the course requires them. No driver is
built from them and `make build` does not know they exist.

**Take one once the course is over.** Both papers draw on all six lectures, so sitting one
partway through examines material nobody has taught you yet, and the result says more about how
far you have read than about what you have understood.

What they check is different from what the exercises check. The exercises are done with a
datasheet open, an assembler to hand, and a test suite that tells you when you are wrong. These
are done with none of those: assembly written out by hand, cycle counts from memory, and at least
one routine per paper that assembles cleanly and is wrong anyway.

---

## The papers

| Paper | Covers | Solutions |
|---|---|---|
| [Paper 1](./paper_1.md), *The Core, the Cost, and the Contract* | L01 to L06, one question each | [Solutions](./paper_1_solutions.md) |
| [Paper 2](./paper_2.md), *Addresses, Vectors, and What Is Still Running* | L01 to L06, one question each | [Solutions](./paper_2_solutions.md) |

Each paper is 100 marks over six questions, and each question carries the marks its parts add up
to, so you can see where the time is meant to go. The reference sheet at the end of each paper
carries every constant, encoding and cycle cost the questions need; nothing is being tested by
being withheld.

---

## About the listings in them
Some questions hand you a short routine to read. Those listings are exam stimulus and nothing
else: they are not part of the driver library, they are not what any lecture asked you to write,
and several of them are wrong on purpose. Each paper says at the top how many of its listings are
wrong, because "find the bug" and "there is no bug" are different exercises and you should know
which one you are doing.

Every cycle count, every returned value and every measured figure in the solutions was checked in
the simulator before it was written down. Where a solution says "measured", it was.

---

## The answers you are expected to get wrong
The solutions name them. `0xE43F` for an `ldi` encoding, `8 x 3` for a loop that runs eight times,
`V = 1` because a result looks negative, `0x0B` for a vector address, `r22` for a third argument.
Each is a specific misunderstanding rather than a slip, and each is worth more attention than the
question it appears in.

---
