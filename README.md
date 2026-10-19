# BTG — Black-box Test Generator

Phần mềm **sinh Test Case tự động bằng phương pháp Hộp đen (Black-box)** cho các hàm Python,
theo tài liệu SRS của dự án.

Áp dụng 3 kỹ thuật:

- **Equivalence Partitioning (EP)** — Phân vùng tương đương
- **Boundary Value Analysis (BVA)** — Phân tích giá trị biên: `min-1, min, min+1, max-1, max, max+1`
- **Pairwise Testing** — Kiểm thử theo cặp, giảm số tổ hợp khi hàm có nhiều tham số

Kiểu dữ liệu hỗ trợ: `int`, `float`, `string` (length, regex), `enum`, `bool`

## Tính năng (theo SRS)

| Mã | Tính năng |
|---|---|
| FR-1.1 / 1.2 | Form động nhập tên hàm, thêm/bớt tham số, cấu hình min/max, length, regex, enum, allow_null... |
| FR-1.3 | Upload file `.py` — tự trích xuất tên hàm, tham số, type hint (kể cả `Literal[...]` → enum) bằng AST |
| FR-1.4 | Validation: báo lỗi khi `min > max`, regex sai, trùng tên tham số |
| FR-2.1 | EP: case hợp lệ + case không hợp lệ theo *Single Fault Assumption* |
| FR-2.2 | BVA cho số và độ dài chuỗi |
| FR-2.3 | Pairwise cho hàm nhiều tham số (> 3) |
| FR-2.4 | Gán nhãn lý do cho từng case (VD `[BVA] age_Min_Minus_1`) + khử trùng lặp |
| FR-3.1 / 3.2 | Oracle: nhấp đúp vào từng test case để tự cấu hình Expected Output / Exception, hoặc đính kèm hàm chuẩn (Ground Truth, dán code hoặc nạp từ file .py riêng) để tự điền kết quả đúng |
| FR-4.1 | Xuất bảng Test Case ra **Excel (.xlsx)** / **CSV** |
| FR-4.2 | Xuất file **`test_generated.py`** dùng `@pytest.mark.parametrize` — chạy được ngay |
| FR-4.3 | Nút **Run Tests** trên UI, hiển thị tỉ lệ Pass/Fail |

Hiệu năng (NFR-01): sinh 38 test case cho hàm 4 tham số trong ~0.003 giây (yêu cầu < 2 giây).

## Cài đặt & chạy giao diện

Giao diện là **ứng dụng desktop bằng CustomTkinter** (không dùng Streamlit,
không mở trình duyệt). Toàn bộ nhãn/biểu tượng trên UI là text thuần —
không dùng icon emoji; khi cần icon, nạp file SVG/PNG qua `CTkImage`.

```bash
git clone https://github.com/thienba33/BTG.git
cd BTG
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Trên giao diện: di chuột qua các ô nhập/nút bấm để xem tooltip hướng dẫn
(NFR-02); nhấp đúp vào cột *Expected Output* / *Expected Exception* trong
bảng kết quả để tự sửa kết quả mong đợi cho từng test case (FR-3.1).

## Chạy thử không cần giao diện (demo)

```bash
python examples/demo.py
```

Demo sinh test case cho hàm `register(username, age, role, active)` trong
`examples/sample_function.py` và ghi kết quả vào thư mục `output/`:
`test_cases.csv`, `test_cases.xlsx`, `test_generated.py`.

Chạy file test được sinh ra:

```bash
pytest output/test_generated.py -q
```

## Chạy unit test của BTG

```bash
pytest -q
```

## Cấu trúc project (NFR-03 — tách lớp rõ ràng)

```
BTG/
├── app.py                  # Lớp giao diện (CustomTkinter desktop UI)
├── btg/
│   ├── models.py           # ParamSpec / FunctionSpec / TestCase
│   ├── validation.py       # Kiểm tra spec (FR-1.4)
│   ├── parser.py           # AST parser: .py -> spec (FR-1.3)
│   ├── values.py           # Giá trị đại diện / không hợp lệ cho từng kiểu
│   ├── generators.py       # Core: EP / BVA / Pairwise + khử trùng (FE-02)
│   ├── executor.py         # Oracle + chạy test, tỉ lệ Pass/Fail (FE-03, FR-4.3)
│   └── exporter.py         # Xuất CSV / Excel / pytest (FE-04)
├── examples/
│   ├── sample_function.py  # Hàm mẫu: check_age, register
│   └── demo.py             # Demo chạy bằng dòng lệnh
├── tests/
│   └── test_btg.py         # 12 unit test cho core
└── requirements.txt
```

## Ví dụ nhanh bằng code

```python
from btg.generators import generate_test_cases
from btg.models import FunctionSpec, ParamSpec, ParamType

spec = FunctionSpec("check_age", [
    ParamSpec("age", ParamType.INT, min_value=0, max_value=150),
])
cases = generate_test_cases(spec, use_ep=True, use_bva=True)
for c in cases:
    print(c.test_id, c.inputs, c.reasoning)
# TC_001 {'age': 75} [EP] Valid_Partition
# TC_002 {'age': -1} [EP] Invalid_Partition_age_Below_Min
# ...
```
