"""BTG — Black-box Test Generator (CustomTkinter desktop app).

Chay:  python app.py

Phong cach giao dien desktop: thanh header, sidebar chia muc, nut bam
icon + chu ngan, bang du lieu khop theme. Icon la Feather Icons (MIT)
dang SVG o assets/icons/svg/, render san sang PNG bang
tools/build_icons.py vi Tkinter khong hien thi SVG truc tiep.

Lop UI tach rieng khoi logic (NFR-03): UI chi doc form -> FunctionSpec,
roi goi btg.generators / btg.executor / btg.exporter.
"""
from __future__ import annotations

import json
import pathlib
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk
from PIL import Image

from btg.exporter import export_csv, export_excel, generate_pytest_code
from btg.executor import apply_oracle, pass_fail_summary, run_test_cases
from btg.generators import generate_test_cases
from btg.models import FunctionSpec, ParamSpec, ParamType
from btg.parser import parse_python_code
from btg.validation import validate_spec

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

TYPE_OPTIONS = [t.value for t in ParamType]
ASSETS_DIR = pathlib.Path(__file__).resolve().parent / "assets"
ICON_DIR = ASSETS_DIR / "icons"

GREEN = "#1F7A3D"
GREEN_HOVER = "#176132"

_icon_cache: dict = {}


def icon(name: str, size: int = 20) -> ctk.CTkImage:
    """Nap icon PNG (2 ban mau cho Light/Dark) thanh CTkImage."""
    key = (name, size)
    if key not in _icon_cache:
        _icon_cache[key] = ctk.CTkImage(
            light_image=Image.open(ICON_DIR / f"{name}_light.png"),
            dark_image=Image.open(ICON_DIR / f"{name}_dark.png"),
            size=(size, size),
        )
    return _icon_cache[key]


def app_logo(size: int = 34) -> ctk.CTkImage:
    """Logo BTG (assets/logo.png) dung o header va icon cua so."""
    return ctk.CTkImage(Image.open(ASSETS_DIR / "logo.png"), size=(size, size))


def section_label(master, text: str) -> ctk.CTkLabel:
    """Nhan tieu de muc kieu sidebar desktop (chu hoa nho, xam)."""
    return ctk.CTkLabel(
        master, text=text.upper(),
        font=ctk.CTkFont(size=11, weight="bold"),
        text_color=("gray45", "gray65"), anchor="w",
    )


def icon_button(master, icon_name: str, text: str, command,
                tip: str | None = None, **kwargs) -> ctk.CTkButton:
    btn = ctk.CTkButton(master, image=icon(icon_name), text=text,
                        compound="left", anchor="w", command=command, **kwargs)
    if tip:
        ToolTip(btn, tip)
    return btn


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
        tk.Label(
            self._tip, text=self.text, justify="left",
            bg="#2b2b2b", fg="white", padx=8, pady=4,
            font=("TkDefaultFont", 9), wraplength=320,
        ).pack()

    def _hide(self, _event=None) -> None:
        if self._after_id is not None:
            self.widget.after_cancel(self._after_id)
            self._after_id = None
        if self._tip is not None:
            self._tip.destroy()
            self._tip = None


# --------------------------------------------------------------- Param card
class ParamCard(ctk.CTkFrame):
    """Mot the tham so trong form dong (FR-1.1, FR-1.2)."""

    def __init__(self, master, on_delete, data: dict | None = None):
        super().__init__(master, border_width=1, corner_radius=8)
        self.on_delete = on_delete
        data = data or {}
        self.title_var = tk.StringVar(value="Tham số")
        self.name_var = tk.StringVar(value=data.get("name", "param"))
        self.type_var = tk.StringVar(value=data.get("type", "int"))
        self.min_var = tk.StringVar(value=str(data.get("min_value", 0)))
        self.max_var = tk.StringVar(value=str(data.get("max_value", 100)))
        self.minlen_var = tk.StringVar(value=str(data.get("min_length", 1)))
        self.maxlen_var = tk.StringVar(value=str(data.get("max_length", 10)))
        self.regex_var = tk.StringVar(value=data.get("regex", "") or "")
        self.allow_empty_var = tk.BooleanVar(value=bool(data.get("allow_empty", False)))
        self.enum_var = tk.StringVar(value=data.get("enum_text", "admin, user, guest"))
        self.allow_null_var = tk.BooleanVar(value=bool(data.get("allow_null", False)))

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(8, 0))
        ctk.CTkLabel(header, textvariable=self.title_var,
                     font=ctk.CTkFont(weight="bold")).pack(side="left")
        del_btn = ctk.CTkButton(
            header, image=icon("trash-2", 16), text="", width=32, height=28,
            fg_color="transparent", hover_color=("#E8C4C4", "#5A2A2A"),
            command=lambda: self.on_delete(self),
        )
        del_btn.pack(side="right")
        ToolTip(del_btn, "Xoá tham số này khỏi hàm")

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=4)
        ctk.CTkLabel(row, text="Tên", width=34, anchor="w").pack(side="left")
        name_entry = ctk.CTkEntry(row, textvariable=self.name_var, width=150)
        name_entry.pack(side="left", padx=(0, 12))
        ToolTip(name_entry, "Tên biến của tham số, phải hợp lệ trong Python "
                            "và không trùng với tham số khác (FR-1.4).")
        self.name_var.trace_add("write", lambda *_: self._refresh_title())
        ctk.CTkLabel(row, text="Kiểu", width=36, anchor="w").pack(side="left")
        type_menu = ctk.CTkOptionMenu(
            row, values=TYPE_OPTIONS, variable=self.type_var, width=104,
            command=lambda _v: self._rebuild_config(),
        )
        type_menu.pack(side="left")
        ToolTip(type_menu, "Kiểu dữ liệu: int, float, string, "
                           "enum (tập giá trị cố định) hoặc bool.")

        self.config_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.config_frame.pack(fill="x", padx=10, pady=(2, 10))
        self._rebuild_config()
        self._refresh_title()

    def _refresh_title(self) -> None:
        self.title_var.set(f"{self.name_var.get()} · {self.type_var.get()}")

    def _rebuild_config(self) -> None:
        for child in self.config_frame.winfo_children():
            child.destroy()
        ptype = self.type_var.get()
        f = self.config_frame
        if ptype in ("int", "float"):
            ctk.CTkLabel(f, text="Min", width=34, anchor="w").grid(row=0, column=0, sticky="w")
            min_entry = ctk.CTkEntry(f, textvariable=self.min_var, width=100)
            min_entry.grid(row=0, column=1, padx=(0, 12))
            ToolTip(min_entry, "Giá trị nhỏ nhất hợp lệ. BVA sinh các điểm "
                               "min-1, min, min+1 (FR-2.2).")
            ctk.CTkLabel(f, text="Max", width=36, anchor="w").grid(row=0, column=2, sticky="w")
            max_entry = ctk.CTkEntry(f, textvariable=self.max_var, width=100)
            max_entry.grid(row=0, column=3, padx=(0, 12))
            ToolTip(max_entry, "Giá trị lớn nhất hợp lệ, phải >= Min (FR-2.2).")
            null_box = ctk.CTkCheckBox(f, text="Allow null", variable=self.allow_null_var)
            null_box.grid(row=0, column=4)
            ToolTip(null_box, "Cho phép None là hợp lệ; nếu tắt, BTG sinh "
                              "case None thuộc vùng không hợp lệ.")
        elif ptype == "string":
            ctk.CTkLabel(f, text="Min length", width=70, anchor="w").grid(row=0, column=0, sticky="w")
            minlen_entry = ctk.CTkEntry(f, textvariable=self.minlen_var, width=64)
            minlen_entry.grid(row=0, column=1, padx=(0, 12))
            ToolTip(minlen_entry, "Độ dài chuỗi tối thiểu hợp lệ.")
            ctk.CTkLabel(f, text="Max length", width=74, anchor="w").grid(row=0, column=2, sticky="w")
            maxlen_entry = ctk.CTkEntry(f, textvariable=self.maxlen_var, width=64)
            maxlen_entry.grid(row=0, column=3, padx=(0, 12))
            ToolTip(maxlen_entry, "Độ dài chuỗi tối đa hợp lệ, phải >= Min length.")
            empty_box = ctk.CTkCheckBox(f, text="Allow empty", variable=self.allow_empty_var)
            empty_box.grid(row=0, column=4, padx=(0, 8))
            ToolTip(empty_box, "Cho phép chuỗi rỗng '' là hợp lệ.")
            null_box = ctk.CTkCheckBox(f, text="Allow null", variable=self.allow_null_var)
            null_box.grid(row=0, column=5)
            ToolTip(null_box, "Cho phép None là hợp lệ.")
            ctk.CTkLabel(f, text="Regex", width=70, anchor="w").grid(row=1, column=0, sticky="w", pady=(6, 0))
            regex_entry = ctk.CTkEntry(f, textvariable=self.regex_var, width=320)
            regex_entry.grid(row=1, column=1, columnspan=5, sticky="w", pady=(6, 0))
            ToolTip(regex_entry, "Tuỳ chọn: mẫu regex chuỗi hợp lệ phải khớp, "
                                 "VD ^\\d{3}$ cho chuỗi 3 chữ số (FR-1.4).")
        elif ptype == "enum":
            ctk.CTkLabel(f, text="Giá trị", width=70, anchor="w").grid(row=0, column=0, sticky="w")
            enum_entry = ctk.CTkEntry(f, textvariable=self.enum_var, width=300)
            enum_entry.grid(row=0, column=1, padx=(0, 12))
            ToolTip(enum_entry, "Danh sách giá trị hợp lệ, cách nhau bởi dấu phẩy. "
                                "Giá trị ngoài danh sách thuộc vùng không hợp lệ.")
            null_box = ctk.CTkCheckBox(f, text="Allow null", variable=self.allow_null_var)
            null_box.grid(row=0, column=2)
            ToolTip(null_box, "Cho phép None là hợp lệ.")
        else:  # bool
            ctk.CTkLabel(f, text="Bool gồm 2 giá trị True / False.",
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
                             min_length=int(self._number(self.minlen_var, "Min length")),
                             max_length=int(self._number(self.maxlen_var, "Max length")),
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
        self.geometry("1340x860")
        self.minsize(1080, 660)
        self.dark_mode = True
        self._set_window_icon()

        self.param_cards: list[ParamCard] = []
        self.spec: FunctionSpec | None = None
        self.cases: list = []
        self.results: list | None = None  # ket qua Run Tests gan nhat
        self.imported_specs: list[FunctionSpec] = []

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build_header()
        self._build_body()
        self._build_statusbar()
        self._style_trees()
        self.add_param({
            "name": "param1", "type": "int",
            "min_value": 0, "max_value": 100,
            "min_length": 1, "max_length": 10,
            "enum_text": "admin, user, guest",
        })

    def _set_window_icon(self) -> None:
        """Dat logo lam icon cua so (taskbar / title bar)."""
        try:
            if sys.platform.startswith("win"):
                ico = ASSETS_DIR / "app_icon.ico"
                if ico.exists():
                    self.iconbitmap(default=str(ico))
            png = ASSETS_DIR / "app_icon.png"
            if png.exists():
                self._window_icon = tk.PhotoImage(file=str(png))
                self.iconphoto(True, self._window_icon)
        except tk.TclError:
            pass

    # ------------------------------------------------------------- header
    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, height=56, corner_radius=0,
                              fg_color=("#E7E7E7", "#1B1B1B"))
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        try:
            logo = ctk.CTkLabel(header, image=app_logo(40), text="")
        except OSError:
            logo = ctk.CTkLabel(header, image=icon("zap", 24), text="")
        logo.pack(side="left", padx=(14, 8))

        gen_btn = ctk.CTkButton(
            header, image=icon("zap"), text="Sinh Test Case", compound="left",
            width=160, height=36, fg_color=GREEN, hover_color=GREEN_HOVER,
            font=ctk.CTkFont(weight="bold"), command=self._generate)
        gen_btn.pack(side="right", padx=(8, 14))
        ToolTip(gen_btn, "Sinh test case theo các kỹ thuật đã chọn. "
                         "Hàm dưới 5 tham số sinh trong < 2 giây (NFR-01).")
        self.theme_btn = ctk.CTkButton(
            header, image=icon("sun"), text="", width=40, height=36,
            fg_color="transparent", hover_color=("gray82", "gray25"),
            command=self._toggle_theme)
        self.theme_btn.pack(side="right")
        ToolTip(self.theme_btn, "Chuyển giao diện Sáng / Tối")

    def _toggle_theme(self) -> None:
        self.dark_mode = not self.dark_mode
        ctk.set_appearance_mode("dark" if self.dark_mode else "light")
        self.theme_btn.configure(image=icon("sun" if self.dark_mode else "moon"))
        self._style_trees()

    # --------------------------------------------------------------- body
    def _build_body(self) -> None:
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)
        self._build_sidebar(body)
        self._build_main(body)

    def _build_sidebar(self, body) -> None:
        sb = ctk.CTkScrollableFrame(body, width=272, corner_radius=0,
                                    fg_color=("#F0F0F0", "#212121"),
                                    scrollbar_button_color=("gray70", "gray35"))
        sb.grid(row=0, column=0, sticky="nsew")

        section_label(sb, "File Python").pack(anchor="w", padx=14, pady=(14, 6))
        icon_button(sb, "folder", "Mở file .py", self._load_py_file,
                    tip="Tự trích xuất tên hàm, tham số và type hint bằng AST "
                        "(FR-1.3). Literal[...] được hiểu là enum.",
                    height=34).pack(fill="x", padx=14)
        self.imported_name_var = tk.StringVar(value="")
        self.imported_menu = ctk.CTkOptionMenu(sb, values=["(chưa có hàm)"],
                                               variable=self.imported_name_var,
                                               height=34)
        self.imported_menu.pack(fill="x", padx=14, pady=(8, 0))
        icon_button(sb, "download", "Điền vào form", self._apply_imported,
                    tip="Nạp hàm đang chọn vào form cấu hình bên phải.",
                    height=34).pack(fill="x", padx=14, pady=(8, 0))

        section_label(sb, "Kỹ thuật sinh test").pack(anchor="w", padx=14, pady=(20, 6))
        self.use_ep_var = tk.BooleanVar(value=True)
        self.use_bva_var = tk.BooleanVar(value=True)
        self.use_pairwise_var = tk.BooleanVar(value=False)
        ep_box = ctk.CTkCheckBox(sb, text="Equivalence Partitioning (EP)",
                                 variable=self.use_ep_var)
        ep_box.pack(anchor="w", padx=14, pady=3)
        ToolTip(ep_box, "Chia miền dữ liệu thành các vùng tương đương, "
                        "mỗi vùng lấy 1 giá trị đại diện (FR-2.1).")
        bva_box = ctk.CTkCheckBox(sb, text="Boundary Value Analysis (BVA)",
                                  variable=self.use_bva_var)
        bva_box.pack(anchor="w", padx=14, pady=3)
        ToolTip(bva_box, "Sinh các điểm sát biên: min-1, min, min+1, "
                         "max-1, max, max+1 (FR-2.2).")
        pw_box = ctk.CTkCheckBox(sb, text="Pairwise", variable=self.use_pairwise_var)
        pw_box.pack(anchor="w", padx=14, pady=3)
        ToolTip(pw_box, "Bao phủ mọi cặp giá trị giữa các tham số — "
                        "khuyên dùng khi hàm có > 3 tham số (FR-2.3).")

        section_label(sb, "Hàm tham chiếu").pack(anchor="w", padx=14, pady=(20, 6))
        icon_button(sb, "database", "Mở file hàm tham chiếu", self._load_gt_file,
                    tip="Nạp code hàm tham chiếu từ một file .py riêng. Hàm này "
                        "dùng để tự điền Expected Output và chạy Run Tests (FR-3.2).",
                    height=34).pack(fill="x", padx=14)
        self.gt_text = ctk.CTkTextbox(sb, height=150)
        self.gt_text.pack(fill="x", padx=14, pady=(8, 14))
        ToolTip(self.gt_text, "Code hàm tham chiếu, cùng tên với hàm đang cấu hình. "
                              "Dán trực tiếp vào đây hoặc nạp từ file.")

    def _build_main(self, body) -> None:
        main = ctk.CTkFrame(body, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew", padx=(12, 12), pady=(10, 6))
        main.grid_rowconfigure(2, weight=1)
        main.grid_rowconfigure(4, weight=1)
        main.grid_columnconfigure(0, weight=1)

        toolbar = ctk.CTkFrame(main, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(toolbar, text="Hàm", width=36, anchor="w").pack(side="left")
        self.func_name_var = tk.StringVar(value="my_function")
        func_entry = ctk.CTkEntry(toolbar, textvariable=self.func_name_var, width=230)
        func_entry.pack(side="left")
        ToolTip(func_entry, "Tên hàm cần sinh test case — phải trùng tên hàm "
                            "trong hàm tham chiếu nếu muốn Run Tests.")
        icon_button(toolbar, "plus", "Thêm tham số", lambda: self.add_param(),
                    tip="Thêm một tham số mới vào hàm (FR-1.1).",
                    width=140, height=32).pack(side="left", padx=(12, 0))

        section_label(main, "Tham số").grid(row=1, column=0, sticky="w", pady=(10, 4))
        self.params_frame = ctk.CTkScrollableFrame(main, fg_color="transparent")
        self.params_frame.grid(row=2, column=0, sticky="nsew")

        actions = ctk.CTkFrame(main, fg_color="transparent")
        actions.grid(row=3, column=0, sticky="ew", pady=(10, 6))
        icon_button(actions, "file-text", "CSV", self._export_csv,
                    tip="Xuất bảng test case ra file CSV (FR-4.1). "
                        "Nếu đã Run Tests, file kèm thêm cột Actual + Status.",
                    width=96, height=32).pack(side="left", padx=(0, 8))
        icon_button(actions, "grid", "Excel", self._export_excel,
                    tip="Xuất bảng test case ra file Excel .xlsx (FR-4.1). "
                        "Nếu đã Run Tests, file kèm thêm cột Actual + Status.",
                    width=96, height=32).pack(side="left", padx=(0, 8))
        icon_button(actions, "code", "Pytest", self._export_pytest,
                    tip="Sinh file test_generated.py dùng @pytest.mark.parametrize (FR-4.2).",
                    width=104, height=32).pack(side="left", padx=(0, 8))
        icon_button(actions, "play", "Run Tests", self._run_tests,
                    tip="Chạy toàn bộ test case với hàm tham chiếu, "
                        "hiển thị tỉ lệ Pass/Fail (FR-4.3).",
                    width=118, height=32).pack(side="left")
        self.summary_var = tk.StringVar(value="")
        ctk.CTkLabel(actions, textvariable=self.summary_var,
                     font=ctk.CTkFont(weight="bold")).pack(side="right")

        tabs = ctk.CTkTabview(main)
        tabs.grid(row=4, column=0, sticky="nsew")
        cases_tab = tabs.add("Test Cases")
        run_tab = tabs.add("Kết quả Run Tests")
        self.cases_tree = self._make_tree(
            cases_tab,
            ("id", "inputs", "expected", "exception", "technique", "reasoning"),
            ["ID", "Inputs", "Expected Output", "Expected Exception",
             "Test Technique", "Reasoning"],
            [76, 270, 140, 150, 92, 280],
        )
        self.cases_tree.bind("<Double-1>", self._on_case_double_click)
        ToolTip(self.cases_tree, "Nhấp đúp vào cột Expected Output hoặc "
                                 "Expected Exception để tự cấu hình kết quả "
                                 "mong đợi cho từng case (FR-3.1).")
        self.run_tree = self._make_tree(
            run_tab,
            ("id", "inputs", "expected", "actual", "status"),
            ["ID", "Inputs", "Expected", "Actual", "Status"],
            [76, 320, 180, 180, 90],
        )

    def _make_tree(self, parent, cols, headings, widths) -> ttk.Treeview:
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.pack(fill="both", expand=True)
        tree = ttk.Treeview(wrap, columns=cols, show="headings", height=12)
        for col, head, width in zip(cols, headings, widths):
            tree.heading(col, text=head)
            tree.column(col, width=width, minwidth=56)
        yscroll = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview)
        xscroll = ttk.Scrollbar(wrap, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        wrap.grid_rowconfigure(0, weight=1)
        wrap.grid_columnconfigure(0, weight=1)
        return tree

    def _style_trees(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        if self.dark_mode:
            bg, fg, head_bg, sel = "#2B2B2B", "#FFFFFF", "#3A3A3A", "#1F6AA5"
            pass_fg, fail_fg = "#4ADE80", "#F87171"
        else:
            bg, fg, head_bg, sel = "#FFFFFF", "#242424", "#E5E5E5", "#1F6AA5"
            pass_fg, fail_fg = "#1F7A3D", "#B3261E"
        style.configure("Treeview", background=bg, foreground=fg,
                        fieldbackground=bg, rowheight=24, borderwidth=0)
        style.configure("Treeview.Heading", background=head_bg, foreground=fg,
                        relief="flat", font=("TkDefaultFont", 10, "bold"))
        style.map("Treeview", background=[("selected", sel)],
                  foreground=[("selected", "#FFFFFF")])
        for tree in (getattr(self, "cases_tree", None),
                     getattr(self, "run_tree", None)):
            if tree is not None:
                tree.tag_configure("Pass", foreground=pass_fg)
                tree.tag_configure("Fail", foreground=fail_fg)

    def _build_statusbar(self) -> None:
        self.status_var = tk.StringVar(
            value="Sẵn sàng — cấu hình tham số rồi bấm 'Sinh Test Case'.")
        bar = ctk.CTkFrame(self, height=26, corner_radius=0,
                           fg_color=("#E7E7E7", "#1B1B1B"))
        bar.grid(row=2, column=0, sticky="ew")
        bar.grid_propagate(False)
        ctk.CTkLabel(bar, textvariable=self.status_var, anchor="w",
                     font=ctk.CTkFont(size=11),
                     text_color="gray").pack(side="left", padx=12)

    def _set_status(self, text: str) -> None:
        self.status_var.set(text)

    # ------------------------------------------------------------ params
    def add_param(self, data: dict | None = None) -> None:
        card = ParamCard(self.params_frame, on_delete=self._delete_param,
                         data=data)
        card.pack(fill="x", padx=4, pady=5)
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

    def _scroll_params_top(self) -> None:
        try:
            self.params_frame._parent_canvas.yview_moveto(0)
        except (AttributeError, tk.TclError):
            pass

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
        self._scroll_params_top()
        self._set_status(f"Đã điền hàm '{spec.name}' vào form.")

    def _load_gt_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Chọn file hàm tham chiếu",
            filetypes=[("Python files", "*.py")])
        if not path:
            return
        try:
            code = open(path, encoding="utf-8").read()
        except OSError as exc:
            messagebox.showerror("BTG", f"Không đọc được file:\n{exc}")
            return
        self._set_gt_code(code)
        self._set_status("Đã nạp hàm tham chiếu từ file.")

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
                note = " Đã dùng hàm tham chiếu để điền Expected Output."
            except Exception as exc:  # noqa: BLE001
                note = f" (Không áp dụng được hàm tham chiếu: {exc})"
        self.spec, self.cases = spec, cases
        self.results = None  # case moi -> ket qua chay cu khong con hop le
        self.run_tree.delete(*self.run_tree.get_children())
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
        self.results = None  # expected doi -> phai Run Tests lai
        self.run_tree.delete(*self.run_tree.get_children())
        self.summary_var.set("")
        self._fill_cases_tree()
        self._set_status(f"Đã cập nhật kết quả mong đợi cho {case.test_id}.")

    # ------------------------------------------------------------- export
    def _require_cases(self) -> bool:
        if not self.cases or self.spec is None:
            messagebox.showinfo("BTG", "Hãy bấm 'Sinh Test Case' trước.")
            return False
        return True

    def _results_note(self) -> str:
        return " (kèm Actual + Status)" if self.results else ""

    def _export_csv(self) -> None:
        if not self._require_cases():
            return
        path = filedialog.asksaveasfilename(
            title="Xuất CSV", defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")], initialfile="test_cases.csv")
        if path:
            with open(path, "wb") as fh:
                fh.write(export_csv(self.cases, self.results))
            self._set_status(f"Đã xuất CSV{self._results_note()}: {path}")

    def _export_excel(self) -> None:
        if not self._require_cases():
            return
        path = filedialog.asksaveasfilename(
            title="Xuất Excel", defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")], initialfile="test_cases.xlsx")
        if path:
            with open(path, "wb") as fh:
                fh.write(export_excel(self.cases, self.results))
            self._set_status(f"Đã xuất Excel{self._results_note()}: {path}")

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
                "BTG", "Cần có hàm tham chiếu ở sidebar trước khi chạy test.")
            return
        try:
            results = run_test_cases(self.spec, self.cases, gt)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("BTG", f"Lỗi khi chạy test:\n{exc}")
            return
        self.results = results
        summary = pass_fail_summary(results)
        self.summary_var.set(
            f"Pass {summary['passed']} · Fail {summary['failed']} · "
            f"Skipped {summary['skipped']} · {summary['pass_rate']}%")
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
        self._set_status("Đã chạy xong — xem tab 'Kết quả Run Tests'.")


def main() -> None:
    app = BTGApp()
    app.mainloop()


if __name__ == "__main__":
    main()
