"""Data models cho BTG (SRS FE-01).

ParamSpec  : dac ta 1 tham so cua ham can kiem thu.
FunctionSpec: dac ta ham (ten + danh sach tham so).
TestCase   : 1 dong test case sinh ra.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any


class ParamType(str, enum.Enum):
    INT = "int"
    FLOAT = "float"
    STRING = "string"
    ENUM = "enum"
    BOOL = "bool"


@dataclass
class ParamSpec:
    name: str
    type: ParamType

    # int / float
    min_value: float | None = None
    max_value: float | None = None

    # string
    min_length: int | None = None
    max_length: int | None = None
    regex: str | None = None
    allow_empty: bool = False

    # enum: danh sach gia tri hop le, vi du ["admin", "user", "guest"]
    enum_values: list[Any] = field(default_factory=list)

    # chung
    allow_null: bool = False

    def __post_init__(self) -> None:
        if isinstance(self.type, str) and not isinstance(self.type, ParamType):
            self.type = ParamType(self.type)
        if self.type in (ParamType.INT, ParamType.FLOAT):
            if self.min_value is not None:
                self.min_value = int(self.min_value) if self.type == ParamType.INT else float(self.min_value)
            if self.max_value is not None:
                self.max_value = int(self.max_value) if self.type == ParamType.INT else float(self.max_value)


@dataclass
class FunctionSpec:
    name: str
    params: list[ParamSpec] = field(default_factory=list)

    def param_names(self) -> list[str]:
        return [p.name for p in self.params]


@dataclass
class TestCase:
    inputs: dict[str, Any]
    technique: str = ""          # "EP" | "BVA" | "Pairwise"
    reasoning: str = ""          # vi du "[BVA] age_Min_Minus_1"
    expected_output: Any = None  # gia tri mong doi (neu biet / co oracle)
    expected_exception: str | None = None  # vi du "ValueError"
    test_id: str = ""            # TC_001 ... (gan sau khi khử trùng)

    def key(self) -> tuple:
        """Khoa de khu trung lap: toan bo du lieu dau vao."""
        return tuple((k, repr(v)) for k, v in self.inputs.items())
