"""Sinh gia tri dai dien cho tung tham so.

Dung chung boi EP / BVA / Pairwise:
- valid_value()   : 1 gia tri nam giua vung hop le
- invalid_values(): cac gia tri nam o vung khong hop le, kem nhan ly do
- string_of_length(): tao chuoi co do dai cho truoc ma (co gang) thoa regex
"""
from __future__ import annotations

import re
from typing import Any

from .models import ParamSpec, ParamType

# ---------------------------------------------------------------- string ---

def _regex_example(pattern: str, target_len: int) -> str | None:
    """Co gang sinh chuoi thoa regex. Thu exrex neu co, neu khong thi None."""
    try:
        import exrex  # type: ignore

        for _ in range(50):
            candidate = exrex.getone(pattern)
            if len(candidate) == target_len:
                return candidate
        return exrex.getone(pattern)
    except Exception:
        return None


def string_of_length(param: ParamSpec, length: int) -> str:
    if length <= 0:
        return ""
    if param.regex:
        example = _regex_example(param.regex, length)
        if example is not None and re.fullmatch(param.regex, example):
            return example
    # Mac dinh: chuoi 'a' lap lai. Neu regex chi cho phep ky tu khac, 'a'
    # van la dai dien thong dung cho cac bai tap EP/BVA theo do dai.
    return "a" * length


# ------------------------------------------------------------------ valid ---

def valid_value(param: ParamSpec) -> Any:
    """Gia tri dai dien hop le (nominal) cua 1 tham so."""
    if param.type == ParamType.INT:
        lo = int(param.min_value) if param.min_value is not None else 0
        hi = int(param.max_value) if param.max_value is not None else lo + 100
        return (lo + hi) // 2

    if param.type == ParamType.FLOAT:
        lo = float(param.min_value) if param.min_value is not None else 0.0
        hi = float(param.max_value) if param.max_value is not None else lo + 100.0
        return round((lo + hi) / 2, 2)

    if param.type == ParamType.STRING:
        lo = param.min_length if param.min_length is not None else 1
        hi = param.max_length if param.max_length is not None else lo + 9
        mid = max(lo, (lo + hi) // 2)
        return string_of_length(param, mid)

    if param.type == ParamType.ENUM:
        return param.enum_values[0] if param.enum_values else None

    if param.type == ParamType.BOOL:
        return True

    return None


# ---------------------------------------------------------------- invalid ---

def invalid_values(param: ParamSpec) -> list[tuple[Any, str]]:
    """Tra ve [(gia_tri, nhan_ly_do), ...] cho cac vung khong hop le."""
    out: list[tuple[Any, str]] = []

    if param.type == ParamType.INT:
        if param.min_value is not None:
            out.append((int(param.min_value) - 1, f"{param.name}_Below_Min"))
        if param.max_value is not None:
            out.append((int(param.max_value) + 1, f"{param.name}_Above_Max"))

    elif param.type == ParamType.FLOAT:
        if param.min_value is not None:
            out.append((round(float(param.min_value) - 1.0, 2), f"{param.name}_Below_Min"))
        if param.max_value is not None:
            out.append((round(float(param.max_value) + 1.0, 2), f"{param.name}_Above_Max"))

    elif param.type == ParamType.STRING:
        lo = param.min_length or 0
        if lo > 0:
            out.append((string_of_length(param, lo - 1), f"{param.name}_Too_Short"))
        if param.max_length is not None:
            # Chuoi qua dai: dung ky tu khac de khong bi trung voi BVA do dai
            out.append(("a" * (param.max_length + 5), f"{param.name}_Too_Long"))
        if not param.allow_empty:
            out.append(("", f"{param.name}_Empty"))
        if param.regex:
            out.append(("!!!invalid!!!", f"{param.name}_Regex_Mismatch"))

    elif param.type == ParamType.ENUM:
        out.append(("__INVALID_ENUM__", f"{param.name}_Invalid_Enum"))

    # bool khong co vung invalid rieng (chi True/False)

    if not param.allow_null:
        out.append((None, f"{param.name}_Null"))
    return out


def candidate_values(param: ParamSpec) -> list[Any]:
    """Tap gia tri ung vien cho Pairwise: gon, dai dien cac vung chinh."""
    if param.type == ParamType.BOOL:
        return [True, False]
    if param.type == ParamType.ENUM:
        return list(param.enum_values)
    if param.type in (ParamType.INT, ParamType.FLOAT):
        vals = [valid_value(param)]
        if param.min_value is not None:
            vals.append(param.min_value)
        if param.max_value is not None:
            vals.append(param.max_value)
        return list(dict.fromkeys(vals))
    if param.type == ParamType.STRING:
        vals = [valid_value(param)]
        lo = param.min_length or 0
        vals.append(string_of_length(param, lo))
        if param.max_length is not None:
            vals.append(string_of_length(param, param.max_length))
        return list(dict.fromkeys(vals))
    return [valid_value(param)]
