# Diagrams
The lecture figures under `lectures/*/appendix/images/` are drawn from code, so changing a
register field, an address or a waveform is an edit and a rebuild rather than a redraw.

The generated PNGs stay committed. GitHub renders the lectures straight from the repository, so
nothing here runs when a reader builds the course; this is an authoring tool you run when a
figure changes. CI redraws every figure and diffs it against what is committed, which is what
makes drift detectable: edit a figure module without re-committing its PNG, or hand-edit a
generated PNG, and that job is where it surfaces.

---

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r diagrams/requirements.txt
```

---

## Rebuilding

```bash
make diagrams                                  # every figure, into the lecture trees
.venv/bin/python diagrams/build.py --list      # what can be built
.venv/bin/python diagrams/build.py sreg
.venv/bin/python diagrams/build.py --outdir /tmp/preview   # look before overwriting
```

`--outdir` writes `<figure>.png` flat into a directory of your choice and leaves the repository
untouched, which is the sane way to iterate on a figure.

**Look at every figure you generate.** Render to a scratch directory and open the PNG. Every
figure in this directory was wrong the first time it rendered, and not one of those faults was
visible from the code: a caption clipped off at both ends because the canvas was sized to the
drawing and not to the text under it, a brace struck through the row of bit numbers it was
supposed to sit above, three column footnotes overlapping each other, a label colliding with the
brace beside it. All of them rendered without an error and produced a file that looked finished
in a directory listing.

---

## Layout

| File | What it holds |
| --- | --- |
| `style.py` | Every color, line weight, font, fill and the output scale. Restyling every figure at once is one edit here. |
| `shapes.py` | The matplotlib primitives more than one module needs: a filled cell, a brace, a span, a callout arrow. |
| `bitfield.py` | A register drawn as its named bits. The workhorse: almost everything this device does is configured by one. |
| `regfile.py` | The 32 registers, as two columns of sixteen. One drawing, four lectures' worth of questions. |
| `memory.py` | Address-space maps: labelled regions with their addresses, several spaces side by side. |
| `flow.py` | Box-and-arrow diagrams, for the toolchain and for what the hardware does when an interrupt fires. |
| `core.py` | L01's figures: the register file, the three address spaces, an instruction encoded, the toolchain. |
| `registers.py` | The bit-field figures, across every lecture that configures a peripheral. |
| `ports.py` | L02's port figures: the four states of a pin, and the Arduino pin map. |
| `circuit.py` | The two figures that are actually circuits, drawn with `schemdraw`: the LED and the button. |
| `stack.py` | L02's call stack, byte by byte, across an `rcall` and its `ret`. |
| `interrupt.py` | L03's interrupt sequence, step by step with the datasheet's cost beside each. |
| `vectors.py` | The 26-entry vector table, with the entries this course uses marked. |
| `pointers.py` | L04's addressing modes: what each of the four forms reads, and where it leaves the pointer. |
| `sram.py` | L04's SRAM map and the stack-depth figure. |
| `timer.py` | L05's timer block diagram and its CTC waveform. |
| `watchdog.py` | L06's watchdog registers, its timed write, and the sleep-mode table. |
| `abi.py` | L06's register contract: the 32 registers coloured by their role in the calling convention. |
| `build.py` | Figure name to figure plus output paths, and the command line. |

---

## Adding a figure

1. Write a builder in the module that owns that kind of picture, or a new module next to
   `build.py` if it is a kind of picture nothing here draws yet. A builder takes
   `(drawing, ax)`: a `schemdraw.Drawing` for the figures that are circuits, and the matplotlib
   axes, which everything else uses. Wrap it in a `style.Figure` with the canvas it needs.
2. Put the figure's geometry in named constants at the top of the module, the way `bitfield.py`
   does. That is what makes a figure cheap to adjust later.
3. Add an entry to `FIGURES` in `build.py` listing every path the figure is written to. A figure
   embedded by more than one lecture gets more than one path, and writing all the copies from one
   source is what keeps them identical.
4. Render it with `--outdir` and **look at it**, then commit the PNG alongside the code.

---

## Two rules that are not style
**A canvas must clear its caption, not just its drawing.** A caption is routinely wider than the
figure it captions, and a canvas pinned to the drawing clips it in silence. `style.caption_bounds`
exists for this and every figure module calls it.

**A number in a figure is a claim.** The addresses and sizes here come from the ATmega328P
datasheet and the instruction encoding from the AVR Instruction Set Manual, and the module says
which beside each one. `ldi_encoding` goes further and was checked against `avr-gcc` itself,
because a figure asserting that `ldi r16, 0x2A` is `0xE20A` is exactly the kind of claim that is
wrong quietly. Where a figure shows a computed number, an appendix should show the arithmetic that
produces it, and the appendix should ask the reader to run it.

---

## Notes

* A figure declares the canvas it is drawn onto rather than being cropped to its contents, so
  figures read one after another line up rather than each being its own size.
* Figures are written as palette PNGs (`style.PALETTE_COLORS`), not RGBA. Line art on white uses
  a few hundred colors at most, so this costs nothing visually and roughly halves what gets
  committed. Median cut is deterministic, so a rebuild stays byte-identical, which is what the CI
  job depends on.
* A fill never carries meaning on its own. Every filled region is also labelled, so a reader
  printing a lecture in greyscale, or one who cannot separate these hues, loses nothing.
* The figures are black on white, which is hard to read in GitHub's dark theme. If that ever
  needs fixing, it is a change to the colors in `style.py` and nowhere else.

---
