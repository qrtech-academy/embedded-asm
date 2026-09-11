# Appendix D - What To Build

## D.1 The task
Write `drivers/source/led_array.asm`, four subroutines that treat a run of LED structures as one
thing.

It is not large. What it is for is the first of the two skills this lecture is about, walking
memory at a stride that is not one. The second, knowing in advance that two things sharing 2048
bytes will not meet, is arithmetic you do on paper ([Appendix C](./c_stack.md)) and then check in
the simulator ([Appendix E](./e_exercises.md)).

Creating `drivers/source/led_array.asm` is all it takes to switch its tests on.

---

## D.2 The array
An array of `count` LED structures, laid out end to end with no gaps, starting at an address the
caller chose. Entry `n` therefore begins `n × LED_SIZE` bytes after the base, and `LED_SIZE` is 7
([`led.inc`](../../../drivers/include/led.inc)).

Nothing marks the end. The count is passed in, and it is the only thing that stops a walk.

---

## D.3 `led_array_init`
**Arguments:** `r25:r24` the base address, `r22` the count, `r20` the Arduino pin of the first LED.
**Returns:** `r24` is 0 on success, 1 if refused.

Initialise `count` LEDs on **consecutive** Arduino pins, starting at the given one. Entry 0 gets
the first pin, entry 1 the next, and so on.

Write it like this:

1. **Refuse an array that would run off the end of the pin numbering.** The last LED would be on
   pin `first + count - 1`, and there is no pin 14. Check this once, before initialising
   anything, rather than discovering it partway through and leaving half an array behind.
2. **A count of zero succeeds and does nothing.** Test the count before the first iteration.
3. **For each entry**, call `led_init` with the entry's address and the entry's pin number, then
   advance the pointer by `LED_SIZE` and the pin number by one.

### Details that are pinned rather than up to you
**`led_init` clobbers the argument registers, and it clobbers `Z`.** Your loop variables cannot
live in `r18` to `r27` or in `r30`/`r31` across the call, and the pointer you are walking is in
`r25:r24` precisely because that is where `led_init` wants it. Pushing what you need before the
call and popping it after is the straightforward answer, and it costs four cycles per register
per iteration; the alternative is to keep the loop state in call-saved registers and pay to save
those once, which is cheaper for a long array and more code. Either is fine. Choosing without
noticing there was a choice is not.

**Advance by `LED_SIZE`, taken from the include file.** Not by 7 written out, and certainly not by
2 or 6, which are the sizes of the fields rather than of the structure. A stride of 6 puts each
entry one byte on top of the last, and everything still looks like a structure.

**Do not call `led_init` for entries beyond the count.** The byte after the last structure is an
ordinary byte and will be initialised as happily as any other.

**Check yourself:** six LEDs from Arduino pin 8 gives entries whose pin fields are 0, 1, 2, 3, 4
and 5, all on port B, at addresses seven apart. Four LEDs from pin 6 straddle the ports: two on
port D at bits 6 and 7, then two on port B at bits 0 and 1.

---

## D.4 `led_array_all_on`, `led_array_all_off` and `led_array_toggle_at`
**`led_array_all_on`** and **`led_array_all_off`** take the base in `r25:r24` and the count in
`r22`, and call `led_on` or `led_off` for every entry. They return nothing.

**`led_array_toggle_at`** takes the base in `r25:r24`, the count in `r22` and an index in `r20`.
It toggles that one entry and returns 0, or returns 1 without touching anything if the index is
not less than the count.

### Details that are pinned rather than up to you
**The bound is `index < count`, and the interesting value is `index == count`.** That is the first
address past the end of the array; it looks like a structure, the driver will accept it, and
nothing else will notice. An implementation that checks `index <= count` passes every test with a
small index in it.

**Two of these three walk and one indexes.** Walking is a loop and an `adiw`; indexing is a
multiply, or a walk of `index` steps. Either is acceptable; if you use `mul`, clear `r1`
afterwards ([B.2](./b_structures.md#b2-an-array-is-a-stride)).

**Test the count at the top.** A count of zero means do nothing, for all three.

---

## D.5 What none of this does
**It does not stop you.** The arithmetic in [Appendix C](./c_stack.md) produces a number and
nothing else. Nothing on the device checks your assembly against it, and a program whose stack
collides with its variables will assemble and run exactly as happily as one whose does not.

**It does not know about anything you did not count.** A subroutine that pushes two registers adds
two bytes that your worst case will not include unless you put them there. A bound is only as good
as the depth you hand it, which is the usual bargain and is why [Appendix E](./e_exercises.md)
asks you to measure as well.

**And the measurement does not know about the interrupt that has not arrived yet**, which is why
neither on its own is enough.

---
