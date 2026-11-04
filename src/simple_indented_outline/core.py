"""Core parser for whitespace-indented outlines.

The parser treats indentation as a stack of levels. A line is a child of the
most recent line whose indentation is strictly less than its own. Indentation
is measured in columns: spaces count as one column, tabs are expanded to the
next multiple of ``tab_width``. This choice makes mixed tabs and spaces
predictable without requiring a specific tab width from the caller.

An ``OutlineError`` is raised when a line's indentation does not match any
level currently on the stack and is not deeper than the previous line. That
is the only inconsistency this library reports; it deliberately does not
try to auto-correct or guess a missing level.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


class OutlineError(ValueError):
    """Raised when indentation is inconsistent.

    Attributes:
        line_number: 1-based index of the offending line in the input.
        column: 0-based column where the indentation stopped being valid.
        message: Human-readable description of the problem.
    """

    def __init__(self, line_number: int, column: int, message: str) -> None:
        self.line_number = line_number
        self.column = column
        self.message = message
        super().__init__(f"line {line_number}, column {column}: {message}")


@dataclass
class Node:
    """A single outline entry.

    ``text`` is the line content with leading indentation stripped and
    trailing newline removed. ``indent`` is the number of columns of leading
    whitespace. ``children`` preserves input order.
    """

    text: str
    indent: int
    children: List["Node"] = field(default_factory=list)

    def walk(self):
        """Yield this node and all descendants in depth-first pre-order."""
        yield self
        for child in self.children:
            yield from child.walk()

    def __repr__(self) -> str:  # pragma: no cover - convenience only
        return f"Node(text={self.text!r}, indent={self.indent}, children={len(self.children)})"


def _expand_tabs(line: str, tab_width: int) -> str:
    """Replace tabs with spaces up to the next tab stop.

    We expand rather than reject tabs because a tab stop is a property of the
    display, not the data. Expanding to a fixed width gives a stable column
    count that the consistency check can compare.
    """
    if tab_width <= 0:
        raise ValueError("tab_width must be positive")
    out = []
    column = 0
    for ch in line:
        if ch == "\t":
            spaces = tab_width - (column % tab_width)
            out.append(" " * spaces)
            column += spaces
        else:
            out.append(ch)
            column += 1
    return "".join(out)


def _indent_width(line: str, tab_width: int) -> int:
    """Return the number of leading whitespace columns in ``line``."""
    expanded = _expand_tabs(line, tab_width)
    return len(expanded) - len(expanded.lstrip(" "))


def parse(text: str, tab_width: int = 4) -> List[Node]:
    """Parse ``text`` into a list of root nodes.

    Args:
        text: The outline source. Blank lines are ignored entirely; they do
            not end a block and do not appear in the tree.
        tab_width: Number of columns a tab advances to. Must be positive.

    Returns:
        The roots of the tree, in input order.

    Raises:
        OutlineError: If a line's indentation is not deeper than its parent
            and does not match an existing level.
    """
    if tab_width <= 0:
        raise ValueError("tab_width must be positive")

    roots: List[Node] = []
    # Stack of (indent, node) for the current path from a root to the last
    # node seen at each level. The top of the stack is always the most
    # recently opened node.
    stack: List[tuple[int, Node]] = []

    for line_number, raw in enumerate(text.splitlines(), start=1):
        if raw.strip() == "":
            continue

        indent = _indent_width(raw, tab_width)
        content = raw.lstrip(" \t")

        # A line must be a child of the most recent line with strictly
        # smaller indentation. Any other indent is an error: it neither
        # matches an open level nor descends from the previous line.
        if stack and indent != 0:
            parent_indent = stack[-1][0]
            if indent <= parent_indent:
                # Dedenting to a level that was never opened is an error.
                if not any(level == indent for level, _ in stack):
                    raise OutlineError(
                        line_number,
                        indent,
                        f"indentation {indent} does not match any open level",
                    )

        # Pop nodes whose indentation is not strictly less than this line's.
        # After this loop, stack[-1] is the deepest node that can be the
        # parent, or the stack is empty for a new root.
        while stack and stack[-1][0] >= indent:
            stack.pop()

        if stack:
            node = Node(text=content, indent=indent)
            stack[-1][1].children.append(node)
        else:
            node = Node(text=content, indent=indent)
            roots.append(node)

        stack.append((indent, node))

    return roots
