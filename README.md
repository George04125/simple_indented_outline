# simple_indented_outline

Parse whitespace-indented text into a tree of nodes and report inconsistent indentation.

```python
from simple_indented_outline import parse

text = """
root
  child
    grandchild
  sibling
"""

roots = parse(text)
root = roots[0]
print(root.text)                       # root
print([c.text for c in root.children]) # ['child', 'sibling']
print(root.children[0].children[0].text)  # grandchild
```

## Why this exists

Outlines, trees, and nested lists are often stored as plain indented text. The
hard part is not building the tree; it is deciding what counts as a valid
indentation step. This library picks one rule: a line is a child of the most
recent line with strictly smaller indentation. Indentation is measured in
columns, with tabs expanded to the next multiple of `tab_width` (default 4).
Any line whose indentation neither matches an open level nor is deeper than
the previous line raises `OutlineError` with the line number and column.

That is a deliberate trade-off: the parser refuses to guess a missing level
instead of silently repairing the input. If your source uses a style where
indentation is not strictly additive, this library will reject it rather than
produce a surprising tree.

## API

- `parse(text: str, tab_width: int = 4) -> list[Node]`
  Returns the root nodes in input order. Blank lines are ignored. Raises
  `OutlineError` on inconsistent indentation and `ValueError` if `tab_width`
  is not positive.
- `Node`
  - `text: str` — line content with leading whitespace removed.
  - `indent: int` — leading whitespace in columns.
  - `children: list[Node]` — child nodes in input order.
  - `walk()` — yields this node and all descendants depth-first.
- `OutlineError`
  - `line_number: int` — 1-based line of the offending input.
  - `column: int` — 0-based column where the indentation stopped being valid.

## The awkward edge

Dedenting to a level that was never opened is an error, not a new root. For
example, `"a\n    b\n  c\n"` raises because `c` is indented two columns while
the only open levels are 0 and 4. If you want `c` to be a sibling of `b`, indent
it four columns; if you want it to be a child of `a`, indent it two columns and
make sure nothing deeper is currently open.

## Performance

The window keeps a bounded buffer, so `push` is constant time and memory does not
grow with the length of the stream. `peak` and `trough` are linear in the window
size, which is the trade that keeps `push` cheap.

