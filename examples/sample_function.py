"""Ham mau de thu BTG: phan loai hoc luc + kiem tra tuoi.

Thu ngay:
1. Mo bang app desktop (python app.py) roi chon file nay, hoac
2. Chay: python examples/demo.py
"""
from typing import Literal
import re


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


def validate_record(
    quantity: int,
    score: float,
    name: str,
    active: bool,
    category: Literal["basic", "premium", "vip"],
) -> str:
    """Ví dụ Pairwise đủ năm kiểu: int, float, string, bool và Literal/enum.

    Khi nạp vào BTG, có thể đặt quantity 1..100, score 0..10 và name dài
    2..12 để các miền hợp lệ và không hợp lệ có ý nghĩa.
    """
    if not 1 <= quantity <= 100:
        raise ValueError("quantity must be 1..100")
    if not 0 <= score <= 10:
        raise ValueError("score must be 0..10")
    if not 2 <= len(name) <= 12:
        raise ValueError("name length must be 2..12")
    if category not in ("basic", "premium", "vip"):
        raise ValueError("invalid category")
    return f"{quantity}:{score:g}:{name}:{active}:{category}"


def validate_product_code(product_id: int, code: str) -> str:
    """Ví dụ int + string có regex; cấu hình code regex thành ^[A-Z]{2}\\d{4}$ trong BTG."""
    if product_id < 1:
        raise ValueError("product_id must be positive")
    if not re.fullmatch(r"[A-Z]{2}\d{4}", code):
        raise ValueError("code must contain two uppercase letters and four digits")
    return f"{product_id}:{code}"
