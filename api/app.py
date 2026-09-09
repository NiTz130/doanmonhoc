"""FastAPI: nhan request, validate, goi dieu_phoi, tra JSON.

CS-6 — file nay khong duoc goi ffmpeg, khong nap model, khong ghep filtergraph.
Bat gap mot trong ba thu do o day nghia la logic da ro ra khoi pipeline va CLI
voi web se cho ket qua khac nhau.
"""
from __future__ import annotations

import shutil
import sqlite3
import tempfile
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import (APIRouter, BackgroundTasks, Body, Depends, FastAPI, File,
                     Form, HTTPException, UploadFile)
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api import nhom, viec
from api.viec import ket_noi
from pipeline import db, dieu_phoi
from pipeline.dieu_phoi import TuyChon
from pipeline.srt import doc_srt, thu_muc_lam_viec

DUOI_VIDEO = {".mp4", ".mkv", ".mov", ".webm", ".avi", ".ts"}
TOI_DA_BYTE = 4 * 1024**3
TAI_LEN = Path("work") / "tai_len"
WEB = Path(__file__).resolve().parent.parent / "web"

app = FastAPI(title="Dich phu de video Anh -> Viet")
api = APIRouter(prefix="/api")
Con = Annotated[sqlite3.Connection, Depends(ket_noi)]


def _cong_viec(con: sqlite3.Connection, cid: str) -> sqlite3.Row:
    row = db.doc_cong_viec(con, cid)
    if row is None:
        raise HTTPException(404, "Khong co cong viec nay")      # khong lo duong dan
    return row


def _work(cid: str) -> Path:
    ho_so = viec.lay(cid)
    if ho_so is None:
        raise HTTPException(409, "Cong viec khong con trong tien trinh nay; tai video lai")
    return thu_muc_lam_viec(ho_so[0])


def _nhan_file(tep: UploadFile, cid: str) -> Path:
    """Ghi ra ngoai work/ truoc, ffprobe xong moi chuyen vao: file rac khong o lai."""
    ten = Path(tep.filename or "video.mp4").name
    if Path(ten).suffix.lower() not in DUOI_VIDEO:
        raise HTTPException(400, f"Chi nhan {', '.join(sorted(DUOI_VIDEO))}")
    fd, tam = tempfile.mkstemp(suffix=Path(ten).suffix)
    tam = Path(tam)
    try:
        with open(fd, "wb") as ra:
            do_lon = 0
            while khoi := tep.file.read(1 << 20):
                do_lon += len(khoi)
                if do_lon > TOI_DA_BYTE:
                    raise HTTPException(400, "File vuot qua gioi han 4 GiB")
                ra.write(khoi)
            if do_lon == 0:
                raise HTTPException(400, "File rong")
        dieu_phoi.nhan_dien(tam)            # validator video duy nhat: ffprobe
    except HTTPException:
        tam.unlink(missing_ok=True)
        raise
    except Exception as exc:
        tam.unlink(missing_ok=True)
        raise HTTPException(400, f"Khong doc duoc file video: {exc}") from None
    dich = TAI_LEN / cid / ten
    dich.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(tam), dich)
    return dich


@api.post("/video", status_code=202)
def tai_len(
    con: Con,
    nen: BackgroundTasks,
    tep: Annotated[UploadFile, File(alias="file")],
    nhom_ten: Annotated[str | None, Form(alias="nhom")] = None,
    lang: Annotated[str, Form()] = "en",
    model: Annotated[str, Form()] = "large-v3",
    model_dich: Annotated[str, Form()] = "deepseek-v4-flash",
    blur: Annotated[str, Form()] = "auto",
    blur_box: Annotated[str | None, Form()] = None,
    font_scale: Annotated[float, Form()] = 0.42,
    separate: Annotated[bool, Form()] = False,
    vad: Annotated[bool, Form()] = True,
    force_asr: Annotated[bool, Form()] = False,
    force: Annotated[bool, Form()] = False,
) -> dict:
    if blur not in {"auto", "on", "off"}:
        raise HTTPException(400, "blur phai la auto, on hoac off")
    hop = None
    if blur_box:
        from pipeline.markbox import kiem_hop, tach_hop
        try:
            hop = kiem_hop(tach_hop(blur_box))
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from None
    cid = str(uuid.uuid4())
    video = _nhan_file(tep, cid)
    if (thu_muc_lam_viec(video) / ".lock").exists():
        # Cung mot lock cua LD-2, khong co hang doi thu hai: mot video mot luc.
        raise HTTPException(409, "Da co tien trinh dang xu ly video nay")
    tc = TuyChon(nhom=nhom_ten or None, lang=lang, model=model, model_dich=model_dich,
                 blur=blur, blur_box=hop, font_scale=font_scale, separate=separate, vad=vad,
                 force_asr=force_asr, force=force)
    viec.dat(cid, video, tc)
    with con:
        db.tao_cong_viec(con, cid)
    nen.add_task(viec.chay_nen, cid)
    return {"id": cid, "trang_thai": "cho"}


@api.get("/cong-viec/{cid}")
def trang_thai(con: Con, cid: str) -> dict:
    row = _cong_viec(con, cid)
    return {"id": row["id"], "trang_thai": row["trang_thai"], "buoc": row["buoc"],
            "tien_do": row["tien_do"], "loi": row["loi"],
            "co_ket_qua": bool(row["duong_dan_ra"])}


@api.get("/cong-viec/{cid}/khung")
def khung(con: Con, cid: str) -> list[dict]:
    """Danh sach khung mau kem moc thoi gian va cau thoai de frontend hien len."""
    _cong_viec(con, cid)
    work = _work(cid)
    goc = work / "sub_goc.srt"
    if not goc.is_file():
        raise HTTPException(409, "Chua co phu de goc nen chua trich duoc khung")
    from pipeline.markbox import moc_khung
    return [m for m in moc_khung(doc_srt(goc))
            if (work / f"khung_{m['i']}.png").is_file()]


@api.get("/cong-viec/{cid}/khung/{i}")
def mot_khung(con: Con, cid: str, i: int) -> FileResponse:
    _cong_viec(con, cid)
    path = _work(cid) / f"khung_{i}.png"
    if not path.is_file():
        raise HTTPException(404, "Khong co khung nay")
    return FileResponse(path, media_type="image/png")


@api.post("/cong-viec/{cid}/hop")
def nhan_hop(con: Con, cid: str, nen: BackgroundTasks,
             than: Annotated[dict, Body()]) -> dict:
    """Nhan hop da ve roi chay tiep tu buoc ket xuat. Bo qua ve = blur off."""
    row = _cong_viec(con, cid)
    if row["trang_thai"] == "dang_chay":
        raise HTTPException(409, "Cong viec dang chay, doi no dung roi gui hop")
    hop = None
    if than.get("co_blur", True):
        from pipeline.markbox import kiem_hop
        try:
            hop = kiem_hop(than)                # dung validator LD-8 cua CLI
        except (ValueError, TypeError) as exc:
            raise HTTPException(400, str(exc)) from None
    viec.dat_hop(cid, hop)
    with con:
        db.cap_nhat_cong_viec(con, cid, trang_thai="cho", loi=None)
    nen.add_task(viec.chay_nen, cid)
    return {"id": cid, "trang_thai": "cho", "hop": hop}


@api.get("/cong-viec/{cid}/ket-qua")
def ket_qua(con: Con, cid: str) -> FileResponse:
    row = _cong_viec(con, cid)
    if not row["duong_dan_ra"] or not Path(row["duong_dan_ra"]).is_file():
        raise HTTPException(404, "Chua co video ket qua")
    path = Path(row["duong_dan_ra"])
    return FileResponse(path, media_type="video/mp4", filename=path.name)


app.include_router(api)
app.include_router(nhom.router)
if WEB.is_dir():
    app.mount("/", StaticFiles(directory=WEB, html=True), name="web")
