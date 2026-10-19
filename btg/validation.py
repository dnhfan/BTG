"""Validation cua Spec — SRS FR-1.4.

Tra ve danh sach loi (chuoi). Danh sach rong = spec hop le.
"""
from __future__ import annotations

import keyword
import re

from .models import FunctionSpec, ParamSpec, ParamType


def _check_identifier(name: str, label: str, errors: list[str]) -> None:
    if not name or not name.isidentifier() or keyword.iskeyword(name):
        errors.append(f"{label} '{name}' khong phai ten Python hop le.")


def validate_param(param: ParamSpec) -> list[str]:
    errors: list[str] = []
    _check_identifier(param.name, "Tham so", errors)

    if param.type in (ParamType.INT, ParamType.FLOAT):
        if param.min_value is not None and param.max_value is not None:
            if param.min_value > param.max_value:
                errors.append(
                    f"Tham so '{param.name}': min ({param.min_value}) > max ({param.max_value})."
                )

    if param.type == ParamType.STRING:
        if param.min_length is not None and param.min_length < 0:
            errors.append(f"Tham so '{param.name}': min_length khong duoc am.")
        if param.max_length is not None and param.max_length < 0:
            errors.append(f"Tham so '{param.name}': max_length khong duoc am.")
        if (
            param.min_length is not None
            and param.max_length is not None
            and param.min_length > param.max_length
        ):
            errors.append(
                f"Tham so '{param.name}': min_length ({param.min_length}) "
                f"> max_length ({param.max_length})."
            )
        if param.regex:
            try:
                re.compile(param.regex)
            except re.error as exc:
                errors.append(f"Tham so '{param.name}': regex sai cu phap: {exc}")

    if param.type == ParamType.ENUM:
        if not param.enum_values:
            errors.append(f"Tham so '{param.name}': enum phai co it nhat 1 gia tri hop le.")
        elif len(set(map(repr, param.enum_values))) != len(param.enum_values):
            errors.append(f"Tham so '{param.name}': enum co gia tri trung nhau.")

    return errors


def validate_spec(spec: FunctionSpec) -> list[str]:
    errors: list[str] = []
    _check_identifier(spec.name, "Ham", errors)
    if not spec.params:
        errors.append("Ham phai co it nhat 1 tham so.")

    names = [p.name for p in spec.params]
    for name in set(names):
        if names.count(name) > 1:
            errors.append(f"Ten tham so bi trung: '{name}'.")

    for param in spec.params:
        errors.extend(validate_param(param))
    return errors
