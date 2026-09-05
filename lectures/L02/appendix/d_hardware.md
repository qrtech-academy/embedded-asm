# Appendix D - Putting It On A Real Board

## D.1 Nothing in this course needs this
Every exercise is written, assembled, simulated and verified on your laptop. No test knows whether
you own a board, and none of them will ever ask.

This appendix exists because an LED that lights is a different experience from a test that passes,
and because the last step of the toolchain is worth having done once. If you have an Arduino Uno
in a drawer, this is twenty minutes. If you do not, skip it; the simulator is not a poor substitute
here, it is the thing the rest of the course is built on.

---

## D.2 What you need
An **Arduino Uno**, or any board with an ATmega328P and a USB serial bridge, and a USB cable.
Nothing else: the LED on pin 13 is already fitted, with its resistor
([A.4](./a_io_ports.md#a4-an-led-and-a-resistor-that-is-not-optional)).

`avrdude` is a separate package, and the course's install lines leave it out on purpose: this is
the only appendix that uses it, and it is optional. Install and check it:

```bash
sudo apt -y install avrdude
avrdude -v 2>&1 | head -n 2
```

---

## D.3 The file `avrdude` wants, you already have
`avrdude` wants an Intel HEX file, and `avra` writes one. `drivers/build/app.hex` is the artefact
this appendix flashes, with no conversion step between the build and the programmer.

That is worth a sentence because it is not the usual arrangement. A GNU-toolchain AVR project
links to an ELF and then runs `avr-objcopy -O ihex` to get here; this course skips both, because
its assembler has no linker and emits the programmer's format directly
([L01 B.4](../../L01/appendix/b_toolchain.md#b4-two-images-for-two-jobs)).

The size comes free with the build, at the end of what `avra` prints:

```text
Segment usage:
   Code      :        17 words (34 bytes)
```

A blinking LED written in assembly comes out at a few dozen bytes against 32 KB of flash. Worth
looking at once, if only to see how much of a microcontroller a small program does not use.

---

## D.4 Finding the board
Plug it in and look:

```bash
ls /dev/ttyACM* /dev/ttyUSB* 2>/dev/null
```

An official Uno is usually `/dev/ttyACM0`; a clone with a CH340 bridge is usually `/dev/ttyUSB0`.

If nothing appears, and you are on **WSL**, that is expected rather than broken: WSL does not see
USB devices without `usbipd-win` forwarding them. Flashing from Windows, or from a native Linux
install, is the shorter path.

If the device appears but you cannot open it, you are not in the right group:

```bash
sudo usermod -a -G dialout "$USER"
```

Then log out and back in, because group membership is established at login.

---

## D.5 Flashing
```bash
avrdude -c arduino -p atmega328p -P /dev/ttyACM0 -b 115200 -U flash:w:drivers/build/app.hex:i
```

| Option | Means |
|---|---|
| `-c arduino` | Talk to the bootloader over serial, not to an external programmer. |
| `-p atmega328p` | The device, so `avrdude` can check it is talking to what it thinks. |
| `-P` | The serial port from D.4. |
| `-b 115200` | The bootloader's baud rate. An older Uno may want `57600`. |
| `-U flash:w:...:i` | Write this Intel HEX file to flash. |

The board resets, the bootloader runs, the program is written and verified, and then your code
starts. If your program has no final loop, you will see it restart repeatedly
(L01 F, exercise 6).

---

## D.6 When it does not work
**`programmer is not responding`.** Usually the wrong port, sometimes the wrong baud rate on an
older board, occasionally a serial monitor somewhere else holding the port open.

**`expected signature ... but found ...`.** The chip is not an ATmega328P. Clone boards sometimes
carry an ATmega328PB, which is a different device with a different signature and a slightly
different peripheral set.

**It flashes cleanly and nothing happens.** Three candidates, in order of likelihood: you flashed
`drivers.hex` rather than `app.hex` and there is no reset vector; your program ran off the end and
is restarting; or the pin is right and the LED is on a different one, because this is not an
official Uno.

**The bootloader is not the only way in.** With an ISP programmer you can write flash directly and
skip it, which is also how you would change the fuses. This course never does either. Fuses are
worth respecting: the wrong clock setting will make a board that no longer responds to a
programmer, and recovering it needs a second board and an afternoon.

---

## D.7 What the board shows you that the simulator does not
Not much, honestly, and it is worth being precise about the short list rather than implying the
hardware is somehow more real.

**That your wiring is right.** The simulator models the chip, not the board, so it cannot tell you
the LED is on pin 12.

**Analogue reality.** Voltage, current, rise times, a supply that sags. None of it is in the
simulator and none of it is in this course either, but it is where embedded work eventually goes.

**That the clock is what you assumed.** Every timing number in this course assumes 16 MHz. On a
bare ATmega328P running from its internal oscillator with the factory `CKDIV8` fuse set, the clock
is 1 MHz and everything is sixteen times slower; clear the fuse and it is 8 MHz and twice as slow.
Every cycle count is still exactly right in each case, which is a good demonstration of the
difference between cycles and seconds.

What the simulator shows you that the board does not is the entire subject of this course: which
register changed, when, and what it cost.

---
