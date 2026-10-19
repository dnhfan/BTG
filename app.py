"""BTG — Black-box Test Generator (CustomTkinter desktop UI).

Chay:  python app.py

Giao dien desktop bang CustomTkinter, tach rieng khoi logic (NFR-03):
UI chi doc form -> FunctionSpec, roi goi btg.generators / btg.executor /
btg.exporter. Giao dien khong dung icon emoji; chi dung text thuan.
Neu can icon sau nay, dung file SVG/PNG nap qua CTkImage.
"""
from __future__ import annotations

import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

from btg.exporter import export_csv, export_excel, generate_pytest_code
from btg.executor import apply_oracle, pass_fail_summary, run_test_cases
from btg.generators import generate_test_cases
from btg.models import FunctionSpec, ParamSpec, ParamType
from btg.parser import parse_python_code
from btg.validation import validate_spec

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

TYPE_OPTIONS = [t.value for t in ParamType]


# ----------------------------------------------------------------- Tooltip
class ToolTip:
    """Tooltip hien khi di chuot qua widget (NFR-02)."""

    def __init__(self, widget: tk.Widget, text: str, delay_ms: int = 500):
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self._after_id: str | None = None
        self._tip: tk.Toplevel | None = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, _event=None) -> None:
        self._after_id = self.widget.after(self.delay_ms, self._show)

    def _show(self) -> None:
        if self._tip is not None:
            return
        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self._tip = tk.Toplevel(self.widget)
        self._tip.wm_overrideredirect(True)
        self._tip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self._tip,
            text=self.text,
            justify="left",
            bg="#2b2b2b",
            fg="white",
            padx=8,
            pady=4,
            font=("TkDefaultFont", 9),
            wraplength=320,
        )
        label.pack()

    def _hide(self, _event=None) -> None:
        if self._after_id is not None:
            self.widget.after_cancel(self._after_id)
            self._after_id = None
        if self._tip is not None:
            self._tip.destroy()
            self._tip = None


def add_tip(widget: tk.Widget, text: str) -> tk.Widget:
    ToolTip(widget, text)
    return widget


# --------------------------------------------------------------- Param card
class ParamCard(ctk.CTkFrame):
    """Mot the tham so trong form dong (FR-1.1, FR-1.2)."""

    def __init__(self, master, on_delete, data: dict | None = None):
        super().__init__(master, border_width=1)
        self.on_delete = on_delete
        data = data or {}
        self.title_var = tk.StringVar(value="Tham số")
        self.name_var = tk.StringVar(value=data.get("name", "param"))
        self.type_var = tk.StringVar(value=data.get("type", "int"))
        # int / float
        self.min_var = tk.StringVar(value=str(data.get("min_value", 0)))
        self.max_var = tk.StringVar(value=str(data.get("max_value", 100)))
        # string
        self.minlen_var = tk.StringVar(value=str(data.get("min_length", 1)))
        self.maxlen_var = tk.StringVar(value=str(data.get("max_length", 10)))
        self.regex_var = tk.StringVar(value=data.get("regex", "") or "")
        self.allow_empty_var = tk.BooleanVar(value=bool(data.get("allow_empty", False)))
        # enum
        self.enum_var = tk.StringVar(
            value=data.get("enum_text", "admin, user, guest")
        )
        self.allow_null_var = tk.BooleanVar(value=bool(data.get("allow_null", False)))

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(8, 2))
        ctk.CTkLabel(header, textvariable=self.title_var,
                     font=ctk.CTkFont(weight="bold")).pack(side="left")
        add_tip(
            ctk.CTkButton(header, text="Xoá", width=56,
                          command=lambda: self.on_delete(self)),
            "Xoá tham số này khỏi hàm",
        ).pack(side="right")

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=4)
        ctk.CTkLabel(row, text="Tên tham số", width=90, anchor="w").pack(side="left")
        name_entry = ctk.CTkEntry(row, textvariable=self.name_var, width=160)
        name_entry.pack(side="left", padx=(0, 12))
        add_tip(name_entry, "Tên biến của tham số, phải hợp lệ trong Python "
                            "và không trùng với tham số khác (FR-1.4).")
        self.name_var.trace_add("write", lambda *_: self._refresh_title())
        ctk.CTkLabel(row, text="Kiểu", width=40, anchor="w").pack(side="left")
        type_menu = ctk.CTkOptionMenu(
            row, values=TYPE_OPTIONS, variable=self.type_var, width=110,
            command=lambda _v: self._rebuild_config(),
        )
        type_menu.pack(side="left")
        add_tip(type_menu, "Kiểu dữ liệu của tham số: int, float, string, "
                           "enum (tập giá trị cố định) hoặc bool.")

        self.config_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.config_frame.pack(fill="x", padx=10, pady=(2, 10))
        self._rebuild_config()
        self._refresh_title()

    def _refresh_title(self) -> None:
        self.title_var.set(f"Tham số: {self.name_var.get()} ({self.type_var.get()})")

    def _rebuild_config(self) -> None:
        for child in self.config_frame.winfo_children():
            child.destroy()
        ptype = self.type_var.get()
        f = self.config_frame
        if ptype in ("int", "float"):
            ctk.CTkLabel(f, text="Min", width=90, anchor="w").grid(row=0, column=0, sticky="w")
            min_entry = ctk.CTkEntry(f, textvariable=self.min_var, width=110)
            min_entry.grid(row=0, column=1, padx=(0, 12))
            add_tip(min_entry, "Giá trị nhỏ nhất hợp lệ. BVA sẽ sinh các điểm "
                               "min-1, min, min+1 (FR-2.2).")
            ctk.CTkLabel(f, text="Max", width=40, anchor="w").grid(row=0, column=2, sticky="w")
            max_entry = ctk.CTkEntry(f, textvariable=self.max_var, width=110)
            max_entry.grid(row=0, column=3, padx=(0, 12))
            add_tip(max_entry, "Giá trị lớn nhất hợp lệ, phải >= Min. "
                               "BVA sẽ sinh max-1, max, max+1 (FR-2.2).")
            null_box = ctk.CTkCheckBox(f, text="Allow null (None)",
                                       variable=self.allow_null_var)
            null_box.grid(row=0, column=4)
            add_tip(null_box, "Cho phép giá trị None là hợp lệ; nếu tắt, "
                              "BTG sẽ sinh case None thuộc vùng không hợp lệ.")
        elif ptype == "string":
            ctk.CTkLabel(f, text="Min length", width=90, anchor="w").grid(row=0, column=0, sticky="w")
            minlen_entry = ctk.CTkEntry(f, textvariable=self.minlen_var, width=70)
            minlen_entry.grid(row=0, column=1, padx=(0, 12))
            add_tip(minlen_entry, "Độ dài chuỗi tối thiểu hợp lệ.")
            ctk.CTkLabel(f, text="Max length", width=80, anchor="w").grid(row=0, column=2, sticky="w")
            maxlen_entry = ctk.CTkEntry(f, textvariable=self.maxlen_var, width=70)
            maxlen_entry.grid(row=0, column=3, padx=(0, 12))
            add_tip(maxlen_entry, "Độ dài chuỗi tối đa hợp lệ, phải >= Min length.")
            empty_box = ctk.CTkCheckBox(f, text="Allow empty",
                                        variable=self.allow_empty_var)
            empty_box.grid(row=0, column=4, padx=(0, 8))
            add_tip(empty_box, "Cho phép chuỗi rỗng '' là hợp lệ.")
            null_box = ctk.CTkCheckBox(f, text="Allow null",
                                       variable=self.allow_null_var)
            null_box.grid(row=0, column=5)
            add_tip(null_box, "Cho phép giá trị None là hợp lệ.")
            ctk.CTkLabel(f, text="Regex", width=90, anchor="w").grid(row=1, column=0, sticky="w", pady=(6, 0))
            regex_entry = ctk.CTkEntry(f, textvariable=self.regex_var, width=330)
            regex_entry.grid(row=1, column=1, columnspan=5, sticky="w", pady=(6, 0))
            add_tip(regex_entry, "Tuỳ chọn: mẫu regex mà chuỗi hợp lệ phải khớp, "
                                 "VD ^\\d{3}$ cho chuỗi 3 chữ số. Regex sai sẽ báo lỗi (FR-1.4).")
        elif ptype == "enum":
            ctk.CTkLabel(f, text="Giá trị hợp lệ", width=90, anchor="w").grid(row=0, column=0, sticky="w")
            enum_entry = ctk.CTkEntry(f, textvariable=self.enum_var, width=330)
            enum_entry.grid(row=0, column=1, padx=(0, 12))
            add_tip(enum_entry, "Danh sách giá trị hợp lệ, cách nhau bởi dấu phẩy. "
                                "Giá trị ngoài danh sách sẽ thuộc vùng không hợp lệ.")
            null_box = ctk.CTkCheckBox(f, text="Allow null",
                                       variable=self.allow_null_var)
            null_box.grid(row=0, column=2)
            add_tip(null_box, "Cho phép giá trị None là hợp lệ.")
        else:  # bool
            ctk.CTkLabel(f, text="Bool tự hiểu 2 giá trị True / False.",
                         text_color="gray").grid(row=0, column=0, sticky="w")
        self._refresh_title()

    # ------------------------------------------------------------- collect
    def _number(self, var: tk.StringVar, label: str) -> float:
        raw = var.get().strip()
        try:
            return float(raw)
        except ValueError:
            raise ValueError(
                f"Tham số '{self.name_var.get()}': {label} phải là số, "
                f"đang nhập '{raw}'."
            ) from None

    def _integer(self, var: tk.StringVar, label: str) -> int:
        return int(self._number(var, label))

    def collect(self) -> ParamSpec:
        name = self.name_var.get().strip()
        ptype = ParamType(self.type_var.get())
        if ptype in (ParamType.INT, ParamType.FLOAT):
            return ParamSpec(name, ptype,
                             min_value=self._number(self.min_var, "Min"),
                             max_value=self._number(self.max_var, "Max"),
                             allow_null=self.allow_null_var.get())
        if ptype == ParamType.STRING:
            return ParamSpec(name, ptype,
                             min_length=self._integer(self.minlen_var, "Min length"),
                             max_length=self._integer(self.maxlen_var, "Max length"),
                             regex=self.regex_var.get().strip() or None,
                             allow_empty=self.allow_empty_var.get(),
                             allow_null=self.allow_null_var.get())
        if ptype == ParamType.ENUM:
            values = [v.strip() for v in self.enum_var.get().split(",") if v.strip()]
            return ParamSpec(name, ptype, enum_values=values,
                             allow_null=self.allow_null_var.get())
        return ParamSpec(name, ptype)


# ------------------------------------------------------------------- App
class BTGApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("BTG — Black-box Test Generator")
        self.geometry("1340x820")
        self.minsize(1100, 680)

        self.param_cards: list[ParamCard] = []
        self.spec: FunctionSpec | None = None
        self.cases: list = []
        self.imported_specs: list[FunctionSpec] = []

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_main()
        self._build_statusbar()
        self.add_param({
            "name": "param1", "type": "int",
            "min_value": 0, "max_value": 100,
            "min_length": 1, "max_length": 10,
            "enum_text": "admin, user, guest",
        })

    # ------------------------------------------------------------- layout
    def _build_sidebar(self) -> None:
        sb = ctk.CTkFrame(self, width=330)
        sb.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        sb.grid_propagate(False)

        ctk.CTkLabel(sb, text="BTG — Black-box Test Generator",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     wraplength=300, justify="left").pack(anchor="w", padx=14, pady=(14, 2))
        ctk.CTkLabel(sb, text="Sinh test case bằng EP, BVA, Pairwise cho hàm Python",
                     text_color="gray", wraplength=300,
                     justify="left").pack(anchor="w", padx=14, pady=(0, 10))

        ctk.CTkLabel(sb, text="1. Nhập từ file Python (.py)",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=14, pady=(6, 4))
        add_tip(
            ctk.CTkButton(sb, text="Chọn file .py...", command=self._load_py_file),
            "Tự trích xuất tên hàm, tham số và type hint bằng AST (FR-1.3). "
            "Literal[...] sẽ được hiểu là enum.",
        ).pack(fill="x", padx=14)
        self.imported_name_var = tk.StringVar(value="")
        self.imported_menu = ctk.CTkOptionMenu(sb, values=["(chưa có hàm)"],
                                               variable=self.imported_name_var)
        self.imported_menu.pack(fill="x", padx=14, pady=(8, 0))
        add_tip(
            ctk.CTkButton(sb, text="Điền hàm đã chọn vào Form",
                          command=self._apply_imported),
            "Nạp hàm đang chọn ở trên vào form cấu hình bên phải.",
        ).pack(fill="x", padx=14, pady=(8, 0))

        ctk.CTkLabel(sb, text="2. Kỹ thuật sinh test",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=14, pady=(16, 4))
        self.use_ep_var = tk.BooleanVar(value=True)
        self.use_bva_var = tk.BooleanVar(value=True)
        self.use_pairwise_var = tk.BooleanVar(value=False)
        ep_box = ctk.CTkCheckBox(sb, text="Equivalence Partitioning (EP)",
                                 variable=self.use_ep_var)
        ep_box.pack(anchor="w", padx=14, pady=2)
        add_tip(ep_box, "Chia miền dữ liệu thành các vùng tương đương, "
                        "mỗi vùng lấy 1 giá trị đại diện (FR-2.1).")
        bva_box = ctk.CTkCheckBox(sb, text="Boundary Value Analysis (BVA)",
                                  variable=self.use_bva_var)
        bva_box.pack(anchor="w", padx=14, pady=2)
        add_tip(bva_box, "Sinh các điểm sát biên: min-1, min, min+1, "
                         "max-1, max, max+1 (FR-2.2).")
        pw_box = ctk.CTkCheckBox(sb, text="Pairwise",
                                 variable=self.use_pairwise_var)
        pw_box.pack(anchor="w", padx=14, pady=2)
        add_tip(pw_box, "Bao phủ mọi cặp giá trị giữa các tham số — "
                        "khuyên dùng khi hàm có > 3 tham số (FR-2.3).")

        ctk.CTkLabel(sb, text="3. Ground Truth (Oracle)",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=14, pady=(16, 4))
        ctk.CTkLabel(sb, text="Hàm chuẩn để tự điền Expected Output và "
                              "chạy Run Tests (FR-3.2).",
                     text_color="gray", wraplength=300,
                     justify="left").pack(anchor="w", padx=14)
        add_tip(
            ctk.CTkButton(sb, text="Chọn file Ground Truth (.py)...",
                          command=self._load_gt_file),
            "Nạp code hàm chuẩn từ một file .py riêng (không nhất thiết "
            "là file đã import ở mục 1).",
        ).pack(fill="x", padx=14, pady=(6, 0))
        self.gt_text = ctk.CTkTextbox(sb, height=170)
        self.gt_text.pack(fill="x", padx=14, pady=(8, 6))
        add_tip(self.gt_text, "Code hàm chuẩn (cùng tên với hàm đang cấu hình). "
                              "Có thể dán trực tiếp vào đây hoặc nạp từ file.")

    def _build_main(self) -> None:
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        main.grid_rowconfigure(1, weight=1)
        main.grid_rowconfigure(3, weight=2)
        main.grid_columnconfigure(0, weight=1)

        # --- Form cấu hình hàm & tham số
        form_box = ctk.CTkFrame(main, fg_color="transparent")
        form_box.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(form_box, text="Tên hàm", width=70, anchor="w").pack(side="left")
        self.func_name_var = tk.StringVar(value="my_function")
        func_entry = ctk.CTkEntry(form_box, textvariable=self.func_name_var, width=240)
        func_entry.pack(side="left")
        add_tip(func_entry, "Tên hàm cần sinh test case — phải trùng tên hàm "
                            "trong Ground Truth nếu muốn Run Tests.")
        add_tip(
            ctk.CTkButton(form_box, text="Thêm tham số", width=120,
                          command=lambda: self.add_param()),
            "Thêm một tham số mới vào form (FR-1.1).",
        ).pack(side="left", padx=(12, 0))
        add_tip(
            ctk.CTkButton(form_box, text="Sinh Test Case", width=140,
                          fg_color="#1f7a3d", hover_color="#176132",
                          command=self._generate),
            "Sinh test case theo các kỹ thuật đã chọn ở sidebar. "
            "Tối đa vài giây với hàm dưới 5 tham số (NFR-01).",
        ).pack(side="right")

        self.params_frame = ctk.CTkScrollableFrame(
            main, label_text="Cấu hình hàm & tham số (FR-1.1, FR-1.2)")
        self.params_frame.grid(row=1, column=0, sticky="nsew", pady=(8, 8))

        # --- Kết quả
        tabs = ctk.CTkTabview(main)
        tabs.grid(row=3, column=0, sticky="nsew")
        cases_tab = tabs.add("Test Cases")
        run_tab = tabs.add("Kết quả Run Tests")

        cols = ("id", "inputs", "expected", "exception", "technique", "reasoning")
        self.cases_tree = self._make_tree(
            cases_tab, cols,
            ["Testcase ID", "Inputs", "Expected Output",
             "Expected Exception", "Test Technique", "Reasoning"],
            [80, 300, 140, 130, 110, 300],
        )
        self.cases_tree.bind("<Double-1>", self._on_case_double_click)
        add_tip(self.cases_tree,
                "Nhấp đúp vào cột Expected Output hoặc Expected Exception "
                "để tự cấu hình kết quả mong đợi cho từng case (FR-3.1).")

        run_cols = ("id", "inputs", "expected", "actual", "status")
        self.run_tree = self._make_tree(
            run_tab, run_cols,
            ["ID", "Inputs", "Expected", "Actual", "Status"],
            [80, 320, 180, 180, 90],
        )
        self.run_tree.tag_configure("Pass", foreground="#1f7a3d")
        self.run_tree.tag_configure("Fail", foreground="#b3261e")

        actions = ctk.CTkFrame(main, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="ew", pady=(0, 2))
        add_tip(ctk.CTkButton(actions, text="Xuất CSV", width=110,
                              command=self._export_csv),
                "Xuất bảng test case ra file CSV (FR-4.1).").pack(side="left", padx=(0, 8))
        add_tip(ctk.CTkButton(actions, text="Xuất Excel", width=110,
                              command=self._export_excel),
                "Xuất bảng test case ra file Excel .xlsx (FR-4.1).").pack(side="left", padx=(0, 8))
        add_tip(ctk.CTkButton(actions, text="Xuất test_generated.py", width=180,
                              command=self._export_pytest),
                "Sinh file pytest dùng @pytest.mark.parametrize, "
                "chạy được ngay (FR-4.2).").pack(side="left", padx=(0, 8))
        add_tip(ctk.CTkButton(actions, text="Run Tests", width=120,
                              command=self._run_tests),
                "Chạy toàn bộ test case với Ground Truth và hiển thị "
                "tỉ lệ Pass/Fail (FR-4.3).").pack(side="left")
        self.summary_var = tk.StringVar(value="")
        ctk.CTkLabel(actions, textvariable=self.summary_var,
                     font=ctk.CTkFont(weight="bold")).pack(side="right")

    def _make_tree(self, parent, cols, headings, widths) -> ttk.Treeview:
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.pack(fill="both", expand=True)
        tree = ttk.Treeview(wrap, columns=cols, show="headings", height=12)
        for col, head, width in zip(cols, headings, widths):
            tree.heading(col, text=head)
            tree.column(col, width=width, minwidth=60)
        yscroll = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview)
        xscroll = ttk.Scrollbar(wrap, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        wrap.grid_rowconfigure(0, weight=1)
        wrap.grid_columnconfigure(0, weight=1)
        return tree

    def _build_statusbar(self) -> None:
        self.status_var = tk.StringVar(
            value="Sẵn sàng. Cấu hình tham số rồi bấm 'Sinh Test Case'.")
        bar = ctk.CTkLabel(self, textvariable=self.status_var, anchor="w",
                           text_color="gray")
        bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 8))

    def _set_status(self, text: str) -> None:
        self.status_var.set(text)

    # ------------------------------------------------------------ params
    def add_param(self, data: dict | None = None) -> None:
        card = ParamCard(self.params_frame, on_delete=self._delete_param,
                         data=data)
        card.pack(fill="x", padx=6, pady=5)
        self.param_cards.append(card)

    def _delete_param(self, card: ParamCard) -> None:
        if len(self.param_cards) <= 1:
            messagebox.showwarning("BTG", "Hàm phải có ít nhất 1 tham số.")
            return
        self.param_cards.remove(card)
        card.destroy()

    def _clear_params(self) -> None:
        for card in self.param_cards:
            card.destroy()
        self.param_cards.clear()

    # ------------------------------------------------------------ import
    def _load_py_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Chọn file Python", filetypes=[("Python files", "*.py")])
        if not path:
            return
        try:
            code = open(path, encoding="utf-8").read()
            specs = parse_python_code(code)
        except SyntaxError as exc:
            messagebox.showerror("BTG", f"File Python lỗi cú pháp:\n{exc}")
            return
        except OSError as exc:
            messagebox.showerror("BTG", f"Không đọc được file:\n{exc}")
            return
        if not specs:
            messagebox.showinfo("BTG", "Không tìm thấy hàm top-level nào trong file.")
            return
        self.imported_specs = specs
        self.imported_menu.configure(values=[s.name for s in specs])
        self.imported_name_var.set(specs[0].name)
        self._set_status(f"Đã đọc {len(specs)} hàm từ file. "
                         "Chọn hàm rồi bấm 'Điền hàm đã chọn vào Form'.")
        self._apply_imported(keep_gt=True, gt_code=code)

    def _apply_imported(self, keep_gt: bool = False, gt_code: str = "") -> None:
        name = self.imported_name_var.get()
        spec = next((s for s in self.imported_specs if s.name == name), None)
        if spec is None:
            messagebox.showinfo("BTG", "Hãy chọn file .py và một hàm trước.")
            return
        self.func_name_var.set(spec.name)
        self._clear_params()
        for p in spec.params:
            self.add_param({
                "name": p.name,
                "type": p.type.value,
                "min_value": p.min_value if p.min_value is not None else 0,
                "max_value": p.max_value if p.max_value is not None else 100,
                "min_length": p.min_length if p.min_length is not None else 1,
                "max_length": p.max_length if p.max_length is not None else 10,
                "regex": p.regex or "",
                "allow_empty": p.allow_empty,
                "allow_null": p.allow_null,
                "enum_text": ", ".join(map(str, p.enum_values)) or "admin, user, guest",
            })
        if keep_gt and gt_code:
            self._set_gt_code(gt_code)
        self._set_status(f"Đã điền hàm '{spec.name}' vào form.")

    def _load_gt_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Chọn file Ground Truth",
            filetypes=[("Python files", "*.py")])
        if not path:
            return
        try:
            code = open(path, encoding="utf-8").read()
        except OSError as exc:
            messagebox.showerror("BTG", f"Không đọc được file:\n{exc}")
            return
        self._set_gt_code(code)
        self._set_status("Đã nạp Ground Truth từ file.")

    def _set_gt_code(self, code: str) -> None:
        self.gt_text.delete("1.0", "end")
        self.gt_text.insert("1.0", code)

    def _gt_code(self) -> str:
        return self.gt_text.get("1.0", "end").strip()

    # ---------------------------------------------------------- generate
    def _build_spec(self) -> FunctionSpec:
        params = [card.collect() for card in self.param_cards]
        return FunctionSpec(self.func_name_var.get().strip(), params)

    def _generate(self) -> None:
        try:
            spec = self._build_spec()
        except ValueError as exc:
            messagebox.showerror("BTG — Lỗi nhập liệu", str(exc))
            return
        errors = validate_spec(spec)
        if errors:
            messagebox.showerror("BTG — Spec không hợp lệ (FR-1.4)",
                                 "\n".join(f"- {e}" for e in errors))
            return
        if not (self.use_ep_var.get() or self.use_bva_var.get()
                or self.use_pairwise_var.get()):
            messagebox.showwarning("BTG", "Hãy chọn ít nhất 1 kỹ thuật sinh test.")
            return
        try:
            cases = generate_test_cases(
                spec,
                use_ep=self.use_ep_var.get(),
                use_bva=self.use_bva_var.get(),
                use_pairwise=self.use_pairwise_var.get(),
            )
        except ValueError as exc:
            messagebox.showerror("BTG", str(exc))
            return
        gt = self._gt_code()
        note = ""
        if gt:
            try:
                cases = apply_oracle(spec, cases, gt)
                note = " Đã dùng Ground Truth để điền Expected Output."
            except Exception as exc:  # noqa: BLE001
                note = f" (Không áp dụng được Ground Truth: {exc})"
        self.spec, self.cases = spec, cases
        self._fill_cases_tree()
        self.summary_var.set("")
        self._set_status(f"Đã sinh {len(cases)} test case cho hàm "
                         f"'{spec.name}'.{note}")

    def _fill_cases_tree(self) -> None:
        self.cases_tree.delete(*self.cases_tree.get_children())
        for idx, c in enumerate(self.cases):
            self.cases_tree.insert(
                "", "end", iid=str(idx),
                values=(
                    c.test_id,
                    json.dumps(c.inputs, ensure_ascii=False, default=str),
                    "" if c.expected_output is None else str(c.expected_output),
                    c.expected_exception or "",
                    c.technique,
                    c.reasoning,
                ),
            )

    # ------------------------------------------------- edit expected (3.1)
    def _on_case_double_click(self, event) -> None:
        if not self.cases:
            return
        row_id = self.cases_tree.identify_row(event.y)
        col_id = self.cases_tree.identify_column(event.x)
        if not row_id or col_id not in ("#3", "#4"):
            return
        case = self.cases[int(row_id)]
        if col_id == "#3":
            current = "" if case.expected_output is None else str(case.expected_output)
            dialog = ctk.CTkInputDialog(
                text=f"Expected Output cho {case.test_id}\n"
                     "(nhập dạng JSON nếu là số/chuỗi/list; để trống = xoá)",
                title="Cấu hình Expected Output (FR-3.1)")
            raw = dialog.get_input()
            if raw is None:
                return
            raw = raw.strip()
            if not raw:
                case.expected_output = None
            else:
                try:
                    case.expected_output = json.loads(raw)
                except json.JSONDecodeError:
                    case.expected_output = raw
                case.expected_exception = None
        else:
            current = case.expected_exception or ""
            dialog = ctk.CTkInputDialog(
                text=f"Expected Exception cho {case.test_id}\n"
                     "(VD: ValueError, TypeError; để trống = xoá)",
                title="Cấu hình Expected Exception (FR-3.1)")
            raw = dialog.get_input()
            if raw is None:
                return
            raw = raw.strip()
            case.expected_exception = raw or None
            if raw:
                case.expected_output = None
        self._fill_cases_tree()
        self._set_status(f"Đã cập nhật kết quả mong đợi cho {case.test_id}.")

    # ------------------------------------------------------------- export
    def _require_cases(self) -> bool:
        if not self.cases or self.spec is None:
            messagebox.showinfo("BTG", "Hãy bấm 'Sinh Test Case' trước.")
            return False
        return True

    def _export_csv(self) -> None:
        if not self._require_cases():
            return
        path = filedialog.asksaveasfilename(
            title="Xuất CSV", defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")], initialfile="test_cases.csv")
        if path:
            with open(path, "wb") as fh:
                fh.write(export_csv(self.cases))
            self._set_status(f"Đã xuất CSV: {path}")

    def _export_excel(self) -> None:
        if not self._require_cases():
            return
        path = filedialog.asksaveasfilename(
            title="Xuất Excel", defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")], initialfile="test_cases.xlsx")
        if path:
            with open(path, "wb") as fh:
                fh.write(export_excel(self.cases))
            self._set_status(f"Đã xuất Excel: {path}")

    def _export_pytest(self) -> None:
        if not self._require_cases():
            return
        path = filedialog.asksaveasfilename(
            title="Xuất file pytest", defaultextension=".py",
            filetypes=[("Python files", "*.py")],
            initialfile="test_generated.py")
        if path:
            code = generate_pytest_code(self.spec, self.cases,
                                        self._gt_code() or None)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(code)
            self._set_status(f"Đã xuất file pytest: {path}")

    # ---------------------------------------------------------- run tests
    def _run_tests(self) -> None:
        if not self._require_cases():
            return
        gt = self._gt_code()
        if not gt:
            messagebox.showwarning(
                "BTG", "Cần có Ground Truth ở sidebar trước khi chạy test.")
            return
        try:
            results = run_test_cases(self.spec, self.cases, gt)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("BTG", f"Lỗi khi chạy test:\n{exc}")
            return
        summary = pass_fail_summary(results)
        self.summary_var.set(
            f"Pass: {summary['passed']}  |  Fail: {summary['failed']}  |  "
            f"Skipped: {summary['skipped']}  |  Pass rate: {summary['pass_rate']}%")
        self.run_tree.delete(*self.run_tree.get_children())
        for r in results:
            c = r.test_case
            expected = c.expected_exception or (
                "" if c.expected_output is None else str(c.expected_output))
            actual = r.actual_exception or (
                "" if r.actual_output is None else str(r.actual_output))
            self.run_tree.insert(
                "", "end",
                values=(c.test_id,
                        json.dumps(c.inputs, ensure_ascii=False, default=str),
                        expected, actual, r.status),
                tags=(r.status,),
            )
        self._set_status("Đã chạy xong. Xem chi tiết ở tab 'Kết quả Run Tests'.")


def main() -> None:
    app = BTGApp()
    app.mainloop()


if __name__ == "__main__":
    main()
