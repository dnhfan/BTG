"""Test Execution & Oracle — SRS FE-03 va FR-4.3.

- load_ground_truth(): nap ham chuan tu chuoi code Python cua nguoi dung.
- apply_oracle(): chay ham chuan cho tung test case, ghi lai
  Expected Output dung (hoac Exception dung) vao chinh test case do.
- run_test_cases(): thuc thi va so sanh, tra ve ket qua Pass/Fail tung case.

LUU Y AN TOAN: chi chay code Ground Truth do chinh nguoi dung cung cap
tren may cua ho (dung cho muc dich hoc tap / kiem thu cuc bo).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .models import FunctionSpec, TestCase


def load_ground_truth(code: str, function_name: str) -> Callable:
    namespace: dict[str, Any] = {}
    exec(compile(code, "<ground_truth>", "exec"), namespace)  # noqa: S102
    func = namespace.get(function_name)
    if not callable(func):
        raise ValueError(
            f"Khong tim thay ham '{function_name}' trong file Ground Truth."
        )
    return func


def _call(func: Callable, spec: FunctionSpec, inputs: dict) -> tuple[Any, str | None]:
    """Goi ham theo dung thu tu tham so. Tra (ket_qua, ten_exception)."""
    args = [inputs.get(name) for name in spec.param_names()]
    try:
        return func(*args), None
    except Exception as exc:  # bat moi exception cua ham duoc kiem thu
        return None, type(exc).__name__


def apply_oracle(
    spec: FunctionSpec, cases: list[TestCase], ground_truth_code: str
) -> list[TestCase]:
    """Dung ham chuan de dien Expected Output / Expected Exception (FR-3.2)."""
    func = load_ground_truth(ground_truth_code, spec.name)
    for case in cases:
        result, exc_name = _call(func, spec, case.inputs)
        if exc_name is not None:
            case.expected_exception = exc_name
            case.expected_output = None
        else:
            case.expected_exception = None
            case.expected_output = result
    return cases


@dataclass
class ExecutionResult:
    test_case: TestCase
    actual_output: Any = None
    actual_exception: str | None = None
    status: str = "Skipped"  # Pass | Fail | Skipped


def run_test_cases(
    spec: FunctionSpec, cases: list[TestCase], ground_truth_code: str
) -> list[ExecutionResult]:
    """Chay test va so sanh voi Expected da co trong tung case (FR-4.3).

    Quy tac:
    - Case co expected_exception: Pass neu ham nem dung loai exception do
      (exception "Exception" chung chung = bat ky exception nao cung Pass).
    - Case co expected_output: Pass neu ket qua thuc te bang expected
      va ham khong nem exception.
    - Case khong co ca hai: chi chay thu, danh dau Skipped (chua co oracle
      de ket luan dung/sai) nhung van ghi lai ket qua thuc te.
    """
    func = load_ground_truth(ground_truth_code, spec.name)
    results: list[ExecutionResult] = []
    for case in cases:
        actual, exc_name = _call(func, spec, case.inputs)
        if case.expected_exception:
            if case.expected_exception == "Exception":
                passed = exc_name is not None
            else:
                passed = exc_name == case.expected_exception
            status = "Pass" if passed else "Fail"
        elif case.expected_output is not None:
            status = "Pass" if (exc_name is None and actual == case.expected_output) else "Fail"
        else:
            status = "Skipped"
        results.append(
            ExecutionResult(case, actual if exc_name is None else None, exc_name, status)
        )
    return results


def pass_fail_summary(results: list[ExecutionResult]) -> dict:
    total = len(results)
    passed = sum(1 for r in results if r.status == "Pass")
    failed = sum(1 for r in results if r.status == "Fail")
    skipped = sum(1 for r in results if r.status == "Skipped")
    decided = passed + failed
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "pass_rate": round(passed / decided * 100, 1) if decided else 0.0,
    }
