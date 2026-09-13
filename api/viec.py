"""Chay cong viec nen trong chinh tien trinh backend (LD-9).

Khong hang doi ngoai, khong WebSocket: `bao_tien_do` ghi vao bang `cong_viec`,
frontend hoi theo chu ky. Bang nay chi bao tien do, khong quyet dinh resume.
"""
from __future__ import annotations

import os
import threading
from contextlib import closing
from dataclasses import replace
from pathlib import Path

from pipeline import db, dieu_phoi
from pipeline.dieu_phoi import TuyChon

DB = Path("work") / "subtitles.db"

# cid -> (video, tuy_chon). Backend chay mot tien trinh nen dict la du; khoi dong
# lai server thi cong viec dang do mat, artifact tren dia van con de chay lai.
_HO_SO: dict[str, tuple[Path, TuyChon]] = {}
_KHOA = threading.Lock()


def ket_noi():
    """Mot ket noi cho mot request; api/ khong giu ket noi qua nhieu request."""
    with closing(db.mo(DB)) as con:
        yield con


def dat(cid: str, video: Path, tc: TuyChon) -> None:
    with _KHOA:
        _HO_SO[cid] = (Path(video), tc)


def lay(cid: str) -> tuple[Path, TuyChon] | None:
    with _KHOA:
        return _HO_SO.get(cid)


def dat_hop(cid: str, hop: list[dict] | dict | None, luu_nhom: bool = False) -> TuyChon:
    """Nhan hop da ve roi chay tiep: cache lam moi dung buoc vung mo va render."""
    video, tc = _HO_SO[cid]
    moi = replace(tc, blur="off", blur_box=None, luu_hop_nhom=False) if hop is None else \
        replace(tc, blur="on", blur_box=hop, luu_hop_nhom=luu_nhom)
    dat(cid, video, moi)
    return moi


def tao_goi(tc: TuyChon):
    """Khong co khoa thi tra None: cache dich van dung duoc, chi dich moi la loi."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not key.strip():
        return None
    from pipeline.translate import tao_goi as _tao
    return _tao(key, tc.model_dich)


def chay_nen(cid: str) -> None:
    """Tac vu nen: moi ket cuc deu ghi lai, khong de cong viec treo o dang_chay."""
    ho_so = lay(cid)
    if ho_so is None:
        return
    video, tc = ho_so
    with closing(db.mo(DB)) as con:
        def ghi(**cot: object) -> None:
            with con:
                db.cap_nhat_cong_viec(con, cid, **cot)

        def tien(buoc: str, ti_le: float) -> None:
            ghi(trang_thai="dang_chay", buoc=buoc, tien_do=float(ti_le))

        try:
            kq = dieu_phoi.chay(video, tc, tien, con=con, goi=tao_goi(tc))
        except FileExistsError as exc:      # lock cua LD-2, khong phai loi logic
            ghi(trang_thai="loi", loi=str(exc))
        except BaseException as exc:        # ngoai le nen phai thanh trang thai loi
            ghi(trang_thai="loi", loi=f"{type(exc).__name__}: {exc}")
        else:
            # cho_chon_khung giu nguyen tien do buoc cuoi da bao; dat cung mot con so
            # o day thi thanh tien do nhay lui khi buoc dich chay tiep sau do.
            ghi(trang_thai=kq.trang_thai,
                duong_dan_ra=str(kq.ra) if kq.ra else None,
                loi=f"giu nguon {len(kq.giu_nguon)} cue" if kq.giu_nguon else None,
                **({"tien_do": 1.0} if kq.ra else {}))
