# L06 Test Suite
Unit tests for everything L06 asks you to write, **and everything the whole course asked you to
write**, using the [QAcademy Test](https://github.com/qrtech-academy/test-framework) framework.

```bash
make            # build and run
make clean      # remove the binary
```

This is the last suite, so `make test` at the repository root runs every test in the course
against your current work.

---

## Cumulative, by reference rather than by copy

| File | Runs when | Tests |
|---|---|---|
| L01 to L05's files | see each lecture's README | the pinned constants and the drivers |
| `avr/watchdog_data_test.cpp` | **always** | The scattered selector bits, and the registers |
| `avr/sleep_data_test.cpp` | **always** | The sleep modes' restart costs, and `SMCR` |
| `asm/watchdog_driver_test.cpp` | `drivers/source/watchdog.asm` exists | The driver, in the simulator |

`watchdog_data_test.cpp` and `sleep_data_test.cpp` are this suite's always-on files, and the last
in the course. The first checks the one piece of arithmetic nothing else will catch: the four
timeout selector bits are not adjacent in `WDTCSR`, so the selector and the byte that selects it
are different numbers, and writing one where the other belongs is not a wrong timeout but a
dangerous one. The second checks that the restart costs in Appendix B.6 are the ones
`atmega328p.hpp` holds.

---

## The one test in this course where the hardware checks the timing
`WatchdogDriver.InitWritesTheByteAsked` looks like an ordinary "did you write the right value"
test and is not. The two writes of the timed sequence have to land within four cycles of each
other, the simulator enforces that faithfully, and a sequence that is merely slightly too slow
leaves `WDTCSR` holding `0x08`.

So if that test fails reporting `8 != 14`, the message is telling you two things: your sequence
was too slow, and the device is now in system reset mode with the shortest timeout. The failure
message is the diagnosis.

---

## Building the capstone
The C program in [D.3](../../appendix/d_what_to_build.md#d3-the-capstone-call-it-from-c) is built by
hand rather than by `make build`, because it is the one program in the course that needs the C
runtime:

```bash
avr-gcc -mmcu=atmega328p -Os drivers/app/main.c drivers/source/utils_gnu.S -o drivers/build/mixed.elf
```

Nothing in `utils.asm` changes. That is the point of it.

---

## Adding a test file
Add its path to `TEST_FILES` in [the Makefile](./Makefile).

---
