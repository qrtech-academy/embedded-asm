# Appendix A - The Pointer Registers

## A.1 Six registers, three pointers
The AVR has no 16-bit registers. What it has is three *pairs* of 8-bit registers that certain
instructions treat as one 16-bit address:

| Pointer | Low byte | High byte | Displacement? |
|---|---|---|---|
| `X` | `r26` (`XL`) | `r27` (`XH`) | no |
| `Y` | `r28` (`YL`) | `r29` (`YH`) | yes |
| `Z` | `r30` (`ZL`) | `r31` (`ZH`) | yes, and `lpm` uses it |

The low byte comes first, which is the same order everything else on this machine uses and the
reason `movw r30, r24` copies `r25:r24` into `Z` in one instruction: `movw` copies a pair to a
pair, and both pairs are low-byte-first.

They are still ordinary registers. Nothing stops you keeping a loop counter in `r30`, and
`ldi r30, 0` is legal because `r30` is in the upper half
([L01 A.2](../../L01/appendix/a_avr_core.md#a2-the-register-file)). What changes is that the
moment you want to reach memory through a pointer, these six are the only ones that can, so a
subroutine that has casually filled `Z` with something else has to put it back first.

**`Y` is worth avoiding.** `r28` and `r29` are call-saved
([L02 B.3](../../L02/appendix/b_subroutines.md#b3-the-calling-contract)), so a subroutine using
`Y` must push both halves on entry and pop them before returning: four instructions and eight
cycles that `X` and `Z` cost nothing. Compiled C uses `Y` as a frame pointer, which is why it is
call-saved and why leaving it alone is the easy choice.

---

## A.2 One instruction, four ways
![Four short strips of memory side by side, one per addressing mode, each showing which byte is read and where the pointer sits before and after: ld reads at Z and leaves it, ld Z+ reads then advances, ld -Z retreats then reads, and ldd Z+3 reads three along without moving Z](./images/addressing_modes.png)

All four put a byte in the destination register and all four cost **two cycles**. What differs is
the byte they chose and where the pointer is afterwards, and neither of those is visible in the
register you just loaded.

| Form | Reads | Leaves the pointer |
|---|---|---|
| `ld r16, Z` | at `Z` | unchanged |
| `ld r16, Z+` | at `Z` | one higher |
| `ld r16, -Z` | at `Z - 1` | one lower |
| `ldd r16, Z+q` | at `Z + q` | unchanged |

`st` is the mirror of all four, and the operand order flips: the pointer comes first when storing
and second when loading. Writing them the other way round is a natural mistake and the
assembler's message about it is not especially helpful.

**The sign is on the side the change happens.** `Z+` increments *after* the access and `-Z`
decrements *before* it, which is why walking forwards uses the first and walking backwards uses
the second, and why the two are not the mirror images they look like.

---

## A.3 Displacement, and its two limits
`ldd` reads the byte a constant number of places past `Z` without moving `Z`, and this is what
makes structures cheap: a field at offset 6 is one two-cycle instruction away, not an add, a load
and a subtract.

Two limits shape how you use it.

**The displacement is a constant, and it is at most 63.** It is encoded in the instruction, so it
cannot come from a register and cannot be worked out at run time. A structure larger than 64 bytes
has fields `ldd` cannot reach, and an array index is never a displacement.

**`X` has no displacement form at all.** There is no `ldd` for it; the encoding space went
elsewhere. So `X` is the pointer for walking, `Z` is the pointer for structures, and a driver that
needs both at once uses both, which is exactly what the LED driver does: `Z` holds the structure
and `X` holds the port register address it read out of it.

---

## A.4 Program memory needs its own instruction
`lpm` reads a byte of **program** memory through `Z`, and it is the only instruction that can.

Three things are different about it, and all three follow from the Harvard split
([L01 A.4](../../L01/appendix/a_avr_core.md#a4-three-address-spaces)):

* **It costs three cycles**, not two.
* **`Z` holds a byte address into flash**, so reaching word address `0x0006` means putting
  `0x000C` in `Z`. This is the same doubling as the vector table
  ([L03 A.2](../../L03/appendix/a_interrupts.md#a2-the-vector-table)), and it catches people
  twice rather than once.
* **The result lands in `r0`** unless you name a destination: `lpm` on its own writes `r0`, and
  `lpm Rd, Z` or `lpm Rd, Z+` writes the register you asked for. One more reason to leave `r0`
  alone.

The failure mode when you forget is silent and specific: an ordinary `ld` with a flash address in
`Z` reads *SRAM* at that address and gets whatever is there. Nothing is checked, and a constant
table you carefully placed in program memory reads back as your own variables.

This course does not use `lpm` for anything. It is here because the moment you want a lookup
table you will need it, and because "a pointer is a pointer" is the intuition it breaks.

---

## A.5 What a pointer costs
Worth having the numbers, because the reason to use displacement addressing is not elegance.

| Doing this | Instructions | Cycles |
|---|---|---|
| Read a field at a known offset, with `ldd` | 1 | 2 |
| The same, by adding the offset to `Z` and taking it off again | 3 | 6 |
| Copy a structure address into `Z` with `movw` | 1 | 1 |
| Advance a pointer by 63 or less, with `adiw` | 1 | 2 |
| Advance a pointer by more than 63 | 2 | 2 |

`adiw` adds an immediate to a register pair, and it has limits of its own: **the immediate is at
most 63**, and it works only on `r24`, `r26`, `r28` and `r30`. Advancing by more than that takes
`subi` and `sbci` with the negated value, which is two instructions and reads strangely the first
time. Subtracting a negative is how you add to a pair, because there is no `addi` and there never
was.

That is not a detail you need to enjoy. It is one you need to recognise, because it is what
walking an array of seven-byte structures looks like.

---
