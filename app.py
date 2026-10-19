"""BTG — Black-box Test Generator (Streamlit UI).

Chay:  streamlit run app.py

Giao dien tach rieng khoi logic (NFR-03): UI chi doc form -> FunctionSpec,
roi goi btg.generators / btg.executor / btg.exporter.
"""
from __future__ import annotations

import json

import streamlit as st

from btg.exporter import export_csv, export_excel, generate_pytest_code
from btg.executor import apply_oracle, pass_fail_summary, run_test_cases
from btg.generators import generate_test_cases
from btg.models import FunctionSpec, ParamSpec, ParamType
from btg.parser import parse_python_code
from btg.validation import validate_spec

st.set_page_config(page_title="BTG - Black-box Test Generator", layout="wide")
st.title("🧪 BTG — Black-box Test Generator")
st.caption("Sinh test case tự động bằng EP • BVA • Pairwise cho hàm Python")

TYPE_OPTIONS = [t.value for t in ParamType]


def default_param(idx: int) -> dict:
    return {
        "name": f"param{idx + 1}",
        "type": "int",
        "min_value": 0.0,
        "max_value": 100.0,
        "min_length": 1,
        "max_length": 10,
        "regex": "",
        "allow_empty": False,
        "allow_null": False,
        "enum_text": "admin, user, guest",
    }


if "params" not in st.session_state:
    st.session_state.params = [default_param(0)]
if "function_name" not in st.session_state:
    st.session_state.function_name = "my_function"
if "ground_truth_code" not in st.session_state:
    st.session_state.ground_truth_code = ""

# ------------------------------------------------------------------ Sidebar
with st.sidebar:
    st.header("1. Nhập từ file Python (.py)")
    uploaded = st.file_uploader("Upload file .py để tự trích xuất hàm (FR-1.3)", type=["py"])
    if uploaded is not None:
        code = uploaded.read().decode("utf-8")
        try:
            specs = parse_python_code(code)
        except SyntaxError as exc:
            st.error(f"File Python lỗi cú pháp: {exc}")
            specs = []
        if specs:
            chosen = st.selectbox("Chọn hàm trong file", [s.name for s in specs])
            if st.button("⬇️ Điền hàm này vào Form"):
                spec = next(s for s in specs if s.name == chosen)
                st.session_state.function_name = spec.name
                new_params = []
                for p in spec.params:
                    d = default_param(0)
                    d.update(
                        name=p.name,
                        type=p.type.value,
                        min_value=float(p.min_value) if p.min_value is not None else 0.0,
                        max_value=float(p.max_value) if p.max_value is not None else 100.0,
                        min_length=int(p.min_length or 1),
                        max_length=int(p.max_length or 10),
                        enum_text=", ".join(map(str, p.enum_values)) or d["enum_text"],
                    )
                    new_params.append(d)
                st.session_state.params = new_params
                st.session_state.ground_truth_code = code
                st.rerun()
        else:
            st.info("Không tìm thấy hàm top-level nào trong file.")

    st.divider()
    st.header("2. Kỹ thuật sinh test")
    use_ep = st.checkbox("Equivalence Partitioning (EP)", value=True)
    use_bva = st.checkbox("Boundary Value Analysis (BVA)", value=True)
    use_pairwise = st.checkbox(
        "Pairwise (khuyên dùng khi > 3 tham số)", value=False
    )

    st.divider()
    st.header("3. Ground Truth (Oracle)")
    st.caption(
        "Dán code hàm chuẩn vào đây: BTG sẽ chạy hàm này để tự điền "
        "Expected Output và cho phép bấm Run Tests (FR-3.2, FR-4.3)."
    )
    st.session_state.ground_truth_code = st.text_area(
        "Code Ground Truth",
        value=st.session_state.ground_truth_code,
        height=180,
        placeholder="def my_function(param1):\n    ...",
    )

# ------------------------------------------------------------- Dynamic form
st.header("Cấu hình hàm & tham số (FR-1.1, FR-1.2)")
st.session_state.function_name = st.text_input(
    "Tên hàm", value=st.session_state.function_name
)

params_to_delete = None
for i, p in enumerate(st.session_state.params):
    with st.expander(f"Tham số {i + 1}: {p['name']} ({p['type']})", expanded=True):
        cols = st.columns([2, 2, 1])
        p["name"] = cols[0].text_input("Tên tham số", value=p["name"], key=f"name_{i}")
        p["type"] = cols[1].selectbox(
            "Kiểu dữ liệu", TYPE_OPTIONS, index=TYPE_OPTIONS.index(p["type"]), key=f"type_{i}"
        )
        if cols[2].button("🗑️ Xoá", key=f"del_{i}"):
            params_to_delete = i

        if p["type"] in ("int", "float"):
            c1, c2, c3 = st.columns(3)
            p["min_value"] = c1.number_input("Min", value=float(p["min_value"]), key=f"min_{i}")
            p["max_value"] = c2.number_input("Max", value=float(p["max_value"]), key=f"max_{i}")
            p["allow_null"] = c3.checkbox("Allow null", value=p["allow_null"], key=f"null_{i}")
        elif p["type"] == "string":
            c1, c2, c3, c4 = st.columns(4)
            p["min_length"] = c1.number_input("Min length", value=int(p["min_length"]), min_value=0, key=f"minlen_{i}")
            p["max_length"] = c2.number_input("Max length", value=int(p["max_length"]), min_value=0, key=f"maxlen_{i}")
            p["allow_empty"] = c3.checkbox("Allow empty", value=p["allow_empty"], key=f"empty_{i}")
            p["allow_null"] = c4.checkbox("Allow null", value=p["allow_null"], key=f"snull_{i}")
            p["regex"] = st.text_input("Regex (tuỳ chọn)", value=p["regex"], key=f"regex_{i}")
        elif p["type"] == "enum":
            p["enum_text"] = st.text_input(
                "Danh sách giá trị hợp lệ (cách nhau bởi dấu phẩy)",
                value=p["enum_text"], key=f"enum_{i}",
            )
            p["allow_null"] = st.checkbox("Allow null", value=p["allow_null"], key=f"enull_{i}")
        elif p["type"] == "bool":
            st.info("Bool tự hiểu 2 giá trị True / False.")

if params_to_delete is not None:
    del st.session_state.params[params_to_delete]
    st.rerun()
if st.button("➕ Thêm tham số"):
    st.session_state.params.append(default_param(len(st.session_state.params)))
    st.rerun()


def build_spec() -> FunctionSpec:
    params: list[ParamSpec] = []
    for p in st.session_state.params:
        ptype = ParamType(p["type"])
        if ptype in (ParamType.INT, ParamType.FLOAT):
            params.append(ParamSpec(p["name"], ptype, min_value=p["min_value"],
                                    max_value=p["max_value"], allow_null=p["allow_null"]))
        elif ptype == ParamType.STRING:
            params.append(ParamSpec(p["name"], ptype, min_length=int(p["min_length"]),
                                    max_length=int(p["max_length"]),
                                    regex=p["regex"] or None,
                                    allow_empty=p["allow_empty"],
                                    allow_null=p["allow_null"]))
        elif ptype == ParamType.ENUM:
            values = [v.strip() for v in p["enum_text"].split(",") if v.strip()]
            params.append(ParamSpec(p["name"], ptype, enum_values=values,
                                    allow_null=p["allow_null"]))
        else:
            params.append(ParamSpec(p["name"], ptype))
    return FunctionSpec(st.session_state.function_name.strip(), params)


# ---------------------------------------------------------------- Generate
st.divider()
if st.button("🚀 Sinh Test Case", type="primary"):
    spec = build_spec()
    errors = validate_spec(spec)
    if errors:
        for err in errors:
            st.error(err)
    else:
        try:
            cases = generate_test_cases(spec, use_ep=use_ep, use_bva=use_bva,
                                        use_pairwise=use_pairwise)
            gt = st.session_state.ground_truth_code.strip()
            if gt:
                try:
                    cases = apply_oracle(spec, cases, gt)
                    st.info("Đã dùng Ground Truth để điền Expected Output.")
                except Exception as exc:  # noqa: BLE001
                    st.warning(f"Không áp dụng được Ground Truth: {exc}")
            st.session_state.spec = spec
            st.session_state.cases = cases
        except ValueError as exc:
            st.error(str(exc))

if "cases" in st.session_state:
    spec: FunctionSpec = st.session_state.spec
    cases = st.session_state.cases
    st.success(f"Đã sinh {len(cases)} test case cho hàm `{spec.name}`")
    rows = [
        {
            "Testcase ID": c.test_id,
            "Inputs": json.dumps(c.inputs, ensure_ascii=False, default=str),
            "Expected Output": "" if c.expected_output is None else str(c.expected_output),
            "Expected Exception": c.expected_exception or "",
            "Test Technique": c.technique,
            "Reasoning": c.reasoning,
        }
        for c in cases
    ]
    st.dataframe(rows, use_container_width=True)

    gt = st.session_state.ground_truth_code.strip()
    c1, c2, c3, c4 = st.columns(4)
    c1.download_button("⬇️ Xuất CSV", export_csv(cases), "test_cases.csv", "text/csv")
    c2.download_button(
        "⬇️ Xuất Excel", export_excel(cases), "test_cases.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    pytest_code = generate_pytest_code(spec, cases, gt or None)
    c3.download_button("⬇️ test_generated.py", pytest_code, "test_generated.py", "text/x-python")

    if c4.button("▶️ Run Tests"):
        if not gt:
            st.warning("Cần dán Ground Truth ở sidebar trước khi chạy test.")
        else:
            try:
                results = run_test_cases(spec, cases, gt)
                summary = pass_fail_summary(results)
                m1, m2, m3 = st.columns(3)
                m1.metric("Pass", summary["passed"])
                m2.metric("Fail", summary["failed"])
                m3.metric("Pass rate", f"{summary['pass_rate']}%")
                st.dataframe(
                    [
                        {
                            "ID": r.test_case.test_id,
                            "Inputs": json.dumps(r.test_case.inputs, ensure_ascii=False, default=str),
                            "Expected": r.test_case.expected_exception or r.test_case.expected_output,
                            "Actual": r.actual_exception or r.actual_output,
                            "Status": r.status,
                        }
                        for r in results
                    ],
                    use_container_width=True,
                )
            except Exception as exc:  # noqa: BLE001
                st.error(f"Lỗi khi chạy test: {exc}")
