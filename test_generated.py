"""File test tu dong sinh boi Black-box Test Generator (BTG).
Ham duoc kiem thu: register(username, age, role, active)
"""
import pytest

# ===== Ham tham chieu / ham duoc kiem thu (nhung tu file nguoi dung) =====
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

# ===== Case khong mong doi exception =====
@pytest.mark.parametrize(
    "username,age,role,active,expected",
    [
        pytest.param('aaaaa', 50, 'admin', True, 'aaaaa:admin:active', id="TC_001"),  # [EP] Valid_Partition
        pytest.param('aaaaaaaaaaaaaaa', 50, 'admin', True, 'aaaaaaaaaaaaaaa:admin:active', id="TC_003"),  # [EP] Invalid_Partition_username_Too_Long
        pytest.param('aaaaa', 50, 'admin', None, 'aaaaa:admin:inactive', id="TC_010"),  # [EP] Invalid_Partition_active_Null
        pytest.param('aaaaaaaaa', 50, 'admin', True, 'aaaaaaaaa:admin:active', id="TC_013"),  # [BVA] username_MaxLen_Minus_1
        pytest.param('aaaaaaaaaa', 50, 'admin', True, 'aaaaaaaaaa:admin:active', id="TC_014"),  # [BVA] username_MaxLen
        pytest.param('aaaaaaaaaaa', 50, 'admin', True, 'aaaaaaaaaaa:admin:active', id="TC_015"),  # [BVA] username_MaxLen_Plus_1
    ],
)
def test_register_valid(username, age, role, active, expected):
    result = register(username, age, role, active)
    # Neu chua co oracle (expected = None) thi chi can ham chay khong loi
    if expected is not None:
        assert result == expected

# ===== Case mong doi exception =====
@pytest.mark.parametrize(
    "username,age,role,active,exc_name",
    [
        pytest.param('', 50, 'admin', True, 'ValueError', id="TC_002"),  # [EP] Invalid_Partition_username_Too_Short
        pytest.param(None, 50, 'admin', True, 'ValueError', id="TC_004"),  # [EP] Invalid_Partition_username_Null
        pytest.param('aaaaa', -1, 'admin', True, 'ValueError', id="TC_005"),  # [EP] Invalid_Partition_age_Below_Min
        pytest.param('aaaaa', 101, 'admin', True, 'ValueError', id="TC_006"),  # [EP] Invalid_Partition_age_Above_Max
        pytest.param('aaaaa', None, 'admin', True, 'TypeError', id="TC_007"),  # [EP] Invalid_Partition_age_Null
        pytest.param('aaaaa', 50, '__INVALID_ENUM__', True, 'ValueError', id="TC_008"),  # [EP] Invalid_Partition_role_Invalid_Enum
        pytest.param('aaaaa', 50, None, True, 'ValueError', id="TC_009"),  # [EP] Invalid_Partition_role_Null
        pytest.param('a', 50, 'admin', True, 'ValueError', id="TC_011"),  # [BVA] username_MinLen
        pytest.param('aa', 50, 'admin', True, 'ValueError', id="TC_012"),  # [BVA] username_MinLen_Plus_1
        pytest.param('aaaaa', 0, 'admin', True, 'ValueError', id="TC_016"),  # [BVA] age_Min
        pytest.param('aaaaa', 1, 'admin', True, 'ValueError', id="TC_017"),  # [BVA] age_Min_Plus_1
        pytest.param('aaaaa', 99, 'admin', True, 'ValueError', id="TC_018"),  # [BVA] age_Max_Minus_1
        pytest.param('aaaaa', 100, 'admin', True, 'ValueError', id="TC_019"),  # [BVA] age_Max
    ],
)
def test_register_raises(username, age, role, active, exc_name):
    exc_type = Exception if exc_name in ("Exception", None) else globals().get(exc_name, Exception)
    # Voi exception cu the (ValueError...), doi ten ben duoi neu ham nem loai khac
    with pytest.raises(Exception) as excinfo:
        register(username, age, role, active)
    if exc_name not in ("Exception", None):
        assert excinfo.type.__name__ == exc_name

