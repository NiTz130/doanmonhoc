"""Chay cong viec nen trong chinh tien trinh backend (LD-9).

Khong hang doi ngoai, khong WebSocket: `bao_tien_do` ghi vao bang `cong_viec`,
frontend hoi theo chu ky. Bang nay chi bao tien do, khong quyet dinh resume.
"""
from __future__ import annotations

import os
import threading
from contextlib import closing
from dataclasses import dataclass, replace
from pathlib import Path

from pipeline import db, dieu_phoi
from pipeline.dieu_phoi import TuyChon
from pipeline.srt import gianh_khoa, thu_muc_lam_viec

DB = Path("work") / "subtitles.db"


@dataclass
class HoSo:
    """Tat ca thu mot CID can de chay tiep, ke ca claim dang giu.

    `checkpoint` do dieu_phoi tra ve luc dung o `cho_chon_khung`; no la ban ghi
    phia server, khong bao gio duoc dung tu than request (LD-3).
    """
    video: Path
    tc: TuyChon
    khoa: Path | None = None
    checkpoint: dict | None = None


# cid -> HoSo. Backend chay mot tien trinh nen dict la du; khoi dong lai server
# thi cong viec dang do mat (LD-5 bao ro), artifact tren dia van con.
_HO_SO: dict[str, HoSo] = {}
_KHOA = threading.Lock()


def ket_noi():
    """Mot ket noi cho mot request; api/ khong giu ket noi qua nhieu request.

    `cung_thread=False` vi Starlette co the doi thread giua cac phan cua cung mot
    request sync; connection van khong roi khoi request nay (LD-2).
    """
    with closing(db.mo(DB, cung_thread=False)) as con:
        yield con


def dat(cid: str, video: Path, tc: TuyChon, khoa: Path | None = None) -> None:
    with _KHOA:
        _HO_SO[cid] = HoSo(Path(video), tc, khoa)


def lay(cid: str) -> HoSo | None:
    with _KHOA:
        return _HO_SO.get(cid)


def dang_theo_doi() -> set[str]:
    with _KHOA:
        return set(_HO_SO)


def _cap_nhat(cid: str, **truong: object) -> None:
    with _KHOA:
        ho_so = _HO_SO.get(cid)
        if ho_so is not None:
            for k, v in truong.items():
                setattr(ho_so, k, v)


def dat_hop(cid: str, hop: list[dict] | dict | None, luu_nhom: bool = False,
            che_do_vung: str = "cong_them") -> TuyChon:
    """Nhan hop da ve roi chay tiep DUNG luot cu, khong phai mo mot luot moi.

    LD-3: ghim lai nguon phu de da chon va bo co force cua luot truoc, nen gui hop
    khong lam ASR chay lai; y dinh lam moi ban dich thi giu trong `force_dich` cho
    den khi buoc dich cua chinh luot do chay xong.
    """
    # Tieu thu checkpoint NGUYEN TU: hai POST vung den cung luc deu thay job o
    # `cho_chon_khung` va deu di qua duoc, roi task thu hai truot claim va ghi de
    # trang thai `loi` len chinh luot dang chay tot (LD-6). Cho duy nhat lam viec
    # nay dung la o day, duoi `_KHOA` da co san.
    with _KHOA:
        ho_so = _HO_SO.get(cid)
        if ho_so is None:
            raise KeyError(cid)
        cp = ho_so.checkpoint
        if not isinstance(cp, dict) or not cp.get("ky_cue"):
            raise LookupError("Khong co ho so buoc chon vung cho cong viec nay")
        ho_so.checkpoint = None
    moi = replace(
        ho_so.tc,
        blur="off" if hop is None else "on",
        blur_box=hop,
        luu_hop_nhom=False if hop is None else luu_nhom,
        che_do_vung=che_do_vung,
        force=False, force_asr=False,
        nguon_sub=cp.get("nguon_sub"),
        force_dich=bool(cp.get("force_dich")),
        ky_cue=cp["ky_cue"],
    )
    _cap_nhat(cid, tc=moi)
    return moi


def tra_checkpoint(cid: str, cp: dict) -> None:
    """Hoan lai checkpoint khi lenh chay tiep khong duoc xep lich: nguoi dung con ve lai."""
    _cap_nhat(cid, checkpoint=cp)


def nha_claim(cid: str) -> None:
    """Quen claim da trao cho CID nay; caller tu xoa file lock."""
    _cap_nhat(cid, khoa=None)


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
    video, tc = ho_so.video, ho_so.tc
    with closing(db.mo(DB)) as con:
        def ghi(**cot: object) -> None:
            with con:
                db.cap_nhat_cong_viec(con, cid, **cot)

        def tien(buoc: str, ti_le: float) -> None:
            ghi(trang_thai="dang_chay", buoc=buoc, tien_do=float(ti_le))

        # Luot dau duoc trao claim tu luc nhan upload (khong co khe ho); luot tiep
        # tuc sau khi nguoi dung ve xong phai gianh lai, vi claim da duoc nha ra
        # trong luc cho nguoi (LD-6).
        khoa = ho_so.khoa
        if khoa is None:
            try:
                khoa = gianh_khoa(thu_muc_lam_viec(video))
            except FileExistsError as exc:
                ghi(trang_thai="loi", loi=str(exc))
                return
            _cap_nhat(cid, khoa=khoa)
        try:
            kq = dieu_phoi.chay(video, tc, tien, con=con, goi=tao_goi(tc), da_khoa=True)
        except BaseException as exc:        # ngoai le nen phai thanh trang thai loi
            ghi(trang_thai="loi", loi=f"{type(exc).__name__}: {exc}")
        else:
            if kq.checkpoint:
                _cap_nhat(cid, checkpoint=kq.checkpoint)
            # cho_chon_khung giu nguyen tien do buoc cuoi da bao; dat cung mot con so
            # o day thi thanh tien do nhay lui khi buoc dich chay tiep sau do.
            ghi(trang_thai=kq.trang_thai,
                duong_dan_ra=str(kq.ra) if kq.ra else None,
                loi=f"giu nguon {len(kq.giu_nguon)} cue" if kq.giu_nguon else None,
                **({"tien_do": 1.0} if kq.ra else {}))
        finally:
            # Nha claim o moi loi ra, ke ca khi dung cho nguoi ve hop.
            khoa.unlink(missing_ok=True)
            _cap_nhat(cid, khoa=None)
