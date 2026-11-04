"""Indented outline parser.

Converts whitespace-indented hierarchical text into a node tree and reports
inconsistent indentation.
"""

from .core import Node, OutlineError, parse

__all__ = ["Node", "OutlineError", "parse"]
