#!/usr/bin/env python3
"""Print an annotated project tree for docs.

Run: python tools/tree_doc.py [--root .] [--name project]
"""

from __future__ import annotations

import argparse
from pathlib import Path, PurePosixPath

# relative path -> note. Order here = order in the output.
FILES = {
    "app.py": "Giao diện CustomTkinter, điều phối sự kiện",
    "btg/models.py": "ParamSpec, FunctionSpec, TestCase, ExecutionResult",
    "btg/validation.py": "Kiểm tra tính hợp lệ của đặc tả",
    "btg/parser.py": "Phân tích AST từ tệp .py",
    "btg/values.py": "Giá trị đại diện, giá trị không hợp lệ",
    "btg/generators.py": "EP, BVA, Pairwise, khử trùng",
    "btg/executor.py": "Hàm tham chiếu, chạy đối chiếu, thống kê",
    "btg/exporter.py": "CSV, Excel, pytest",
    "examples/sample_function.py": "",
    "docs/HUONG_DAN_SU_DUNG.md": "",
}


def build(paths):
    tree = {}
    for p in paths:
        node = tree
        for part in PurePosixPath(p).parts:
            node = node.setdefault(part, {})
    return tree


def render(node, prefix="", base=""):
    lines = []
    entries = list(node.items())  # insertion order, not alphabetical
    for i, (name, child) in enumerate(entries):
        last = i == len(entries) - 1
        rel = f"{base}/{name}" if base else name
        if child:
            lines.append(f"{prefix}{'└── ' if last else '├── '}{name}/")
            lines.extend(render(child, prefix + ("    " if last else "│   "), rel))
        else:
            note = FILES.get(rel, "")
            lines.append(
                f"{prefix}{'└── ' if last else '├── '}{name}"
                + (f"   # {note}" if note else "")
            )
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--name", default="project")
    args = ap.parse_args()

    root = Path(args.root)
    kept = [p for p in FILES if (root / p).exists()]  # skip files not present
    print(f"{args.name}/")
    print("\n".join(render(build(kept))))


if __name__ == "__main__":
    main()
