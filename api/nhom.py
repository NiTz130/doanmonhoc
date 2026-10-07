"""Route nhom, thuat ngu va khung mac dinh.

Router rieng de phan viec nay khong phai sua `api/app.py`. Khong goi `pipeline/db.py`
truc tiep: moi truy van di qua `dieu_phoi`, nen CLI va web khong the lech nhau.

Danh sach giu nguyen dang body cu (mang / object); tong so ban ghi truoc khi cat trang
nam o header `X-Tong-So`, de frontend cu khong vo.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Response

from api.viec import ket_noi
from pipeline import dieu_phoi
from pipeline.dieu_phoi import DangBan, KhongCo

router = APIRouter(prefix="/api/nhom", tags=["nhom"])
Con = Annotated[sqlite3.Connection, Depends(ket_noi)]


@contextmanager
def loi_http(*them: type[Exception]):
    """Mot cho duy nhat doi loi nghiep vu thanh ma HTTP: ValueError 400, KhongCo 404, DangBan 409."""
    try:
        yield
    except KhongCo as exc:
        raise HTTPException(404, str(exc)) from None
    except DangBan as exc:
        raise HTTPException(409, str(exc)) from None
    except (ValueError, TypeError, *them) as exc:
        raise HTTPException(400, str(exc)) from None


def liet_ke(res: Response, ham, *a, **kw):
    """Chay ham liet ke (tra (du lieu, tong)), dat X-Tong-So, tra du lieu."""
    with loi_http():
        du_lieu, tong = ham(*a, **kw)
    res.headers["X-Tong-So"] = str(tong)
    return du_lieu


@router.get("")
def danh_sach(con: Con, res: Response, q: str | None = None, sap_xep: str = "ten",
              thu_tu: str = "asc", trang: int = 1, moi_trang: int = 50) -> list[dict]:
    return liet_ke(res, dieu_phoi.nhom_tim, con, q=q, sap_xep=sap_xep, thu_tu=thu_tu,
                   trang=trang, moi_trang=moi_trang)


@router.post("", status_code=201)
def tao(con: Con, ten: Annotated[str, Body(embed=True)]) -> dict:
    with loi_http():
        with con:
            dieu_phoi.nhom_tao(con, ten)
    return {"ten": ten}


@router.delete("/{ten}", status_code=204)
def xoa(con: Con, ten: str) -> Response:
    with loi_http():
        with con:
            dieu_phoi.nhom_xoa(con, ten)
    return Response(status_code=204)


@router.get("/{ten}/thuat-ngu")
def doc_thuat_ngu(con: Con, res: Response, ten: str, q: str | None = None,
                  sap_xep: str = "goc", thu_tu: str = "asc", trang: int = 1,
                  moi_trang: int = 50) -> dict[str, str]:
    return liet_ke(res, dieu_phoi.nhom_thuat_ngu_tim, con, ten, q=q, sap_xep=sap_xep,
                   thu_tu=thu_tu, trang=trang, moi_trang=moi_trang)


@router.post("/{ten}/thuat-ngu")
def dat_thuat_ngu(con: Con, ten: str, than: Annotated[dict, Body()]) -> dict[str, str]:
    with loi_http(sqlite3.IntegrityError):
        with con:
            dieu_phoi.nhom_dat_thuat_ngu(con, ten, than.get("goc"), than.get("dich"))
            return dieu_phoi.nhom_thuat_ngu(con, ten)


@router.delete("/{ten}/thuat-ngu/{goc}", status_code=204)
def xoa_thuat_ngu(con: Con, ten: str, goc: str) -> Response:
    with loi_http():
        with con:
            dieu_phoi.nhom_xoa_thuat_ngu(con, ten, goc)
    return Response(status_code=204)


@router.get("/{ten}/hop")
def doc_hop(con: Con, ten: str) -> dict | None:
    with loi_http():
        return dieu_phoi.nhom_hop(con, ten)


@router.post("/{ten}/hop")
def dat_hop(con: Con, ten: str, than: Annotated[dict, Body()]) -> dict:
    """Hop di qua dung validator cua CLI; frontend kiem them chi de bao som."""
    with loi_http(KeyError):
        with con:
            return dieu_phoi.nhom_dat_hop(con, ten, than,
                                          int(than.get("W", 1920)), int(than.get("H", 1080)))
