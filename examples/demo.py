"""Demo chay BTG khong can giao dien: sinh test case cho ham `register`.

Chay tu thu muc goc project:  python examples/demo.py
Ket qua ghi vao thu muc output/: test_cases.csv, test_cases.xlsx, test_generated.py
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from btg.exporter import export_csv, export_excel, generate_pytest_code
from btg.executor import apply_oracle, pass_fail_summary, run_test_cases
from btg.generators import generate_test_cases
from btg.models import FunctionSpec, ParamSpec, ParamType

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE.parent / "output"
OUT.mkdir(exist_ok=True)

spec = FunctionSpec(
    name="register",
    params=[
        ParamSpec("username", ParamType.STRING, min_length=3, max_length=20),
        ParamSpec("age", ParamType.INT, min_value=18, max_value=60),
        ParamSpec("role", ParamType.ENUM, enum_values=["admin", "user", "guest"]),
        ParamSpec("active", ParamType.BOOL),
    ],
)

ground_truth = (HERE / "sample_function.py").read_text(encoding="utf-8")

if __name__ == "__main__":
    cases = generate_test_cases(spec, use_ep=True, use_bva=True, use_pairwise=True)
    print(f"Da sinh {len(cases)} test case (truoc oracle)")
    for c in cases[:8]:
        print(c.test_id, c.inputs, "|", c.reasoning)

    cases = apply_oracle(spec, cases, ground_truth)
    results = run_test_cases(spec, cases, ground_truth)
    print("Tom tat chay test:", pass_fail_summary(results))

    (OUT / "test_cases.csv").write_bytes(export_csv(cases))
    (OUT / "test_cases.xlsx").write_bytes(export_excel(cases))
    (OUT / "test_generated.py").write_text(
        generate_pytest_code(spec, cases, ground_truth), encoding="utf-8"
    )
    print(f"Da ghi ket qua vao: {OUT}")
