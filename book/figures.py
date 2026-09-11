#!/usr/bin/env python3
"""Render the lecture figures as vector PDFs for the book.

    .venv/bin/python book/figures.py OUTDIR FIGURE...

The lectures embed 130 dpi PNGs, which is right for a screen and soft on paper. The drawings
themselves are vector, so this reuses the figure builders in diagrams/ unchanged and swaps
only the last step: matplotlib writes a PDF instead of a palette PNG. Nothing in diagrams/ is
modified, and a figure changed there is changed here on the next build.

A few figures were laid out for a screen and are too wide for a page at the book's common scale.
Those get a book layout here, drawn with the same builder data and the same style, so that the
drawing and every label in it still come from diagrams/ and only the arrangement differs.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "diagrams"))

import build  # noqa: E402
import flow  # noqa: E402
import pointers  # noqa: E402
import shapes  # noqa: E402
import style  # noqa: E402  (imports matplotlib with the Agg backend)
import timer  # noqa: E402
import matplotlib  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import schemdraw  # noqa: E402

# Embed the monospace face as TrueType rather than Type 3, so the text in a figure is real
# text: searchable, selectable, and hinted the same way as the code in the book around it.
matplotlib.rcParams["pdf.fonttype"] = 42


# ----------------------------------------------------------------------------------------
# The addressing modes, as two rows of two rather than one row of four. The course's layout is
# 27 units wide, which a page would shrink to a third; two rows are 17, which it does not.
# ----------------------------------------------------------------------------------------
_PANEL_W = pointers._MODE_CELLS * pointers._MODE_CELL_W
_PANEL_TOP = pointers._MODE_TITLE_GAP + style.text_height(style.SMALL_SIZE)
_PANEL_BOTTOM = -pointers._MODE_ARROW - 0.72 - style.text_height(style.TINY_SIZE)
_ROW_PITCH = _PANEL_TOP - _PANEL_BOTTOM + 0.7


def _draw_modes_2x2(drawing, ax) -> None:
    """pointers._draw_modes, with each panel placed on a two by two grid."""
    p = pointers
    for panel, (instruction, target, ends, note) in enumerate(p._MODES):
        left = (panel % 2) * (_PANEL_W + p._MODE_GAP)
        dy = -(panel // 2) * _ROW_PITCH
        style.text(ax, instruction, (left + _PANEL_W / 2, dy + p._MODE_TITLE_GAP),
                   valign="bottom", size=style.SMALL_SIZE)
        for index in range(p._MODE_CELLS):
            fill = "accent" if index == target else "plain"
            shapes.cell(ax, left + index * p._MODE_CELL_W, dy, p._MODE_CELL_W, p._MODE_CELL_H,
                        fill)
        start_x = left + (p._BASE_INDEX + 0.5) * p._MODE_CELL_W
        end_x = left + (ends + 0.5) * p._MODE_CELL_W
        shapes.arrow(ax, (start_x, dy + p._MODE_CELL_H + p._MODE_ARROW),
                     (start_x, dy + p._MODE_CELL_H + 0.1), color=style.MUTED_COLOR)
        style.text(ax, "Z before", (start_x, dy + p._MODE_CELL_H + p._MODE_ARROW + 0.12),
                   valign="bottom", size=style.TINY_SIZE, color=style.MUTED_COLOR)
        shapes.arrow(ax, (end_x, dy - p._MODE_ARROW), (end_x, dy - 0.1),
                     color=style.ACCENT_COLOR_2)
        style.text(ax, "Z after", (end_x, dy - p._MODE_ARROW - 0.12), valign="top",
                   size=style.TINY_SIZE, color=style.ACCENT_COLOR_2)
        style.text(ax, note, (left + _PANEL_W / 2, dy - p._MODE_ARROW - 0.72), valign="top",
                   size=style.TINY_SIZE, color=style.MUTED_COLOR)
    style.caption(ax, p._MODE_CAPTION, _MODES_RIGHT / 2, _MODES_BOTTOM)


_MODES_RIGHT = 2 * _PANEL_W + pointers._MODE_GAP
_MODES_BOTTOM = _PANEL_BOTTOM - _ROW_PITCH - 0.55
_MODES_TEXT_LEFT, _MODES_TEXT_RIGHT = style.caption_bounds(pointers._MODE_CAPTION,
                                                            _MODES_RIGHT / 2)

# ----------------------------------------------------------------------------------------
# The timer block diagram, as two columns of four rows rather than a row of three with a column
# hanging off its end. The nodes, labels, fills and arrows are timer.py's; only the positions
# move, and the last arrow now runs right to left into the handler.
# ----------------------------------------------------------------------------------------
_COLUMN = 10.0
_ROW = 3.2
_BLOCK_AT = {
    "The 16 MHz clock": (0.0, 0.0),
    "Prescaler": (0.0, -_ROW),
    "TCNT1": (_COLUMN, -_ROW),
    "Comparator": (_COLUMN, -2 * _ROW),
    "OCR1A": (0.0, -2 * _ROW),
    "On a match": (_COLUMN, -3 * _ROW),
    "Your handler": (0.0, -3 * _ROW),
}
_BLOCK_NODES_2COL = tuple(
    flow.Node(node.label, _BLOCK_AT[node.label], node.detail, node.fill, node.width, node.height)
    for node in timer._BLOCK_NODES)


BOOK_LAYOUTS: dict[str, style.Figure] = {
    "timer_block": flow.figure(_BLOCK_NODES_2COL, timer._BLOCK_EDGES,
                               caption=timer._BLOCK_CAPTION),
    "addressing_modes": style.Figure(
        _draw_modes_2x2,
        (min(0.0, _MODES_TEXT_LEFT) - 0.45,
         _MODES_BOTTOM - style.caption_height(pointers._MODE_CAPTION) - 0.45,
         max(_MODES_RIGHT, _MODES_TEXT_RIGHT) + 0.45,
         _PANEL_TOP + 0.45)),
}


def render_pdf(figure: style.Figure, path: Path) -> None:
    """Draw one figure onto its declared canvas and write it as a PDF.

    The same steps as style.render, less the palette pass, which only a PNG needs.
    """
    xmin, ymin, xmax, ymax = figure.canvas
    fig, ax = plt.subplots(
        figsize=((xmax - xmin) * style.INCHES_PER_UNIT, (ymax - ymin) * style.INCHES_PER_UNIT))
    try:
        drawing = schemdraw.Drawing(canvas=ax)
        drawing.config(fontsize=style.FONT_SIZE, font=style.FONT, color=style.LINE_COLOR,
                       lw=style.WIRE_WIDTH)
        figure.draw(drawing, ax)
        drawing.draw(show=False, canvas=ax)
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        ax.set_aspect("equal")
        ax.axis("off")
        fig.subplots_adjust(left=0, bottom=0, right=1, top=1)
        # A fixed creation date keeps a rebuild byte-identical.
        fig.savefig(path, format="pdf", facecolor=style.BACKGROUND,
                    metadata={"CreationDate": None})
    finally:
        plt.close(fig)


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    outdir = Path(sys.argv[1])
    outdir.mkdir(parents=True, exist_ok=True)
    for name in sys.argv[2:]:
        figure = BOOK_LAYOUTS.get(name) or build.FIGURES[name][0]
        path = outdir / f"{name}.pdf"
        render_pdf(figure, path)
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
