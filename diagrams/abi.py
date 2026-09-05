"""The calling contract, drawn on the register file.

L02 introduces it and L06 needs every detail of it, so this is one figure used by both lectures,
written once and listed under two paths in build.py. The thing it has to make obvious is that the
32 registers are divided by *convention* rather than by hardware: nothing stops a subroutine
writing to r16, and everything breaks quietly when it does.
"""

from __future__ import annotations

import regfile
import shapes
import style

# Call-clobbered: r18 to r27, r30 and r31. A subroutine may destroy these.
_CLOBBERED = set(range(18, 28)) | {30, 31}

# Call-saved: r2 to r17, r28 and r29. A subroutine that uses one must put it back.
_SAVED = set(range(2, 18)) | {28, 29}

# The argument and return registers this course uses, which are a subset of the clobbered set.
_ROLES = {
    24: "arg 1 / return",
    25: "arg 1 high",
    22: "arg 2",
    23: "arg 2 high",
    0: "lpm target",
    1: "zero, in C",
}


def _annotate(ax, layout) -> None:
    """Brace the two halves of the contract, and caption what the colours mean."""
    # The call-clobbered run r18 to r27 is contiguous in the right-hand column, so it braces
    # cleanly; r30 and r31 are the tail of the same column and get their own.
    _, low, edge, _ = layout.cell(27)
    _, _, _, top = layout.cell(18)
    shapes.vbrace(ax, low, top, edge + 0.30, "yours to destroy", size=style.SMALL_SIZE)

    _, low, edge, _ = layout.cell(31)
    _, _, _, top = layout.cell(30)
    shapes.vbrace(ax, low, top, edge + 0.30, "also yours", size=style.SMALL_SIZE)

    # The call-saved run r2 to r15 fills most of the left column.
    left, _, _, _ = layout.cell(2)
    _, low, _, _ = layout.cell(15)
    _, _, _, top = layout.cell(2)
    shapes.vbrace(ax, low, top, left - 0.30, "give these back", left=True,
                  color=style.ACCENT_COLOR_2, size=style.SMALL_SIZE)


REGISTER_CONTRACT = regfile.figure(
    fills={number: "accent" for number in _CLOBBERED}
    | {number: "accent2" for number in _SAVED},
    labels=_ROLES,
    caption=("Red is call-clobbered and blue is call-saved. Nothing in the hardware enforces",
             "either: this is a convention, and the compiler is the other party to it."),
    annotate=_annotate,
    pad=(3.4, 0.0, 3.4, 0.0))
