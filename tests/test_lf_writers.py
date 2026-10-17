#!/usr/bin/env python3
"""WP-CI2: require explicit LF encoding of all script text writes."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


class LFWriterGuard(unittest.TestCase):
    def test_all_script_text_writers_specify_lf_newline(self):
        """Cover open, Path.open and Path.write_text; binary writes are exempt."""
        missing = []
        checked = 0
        for path in sorted(SCRIPTS.rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"),
                             filename=path.as_posix())
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                is_write_text = (isinstance(func, ast.Attribute)
                                 and func.attr == "write_text")
                is_builtin_open = isinstance(func, ast.Name) and func.id == "open"
                is_path_open = isinstance(func, ast.Attribute) and func.attr == "open"
                if not (is_write_text or is_builtin_open or is_path_open):
                    continue
                kwargs = {kw.arg: kw.value for kw in node.keywords
                          if kw.arg is not None}
                if not is_write_text:
                    mode_pos = 1 if is_builtin_open else 0
                    mode_node = kwargs.get("mode")
                    if mode_node is None and len(node.args) > mode_pos:
                        mode_node = node.args[mode_pos]
                    if mode_node is None:
                        continue  # default mode is read-only
                    try:
                        mode = ast.literal_eval(mode_node)
                    except (ValueError, TypeError, SyntaxError):
                        missing.append(f"{path.relative_to(ROOT)}:{node.lineno}: dynamic open mode")
                        continue
                    if not isinstance(mode, str):
                        missing.append(f"{path.relative_to(ROOT)}:{node.lineno}: invalid open mode")
                        continue
                    if "b" in mode or not any(c in mode for c in "wax+"):
                        continue
                checked += 1
                newline = kwargs.get("newline")
                if not (isinstance(newline, ast.Constant)
                        and newline.value == "\n"):
                    missing.append(f"{path.relative_to(ROOT)}:{node.lineno}: "
                                   f"{'write_text' if is_write_text else 'text open'} "
                                   'must specify newline="\n"')
        self.assertGreater(checked, 0, "No text writers were inspected")
        self.assertFalse(missing, "Text writers without explicit LF policy:\n" +
                         "\n".join(missing))


if __name__ == "__main__":
    unittest.main(verbosity=2)
