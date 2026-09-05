# L05 Test Suite
Unit tests for everything L05 asks you to write, **and everything L01 to L04 asked you to write**,
using the [QAcademy Test](https://github.com/qrtech-academy/test-framework) framework.

```bash
make            # build and run
make clean      # remove the binary
```

---

## Cumulative, by reference rather than by copy

| File | Runs when | Tests |
|---|---|---|
| L01 to L04's files | see each lecture's README | the pinned constants and the drivers |
| `avr/timer_data_test.cpp` | **always** | The prescalers, counter widths and registers |
| `asm/timer_driver_test.cpp` | `drivers/source/timer.asm` exists | The software timer, in the simulator |

`timer_data_test.cpp` is this suite's always-on file. It checks the device facts every frequency
calculation rests on, including one that is easy to read past: the prescaler steps are **not**
uniform. The bottom two are factors of eight and the top two are factors of four.

---

## What the driver tests are really asking
Almost all of them are about *when* it fires, because that is the only thing this driver does and
because being one interrupt out is invisible in every other way.

**`FiresOnTheTargetCall`** is the important one. With a target of 4, the fourth call returns 1 and
the three before it return 0. Comparing before incrementing rather than after gives a rate 25%
fast at that target and 0.1% fast at a target of 1000, and neither announces itself.

**`CountsPastTwoHundredAndFiftyFive`** is the only test that catches a driver comparing just the
low bytes of the count and the target. Every other test uses a target of 10 or less, where the
high bytes are both zero and comparing them adds nothing. A target of 300 is in the suite for
exactly this reason.

---

## Measuring a period
`--watch` records a pin's transitions and reports the gaps between them, and a period is a gap:

```bash
make measure IMAGE=app CALLS="--watch B0 --run 200000"
```

Point it at a pin your compare-match handler toggles. The first gap is not a period; the
[cross-check](../../appendix/d_exercises.md) asks you why.

---

## Adding a test file
Add its path to `TEST_FILES` in [the Makefile](./Makefile).

---
