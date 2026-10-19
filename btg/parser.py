"""Spec Parser bang AST — SRS FR-1.3.

Doc code Python, trich xuat ten ham + tham so + type hint:
    def tinh_tong(a: int, b: float, ten: str, active: bool) -> ...
    def chon(role: Literal["admin", "user"]) -> ...   -> enum

Rang buoc mac dinh khi khong co thong tin khac:
    int   -> min=0,    max=100
    float -> min=0.0,  max=100.0
    str   -> min_length=1, max_length=10
Nguoi dung co the sua lai cac rang buoc nay tren UI sau khi parse.
"""
from __future__ import annotations

import ast
import pathlib

from .models import FunctionSpec, ParamSpec, ParamType

_TYPE_MAP = {
    "int": ParamType.INT,
    "float": ParamType.FLOAT,
    "str": ParamType.STRING,
    "string": ParamType.STRING,
    "bool": ParamType.BOOL,
}


def _default_param(name: str, ptype: ParamType, enum_values=None) -> ParamSpec:
    if ptype == ParamType.INT:
        return ParamSpec(name, ptype, min_value=0, max_value=100)
    if ptype == ParamType.FLOAT:
        return ParamSpec(name, ptype, min_value=0.0, max_value=100.0)
    if ptype == ParamType.STRING:
        return ParamSpec(name, ptype, min_length=1, max_length=10)
    if ptype == ParamType.ENUM:
        return ParamSpec(name, ptype, enum_values=list(enum_values or []))
    return ParamSpec(name, ptype)


def _annotation_to_param(name: str, node: ast.expr | None) -> ParamSpec:
    if node is None:
        # Khong co type hint -> mac dinh coi la int (pho bien nhat trong bai tap)
        return _default_param(name, ParamType.INT)

    # Literal["a", "b"] -> enum
    if isinstance(node, ast.Subscript) and getattr(node.value, "id", "") == "Literal":
        values: list = []
        elts = node.slice.elts if isinstance(node.slice, ast.Tuple) else [node.slice]
        for elt in elts:
            if isinstance(elt, ast.Constant):
                values.append(elt.value)
        return _default_param(name, ParamType.ENUM, values)

    ann_name = ""
    if isinstance(node, ast.Name):
        ann_name = node.id
    elif isinstance(node, ast.Constant) and isinstance(node.value, str):
        ann_name = node.value
    elif isinstance(node, ast.Attribute):
        ann_name = node.attr

    ptype = _TYPE_MAP.get(ann_name)
    if ptype is None:
        # Kieu la 1 class tu dinh nghia -> coi nhu enum theo ten class
        return _default_param(name, ParamType.ENUM, [ann_name] if ann_name else [])
    return _default_param(name, ptype)


def parse_python_code(code: str) -> list[FunctionSpec]:
    """Parse chuoi code Python -> danh sach FunctionSpec."""
    tree = ast.parse(code)
    specs: list[FunctionSpec] = []
    for node in tree.body:  # chi ham cap top-level
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        params: list[ParamSpec] = []
        args = node.args
        positional = list(args.args)
        # Bo qua self / cls cua method neu co
        if positional and positional[0].arg in ("self", "cls"):
            positional = positional[1:]
        for arg in positional:
            params.append(_annotation_to_param(arg.arg, arg.annotation))
        for arg in args.kwonlyargs:
            params.append(_annotation_to_param(arg.arg, arg.annotation))
        specs.append(FunctionSpec(name=node.name, params=params))
    return specs


def parse_python_file(path: str | pathlib.Path) -> list[FunctionSpec]:
    code = pathlib.Path(path).read_text(encoding="utf-8")
    return parse_python_code(code)
