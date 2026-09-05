# L04 Test Suite
Unit tests for everything L04 asks you to write, **and everything L01 to L03 asked you to write**,
using the [QAcademy Test](https://github.com/qrtech-academy/test-framework) framework.

```bash
make            # build and run
make clean      # remove the binary
```

---

## Cumulative, by reference rather than by copy
Earlier lectures' test files are named where they live rather than copied here, so work you do in
L04 that breaks an earlier driver fails in L04, which is where you are looking.

| File | Runs when | Tests |
|---|---|---|
| L01's files | see [L01's README](../../../L01/exercises/test/README.md) | the core's constants and `utils.asm` |
| L02's files | see [L02's README](../../../L02/exercises/test/README.md) | the board's pin numbering and `led.asm` |
| L03's files | see [L03's README](../../../L03/exercises/test/README.md) | the vector numbers and `button.asm` |
| `avr/struct_data_test.cpp` | **always** | The driver structure layouts |
| `asm/led_array_test.cpp` | `drivers/source/led_array.asm` exists | The array driver, in the simulator |

`struct_data_test.cpp` is this suite's always-on file. The structure offsets live in two places,
the `.inc` files the assembly includes and `avr/drivers.hpp` the tests read, and two copies of a
set of constants is exactly what drifts. So what it checks is not the numbers one at a time, which
would be the list written a third time, but the relationships that make them a layout: that fields
abut, that each structure is as big as its fields, and that a button structure begins with an LED
structure.

---

## What the array tests are really asking
Two questions, and each has a characteristic failure that produces working-looking code.

**Does it walk at the structure's stride?** A stride of anything else puts each entry partly on
top of the last, and every address involved stays legal. The signature is that **entry 0 always
works**: a quick check with one LED passes, and the tests that read entries 1 upwards do not.

**Does it stop where it was told?** Nothing in memory marks the end of an array. The single test
that separates a loop testing its count at the top from one testing it at the bottom is the
**empty-array** case, because zero is the only count for which the two differ.

The tests read structures back at addresses the *test* computed rather than asking the driver
where entry 2 is. Asking the driver would get the driver's own wrong answer, consistently, and
pass.

---

## Measuring the stack
`make measure` reports how far down the stack went, over everything it did:

```bash
make measure IMAGE=app CALLS="--run 4000 --drive B4=0 --run 300 --drive B4=1 --run 300"
```

`--run` lets the program run on its own, which is the only way to reach an interrupt handler.
Note that a `symbol:args` step adds two bytes of its own, standing in for the `rcall` the tool did
not make; a `--run` measurement does not, because the program made its own calls.

---

## Adding a test file
Add its path to `TEST_FILES` in [the Makefile](./Makefile).

---
