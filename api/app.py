"""FastAPI: nhan request, validate, goi dieu_phoi, tra JSON.

CS-6 — file nay khong duoc goi ffmpeg, khong nap model, khong ghep filtergraph.
Bat gap mot trong ba thu do o day nghia la logic da ro ra khoi pipeline va CLI
voi web se cho ket qua khac nhau.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import sqlite3
import tempfile
import uuid
from contextlib import asynccontextmanager, closing
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
from pipeline.srt import (bam_file, chu_ky, doc_srt, gianh_khoa,
                          thu_muc_lam_viec)

DUOI_VIDEO = {".mp4", ".mkv", ".mov", ".webm", ".avi", ".ts"}
TOI_DA_BYTE = 4 * 1024**3
TAI_LEN = Path("work") / "tai_len"
NGUON = TAI_LEN / "nguon"
# Duoi co dinh: doi ten hay doi duoi file tai len khong duoc doi danh tinh tai
# nguyen. Kiem hop le van dua tren ten upload va noi dung qua ffprobe.
TEN_NGUON = "nguon.media"
WEB = Path(__file__).resolve().parent.parent / "web"


@asynccontextmanager
async def vong_doi(app: FastAPI):
    # LD-5: job khong-terminal cua tien trinh truoc khong con chu so huu; bao loi
    # co huong dan thay vi de frontend hoi mai mot cong viec da mat.
    with closing(db.mo(viec.DB)) as con:
        with con:
            db.don_cong_viec_mat_ho_so(con, viec.dang_theo_doi())
    yield


app = FastAPI(title="Dich phu de video Anh -> Viet", lifespan=vong_doi)
api = APIRouter(prefix="/api")
Con = Annotated[sqlite3.Connection, Depends(ket_noi)]


def _cong_viec(con: sqlite3.Connection, cid: str) -> sqlite3.Row:
    row = db.doc_cong_viec(con, cid)
    if row is None:
        raise HTTPException(404, "Khong co cong viec nay")      # khong lo duong dan
    return row


def _ho_so(cid: str) -> viec.HoSo:
    ho_so = viec.lay(cid)
    if ho_so is None:
        raise HTTPException(409, "Cong viec khong con trong tien trinh nay; tai video lai")
    return ho_so


def _snapshot(cid: str) -> Path:
    """Khung mau va ban sao cue cua rieng CID nay, khong dung chung voi CID khac."""
    return TAI_LEN / cid / "khung"


def _ten_sach(ten: str) -> str:
    sach = re.sub(r"[^\w.-]+", "_", Path(ten).stem, flags=re.UNICODE).strip("._")
    return sach[:80] or "video"


def _nhan_file(tep: UploadFile) -> tuple[Path, str, str]:
    """Ghi ra ngoai work/ truoc, ffprobe xong moi nhan: file rac khong o lai.

    Tra (file tam, SHA256 noi dung, ten goc da lam sach). Hash tinh theo khoi ngay
    luc ghi, khong nap ca file vao RAM.
    """
    ten = Path(tep.filename or "video.mp4").name
    if Path(ten).suffix.lower() not in DUOI_VIDEO:
        raise HTTPException(400, f"Chi nhan {', '.join(sorted(DUOI_VIDEO))}")
    fd, tam = tempfile.mkstemp(suffix=Path(ten).suffix)
    tam = Path(tam)
    bam = hashlib.sha256()
    try:
        with open(fd, "wb") as ra:
            do_lon = 0
            while khoi := tep.file.read(1 << 20):
                do_lon += len(khoi)
                if do_lon > TOI_DA_BYTE:
                    raise HTTPException(400, "File vuot qua gioi han 4 GiB")
                bam.update(khoi)
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
    return tam, bam.hexdigest(), _ten_sach(ten)


def _canonical(bam: str, nhom_ten: str | None) -> Path:
    """Mot tai nguyen xu ly cho moi cap (noi dung video, nhom) — DEC-1/LD-1.

    Nhom la mot phan cua danh tinh vi thuat ngu cua nhom lam doi ban dich; `None`
    la namespace rieng, khong phai chuoi "None". CID van la UUID moi moi lan.
    """
    return NGUON / chu_ky(["nhom", nhom_ten])[:16] / bam / TEN_NGUON


def _cong_bo(tam: Path, dich: Path, bam: str) -> None:
    """Dua file da validate vao dung cho canonical; da co thi phai chung minh trung."""
    dich.parent.mkdir(parents=True, exist_ok=True)
    if dich.is_file():
        if bam_file(dich) != bam:
            raise HTTPException(409, "Nguon da luu khong khop noi dung vua tai len; "
                                     "kiem tra thu muc work truoc khi chay lai")
        tam.unlink(missing_ok=True)
        return
    shutil.move(str(tam), dich)


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
    nhom_ten = nhom_ten or None
    if nhom_ten is not None and not nhom_ten.strip():
        raise HTTPException(400, "Ten nhom khong duoc chi gom khoang trang")
    hop = None
    if blur_box:
        from pipeline.markbox import kiem_hop, tach_hop
        try:
            hop = kiem_hop(tach_hop(blur_box))
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from None

    tam, bam, ten_goc = _nhan_file(tep)
    video = _canonical(bam, nhom_ten)
    try:
        # Gianh claim TRUOC khi cong bo nguon: kiem `.lock.exists()` roi tao sau
        # khong phai claim nguyen tu, hai upload cung luc se cung di qua (LD-6).
        khoa = gianh_khoa(thu_muc_lam_viec(video))
    except FileExistsError:
        tam.unlink(missing_ok=True)
        raise HTTPException(409, "Da co tien trinh dang xu ly video nay") from None
    cid = None
    try:
        _cong_bo(tam, video, bam)
        cid = str(uuid.uuid4())
        tc = TuyChon(nhom=nhom_ten, lang=lang, model=model, model_dich=model_dich,
                     blur=blur, blur_box=hop, font_scale=font_scale, separate=separate,
                     vad=vad, force_asr=force_asr, force=force,
                     # Ket qua va khung mau rieng tung CID: hai luot cung mot video
                     # khong ghi de output cua nhau.
                     ra=TAI_LEN / cid / f"{ten_goc}_vi.mp4",
                     thu_muc_khung=TAI_LEN / cid / "khung")
        viec.dat(cid, video, tc, khoa)
        with con:
            db.tao_cong_viec(con, cid)
        # Xep lich nam TRONG try: that bai o day ma khong don thi claim con lai
        # tren dia va job nam mai o `cho` khong bao gio co ai chay.
        nen.add_task(viec.chay_nen, cid)
    except BaseException:
        tam.unlink(missing_ok=True)
        khoa.unlink(missing_ok=True)
        if cid is not None:
            # Job da ghi vao DB roi thi khong duoc de no nam mai o `cho`: khong con
            # claim va khong con task nao se nhan no (LD-5).
            viec.nha_claim(cid)
            with con:
                db.cap_nhat_cong_viec(con, cid, trang_thai="loi",
                                      loi="Khong xep duoc lich xu ly; hay tai video lai")
        raise
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
    snap = _snapshot(cid)
    goc = snap / "sub_goc.srt"
    if not goc.is_file():
        raise HTTPException(409, "Chua co phu de goc nen chua trich duoc khung")
    from pipeline.markbox import moc_khung
    return [m for m in moc_khung(doc_srt(goc))
            if (snap / f"khung_{m['i']}.png").is_file()]


@api.get("/cong-viec/{cid}/khung/{i}")
def mot_khung(con: Con, cid: str, i: int) -> FileResponse:
    _cong_viec(con, cid)
    _ho_so(cid)
    path = _snapshot(cid) / f"khung_{i}.png"
    if not path.is_file():
        raise HTTPException(404, "Khong co khung nay")
    return FileResponse(path, media_type="image/png")


@api.post("/cong-viec/{cid}/hop")
def nhan_hop(con: Con, cid: str, nen: BackgroundTasks,
             than: Annotated[dict, Body()]) -> dict:
    """Nhan hop da ve roi chay tiep tu buoc dich. Bo qua ve = blur off."""
    row = _cong_viec(con, cid)
    if row["trang_thai"] == "dang_chay":
        raise HTTPException(409, "Cong viec dang chay, doi no dung roi gui hop")
    ho_so = _ho_so(cid)
    cp = ho_so.checkpoint
    if not isinstance(cp, dict) or not cp.get("ky_cue"):
        raise HTTPException(409, "Cong viec chua di den buoc chon vung; tai video lai")
    goc = thu_muc_lam_viec(ho_so.video) / "sub_goc.srt"
    if not goc.is_file() or bam_file(goc) != cp["ky_cue"]:
        # LD-4: chi so cau thoai cua vung chi co nghia tren dung bo cue da chup.
        raise HTTPException(409, "Phu de goc da doi so voi luc chon vung; "
                                 "tai video lai va chon lai vung")
    from pipeline.markbox import VANG_MAT, kiem_che_do, kiem_vung
    # So cue lay tu dung ban snapshot ma nguoi dung vua ve len, khong phai tu ban
    # sub_goc dung chung co the da bi CID khac lam moi.
    snap = _snapshot(cid) / "sub_goc.srt"
    if not snap.is_file():
        raise HTTPException(409, "Khong con khung mau cua lan chon vung nay; tai video lai")
    vung = None
    try:
        for ten in ("co_blur", "luu_nhom"):
            if ten in than and not isinstance(than[ten], bool):
                raise ValueError(f"{ten} phai la boolean")
        # Mode duoc kiem ca khi bo qua lam mo, va chi so cau thoai duoc kiem ngay o
        # day: sai pham nao cung phai thanh 400 TRUOC khi job/nhom/artifact doi
        # trang thai, chu khong vo ra trong tac vu nen (LD-7a).
        che_do = kiem_che_do(than.get("che_do_vung", VANG_MAT))
        if than.get("co_blur", True):
            # `vung` la danh sach hop kem cue; thieu thi coi than la mot hop cho moi cau.
            vung = kiem_vung(than.get("vung", than), so_cue=len(doc_srt(snap)),
                             che_do=che_do)                  # validator LD-8 cua CLI
    except (ValueError, TypeError) as exc:
        raise HTTPException(400, str(exc)) from None
    try:
        # Tieu thu checkpoint: POST thu hai cho cung luot se ra 409 o day chu khong
        # tao task thu hai roi lam hong trang thai cua luot dang chay (LD-6).
        viec.dat_hop(cid, vung, than.get("luu_nhom", False), che_do)
    except (KeyError, LookupError):
        raise HTTPException(409, "Cong viec nay khong con cho ve vung; tai video lai") from None
    try:
        with con:
            db.cap_nhat_cong_viec(con, cid, trang_thai="cho", loi=None)
        nen.add_task(viec.chay_nen, cid)
    except BaseException:
        # Khong xep lich duoc thi tra checkpoint lai de nguoi dung con gui vung lan nua.
        viec.tra_checkpoint(cid, cp)
        raise
    return {"id": cid, "trang_thai": "cho", "vung": vung, "che_do_vung": che_do}


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
