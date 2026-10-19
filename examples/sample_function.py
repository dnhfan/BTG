"""Ham mau de thu BTG: phan loai hoc luc + kiem tra tuoi.

Thu ngay:
1. Upload file nay tren giao dien Streamlit, hoac
2. Chay: python examples/demo.py
"""
from typing import Literal


def check_age(age: int) -> str:
    """Duoi 0 hoac tren 150 -> ValueError. 0-17: tre em, 18-64: nguoi lon, >=65: nguoi cao tuoi."""
    if age is None:
        raise TypeError("age must not be None")
    if age < 0 or age > 150:
        raise ValueError("age out of range")
    if age < 18:
        return "child"
    if age < 65:
        return "adult"
    return "senior"


def register(username: str, age: int, role: Literal["admin", "user", "guest"], active: bool) -> str:
    """Dang ky nguoi dung: username dai 3-20 ky tu, tuoi 18-60."""
    if not username or not (3 <= len(username) <= 20):
        raise ValueError("username length must be 3..20")
    if age < 18 or age > 60:
        raise ValueError("age must be 18..60")
    if role not in ("admin", "user", "guest"):
        raise ValueError("invalid role")
    return f"{username}:{role}:{'active' if active else 'inactive'}"
