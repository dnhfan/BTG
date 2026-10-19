"""Black-box Test Generator (BTG).

Sinh test case tu dong bang cac ky thuat hop den:
Equivalence Partitioning (EP), Boundary Value Analysis (BVA), Pairwise.
"""

from .models import FunctionSpec, ParamSpec, ParamType, TestCase
from .generators import generate_test_cases
from .parser import parse_python_code, parse_python_file

__all__ = [
    "FunctionSpec",
    "ParamSpec",
    "ParamType",
    "TestCase",
    "generate_test_cases",
    "parse_python_code",
    "parse_python_file",
]
__version__ = "1.0.0"
