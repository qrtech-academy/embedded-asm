# The Device Constants
Four C++ headers, and they are the only C++ this course ships. **They are ours, not yours**: no
exercise asks you to change them, and nothing here is a program.

```text
device/include/avr/
├── atmega328p.hpp     The datasheet's numbers, pinned in one place.
├── arduino_uno.hpp    The board's pin numbering, which is not the chip's.
└── drivers.hpp        The assembly structures' field offsets, as C++ sees them.
```

---

## Why they exist
Because the test suites have to check your assembly against **the datasheet**, and not against
themselves. When `led_test.cpp` reads a byte out of the simulator to see whether `led_init` wrote
`DDRB`, it needs an address, and the honest place for that address is one header that says where
it came from, rather than a literal `0x24` in whichever test happened to need it first.

That is also why there is an always-on test per suite checking these against each other:
`device_test.cpp` asserts that DDRB is PINB plus one and PORTB is PINB plus two, for all three
ports, because that arithmetic is what your drivers actually do. If the constants and the drivers
disagree, one of them is wrong and the suite says so on a fresh clone, before you have written a
line.

`drivers.hpp` is the same idea for structure layouts: it holds the offsets that
`drivers/include/*.inc` gives your assembly, so a test can read a field out of SRAM at the place
your driver put it. Two copies of a set of constants is exactly what drifts, so the always-on
tests check the *relationships* between them rather than restating the list.

---

## What used to be here
A C++17 host toolkit: seven classes computing cycle counts, pin mappings, vector addresses, stack
depths, timer prescalers and watchdog control bytes, with interfaces, stubs, a factory and a demo.
It was removed, and the reasoning is worth writing down so nobody rebuilds it by accident.

Its job was to be the middle of three: compute a number by hand, compute it again in your own
code, then measure it. But the middle leg turned out to be **the same arithmetic as the first**,
typed into C++. `deepestStack` is a multiplication and three additions. `responseCycles` is one
addition. The largest of them, choosing a timer prescaler, is a loop over five values that a
reader runs once, on paper, at design time, because the assembly driver they then write has the
answer hard-coded.

What that cost was real: a second source of truth for every number the appendices quote, kept in
step with them by hand. It drifted, more than once.

So the course now checks each number **twice**: once by hand, before any code exists, and once in
the simulator. Where they disagree, that is the lesson. And in L03 they disagree because the
*simulator* is wrong, which is a better thing to learn than a class that reproduces a datasheet.

**If you want to build one anyway**, it is a good exercise and nothing here will stop you or check
it. The numbers worth computing are the ones the appendices work out by hand: the cycle table in
L01 C.2, the pin mapping in L02 A.6, the vector arithmetic in L03 A.2, the stack bound in
L04 C.2, the prescaler search in L05 B.3, and the watchdog control byte in L06 A.3. Design the
interface yourself; there are deliberately no contracts here to fill in, because a shipped
signature is not a thing you wrote.

---
