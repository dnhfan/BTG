"""File mau de test tinh nang "Mo file .py" (FR-1.3) cua BTG.

Cach test:
1. Mo app BTG -> muc FILE PYTHON -> "Mo file .py" -> chon file nay.
2. Dropdown se liet ke 4 ham duoi day -> chon 1 ham -> "Dien vao form".
3. Form tu dien: ten ham, tham so, type hint (Literal -> enum).
4. Bam "Sinh Test Case", sau do "Run Tests" (file nay dong vai tro
   hàm tham chiếu luon vi cac ham da duoc cai dat day du).

Du kien khi vua nap xong (chua sua Min/Max, chi bat EP + BVA),
va Run Tests se Pass 100% vi file nay lam hàm tham chiếu luon:
- tinh_tien_thue : 10 test case
- kiem_tra_email :  9 test case
- xep_loai_hoc_luc:  9 test case
- tao_don_hang   : 19 test case
"""
from typing import Literal


def tinh_tien_thue(gia: float, khu_vuc: Literal["noi_thanh", "ngoai_thanh"]) -> float:
    """Thue: noi thanh 10%, ngoai thanh 5%. Gia hop le: 0 .. 1_000_000."""
    if gia is None:
        raise TypeError("gia must not be None")
    if gia < 0 or gia > 1_000_000:
        raise ValueError("gia out of range")
    if khu_vuc not in ("noi_thanh", "ngoai_thanh"):
        raise ValueError("invalid khu_vuc")
    return gia * (0.10 if khu_vuc == "noi_thanh" else 0.05)


def kiem_tra_email(email: str) -> bool:
    """Email hop le: dai 5..50 ky tu, co '@' va dau '.' sau '@'."""
    if email is None:
        raise TypeError("email must not be None")
    if not (5 <= len(email) <= 50):
        return False
    if "@" not in email:
        return False
    return "." in email.split("@", 1)[1]


def xep_loai_hoc_luc(diem: float, chuyen_can: bool) -> str:
    """Diem 0..10. >=8: Gioi, >=6.5: Kha, >=5: Trung binh, con lai: Yeu.
    Khong chuyen can thi ha 1 bac (tru khi dang o Yeu)."""
    if diem is None:
        raise TypeError("diem must not be None")
    if diem < 0 or diem > 10:
        raise ValueError("diem out of range")
    if diem >= 8:
        loai = "Gioi"
    elif diem >= 6.5:
        loai = "Kha"
    elif diem >= 5:
        loai = "Trung binh"
    else:
        loai = "Yeu"
    if not chuyen_can and loai != "Yeu":
        loai = {"Gioi": "Kha", "Kha": "Trung binh",
                "Trung binh": "Yeu"}[loai]
    return loai


def tao_don_hang(san_pham: str, so_luong: int,
                 loai_khach: Literal["thuong", "vip", "sieu_vip"],
                 giao_nhanh: bool) -> str:
    """Tao don hang: ten san pham 2..30 ky tu, so luong 1..100."""
    if not san_pham or not (2 <= len(san_pham) <= 30):
        raise ValueError("ten san pham phai dai 2..30 ky tu")
    if so_luong is None:
        raise TypeError("so_luong must not be None")
    if so_luong < 1 or so_luong > 100:
        raise ValueError("so_luong must be 1..100")
    if loai_khach not in ("thuong", "vip", "sieu_vip"):
        raise ValueError("invalid loai_khach")
    return (f"{san_pham} x{so_luong} [{loai_khach}] "
            f"{'giao nhanh' if giao_nhanh else 'giao thuong'}")
