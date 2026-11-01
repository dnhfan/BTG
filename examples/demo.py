"""Demo chay BTG khong can giao dien cho tat ca ham trong sample_function.py.

Chay tu thu muc goc project:  python examples/demo.py
Ket qua moi ham ghi rieng vao output/<ten_ham>_{cases.csv,cases.xlsx,tests.py}.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from btg.exporter import export_csv, export_excel, generate_pytest_code
from btg.executor import apply_oracle, pass_fail_summary, run_test_cases
from btg.generators import generate_test_cases
from btg.parser import parse_python_file

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE.parent / "output"
OUT.mkdir(exist_ok=True)

SAMPLE_FILE = HERE / "sample_function.py"
ground_truth = SAMPLE_FILE.read_text(encoding="utf-8")

# Type hints duoc parser tu dong; cac mien nghiep vu va regex khong nam trong
# type hint nen khai bao tai day (tuong ung voi viec chinh form tren giao dien).
PARAM_OVERRIDES = {
    "check_age": {"age": {"min_value": 0, "max_value": 150}},
    "register": {
        "username": {"min_length": 3, "max_length": 20},
        "age": {"min_value": 18, "max_value": 60},
    },
    "validate_record": {
        "quantity": {"min_value": 1, "max_value": 100},
        "score": {"min_value": 0.0, "max_value": 10.0},
        "name": {"min_length": 2, "max_length": 12},
    },
    "validate_product_code": {
        "product_id": {"min_value": 1, "max_value": 100},
        "code": {"min_length": 6, "max_length": 6, "regex": r"^[A-Z]{2}\d{4}$"},
    },
}


def configure_specs():
    specs = parse_python_file(SAMPLE_FILE)
    for spec in specs:
        overrides = PARAM_OVERRIDES.get(spec.name, {})
        for param in spec.params:
            for key, value in overrides.get(param.name, {}).items():
                setattr(param, key, value)
    return specs

if __name__ == "__main__":
    specs = configure_specs()
    total_cases = 0
    for spec in specs:
        cases = generate_test_cases(spec, use_ep=True, use_bva=True, use_pairwise=True)
        total_cases += len(cases)
        cases = apply_oracle(spec, cases, ground_truth)
        results = run_test_cases(spec, cases, ground_truth)
        print(f"\n{spec.name}: {len(cases)} test case")
        print("Tom tat chay test:", pass_fail_summary(results))
        for case in cases[:5]:
            print(case.test_id, case.inputs, "|", case.reasoning)

        (OUT / f"{spec.name}_cases.csv").write_bytes(export_csv(cases, results))
        (OUT / f"{spec.name}_cases.xlsx").write_bytes(export_excel(cases, results))
        (OUT / f"{spec.name}_tests.py").write_text(
            generate_pytest_code(spec, cases, ground_truth), encoding="utf-8"
        )

    print(f"\nDa xu ly {len(specs)} ham, tong {total_cases} test case.")
    print(f"Da ghi ket qua vao: {OUT}")
