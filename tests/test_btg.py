"""Unit test cho BTG core. Chay: pytest -q"""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import itertools

import pytest

from btg.executor import apply_oracle, pass_fail_summary, run_test_cases
from btg.exporter import export_csv, export_excel, generate_pytest_code
from btg.generators import generate_bva, generate_ep, generate_pairwise, generate_test_cases
from btg.models import FunctionSpec, ParamSpec, ParamType
from btg.parser import parse_python_code
from btg.validation import validate_spec
from btg.values import candidate_values


def age_spec():
    return FunctionSpec("check_age", [ParamSpec("age", ParamType.INT, min_value=0, max_value=150)])


def register_spec():
    return FunctionSpec(
        "register",
        [
            ParamSpec("username", ParamType.STRING, min_length=3, max_length=20),
            ParamSpec("age", ParamType.INT, min_value=18, max_value=60),
            ParamSpec("role", ParamType.ENUM, enum_values=["admin", "user", "guest"]),
            ParamSpec("active", ParamType.BOOL),
        ],
    )


# ------------------------------------------------------------- validation
def test_validation_min_greater_than_max():
    spec = FunctionSpec("f", [ParamSpec("x", ParamType.INT, min_value=10, max_value=1)])
    assert any("min" in e for e in validate_spec(spec))


def test_validation_duplicate_param_and_bad_regex():
    spec = FunctionSpec(
        "f",
        [
            ParamSpec("s", ParamType.STRING, min_length=1, max_length=5, regex="[unclosed"),
            ParamSpec("s", ParamType.INT),
        ],
    )
    errors = validate_spec(spec)
    assert any("trung" in e for e in errors)
    assert any("regex" in e for e in errors)


def test_generate_raises_on_invalid_spec():
    spec = FunctionSpec("f", [ParamSpec("x", ParamType.INT, min_value=10, max_value=1)])
    with pytest.raises(ValueError):
        generate_test_cases(spec)


# --------------------------------------------------------------------- EP
def test_ep_has_valid_and_single_fault_invalid():
    cases = generate_ep(age_spec())
    assert cases[0].reasoning == "[EP] Valid_Partition"
    invalid = [c for c in cases if "Invalid" in c.reasoning]
    assert invalid, "EP phai sinh case invalid"
    # Single Fault: case invalid chi co 1 tham so -> gia tri do la gia tri sai
    assert any(c.inputs["age"] == -1 for c in invalid)
    assert any(c.inputs["age"] == 151 for c in invalid)
    assert any(c.inputs["age"] is None for c in invalid)


# -------------------------------------------------------------------- BVA
def test_bva_points():
    values = {c.inputs["age"] for c in generate_bva(age_spec())}
    assert {-1, 0, 1, 149, 150, 151} <= values


def test_bva_string_lengths():
    spec = FunctionSpec("f", [ParamSpec("s", ParamType.STRING, min_length=3, max_length=5)])
    lengths = {len(c.inputs["s"]) for c in generate_bva(spec)}
    assert {2, 3, 4, 5, 6} <= lengths


# --------------------------------------------------------------- pairwise
def test_pairwise_covers_all_pairs():
    spec = register_spec()
    cases = generate_pairwise(spec)
    cand = {p.name: candidate_values(p) for p in spec.params}
    names = [p.name for p in spec.params]
    full = set(itertools.product(*[cand[n] for n in names]))
    assert len(cases) < len(full), "Pairwise phai it hon full combination"
    for i, j in itertools.combinations(range(len(names)), 2):
        for vi in cand[names[i]]:
            for vj in cand[names[j]]:
                assert any(
                    c.inputs[names[i]] == vi and c.inputs[names[j]] == vj for c in cases
                ), f"Chua phu cap {names[i]}={vi}, {names[j]}={vj}"


# ------------------------------------------------------------------ dedup
def test_deduplication_and_ids():
    cases = generate_test_cases(age_spec(), use_ep=True, use_bva=True)
    keys = [tuple(sorted((k, repr(v)) for k, v in c.inputs.items())) for c in cases]
    assert len(keys) == len(set(keys))
    assert cases[0].test_id == "TC_001"


# ----------------------------------------------------------------- parser
def test_parser_extracts_types_and_literal_enum():
    code = '''
from typing import Literal

def register(username: str, age: int, role: Literal["admin", "user"], active: bool, score: float):
    pass
'''
    (spec,) = parse_python_code(code)
    types = {p.name: p.type for p in spec.params}
    assert types["username"] == ParamType.STRING
    assert types["age"] == ParamType.INT
    assert types["active"] == ParamType.BOOL
    assert types["score"] == ParamType.FLOAT
    role = next(p for p in spec.params if p.name == "role")
    assert role.type == ParamType.ENUM and role.enum_values == ["admin", "user"]


# ------------------------------------------------------- oracle / executor
GROUND_TRUTH = '''
def check_age(age):
    if age is None:
        raise TypeError("age must not be None")
    if age < 0 or age > 150:
        raise ValueError("age out of range")
    if age < 18:
        return "child"
    if age < 65:
        return "adult"
    return "senior"
'''


def test_oracle_fills_expected_output():
    cases = generate_test_cases(age_spec(), use_ep=True, use_bva=True)
    cases = apply_oracle(age_spec(), cases, GROUND_TRUTH)
    valid = next(c for c in cases if c.reasoning == "[EP] Valid_Partition")
    assert valid.expected_output == "senior"  # age nominal = 75
    assert valid.expected_exception is None


def test_run_tests_all_pass_with_oracle():
    cases = generate_test_cases(age_spec(), use_ep=True, use_bva=True)
    cases = apply_oracle(age_spec(), cases, GROUND_TRUTH)
    results = run_test_cases(age_spec(), cases, GROUND_TRUTH)
    summary = pass_fail_summary(results)
    assert summary["failed"] == 0
    assert summary["pass_rate"] == 100.0


# ---------------------------------------------------------------- exporter
def test_export_csv_and_pytest_code():
    cases = generate_test_cases(age_spec(), use_ep=True, use_bva=True)
    cases = apply_oracle(age_spec(), cases, GROUND_TRUTH)
    csv_bytes = export_csv(cases)
    assert b"Testcase ID" in csv_bytes and b"TC_001" in csv_bytes

    code = generate_pytest_code(age_spec(), cases, GROUND_TRUTH)
    compile(code, "test_generated.py", "exec")  # code sinh ra phai hop le
    assert "@pytest.mark.parametrize" in code
    assert "check_age" in code


def test_export_with_results_adds_actual_and_status_columns():
    cases = generate_test_cases(age_spec(), use_ep=True, use_bva=True)
    cases = apply_oracle(age_spec(), cases, GROUND_TRUTH)
    results = run_test_cases(age_spec(), cases, GROUND_TRUTH)

    plain = export_csv(cases).decode("utf-8-sig")
    assert "Actual Output" not in plain and "Status" not in plain

    full = export_csv(cases, results).decode("utf-8-sig")
    header = full.splitlines()[0]
    assert "Actual Output" in header and "Actual Exception" in header
    assert "Status" in header
    assert "Pass" in full

    excel = export_excel(cases, results)
    assert excel[:2] == b"PK"  # file xlsx la zip
