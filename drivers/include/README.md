# Shared Assembly Headers
`.inc` files included by more than one driver:
* Struct field offsets.
* The constants a driver and its tests both have to agree on.

There is no vector-table header and there does not need to be one: `m328Pdef.inc` already names
every vector, so `.org PCI0addr` and `.org OC1Aaddr` come from the device file rather than from
anything this directory would have to keep in step with the datasheet.

**These are ours, not yours.** A struct's field offsets are part of the contract a test checks
against, in the same way a C++ header is: the tests read your LED struct out of SRAM at the
offsets declared here, so they are given rather than chosen. What goes in the fields is yours.

| File | Lecture | What it pins |
|---|---|---|
| `led.inc` | L02 | The LED structure's field offsets and size. |
| `btn.inc` | L03 | The button structure's field offsets and size. |
| `timer.inc` | L05 | The software timer structure's field offsets and size. |

Include one from your `.asm` with `.include "led.inc"`; `make build` puts this directory on the
assembler's include path. The directive is `.include` and not `#include`: `avra` runs no C
preprocessor, and Microchip Studio rejects the `#` form outright.

---
