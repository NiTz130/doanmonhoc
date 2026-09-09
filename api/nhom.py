"""Route nhom, thuat ngu va khung mac dinh.

Router rieng de phan viec nay khong phai sua `api/app.py`. Khong goi `pipeline/db.py`
truc tiep: moi truy van di qua `dieu_phoi`, nen CLI va web khong the lech nhau.
"""
from __future__ import annotations

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException

from api.viec import ket_noi
from pipeline import dieu_phoi

router = APIRouter(prefix="/api/nhom", tags=["nhom"])
Con = Annotated[sqlite3.Connection, Depends(ket_noi)]


def _400(exc: Exception) -> HTTPException:
    return HTTPException(400, str(exc))


@router.get("")
def danh_sach(con: Con) -> list[dict]:
    return dieu_phoi.nhom_danh_sach(con)


@router.post("", status_code=201)
def tao(con: Con, ten: Annotated[str, Body(embed=True)]) -> dict:
    try:
        with con:
            dieu_phoi.nhom_tao(con, ten)
    except (ValueError, TypeError) as exc:
        raise _400(exc) from None
    return {"ten": ten}


@router.get("/{ten}/thuat-ngu")
def doc_thuat_ngu(con: Con, ten: str) -> dict[str, str]:
    try:
        with con:
            return dieu_phoi.nhom_thuat_ngu(con, ten)
    except (ValueError, TypeError) as exc:
        raise _400(exc) from None


@router.post("/{ten}/thuat-ngu")
def dat_thuat_ngu(con: Con, ten: str, than: Annotated[dict, Body()]) -> dict[str, str]:
    try:
        with con:
            dieu_phoi.nhom_dat_thuat_ngu(con, ten, than.get("goc"), than.get("dich"),
                                         bool(than.get("khoa")))
            return dieu_phoi.nhom_thuat_ngu(con, ten)
    except (ValueError, TypeError, sqlite3.IntegrityError) as exc:
        raise _400(exc) from None


@router.get("/{ten}/hop")
def doc_hop(con: Con, ten: str) -> dict | None:
    try:
        with con:
            return dieu_phoi.nhom_hop(con, ten)
    except (ValueError, TypeError) as exc:
        raise _400(exc) from None


@router.post("/{ten}/hop")
def dat_hop(con: Con, ten: str, than: Annotated[dict, Body()]) -> dict:
    """Hop di qua dung validator cua CLI; frontend kiem them chi de bao som."""
    try:
        with con:
            return dieu_phoi.nhom_dat_hop(con, ten, than,
                                          int(than.get("W", 1920)), int(than.get("H", 1080)))
    except (ValueError, TypeError, KeyError) as exc:
        raise _400(exc) from None
