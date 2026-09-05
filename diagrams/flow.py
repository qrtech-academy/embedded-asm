"""Box-and-arrow diagrams: what turns into what, and in which order.

Two quite different things are drawn with the same shapes, and that is deliberate. L01 uses
this for the toolchain, where the boxes are files and programs and the arrows are "produces".
L03 uses it for what the hardware does when an interrupt fires, where the boxes are steps and
the arrows are "then". A reader who has learned to read one reads the other for free.

Nodes are placed by hand at explicit centres rather than laid out automatically. These
diagrams are small, they are read in a fixed order, and where a box sits carries meaning:
automatic layout would give up that control to save an afternoon.

Edges are routed centre to centre and then clipped to both boxes' borders, so an arrow always
touches the boxes it connects and never crosses into them, whatever direction it runs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import schemdraw

import shapes
import style

# ----------------------------------------------------------------------------------------
# Geometry, in canvas units.
# ----------------------------------------------------------------------------------------
NODE_W = 4.6
NODE_H = 1.55
DETAIL_GAP = 0.22      # Between a node's label and the line under it.
EDGE_LABEL_GAP = 0.24  # Between an arrow and the text alongside it.
CAPTION_DROP = 0.55    # Between the lowest box and the first caption line.
MARGIN = 0.50


@dataclass(frozen=True)
class Node:
    """One box: where it sits, what it says, and how it is filled."""

    label: str
    pos: tuple[float, float]      # Centre, in canvas units.
    detail: str | None = None
    fill: str = "plain"
    width: float = NODE_W
    height: float = NODE_H

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        """(left, low, right, high) of the box."""
        x, y = self.pos
        return (x - self.width / 2, y - self.height / 2,
                x + self.width / 2, y + self.height / 2)


@dataclass(frozen=True)
class Edge:
    """One arrow, from the node at index `src` to the node at index `dst`."""

    src: int
    dst: int
    label: str | None = None
    dashed: bool = False
    # Which side of the arrow the label sits on, and how far. The default puts it above a
    # horizontal arrow; a vertical one usually wants it to the side instead.
    label_offset: tuple[float, float] = (0.0, EDGE_LABEL_GAP)


def _border(node: Node, towards: tuple[float, float]) -> tuple[float, float]:
    """The point on `node`'s border on the straight line from its centre towards a point.

    Scaling the direction vector by whichever axis leaves the box first is what makes one
    routing rule work for a horizontal arrow, a vertical one, and everything between. Doing
    it per axis instead would need a special case for each, and would get one of them wrong.
    """
    x, y = node.pos
    dx, dy = towards[0] - x, towards[1] - y
    if dx == 0 and dy == 0:
        return node.pos

    # How far along the direction the border lies, on each axis independently; the nearer of
    # the two is the one the line actually crosses.
    scale_x = abs((node.width / 2) / dx) if dx else float("inf")
    scale_y = abs((node.height / 2) / dy) if dy else float("inf")
    scale = min(scale_x, scale_y)
    return x + dx * scale, y + dy * scale


def draw(nodes: Sequence[Node], edges: Sequence[Edge], caption: Sequence[str],
         drawing: schemdraw.Drawing, ax) -> None:
    """Draw every box, then every arrow between them.

    Public because a figure that wants to add its own annotations on top of a flow, as L03's
    interrupt sequence does with its cycle costs, needs to render the flow itself and then keep
    drawing rather than handing the whole figure over.
    """
    for node in nodes:
        left, low, _, _ = node.bounds
        shapes.cell(ax, left, low, node.width, node.height, node.fill)

        x, y = node.pos
        if node.detail is None:
            style.text(ax, node.label, (x, y), size=style.SMALL_SIZE)
        else:
            style.text(ax, node.label, (x, y + DETAIL_GAP), valign="bottom",
                       size=style.SMALL_SIZE)
            style.text(ax, node.detail, (x, y - DETAIL_GAP), valign="top",
                       size=style.TINY_SIZE, color=style.MUTED_COLOR)

    for edge in edges:
        source, target = nodes[edge.src], nodes[edge.dst]
        start = _border(source, target.pos)
        end = _border(target, source.pos)
        shapes.arrow(ax, start, end, dashed=edge.dashed)

        if edge.label is not None:
            mid = ((start[0] + end[0]) / 2 + edge.label_offset[0],
                   (start[1] + end[1]) / 2 + edge.label_offset[1])
            style.text(ax, edge.label, mid, size=style.TINY_SIZE,
                       valign="bottom" if edge.label_offset[1] >= 0 else "top")

    if caption:
        lowest = min(node.bounds[1] for node in nodes)
        left = min(node.bounds[0] for node in nodes)
        right = max(node.bounds[2] for node in nodes)
        style.caption(ax, caption, (left + right) / 2, lowest - CAPTION_DROP)


def figure(nodes: Sequence[Node], edges: Sequence[Edge],
           caption: Sequence[str] = ()) -> style.Figure:
    """A ready-to-render flow diagram, sized to the boxes and their labels."""
    left = min(node.bounds[0] for node in nodes)
    low = min(node.bounds[1] for node in nodes)
    right = max(node.bounds[2] for node in nodes)
    high = max(node.bounds[3] for node in nodes)

    # An edge's label sits wherever its offset puts it, which is routinely outside the boxes:
    # a label lifted clear of two boxes it would otherwise sit across ends up above both of
    # them. Sizing the canvas to the boxes alone clips it, and clips it silently.
    for edge in edges:
        if edge.label is None:
            continue
        source, target = nodes[edge.src], nodes[edge.dst]
        start = _border(source, target.pos)
        end = _border(target, source.pos)
        x = (start[0] + end[0]) / 2 + edge.label_offset[0]
        y = (start[1] + end[1]) / 2 + edge.label_offset[1]
        half = style.text_width(edge.label, style.TINY_SIZE) / 2
        height = style.text_height(style.TINY_SIZE)
        left, right = min(left, x - half), max(right, x + half)
        if edge.label_offset[1] >= 0:
            high = max(high, y + height)
        else:
            low = min(low, y - height)

    if caption:
        low -= CAPTION_DROP + style.caption_height(caption)
        span_left, span_right = style.caption_bounds(caption, (left + right) / 2)
        left, right = min(left, span_left), max(right, span_right)

    return style.Figure(
        draw=lambda d, ax: draw(nodes, edges, caption, d, ax),
        canvas=(left - MARGIN, low - MARGIN, right + MARGIN, high + MARGIN))
