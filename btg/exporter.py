"""Exporter — SRS FE-04.

- export_csv / export_excel : bang test case (FR-4.1)
  Cot: Testcase ID, Inputs, Expected Output, Test Technique, Reasoning
  (bo sung cot Expected Exception de file pytest va bao cao ro rang hon)
- generate_pytest_code      : file test_generated.py (FR-4.2)
  dung @pytest.mark.parametrize, nhung kem code ham tham chieu neu co
  de file chay duoc ngay ma khong can import them.
"""
from __future__ import annotations

import csv
import io
import json

from .models import FunctionSpec, TestCase

COLUMNS = [
    "Testcase ID",
    "Inputs",
    "Expected Output",
    "Expected Exception",
    "Test Technique",
    "Reasoning",
]


def _rows(cases: list[TestCase]) -> list[dict]:
    rows = []
    for case in cases:
        rows.append(
            {
                "Testcase ID": case.test_id,
                "Inputs": json.dumps(case.inputs, ensure_ascii=False, default=str),
                "Expected Output": "" if case.expected_output is None else str(case.expected_output),
                "Expected Exception": case.expected_exception or "",
                "Test Technique": case.technique,
                "Reasoning": case.reasoning,
            }
        )
    return rows


def export_csv(cases: list[TestCase]) -> bytes:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=COLUMNS)
    writer.writeheader()
    writer.writerows(_rows(cases))
    return buffer.getvalue().encode("utf-8-sig")  # BOM de Excel doc dung tieng Viet


def export_excel(cases: list[TestCase]) -> bytes:
    from openpyxl import Workbook
    from openpyxl.styles import Font

    wb = Workbook()
    ws = wb.active
    ws.title = "Test Cases"
    ws.append(COLUMNS)
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for row in _rows(cases):
        ws.append([row[col] for col in COLUMNS])
    for col in ws.columns:
        width = max(len(str(c.value or "")) for c in col) + 2
        ws.column_dimensions[col[0].column_letter].width = min(width, 60)
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


# -------------------------------------------------------------- pytest ---

def generate_pytest_code(
    spec: FunctionSpec,
    cases: list[TestCase],
    ground_truth_code: str | None = None,
    source_module: str = "function_under_test",
) -> str:
    """Sinh noi dung file test_generated.py.

    - Neu co ground_truth_code: nhung thang code do vao file test.
    - Neu khong: sinh dong import `from <source_module> import <ham>`
      de nguoi dung sua lai ten module cho dung voi project cua ho.
    """
    lines: list[str] = []
    lines.append('"""File test tu dong sinh boi Black-box Test Generator (BTG).')
    lines.append(f"Ham duoc kiem thu: {spec.name}({', '.join(spec.param_names())})")
    lines.append('"""')
    lines.append("import pytest")
    lines.append("")
    if ground_truth_code:
        lines.append("# ===== Ham tham chieu / ham duoc kiem thu (nhung tu file nguoi dung) =====")
        lines.append(ground_truth_code.rstrip())
        lines.append("")
    else:
        lines.append(f"# TODO: sua lai ten module neu can")
        lines.append(f"from {source_module} import {spec.name}")
        lines.append("")

    valid_rows, exception_rows = [], []
    for case in cases:
        values = tuple(case.inputs.get(name) for name in spec.param_names())
        if case.expected_exception:
            exception_rows.append((case, values))
        else:
            valid_rows.append((case, values))

    argnames = ",".join(spec.param_names())

    if valid_rows:
        lines.append("# ===== Case khong mong doi exception =====")
        lines.append("@pytest.mark.parametrize(")
        lines.append(f'    "{argnames},expected",')
        lines.append("    [")
        for case, values in valid_rows:
            args_str = ", ".join(repr(v) for v in values + (case.expected_output,))
            lines.append(f'        pytest.param({args_str}, id="{case.test_id}"),  # {case.reasoning}')
        lines.append("    ],")
        lines.append(")")
        sig = ", ".join(spec.param_names() + ["expected"])
        lines.append(f"def test_{spec.name}_valid({sig}):")
        call = f"{spec.name}({', '.join(spec.param_names())})"
        lines.append("    result = " + call)
        lines.append("    # Neu chua co oracle (expected = None) thi chi can ham chay khong loi")
        lines.append("    if expected is not None:")
        lines.append("        assert result == expected")
        lines.append("")

    if exception_rows:
        lines.append("# ===== Case mong doi exception =====")
        lines.append("@pytest.mark.parametrize(")
        lines.append(f'    "{argnames},exc_name",')
        lines.append("    [")
        for case, values in exception_rows:
            args_str = ", ".join(repr(v) for v in values + (case.expected_exception,))
            lines.append(f'        pytest.param({args_str}, id="{case.test_id}"),  # {case.reasoning}')
        lines.append("    ],")
        lines.append(")")
        sig = ", ".join(spec.param_names() + ["exc_name"])
        lines.append(f"def test_{spec.name}_raises({sig}):")
        lines.append("    exc_type = Exception if exc_name in (\"Exception\", None) else globals().get(exc_name, Exception)")
        lines.append("    # Voi exception cu the (ValueError...), doi ten ben duoi neu ham nem loai khac")
        call = f"{spec.name}({', '.join(spec.param_names())})"
        lines.append("    with pytest.raises(Exception) as excinfo:")
        lines.append(f"        {call}")
        lines.append("    if exc_name not in (\"Exception\", None):")
        lines.append("        assert excinfo.type.__name__ == exc_name")
        lines.append("")

    return "\n".join(lines) + "\n"
