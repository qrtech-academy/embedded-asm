"""L01 figures: the machine, and the toolchain that puts something on it.

Four pictures, and between them they are the whole of the first lecture: what the register
file is, what the three address spaces are, what an instruction actually is once assembled,
and what turns a text file into all of that.

Every number here comes from one of two documents, and which one is named beside it:
the ATmega328P datasheet for the memory sizes and addresses, and the AVR Instruction Set
Manual for the encoding. The `ldi` word below was additionally checked against the assembler
itself, because a figure claiming a specific hexadecimal value is exactly the kind of claim
that is wrong quietly.
"""

from __future__ import annotations

import bitfield
import flow
import memory
import regfile
import shapes
import style

# ----------------------------------------------------------------------------------------
# A.2: the register file.
#
# Two columns of sixteen, which is the split that matters: an immediate instruction encodes
# its destination in four bits and can therefore only name r16 to r31.
# ----------------------------------------------------------------------------------------

# The pointer register pairs, low byte first. These are r26 to r31, so they are the bottom
# six cells of the right-hand column.
_POINTERS = {26: "XL", 27: "XH", 28: "YL", 29: "YH", 30: "ZL", 31: "ZH"}


def _annotate_regfile(ax, layout) -> None:
    """Brace the immediate-capable half, and the three pointer pairs inside it."""
    # The right-hand column, braced along its top: everything ldi can reach.
    left, right = layout.column_x(1)
    _, _, _, high = layout.cell(16)
    shapes.brace(ax, left, right, high + 0.30, "immediates reach only these",
                 size=style.TINY_SIZE)

    # The three pointer pairs, braced individually down the right-hand side.
    for name, (low_reg, high_reg) in (("X", (26, 27)), ("Y", (28, 29)), ("Z", (30, 31))):
        _, low, edge, _ = layout.cell(high_reg)
        _, _, _, top = layout.cell(low_reg)
        shapes.vbrace(ax, low, top, edge + 0.30, name, color=style.ACCENT_COLOR_2,
                      size=style.FONT_SIZE)


REGISTER_FILE = regfile.figure(
    fills={number: "accent" for number in range(16, 32)}
    | {number: "accent2" for number in _POINTERS},
    labels=_POINTERS | {0: "lpm target"},
    caption=("All 32 are equal to ld, st, mov and add.",
             "Only ldi, andi, ori, subi and cpi are restricted to the upper half."),
    annotate=_annotate_regfile,
    pad=(0.0, 0.0, 1.6, 1.15))


# ----------------------------------------------------------------------------------------
# A.4: the three address spaces.
#
# Sizes and addresses from the ATmega328P datasheet. RAMEND is 0x08FF, which is the number
# the reader will write into the stack pointer in this lecture's first complete program.
# ----------------------------------------------------------------------------------------
_FLASH = memory.Column(
    "Program memory",
    [
        # Word addresses throughout this column, which is what the datasheet's vector table
        # gives and what .org takes. Each vector is two words, not two bytes, because jmp is
        # a two-word instruction on a part this size: that is why PCINT0 sits at 0x06 and not
        # at 0x03. Getting this wrong puts every handler at half its correct address.
        memory.Region("Interrupt vectors", "0x0000", "0x0033",
                      "26 vectors, 2 words each", "accent", height=1.30),
        memory.Region("Application section", "0x0034", "0x37FF",
                      "your code lives here", height=1.55),
        memory.Region("Boot section", "0x3800", "0x3FFF",
                      "bootloader; size set by fuses", "muted", height=1.30),
    ],
    width=5.6,
    note=("32 KB, addressed as 16K words.", "Reached by lpm, never by ld."))

_DATA = memory.Column(
    "Data memory",
    [
        memory.Region("Register file", "0x0000", "0x001F",
                      "r0 to r31, 32 bytes", "accent2", height=1.30),
        memory.Region("I/O registers", "0x0020", "0x005F",
                      "in / out reach these 64", "accent", height=1.30),
        memory.Region("Extended I/O", "0x0060", "0x00FF",
                      "lds / sts only, 160 bytes", height=1.30),
        memory.Region("Internal SRAM", "0x0100", "0x08FF",
                      "2048 bytes; RAMEND = 0x08FF", height=1.55),
    ],
    width=5.6,
    note=("One flat space, and the register file", "really is addressable inside it."))

_EEPROM = memory.Column(
    "EEPROM",
    [
        memory.Region("EEPROM", "0x0000", "0x03FF",
                      "1024 bytes, survives power off", height=2.20),
    ],
    width=5.6,
    note=("Not in the data space at all.", "Reached only via EEAR, EEDR, EECR."))

MEMORY_SPACES = memory.figure(
    [_FLASH, _DATA, _EEPROM],
    caption=("Three separate address spaces, not three regions of one.",
             "Address 0x0060 names a different byte in each of them."))


# ----------------------------------------------------------------------------------------
# A.6: what an instruction is, once assembled.
#
# `ldi Rd, K` is 1110 KKKK dddd KKKK, with d = Rd - 16. So `ldi r16, 0x2A` assembles to
# 0xE20A. Checked against avr-gcc rather than taken from the manual alone.
# ----------------------------------------------------------------------------------------
_ENCODING_CELL_W = 1.02

_PATTERN = bitfield.Register(
    "pattern",
    [bitfield.Bit(c, fill) for c, fill in
     [("1", "muted"), ("1", "muted"), ("1", "muted"), ("0", "muted"),
      ("K", "accent"), ("K", "accent"), ("K", "accent"), ("K", "accent"),
      ("d", "accent2"), ("d", "accent2"), ("d", "accent2"), ("d", "accent2"),
      ("K", "accent"), ("K", "accent"), ("K", "accent"), ("K", "accent")]])

_ASSEMBLED = bitfield.Register(
    "0xE20A",
    [bitfield.Bit(c, fill) for c, fill in
     [("1", "muted"), ("1", "muted"), ("1", "muted"), ("0", "muted"),
      ("0", "accent"), ("0", "accent"), ("1", "accent"), ("0", "accent"),
      ("0", "accent2"), ("0", "accent2"), ("0", "accent2"), ("0", "accent2"),
      ("1", "accent"), ("0", "accent"), ("1", "accent"), ("0", "accent")]])


def _annotate_encoding(ax, layout) -> None:
    """Name the three fields above the word, and say what each came out as below it."""
    _, high = layout.row_y(0)
    low, _ = layout.row_y(1)
    lift = high + bitfield.BRACE_LIFT

    def cells(first: int, last: int) -> tuple[float, float]:
        return layout.cell_x(first)[0], layout.cell_x(last)[1]

    opcode_left, opcode_right = cells(0, 3)
    shapes.brace(ax, opcode_left, opcode_right, lift, "opcode",
                 color=style.MUTED_COLOR, size=style.TINY_SIZE)

    dest_left, dest_right = cells(8, 11)
    shapes.brace(ax, dest_left, dest_right, lift, "d = Rd - 16",
                 color=style.ACCENT_COLOR_2, size=style.TINY_SIZE)

    # The immediate is split across the word, which is the whole reason this figure exists.
    # Braced as two halves rather than as one span from the first K to the last: a single
    # brace would run over the register field between them and say the opposite of the truth.
    high_left, high_right = cells(4, 7)
    low_left, low_right = cells(12, 15)
    shapes.brace(ax, high_left, high_right, lift, "K[7:4]", size=style.TINY_SIZE)
    shapes.brace(ax, low_left, low_right, lift, "K[3:0]", size=style.TINY_SIZE)

    shapes.brace(ax, dest_left, dest_right, low - 0.30, "r16", below=True,
                 color=style.ACCENT_COLOR_2, size=style.TINY_SIZE)
    shapes.brace(ax, high_left, high_right, low - 0.30, "0x2", below=True,
                 size=style.TINY_SIZE)
    shapes.brace(ax, low_left, low_right, low - 0.30, "0xA", below=True,
                 size=style.TINY_SIZE)


LDI_ENCODING = bitfield.figure(
    [_PATTERN, _ASSEMBLED],
    caption=("ldi r16, 0x2A assembles to 0xE20A. The immediate is stored in two halves,",
             "and the register field holds 0, because ldi can only name r16 to r31."),
    annotate=_annotate_encoding,
    caption_drop=1.30,
    cell_w=_ENCODING_CELL_W,
    pad=(0.0, 0.30, 0.0, 1.15))


# ----------------------------------------------------------------------------------------
# B.1: the toolchain.
#
# One source file, one command, two output files, and three different things you can do with
# them. The assembler is drawn as a box rather than as an arrow label because it is a program
# you run and can pass options to, and the reader is about to run it.
#
# The hex and the map are drawn as two boxes rather than one, because that is the fact the
# appendix spends a paragraph on: the hex has no symbol table, and everything downstream that
# knows a name by name learned it from the map.
# ----------------------------------------------------------------------------------------
_SOURCE = flow.Node("led.asm", (0.0, 0.0), "assembly you wrote", "accent2")
_ASSEMBLER = flow.Node("avra", (6.6, 0.0), "no linker, no preprocessor", width=5.4)
_LISTING = flow.Node("drivers.lst", (13.4, 2.6), "your source, with the bytes", width=5.4)
_HEX = flow.Node("drivers.hex", (13.4, 0.0), "the bytes, and no names", "accent", width=5.4)
_MAP = flow.Node("drivers.map", (13.4, -2.6), "every label and its address", "accent", width=5.4)
_AVRDUDE = flow.Node("avrdude", (20.6, 1.3), "optional, a real board", "muted", width=5.6)
_SIMAVR = flow.Node("the test suite", (20.6, -1.3), "what it does, in cycles", width=5.6)

TOOLCHAIN = flow.figure(
    [_SOURCE, _ASSEMBLER, _LISTING, _HEX, _MAP, _AVRDUDE, _SIMAVR],
    [
        flow.Edge(0, 1),
        flow.Edge(1, 2),
        flow.Edge(1, 3),
        flow.Edge(1, 4),
        flow.Edge(3, 5, dashed=True),
        flow.Edge(3, 6),
        flow.Edge(4, 6),
    ],
    caption=("A hex file carries addresses and bytes and nothing else, so the harness reads the",
             "map beside it. That pair is what lets a test call led_init by name, set r25:r24",
             "and r22, run it, and read DDRB afterwards."))
