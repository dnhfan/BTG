"""BTG — Black-box Test Generator (CustomTkinter desktop app).

Chay:  python app.py

Phong cach giao dien desktop theo GNOME Human Interface Guidelines &
Adwaita: headerbar GNOME, sidebar chia muc, nut bam icon + chu, bang
du lieu khop theme sang/toi. Icon la Feather Icons (MIT) dang SVG o
assets/icons/svg/, render san sang PNG bang tools/build_icons.py vi
Tkinter khong hien thi SVG truc tiep.

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

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

TYPE_OPTIONS = [t.value for t in ParamType]
ASSETS_DIR = pathlib.Path(__file__).resolve().parent / "assets"
ICON_DIR = ASSETS_DIR / "icons"

# ─── Adwaita / GNOME HIG colour palette ──────────────────────────────────────
# Accent: GNOME Blue (light/dark variants follow system).
# Naming mirrors libadwaita CSS variable semantics so intent is clear.
PRIMARY          = ("#1C71D8", "#3584E4")   # suggested-action / accent
PRIMARY_HOVER    = ("#1558A8", "#2A6FC0")
PRIMARY_TEXT     = "#FFFFFF"

# Secondary buttons: outlined/flat — transparent bg, subtle border.
SECONDARY        = "transparent"
SECONDARY_HOVER  = ("#E0E0E0", "#3A3A3A")
SECONDARY_TEXT   = ("#1C1C1C", "#FFFFFF")
SECONDARY_BORDER = ("#C0C0C0", "#525252")

# Surfaces
HEADERBAR_BG     = ("#E4E4E4", "#242424")   # headerbar_bg_color
SIDEBAR_BG       = ("#EFEFEF", "#2D2D2D")   # sidebar background
CARD_BG          = ("#FFFFFF", "#313131")   # cards / elevated surfaces
WINDOW_BG        = ("#FAFAFA", "#242424")

# Semantic
DESTRUCTIVE      = ("#C01C28", "#E01B24")   # trash / error
SUCCESS_FG       = ("#1A7F4A", "#2EC27E")   # Pass
FAIL_FG          = ("#C01C28", "#FF7B7B")   # Fail

# Text
TEXT_DIM         = ("gray40", "gray65")     # section labels, hints

# Scrollbar
SB_BG            = ("#B8B8B8", "#4D4D4D")
SB_TROUGH        = ("#E8E8E8", "#2A2A2A")

# Treeview alternating row (very subtle)
TREE_ODD_DARK    = "#2E2E2E"
TREE_ODD_LIGHT   = "#F4F4F4"

# Separator / sash
SASH_COLOR_DARK  = "#3A3A3A"
SASH_COLOR_LIGHT = "#D0D0D0"

# Apply the same surfaces to controls created dynamically in parameter cards
# and dialogs. Keep this local to the UI; the core has no theme dependency.
for widget, options in {
    "CTk": {"fg_color": WINDOW_BG},
    "CTkToplevel": {"fg_color": WINDOW_BG},
    "CTkFrame": {"fg_color": CARD_BG, "top_fg_color": CARD_BG,
                 "border_color": SECONDARY_BORDER},
    "CTkLabel": {"text_color": SECONDARY_TEXT},
    "CTkEntry": {"fg_color": CARD_BG, "border_color": SECONDARY_BORDER,
                 "border_width": 1, "text_color": SECONDARY_TEXT},
    "CTkOptionMenu": {"fg_color": SECONDARY_HOVER,
                      "button_color": SECONDARY_HOVER,
                      "button_hover_color": SECONDARY_BORDER,
                      "text_color": SECONDARY_TEXT},
    "CTkCheckBox": {"fg_color": PRIMARY, "hover_color": PRIMARY_HOVER,
                    "border_color": SECONDARY_BORDER, "border_width": 2,
                    "corner_radius": 4, "text_color": SECONDARY_TEXT,
                    "checkmark_color": PRIMARY_TEXT},
    "CTkScrollbar": {"button_color": SB_BG},
    "CTkTextbox": {"fg_color": CARD_BG, "text_color": SECONDARY_TEXT,
                   "border_color": SECONDARY_BORDER},
    "CTkSegmentedButton": {"fg_color": SIDEBAR_BG,
                           "selected_color": CARD_BG,
                           "selected_hover_color": SECONDARY_HOVER,
                           "unselected_color": SIDEBAR_BG,
                           "unselected_hover_color": SECONDARY_HOVER,
                           "text_color": SECONDARY_TEXT},
    "DropdownMenu": {"fg_color": CARD_BG, "hover_color": SECONDARY_HOVER,
                     "text_color": SECONDARY_TEXT},
}.items():
    ctk.ThemeManager.theme[widget].update(options)

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
    """Nhan tieu de muc kieu GNOME HIG (bold, dimmed — KHONG all-caps)."""
    return ctk.CTkLabel(
        master, text=text,
        font=ctk.CTkFont(size=13, weight="bold"),
        text_color=TEXT_DIM, anchor="w",
    )


def icon_button(master, icon_name: str, text: str, command,
                tip: str | None = None, **kwargs) -> ctk.CTkButton:
    """Nut bam kieu GNOME HIG secondary: outlined/flat, khong bg mac dinh."""
    kwargs.setdefault("fg_color", SECONDARY)
    kwargs.setdefault("hover_color", SECONDARY_HOVER)
    kwargs.setdefault("text_color", SECONDARY_TEXT)
    kwargs.setdefault("border_width", 1)
    kwargs.setdefault("border_color", SECONDARY_BORDER)
    kwargs.setdefault("corner_radius", 6)
    btn = ctk.CTkButton(master, image=icon(icon_name), text=text,
                        compound="left", anchor="w", command=command, **kwargs)
    if tip:
        ToolTip(btn, tip)
    return btn


# ----------------------------------------------------------------- Tooltip
class ToolTip:
    """Tooltip theo theme sang/toi, chu nho ro rang (NFR-02)."""

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
        # Adwaita style: nen bien doi theo theme
        is_dark = ctk.get_appearance_mode() == "Dark"
        bg_color = "#383838" if is_dark else "#F0F0F0"
        fg_color = "#EEEEEE" if is_dark else "#1C1C1C"
        border_color = "#505050" if is_dark else "#C8C8C8"
        outer = tk.Frame(self._tip, bg=border_color, bd=1)
        outer.pack()
        tk.Label(
            outer, text=self.text, justify="left",
            bg=bg_color, fg=fg_color, padx=10, pady=5,
            font=("TkDefaultFont", 9), wraplength=340,
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
    """Mot the tham so trong form dong — kieu Adwaita card (FR-1.1, FR-1.2)."""

    def __init__(self, master, on_delete, data: dict | None = None):
        super().__init__(master, border_width=1, corner_radius=12,
                         fg_color=CARD_BG,
                         border_color=("#D4D4D4", "#3E3E3E"))
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
        header.pack(fill="x", padx=14, pady=(12, 0))
        ctk.CTkLabel(header, textvariable=self.title_var,
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
        del_btn = ctk.CTkButton(
            header, image=icon("trash-2", 16), text="", width=32, height=28,
            fg_color="transparent",
            hover_color=("#FFDAD6", "#5A2020"),
            text_color=DESTRUCTIVE,
            border_width=0,
            corner_radius=6,
            command=lambda: self.on_delete(self),
        )
        del_btn.pack(side="right")
        ToolTip(del_btn, "Xoá tham số này khỏi hàm")

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=(8, 0))
        ctk.CTkLabel(row, text="Tên", width=34, anchor="w").pack(side="left")
        name_entry = ctk.CTkEntry(row, textvariable=self.name_var, width=150)
        name_entry.pack(side="left", fill="x", expand=True, padx=(0, 12))
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
        self.config_frame.pack(fill="x", padx=14, pady=(4, 14))
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
            ctk.CTkLabel(f, text="Nhỏ nhất", width=76, anchor="w").grid(row=0, column=0, sticky="w")
            min_entry = ctk.CTkEntry(f, textvariable=self.min_var, width=100)
            min_entry.grid(row=0, column=1, padx=(0, 12))
            ToolTip(min_entry, "Giá trị nhỏ nhất hợp lệ. BVA sinh các điểm "
                               "min-1, min, min+1 (FR-2.2).")
            ctk.CTkLabel(f, text="Lớn nhất", width=76, anchor="w").grid(row=0, column=2, sticky="w")
            max_entry = ctk.CTkEntry(f, textvariable=self.max_var, width=100)
            max_entry.grid(row=0, column=3, padx=(0, 12))
            ToolTip(max_entry, "Giá trị lớn nhất hợp lệ, phải >= Min (FR-2.2).")
            null_box = ctk.CTkCheckBox(f, text="Cho phép null", variable=self.allow_null_var)
            null_box.grid(row=1, column=0, columnspan=4, sticky="w", pady=(10, 0))
            ToolTip(null_box, "Cho phép None là hợp lệ; nếu tắt, BTG sinh "
                              "case None thuộc vùng không hợp lệ.")
        elif ptype == "string":
            ctk.CTkLabel(f, text="Độ dài min", width=80, anchor="w").grid(row=0, column=0, sticky="w")
            minlen_entry = ctk.CTkEntry(f, textvariable=self.minlen_var, width=64)
            minlen_entry.grid(row=0, column=1, padx=(0, 12))
            ToolTip(minlen_entry, "Độ dài chuỗi tối thiểu hợp lệ.")
            ctk.CTkLabel(f, text="Độ dài max", width=82, anchor="w").grid(row=0, column=2, sticky="w")
            maxlen_entry = ctk.CTkEntry(f, textvariable=self.maxlen_var, width=64)
            maxlen_entry.grid(row=0, column=3, padx=(0, 12))
            ToolTip(maxlen_entry, "Độ dài chuỗi tối đa hợp lệ, phải >= Min length.")
            empty_box = ctk.CTkCheckBox(f, text="Cho phép rỗng", variable=self.allow_empty_var)
            empty_box.grid(row=2, column=0, columnspan=2, sticky="w", pady=(10, 0))
            ToolTip(empty_box, "Cho phép chuỗi rỗng '' là hợp lệ.")
            null_box = ctk.CTkCheckBox(f, text="Cho phép null", variable=self.allow_null_var)
            null_box.grid(row=2, column=2, columnspan=2, sticky="w", pady=(10, 0))
            ToolTip(null_box, "Cho phép None là hợp lệ.")
            ctk.CTkLabel(f, text="Regex", width=70, anchor="w").grid(row=1, column=0, sticky="w", pady=(6, 0))
            regex_entry = ctk.CTkEntry(f, textvariable=self.regex_var, width=320)
            regex_entry.grid(row=1, column=1, columnspan=3, sticky="ew", pady=(6, 0))
            ToolTip(regex_entry, "Tuỳ chọn: mẫu regex chuỗi hợp lệ phải khớp, "
                                 "VD ^\\d{3}$ cho chuỗi 3 chữ số (FR-1.4).")
        elif ptype == "enum":
            ctk.CTkLabel(f, text="Giá trị", width=70, anchor="w").grid(row=0, column=0, sticky="w")
            enum_entry = ctk.CTkEntry(f, textvariable=self.enum_var, width=300)
            enum_entry.grid(row=0, column=1, padx=(0, 12))
            ToolTip(enum_entry, "Danh sách giá trị hợp lệ, cách nhau bởi dấu phẩy. "
                                "Giá trị ngoài danh sách thuộc vùng không hợp lệ.")
            null_box = ctk.CTkCheckBox(f, text="Cho phép null", variable=self.allow_null_var)
            null_box.grid(row=0, column=2)
            ToolTip(null_box, "Cho phép None là hợp lệ.")
        else:  # bool
            ctk.CTkLabel(f, text="Bool gồm 2 giá trị True / False.",
                         text_color=TEXT_DIM).grid(row=0, column=0, sticky="w")
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
        self.geometry("1280x820")
        self.minsize(1080, 660)
        import tkinter.font as tkfont
        families = set(tkfont.families(self))
        self.ui_font = next((f for f in ("Adwaita Sans", "Cantarell", "Noto Sans", "DejaVu Sans")
                             if f in families), tkfont.nametofont("TkDefaultFont").actual("family"))
        self.mono_font = next((f for f in ("Adwaita Mono", "DejaVu Sans Mono", "Consolas")
                               if f in families), tkfont.nametofont("TkFixedFont").actual("family"))
        ctk.ThemeManager.theme["CTkFont"]["family"] = self.ui_font
        self.dark_mode = ctk.get_appearance_mode() == "Dark"
        self._set_window_icon()

        self.param_cards: list[ParamCard] = []
        self.spec: FunctionSpec | None = None
        self.cases: list = []
        self.results: list | None = None  # ket qua Chạy test gan nhat
        self.gt_code_str: str = ""        # code ham tham chieu (luu trong bien,
        self.gt_source: str = ""          # khong con o text tren sidebar)
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
        header = ctk.CTkFrame(self, height=54, corner_radius=0,
                              fg_color=HEADERBAR_BG)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure((0, 2), weight=1, uniform="header")
        header.grid_columnconfigure(1, weight=0)
        icon_button(header, "folder", "Mở file Python", self._load_py_file,
                    tip="Mở file Python và trích xuất các hàm.",
                    border_width=0, height=36, width=164).grid(
                        row=0, column=0, sticky="w", padx=12, pady=9)
        title = ctk.CTkFrame(header, fg_color="transparent")
        title.grid(row=0, column=1)
        try:
            logo = app_logo(30)
        except OSError:
            logo = icon("zap", 24)
        ctk.CTkLabel(title, image=logo, text="").pack(side="left", padx=(0, 8))
        ctk.CTkLabel(title, text="BTG · Kiểm thử hộp đen",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        self.theme_btn = icon_button(
            header, "sun" if self.dark_mode else "moon", "", self._toggle_theme,
            tip="Chuyển giao diện sáng / tối", width=36, height=36,
            border_width=0)
        self.theme_btn.grid(row=0, column=2, sticky="e", padx=12)
        ctk.CTkFrame(header, height=1, corner_radius=0,
                      fg_color=SECONDARY_BORDER).grid(
                          row=1, column=0, columnspan=3, sticky="ew")

    def _toggle_theme(self) -> None:
        self.dark_mode = not self.dark_mode
        ctk.set_appearance_mode("dark" if self.dark_mode else "light")
        self.theme_btn.configure(image=icon("sun" if self.dark_mode else "moon"))
        self.paned.configure(bg=SASH_COLOR_DARK if self.dark_mode else SASH_COLOR_LIGHT)
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
                                    fg_color=SIDEBAR_BG,
                                    scrollbar_button_color=("gray70", "gray35"))
        sb.grid(row=0, column=0, sticky="nsew")

        section_label(sb, "File Python").pack(anchor="w", padx=14, pady=(14, 6))
        icon_button(sb, "folder", "Mở file .py", self._load_py_file,
                    tip="Tự trích xuất tên hàm, tham số và type hint bằng AST "
                        "(FR-1.3). Literal[...] được hiểu là enum.",
                    height=34).pack(fill="x", padx=14)
        ctk.CTkLabel(sb, text="Hàm trong file", anchor="w",
                     font=ctk.CTkFont(size=11),
                     text_color=TEXT_DIM).pack(anchor="w", padx=14, pady=(10, 2))
        self.imported_name_var = tk.StringVar(value="(chưa có hàm)")
        self.imported_menu = ctk.CTkOptionMenu(
            sb, values=["(chưa có hàm)"], variable=self.imported_name_var,
            height=34,
            state="disabled")
        self.imported_menu.pack(fill="x", padx=14)
        self.apply_btn = icon_button(
            sb, "download", "Điền vào form", self._apply_imported,
            tip="Nạp hàm đang chọn vào form cấu hình bên phải.",
            height=34, state="disabled")
        self.apply_btn.pack(fill="x", padx=14, pady=(8, 0))

        section_label(sb, "Kỹ thuật sinh test").pack(anchor="w", padx=14, pady=(20, 6))
        self.use_ep_var = tk.BooleanVar(value=True)
        self.use_bva_var = tk.BooleanVar(value=True)
        self.use_pairwise_var = tk.BooleanVar(value=False)
        ep_box = ctk.CTkCheckBox(sb, text="Phân vùng tương đương (EP)",
                                 variable=self.use_ep_var)
        ep_box.pack(anchor="w", padx=14, pady=3)
        ToolTip(ep_box, "Chia miền dữ liệu thành các vùng tương đương, "
                        "mỗi vùng lấy 1 giá trị đại diện (FR-2.1).")
        bva_box = ctk.CTkCheckBox(sb, text="Phân tích giá trị biên (BVA)",
                                  variable=self.use_bva_var)
        bva_box.pack(anchor="w", padx=14, pady=3)
        ToolTip(bva_box, "Sinh các điểm sát biên: min-1, min, min+1, "
                         "max-1, max, max+1 (FR-2.2).")
        pw_box = ctk.CTkCheckBox(sb, text="Kết hợp từng cặp (Pairwise)", variable=self.use_pairwise_var)
        pw_box.pack(anchor="w", padx=14, pady=3)
        ToolTip(pw_box, "Bao phủ mọi cặp giá trị giữa các tham số — "
                        "khuyên dùng khi hàm có > 3 tham số (FR-2.3).")

        section_label(sb, "Hàm tham chiếu").pack(anchor="w", padx=14, pady=(20, 6))
        icon_button(sb, "code", "Mở file hàm tham chiếu", self._load_gt_file,
                    tip="Nạp code hàm tham chiếu (bản cài đặt chuẩn) từ một "
                        "file .py. Hàm này dùng để tự điền Expected Output "
                        "và chạy Chạy test (FR-3.2).",
                    height=34).pack(fill="x", padx=14)
        # Trang thai gon: sidebar chi hien da nap hay chua + nut mo popup
        # xem/sua code, thay cho o text to chiem cho truoc day.
        gt_status = ctk.CTkFrame(sb, fg_color="transparent")
        gt_status.pack(fill="x", padx=14, pady=(8, 0))
        self.gt_status_icon = ctk.CTkLabel(gt_status, text="")
        self.gt_status_icon.pack(side="left")
        self.gt_status_var = tk.StringVar(value="Chưa có hàm tham chiếu")
        ctk.CTkLabel(gt_status, textvariable=self.gt_status_var, anchor="w",
                     text_color=TEXT_DIM, wraplength=230,
                     justify="left").pack(side="left", padx=(6, 0))
        icon_button(sb, "edit-2", "Xem / nhập code", self._open_gt_editor,
                    tip="Mở cửa sổ xem và sửa code hàm tham chiếu, "
                        "hoặc dán code trực tiếp vào đó.",
                    height=32).pack(fill="x", padx=14, pady=(8, 14))

    def _build_main(self, body) -> None:
        main = ctk.CTkFrame(body, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew", padx=18, pady=(16, 10))
        main.grid_rowconfigure(3, weight=1)
        main.grid_columnconfigure(0, weight=1)

        heading = ctk.CTkFrame(main, fg_color="transparent")
        heading.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        ctk.CTkLabel(heading, text="Cấu hình kiểm thử",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(side="left")
        icon_button(heading, "zap", "Sinh test case", self._generate,
                    tip="Sinh test theo các kỹ thuật đã chọn.",
                    fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
                    text_color=PRIMARY_TEXT, border_width=0,
                    width=160, height=36).pack(side="right")
        toolbar = ctk.CTkFrame(main, fg_color="transparent")
        toolbar.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkLabel(toolbar, text="Hàm", width=36, anchor="w").pack(side="left")
        self.func_name_var = tk.StringVar(value="my_function")
        func_entry = ctk.CTkEntry(toolbar, textvariable=self.func_name_var, width=230)
        func_entry.pack(side="left")
        ToolTip(func_entry, "Tên hàm cần sinh test case — phải trùng tên hàm "
                            "trong hàm tham chiếu nếu muốn Chạy test.")
        icon_button(toolbar, "plus", "Thêm tham số", lambda: self.add_param(),
                    tip="Thêm một tham số mới vào hàm (FR-1.1).",
                    width=140, height=32).pack(side="left", padx=(12, 0))

        self.param_count_var = tk.StringVar(value="Tham số · 0")
        ctk.CTkLabel(main, textvariable=self.param_count_var,
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=TEXT_DIM).grid(row=2, column=0, sticky="w", pady=(0, 6))

        # Thanh chia keo duoc (splitter) giua khung tham so va khung ket
        # qua: nguoi dung tu keo de uu tien phan minh dang lam.
        self.paned = tk.PanedWindow(main, orient="vertical", sashwidth=5,
                                    bd=0, bg=SASH_COLOR_DARK if self.dark_mode else SASH_COLOR_LIGHT,
                                    opaqueresize=True, sashcursor="sb_v_double_arrow")
        self.paned.grid(row=3, column=0, sticky="nsew")
        top = ctk.CTkFrame(self.paned, fg_color=WINDOW_BG, corner_radius=0)
        bottom = ctk.CTkFrame(self.paned, fg_color=WINDOW_BG, corner_radius=0)
        self.paned.add(top, minsize=105, stretch="always")
        self.paned.add(bottom, minsize=230, stretch="always")
        self.after(200, self._place_sash)

        self.params_frame = ctk.CTkScrollableFrame(top, fg_color="transparent")
        self.params_frame.pack(fill="both", expand=True)

        actions = ctk.CTkFrame(bottom, fg_color="transparent")
        actions.pack(fill="x", pady=(8, 6))
        self.btn_csv = icon_button(
            actions, "file-text", "CSV", self._export_csv,
            tip="Xuất bảng test case ra file CSV (FR-4.1). "
                "Nếu đã Chạy test, file kèm thêm cột Actual + Status.",
            width=96, height=32, state="disabled")
        self.btn_csv.pack(side="left", padx=(0, 8))
        self.btn_excel = icon_button(
            actions, "grid", "Excel", self._export_excel,
            tip="Xuất bảng test case ra file Excel .xlsx (FR-4.1). "
                "Nếu đã Chạy test, file kèm thêm cột Actual + Status.",
            width=96, height=32, state="disabled")
        self.btn_excel.pack(side="left", padx=(0, 8))
        self.btn_pytest = icon_button(
            actions, "terminal", "Pytest", self._export_pytest,
            tip="Sinh file test_generated.py dùng @pytest.mark.parametrize (FR-4.2).",
            width=104, height=32, state="disabled")
        self.btn_pytest.pack(side="left", padx=(0, 8))
        self.btn_run = icon_button(
            actions, "play", "Chạy test", self._run_tests,
            tip="Chạy toàn bộ test case với hàm tham chiếu, "
                "hiển thị tỉ lệ Pass/Fail (FR-4.3).",
            width=118, height=32, state="disabled")
        self.btn_run.pack(side="left")
        self.summary_var = tk.StringVar(value="Chưa có kết quả chạy")
        ctk.CTkLabel(bottom, textvariable=self.summary_var, anchor="w",
                     text_color=TEXT_DIM,
                     font=ctk.CTkFont(size=12)).pack(fill="x", padx=2)
        self.case_count_var = tk.StringVar(value="0 test case")
        ctk.CTkLabel(actions, textvariable=self.case_count_var,
                     text_color=TEXT_DIM).pack(side="right")

        self.tabs = tabs = ctk.CTkTabview(bottom, fg_color=CARD_BG,
                                             border_width=1, border_color=SECONDARY_BORDER,
                                             corner_radius=10)
        tabs.pack(fill="both", expand=True)
        cases_tab = tabs.add("Test case")
        run_tab = tabs.add("Kết quả chạy")
        self.cases_tree = self._make_tree(
            cases_tab,
            ("id", "inputs", "expected", "exception", "technique", "reasoning"),
            ["ID", "Inputs", "Expected Output", "Expected Exception",
             "Test Technique", "Reasoning"],
            [76, 250, 140, 165, 125, 255],
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

        self.cases_hint = self._placeholder(
            cases_tab, "sliders", "Sẵn sàng tạo bộ kiểm thử",
            "Cấu hình tham số và chọn kỹ thuật bên trái.\n"
            "Bấm Sinh test case để bắt đầu.")
        self.run_hint = self._placeholder(
            run_tab, "play", "Chưa có kết quả chạy",
            "Nạp hàm tham chiếu, sinh test case rồi bấm Chạy test.\n"
            "Kết quả Pass / Fail sẽ xuất hiện tại đây.")

    def _placeholder(self, parent, icon_name: str, title: str, description: str):
        panel = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=0)
        content = ctk.CTkFrame(panel, fg_color="transparent")
        content.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(content, image=icon(icon_name, 28), text="").pack(pady=(8, 4))
        ctk.CTkLabel(content, text=title,
                     font=ctk.CTkFont(size=16, weight="bold")).pack()
        ctk.CTkLabel(content, text=description, justify="center",
                     text_color=TEXT_DIM, font=ctk.CTkFont(size=12)).pack(padx=16, pady=(4, 8))
        panel.place(relx=0, rely=0, relwidth=1, relheight=1)
        return panel

    def _place_sash(self) -> None:
        try:
            height = self.paned.winfo_height()
            if height > 100:
                self.paned.sash_place(0, 0, int(height * 0.36))
        except tk.TclError:
            pass

    def _sync_output_buttons(self) -> None:
        self.case_count_var.set(f"{len(self.cases)} test case")
        state = "normal" if self.cases else "disabled"
        for btn in (self.btn_csv, self.btn_excel, self.btn_pytest,
                    self.btn_run):
            btn.configure(state=state)
        if self.cases:
            self.cases_hint.place_forget()
        else:
            self.cases_hint.place(relx=0, rely=0, relwidth=1, relheight=1)

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
            bg, fg, head_bg, sel = "#2B2B2B", "#FFFFFF", "#383838", PRIMARY[1]
            odd_bg = TREE_ODD_DARK
            sb_bg, sb_trough = "#4D4D4D", "#242424"
            pass_fg, fail_fg = SUCCESS_FG[1], FAIL_FG[1]
        else:
            bg, fg, head_bg, sel = "#FFFFFF", "#242424", "#F2F2F2", PRIMARY[0]
            odd_bg = TREE_ODD_LIGHT
            sb_bg, sb_trough = "#B8B8B8", "#EFEFEF"
            pass_fg, fail_fg = SUCCESS_FG[0], FAIL_FG[0]
        style.configure("Treeview", background=bg, foreground=fg,
                        fieldbackground=bg, rowheight=34, borderwidth=0,
                        bordercolor=bg, lightcolor=bg, darkcolor=bg,
                        font=(self.mono_font, 10))
        style.configure("Treeview.Heading", background=head_bg, foreground=fg,
                        relief="flat", borderwidth=0,
                        font=(self.ui_font, 10, "bold"))
        style.map("Treeview.Heading", background=[("active", head_bg)])
        style.map("Treeview", background=[("selected", sel)],
                  foreground=[("selected", "#FFFFFF")])
        # Thanh cuon theo theme thay vi mac dinh cua OS
        for orient in ("Vertical", "Horizontal"):
            style.layout(f"{orient}.TScrollbar", [
                (f"{orient}.Scrollbar.trough", {"sticky": "nswe", "children": [
                    (f"{orient}.Scrollbar.thumb", {"sticky": "nswe", "expand": "1"})
                ]})
            ])
            style.configure(f"{orient}.TScrollbar", background=sb_bg, width=10,
                            arrowsize=10,
                            troughcolor=sb_trough, borderwidth=0,
                            bordercolor=sb_trough, lightcolor=sb_bg,
                            darkcolor=sb_bg, arrowcolor=fg)
        for tree in (getattr(self, "cases_tree", None),
                     getattr(self, "run_tree", None)):
            if tree is not None:
                tree.tag_configure("Pass", foreground=pass_fg)
                tree.tag_configure("Fail", foreground=fail_fg)
                tree.tag_configure("oddrow", background=odd_bg)

    def _build_statusbar(self) -> None:
        self.status_var = tk.StringVar(
            value="Sẵn sàng — cấu hình tham số rồi bấm 'Sinh test case'.")
        bar = ctk.CTkFrame(self, height=26, corner_radius=0,
                           fg_color=HEADERBAR_BG)
        bar.grid(row=2, column=0, sticky="ew")
        bar.grid_propagate(False)
        ctk.CTkLabel(bar, textvariable=self.status_var, anchor="w",
                     font=ctk.CTkFont(size=11),
                     text_color=("gray38", "gray78")).pack(side="left", padx=12)

    def _set_status(self, text: str) -> None:
        self.status_var.set(text)

    # ------------------------------------------------------------ params
    def add_param(self, data: dict | None = None) -> None:
        card = ParamCard(self.params_frame, on_delete=self._delete_param,
                         data=data)
        card.pack(fill="x", padx=6, pady=6)
        self.param_cards.append(card)
        self.param_count_var.set(f"Tham số · {len(self.param_cards)}")

    def _delete_param(self, card: ParamCard) -> None:
        if len(self.param_cards) <= 1:
            messagebox.showwarning("BTG", "Hàm phải có ít nhất 1 tham số.")
            return
        self.param_cards.remove(card)
        card.destroy()
        self.param_count_var.set(f"Tham số · {len(self.param_cards)}")

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
        self._import_source = pathlib.Path(path).name
        self.imported_menu.configure(values=[s.name for s in specs],
                                     state="normal")
        self.apply_btn.configure(state="normal")
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
            self._set_gt_code(gt_code,
                              source=getattr(self, "_import_source", ""))
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
        self._set_gt_code(code, source=pathlib.Path(path).name)
        self._set_status("Đã nạp hàm tham chiếu từ file.")

    # ------------------------------------------- ham tham chieu (FR-3.2)
    def _set_gt_code(self, code: str, source: str = "") -> None:
        self.gt_code_str = code
        self.gt_source = source
        self._refresh_gt_status()

    def _gt_code(self) -> str:
        return self.gt_code_str.strip()

    def _refresh_gt_status(self) -> None:
        code = self._gt_code()
        if code:
            lines = code.count("\n") + 1
            origin = self.gt_source or "code đã nhập"
            self.gt_status_var.set(f"Đã nạp: {origin} ({lines} dòng)")
            self.gt_status_icon.configure(image=icon("check-circle", 16))
        else:
            self.gt_status_var.set("Chưa có hàm tham chiếu")
            self.gt_status_icon.configure(image=icon("x-circle", 16))

    def _open_gt_editor(self) -> None:
        """Popup xem / sua / dan code ham tham chieu."""
        win = ctk.CTkToplevel(self)
        win.title("Hàm tham chiếu")
        win.geometry("760x540")
        win.minsize(560, 400)
        win.transient(self)
        ctk.CTkLabel(
            win, anchor="w", text_color=TEXT_DIM, wraplength=510, justify="left",
            text="Code hàm chuẩn, cùng tên với hàm đang cấu hình. BTG chạy "
                 "hàm này để tự điền Expected Output và Chạy test.",
        ).pack(fill="x", padx=14, pady=(12, 6))
        text = ctk.CTkTextbox(win, font=ctk.CTkFont(family=self.mono_font, size=13))
        text.pack(fill="both", expand=True, padx=14)
        text.insert("1.0", self.gt_code_str)
        ToolTip(text, "Dán code trực tiếp vào đây hoặc sửa code đã nạp, "
                      "rồi bấm Lưu.")

        btns = ctk.CTkFrame(win, fg_color="transparent")
        btns.pack(fill="x", padx=14, pady=12)

        def save() -> None:
            self._set_gt_code(text.get("1.0", "end").strip(),
                              source="code đã nhập")
            self._set_status("Đã lưu code hàm tham chiếu.")
            win.destroy()

        def clear() -> None:
            text.delete("1.0", "end")

        icon_button(btns, "check-circle", "Lưu", save,
                    tip="Lưu code và đóng cửa sổ.",
                    width=100, height=34, fg_color=PRIMARY,
                    hover_color=PRIMARY_HOVER, text_color=PRIMARY_TEXT,
                    border_width=0).pack(side="right", padx=(8, 0))
        icon_button(btns, "trash-2", "Xoá trắng", clear,
                    tip="Xoá toàn bộ code trong ô (chưa lưu cho đến khi bấm Lưu).",
                    width=110, height=32).pack(side="left", padx=(8, 0))
        icon_button(btns, "x-circle", "Đóng", win.destroy,
                    tip="Đóng mà không lưu thay đổi.",
                    width=100, height=32).pack(side="right")
        win.after(80, win.lift)
        win.after(100, text.focus_set)
        win.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - win.winfo_width()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - win.winfo_height()) // 2
        win.geometry(f"+{max(x, 0)}+{max(y, 0)}")

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
            messagebox.showwarning(
                "BTG — Chưa chọn kỹ thuật",
                "Bạn chưa chọn kỹ thuật sinh test nào.\n"
                "Hãy tick ít nhất 1 kỹ thuật (EP, BVA hoặc Pairwise) "
                "ở sidebar bên trái rồi bấm Sinh test case lại.")
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
        self.run_hint.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._fill_cases_tree()
        self.summary_var.set("Chưa có kết quả chạy")
        self._set_status(f"Đã sinh {len(cases)} test case cho hàm "
                         f"'{spec.name}'.{note}")

    def _fill_cases_tree(self) -> None:
        self.cases_tree.delete(*self.cases_tree.get_children())
        for idx, c in enumerate(self.cases):
            self.cases_tree.insert(
                "", "end", iid=str(idx),
                tags=("oddrow",) if idx % 2 else (),
                values=(
                    c.test_id,
                    json.dumps(c.inputs, ensure_ascii=False, default=str),
                    "" if c.expected_output is None else str(c.expected_output),
                    c.expected_exception or "",
                    c.technique,
                    c.reasoning,
                ),
            )
        self._sync_output_buttons()

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
        self.results = None  # expected doi -> phai Chạy test lai
        self.run_tree.delete(*self.run_tree.get_children())
        self.run_hint.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.summary_var.set("Chưa có kết quả chạy")
        self._fill_cases_tree()
        self._set_status(f"Đã cập nhật kết quả mong đợi cho {case.test_id}.")

    # ------------------------------------------------------------- export
    def _require_cases(self) -> bool:
        if not self.cases or self.spec is None:
            messagebox.showinfo("BTG", "Hãy bấm 'Sinh test case' trước.")
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
        for idx, r in enumerate(results):
            c = r.test_case
            expected = c.expected_exception or (
                "" if c.expected_output is None else str(c.expected_output))
            actual = r.actual_exception or (
                "" if r.actual_output is None else str(r.actual_output))
            tags = (r.status, "oddrow") if idx % 2 else (r.status,)
            self.run_tree.insert(
                "", "end",
                values=(c.test_id,
                        json.dumps(c.inputs, ensure_ascii=False, default=str),
                        expected, actual, r.status),
                tags=tags,
            )
        self.run_hint.place_forget()
        self._set_status("Đã chạy xong — xem tab Kết quả chạy.")


def main() -> None:
    app = BTGApp()
    app.mainloop()


if __name__ == "__main__":
    main()
