import unittest

from simple_indented_outline import Node, OutlineError, parse


class TestParse(unittest.TestCase):
    def test_empty_input(self):
        self.assertEqual(parse(""), [])

    def test_single_root(self):
        roots = parse("alpha")
        self.assertEqual(len(roots), 1)
        self.assertEqual(roots[0].text, "alpha")
        self.assertEqual(roots[0].indent, 0)
        self.assertEqual(roots[0].children, [])

    def test_nested_children(self):
        text = "root\n  child\n    grandchild\n"
        roots = parse(text)
        self.assertEqual(len(roots), 1)
        root = roots[0]
        self.assertEqual(root.text, "root")
        self.assertEqual(len(root.children), 1)
        child = root.children[0]
        self.assertEqual(child.text, "child")
        self.assertEqual(len(child.children), 1)
        self.assertEqual(child.children[0].text, "grandchild")

    def test_siblings(self):
        text = "a\n  b\n  c\nd\n"
        roots = parse(text)
        self.assertEqual([r.text for r in roots], ["a", "d"])
        self.assertEqual([c.text for c in roots[0].children], ["b", "c"])

    def test_blank_lines_ignored(self):
        text = "a\n\n  b\n\n"
        roots = parse(text)
        self.assertEqual(len(roots), 1)
        self.assertEqual(roots[0].text, "a")
        self.assertEqual([c.text for c in roots[0].children], ["b"])

    def test_tabs_expand_to_tab_width(self):
        text = "a\n\tb\n\t\tc\n"
        roots = parse(text, tab_width=4)
        self.assertEqual(roots[0].children[0].indent, 4)
        self.assertEqual(roots[0].children[0].children[0].indent, 8)

    def test_mixed_tabs_and_spaces(self):
        text = "a\n\tb\n    c\n"
        roots = parse(text, tab_width=4)
        self.assertEqual([c.text for c in roots[0].children], ["b", "c"])

    def test_inconsistent_indentation_raises(self):
        # 'b' is indented 4, then 'c' is indented 2. 2 does not match the
        # root level (0) or the current level (4), and is not deeper than
        # the previous line, so it is an error.
        text = "a\n    b\n  c\n"
        with self.assertRaises(OutlineError) as ctx:
            parse(text)
        self.assertEqual(ctx.exception.line_number, 3)
        self.assertEqual(ctx.exception.column, 2)

    def test_dedent_to_existing_level_is_allowed(self):
        text = "a\n  b\n    c\n  d\n"
        roots = parse(text)
        self.assertEqual([c.text for c in roots[0].children], ["b", "d"])
        self.assertEqual([c.text for c in roots[0].children[0].children], ["c"])

    def test_negative_tab_width_rejected(self):
        with self.assertRaises(ValueError):
            parse("a", tab_width=0)

    def test_walk_yields_preorder(self):
        roots = parse("a\n  b\n    c\n  d\n")
        self.assertEqual([n.text for n in roots[0].walk()], ["a", "b", "c", "d"])

    def test_node_repr_does_not_crash(self):
        node = Node(text="x", indent=0)
        self.assertIn("x", repr(node))


if __name__ == "__main__":
    unittest.main()
