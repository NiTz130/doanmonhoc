"""Dieu phoi sau buoc cho ca CLI lan API. Chi file nay duoc goi db.py."""
from __future__ import annotations

import importlib
import json
import logging
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from pipeline import db
from pipeline.srt import (Cue, bam_file, chu_ky, doc_json, doc_srt, ghi_json,
                          khoa_work, thu_muc_lam_viec)

# Tang khi doi cach sinh artifact cua mot buoc: moi manifest cu thanh cache miss.
VER = {"audio": 1, "sub_goc": 1, "sub_vi": 1, "vung_blur": 2}
PROMPT_VER = 2                          # doi prompt phai lam moi moi ban dich cu
HAU_TO = "_vi.mp4"
MANIFEST = "trang_thai.json"
# Duoi nguong nay coi nhu nhan dang hong, khong phai video it thoai.
TI_LE_PHU_TOI_THIEU = 0.25


def _nap(ten: str):
    """Nap module xu ly muon; test thay ham nay bang ban gia."""
    return importlib.import_module(f"pipeline.{ten}")


@dataclass(frozen=True)
class TuyChon:
    """Mot bo tuy chon duy nhat cho CLI va than request API."""
    nhom: str | None = None
    lang: str = "en"
    model: str = "large-v3"
    model_dich: str = "deepseek-v4-flash"
    blur: str = "auto"                      # auto | on | off
    # Mot dict = mot hop cho moi cau (CLI, khung nhom); danh sach = hop gan cue rieng.
    blur_box: dict[str, float] | list[dict] | None = None
    luu_hop_nhom: bool = False           # hop nay co thanh mac dinh cua nhom khong
    font_scale: float = 0.42
    separate: bool = False
    vad: bool = True                        # Silero VAD; tat khi video ca nhac
    force_asr: bool = False
    force: bool = False
    ra: Path | None = None


@dataclass
class KetQua:
    trang_thai: str                         # xong | suy_giam | cho_chon_khung
    work: Path
    ra: Path | None = None
    khung: list[Path] = field(default_factory=list)
    giu_nguon: list[int] = field(default_factory=list)


class ChoChonKhung(Exception):
    """Chua co hop blur: khong phai loi, caller quyet dinh cho hay dung."""

    def __init__(self, khung: list[Path]) -> None:
        super().__init__("Chua co vung lam mo cho video nay")
        self.khung = khung


def nhan_dien(video: Path) -> tuple[int, int, float]:
    ket = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-show_entries", "format=duration",
         "-of", "json", str(Path(video).resolve())],
        check=True, capture_output=True, text=True)
    d = json.loads(ket.stdout)
    if not d.get("streams"):
        raise ValueError(f"Khong tim thay luong video trong {video}")
    s = d["streams"][0]
    return int(s["width"]), int(s["height"]), float(d["format"]["duration"])


# ---------------------------------------------------------------- manifest

def _doc_manifest(work: Path) -> dict:
    return doc_json(work / MANIFEST)


def _ghi_manifest(work: Path, buoc: str, ky: str, artifact: Path, **them) -> None:
    """Ghi sau artifact: crash o giua chi gay cache miss, khong bao xong nham."""
    m = _doc_manifest(work)
    m[buoc] = {"ver": VER[buoc], "ky": ky, "hash": bam_file(artifact), **them}
    ghi_json(work / MANIFEST, m)


def _cache(work: Path, buoc: str, ky: str, artifact: Path) -> dict | None:
    """Tra ban ghi manifest khi artifact con nguyen ven va dung chu ky."""
    m = _doc_manifest(work).get(buoc)
    if not isinstance(m, dict) or m.get("ver") != VER[buoc] or m.get("ky") != ky:
        return None
    if not Path(artifact).is_file() or m.get("hash") != bam_file(artifact):
        return None
    return m


# ---------------------------------------------------------------- tung buoc

def _buoc_audio(video: Path, work: Path, tc: TuyChon, bam: Callable[[Path], str]) -> Path:
    ra = work / ("vocals.wav" if tc.separate else "audio.wav")
    ky = chu_ky(["audio", bam(video), tc.separate])
    if not tc.force and _cache(work, "audio", ky, ra):
        return ra
    that = Path(_nap("audio").tach(video, work / "audio.wav", tc.separate))
    _ghi_manifest(work, "audio", ky, that)
    return that


def _nguon_sub(video: Path, tc: TuyChon, bam: Callable[[Path], str]) -> tuple[str, str]:
    """Chon nguon phu de goc truoc khi ky, de doi nguon lam moi cache."""
    if tc.force_asr:
        return "asr", ""
    subs = _nap("subs")
    sidecar = subs.tim_sidecar(video, tc.lang)
    if sidecar is not None:
        return "sidecar", bam(sidecar)
    if any(t.get("codec_name") in subs.CODEC_CHU for t in subs.probe_subs(video)):
        return "nhung", bam(video)
    return "asr", ""


def _buoc_sub_goc(video: Path, work: Path, tc: TuyChon,
                  bam: Callable[[Path], str]) -> tuple[Path, str]:
    ra = work / "sub_goc.srt"
    che_do, phu_thuoc = _nguon_sub(video, tc, bam)
    wav = None
    if che_do == "asr":
        wav = _buoc_audio(video, work, tc, bam)     # resume --separate dung dung vocals
        phu_thuoc = bam(wav)
    ky = chu_ky(["sub_goc", che_do, phu_thuoc, tc.lang, tc.model, tc.vad])
    # force_asr bo cache sub goc moi lan duoc truyen, ke ca khi noi dung trung.
    if not (tc.force or tc.force_asr) and _cache(work, "sub_goc", ky, ra):
        return ra, che_do
    if che_do == "asr":
        _nap("asr").nhan_dang(wav, ra, tc.lang, tc.model, vad=tc.vad)
    elif not _nap("subs").tim_phu_de(video, ra, tc.lang):
        raise RuntimeError(f"Mat nguon phu de giua chung: {video}")
    _ghi_manifest(work, "sub_goc", ky, ra)
    return ra, che_do


def _sua_tay(ra: Path, goc: list[Cue]) -> bool:
    """Ban dich sua tay duoc giu neu con du cue va dung moc thoi gian."""
    try:
        cues = doc_srt(ra)
    except (OSError, ValueError):
        return False
    return len(cues) == len(goc) and all(
        a.bat_dau == b.bat_dau and a.ket_thuc == b.ket_thuc for a, b in zip(cues, goc))


def _buoc_dich(work: Path, sub_goc: Path, cues: list[Cue], tc: TuyChon,
               glossary: dict[str, str], goi: Callable | None,
               bam: Callable[[Path], str],
               ap_dung: Callable[[str, dict], dict]) -> tuple[list[int], int, int]:
    ra = work / "sub_vi.srt"
    ky = chu_ky(["sub_vi", bam(sub_goc), tc.model_dich, PROMPT_VER, glossary])
    # --force-asr lam moi ban dich ke ca khi ASR sinh ra noi dung trung y het.
    cu = None if (tc.force or tc.force_asr) else _doc_manifest(work).get("sub_vi")
    if isinstance(cu, dict) and cu.get("ver") == VER["sub_vi"] and cu.get("ky") == ky and ra.is_file():
        if cu.get("hash") == bam_file(ra) or _sua_tay(ra, cues):
            # Crash sau artifact truoc khi ghi DB: hoan tat not phan ghi glossary.
            ap_dung(cu["hash"], cu.get("moi") or {})
            if cu.get("hash") != bam_file(ra):
                _ghi_manifest(work, "sub_vi", ky, ra, moi={}, sua_tay=True)
            return list(cu.get("giu_nguon") or []), 0, 0     # cache hit: khong ton token

    if goi is None:
        raise RuntimeError("Thieu DEEPSEEK_API_KEY nen khong dich duoc")
    kq = _nap("translate").dich([c.text for c in cues], glossary, goi)
    from pipeline.srt import ghi_srt
    ghi_srt([Cue(c.idx, c.bat_dau, c.ket_thuc, t) for c, t in zip(cues, kq.ban)], ra)
    _ghi_manifest(work, "sub_vi", ky, ra, moi=kq.thuat_ngu_moi, giu_nguon=kq.giu_nguon)
    # Sau khi ghi DB, doi baseline sang glossary that su cua nhom de lan sau khong
    # tu lam moi cache boi chinh nhung tu vua hoc (video le khong hoc gi, baseline giu nguyen).
    _ghi_manifest(work, "sub_vi",
                  chu_ky(["sub_vi", bam(sub_goc), tc.model_dich, PROMPT_VER,
                          ap_dung(bam_file(ra), kq.thuat_ngu_moi)]),
                  ra, moi={}, giu_nguon=kq.giu_nguon)
    return kq.giu_nguon, kq.token_vao, kq.token_ra


def _cue_cua(v: dict, cues: list[Cue]) -> list[Cue]:
    """cue=None nghia la hop ap cho moi cau; khong thi chi nhung cau duoc gan."""
    if v.get("cue") is None:
        return cues
    return [cues[i] for i in v["cue"] if i < len(cues)]


def _hop_chung(vung: list[dict]) -> dict[str, float]:
    """Khung mac dinh nhom lay hop chinh, dung quy tac render dung cho kieu chu."""
    chung = _nap("markbox").hop_chinh(vung)
    return {k: chung[k] for k in "xywh"}


def _buoc_hop(video: Path, work: Path, tc: TuyChon, W: int, H: int, cues: list[Cue],
              bam: Callable[[Path], str], hop_nhom: dict | None,
              luu_nhom: Callable[[dict], None]) -> list[dict]:
    """Co flags duoc xet truoc cache, nen doi --blur khong bi JSON cu che."""
    ra = work / "vung_blur.json"
    kiem = _nap("markbox").kiem_vung
    if tc.blur == "off" or (tc.blur == "auto" and W / H < 1.2):
        ghi_json(ra, {"co_blur": False})       # khong xoa hop cua nhom
        return []
    ky = chu_ky(["vung_blur", bam(video), W, H])
    if tc.blur_box is not None:
        vung = kiem(tc.blur_box, W, H, len(cues))
        if tc.luu_hop_nhom:             # ve hop cho mot video khong am tham doi ca nhom
            luu_nhom(_hop_chung(vung))
    else:
        # Hop rieng cua video thang hop mac dinh cua nhom: no duoc ve tren dung khung
        # hinh nay, con hop nhom chi la diem khoi dau khi video chua co gi.
        cu = None if tc.force else _cache(work, "vung_blur", ky, ra)
        luu = doc_json(ra) if cu else {}
        if cu and luu.get("co_blur"):
            vung = kiem(luu["vung"], W, H, len(cues))
        elif hop_nhom is not None:
            vung = kiem(hop_nhom, W, H, len(cues))
        else:
            raise ChoChonKhung(_nap("markbox").trich_khung(video, cues, work))
    ghi_json(ra, {"co_blur": True, "vung": vung})
    _ghi_manifest(work, "vung_blur", ky, ra)
    return vung


# ---------------------------------------------------------------- luong chinh

def chay(video: Path, tuy_chon: TuyChon | None = None,
         bao_tien_do: Callable[[str, float], None] | None = None,
         con=None, goi: Callable | None = None) -> KetQua:
    """Chay tron mot video. API va CLI khac nhau dung mot cho: bao_tien_do."""
    video = Path(video)
    tc = tuy_chon or TuyChon()
    tien = bao_tien_do or (lambda buoc, ti_le: None)
    if not video.is_file():
        raise FileNotFoundError(f"Khong tim thay video: {video}")
    if not (isinstance(tc.font_scale, float | int) and tc.font_scale > 0):
        raise ValueError("font-scale phai la so duong")
    work = thu_muc_lam_viec(video)
    dong_db = con is None
    con = con or db.mo(Path("work") / "subtitles.db")
    try:
        with khoa_work(work):
            return _chay(video, work, tc, tien, con, goi)
    finally:
        if dong_db:
            con.close()


def _chay(video: Path, work: Path, tc: TuyChon, tien: Callable, con, goi) -> KetQua:
    dem: dict[Path, str] = {}

    def bam(path: Path) -> str:               # moi file bam dung mot lan mot luot
        path = Path(path)
        if path not in dem:
            dem[path] = bam_file(path)
        return dem[path]

    def nhat_ky(buoc: str, ket_qua: str, t0: float, loi: str | None = None,
                token_vao: int | None = None, token_ra: int | None = None) -> None:
        with con:
            db.ghi_nhat_ky(con, vid, buoc, ket_qua, round(time.monotonic() - t0, 3),
                           token_vao, token_ra, loi)

    tien("nhan_dien", 0.0)
    W, H, thoi_luong = nhan_dien(video)
    with con:
        nid = db.lay_nhom(con, tc.nhom) if tc.nhom else None
        vid = db.ghi_video(con, video, work, nid, W, H, thoi_luong)
        glossary = db.doc_thuat_ngu(con, nid) if nid else {}
        hop_nhom = db.doc_hop(con, nid) if nid else None

    tien("sub_goc", 0.1)
    t0 = time.monotonic()
    sub_goc, che_do = _buoc_sub_goc(video, work, tc, bam)
    cues = doc_srt(sub_goc)
    # Phu de phu qua it so voi thoi luong la hong im lang: video van xuat ra "xong"
    # nhung 90% khong co chu. Hay gap khi VAD coi nhac nen la khong phai tieng noi.
    phu = max(c.ket_thuc for c in cues) - min(c.bat_dau for c in cues)
    thieu = che_do == "asr" and thoi_luong > 0 and phu / thoi_luong < TI_LE_PHU_TOI_THIEU
    nhat_ky("sub_goc", "suy_giam" if thieu else ("xong" if che_do == "asr" else "bo_qua"), t0,
            f"phu de chi phu {phu:.0f}s / {thoi_luong:.0f}s" if thieu else None)
    if thieu:
        canh_bao = (f"Phu de nhan dang chi phu {phu:.0f}s trong {thoi_luong:.0f}s video "
                    f"({phu / thoi_luong:.0%}). Neu day la video ca nhac, chay lai voi "
                    f"--vad off (va --force-asr), hoac --separate de tach giong hat.")
        logging.warning(canh_bao)
        tien("canh_bao", 0.1)

    # Vung mo dung TRUOC buoc dich, du no chi can cue chu khong can ban dich: hop
    # do nguoi dung ve, nen dung o day thi nguoi dung ve xong ngay sau ASR thay vi
    # ngoi cho het ca buoc dich, va bo cuoc o man ve hop cung khong mat tien API.
    tien("vung_blur", 0.4)

    def luu_nhom(hop: dict) -> None:
        if nid:
            with con:
                db.ghi_hop(con, nid, hop)

    try:
        vung = _buoc_hop(video, work, tc, W, H, cues, bam, hop_nhom, luu_nhom)
    except ChoChonKhung as cho:
        nhat_ky("vung_blur", "bo_qua", time.monotonic(), "cho_chon_khung")
        return KetQua("cho_chon_khung", work, khung=cho.khung)

    def ap_dung(hash_artifact: str, moi: dict[str, str]) -> dict[str, str]:
        """Ghi tu moi trong mot transaction roi tra glossary nhom sau khi ap dung."""
        db.ap_dung_dich(con, vid, nid, hash_artifact, moi)
        return db.doc_thuat_ngu(con, nid) if nid else {}

    tien("dich", 0.5)
    t0 = time.monotonic()
    try:
        giu_nguon, tk_vao, tk_ra = _buoc_dich(work, sub_goc, cues, tc, glossary, goi, bam, ap_dung)
    except BaseException as exc:
        nhat_ky("dich", "loi", t0, str(exc))
        raise
    nhat_ky("dich", "suy_giam" if giu_nguon else "xong", t0,
            f"giu nguon {len(giu_nguon)} cue" if giu_nguon else None, tk_vao, tk_ra)

    tien("render", 0.85)
    t0 = time.monotonic()
    ra = Path(tc.ra) if tc.ra else video.with_name(video.stem + HAU_TO)
    render = _nap("render")
    try:
        render.ket_xuat(video, work / "sub_vi.srt",
                        [(v, render.khoang_mo(_cue_cua(v, cues), thoi_luong)) for v in vung],
                        {"font_scale": tc.font_scale, "W": W, "H": H,
                         "FontSize": 22 if W / H >= 1.2 else 16,
                         "MarginV": 30 if W / H >= 1.2 else 90}, ra)
    except BaseException as exc:
        nhat_ky("render", "loi", t0, str(exc))
        raise
    nhat_ky("render", "xong", t0)
    tien("render", 1.0)
    # Phu de phu qua it cung la suy giam: bao "xong" va thoat 0 thi script goi
    # main.py se dem video chi co 10% phu de la thanh cong.
    return KetQua("suy_giam" if (giu_nguon or thieu) else "xong", work, ra=ra,
                  giu_nguon=giu_nguon)


# ------------------------------------------------- quan ly nhom (CLI va API)
# IC-2: chi file nay goi db.py. CLI va api/nhom.py deu di qua bon ham duoi.

def nhom_danh_sach(con) -> list[dict]:
    return [dict(r) for r in con.execute(
        "SELECT ten,blur_x,blur_y,blur_w,blur_h FROM nhom ORDER BY ten")]


def nhom_tao(con, ten: str) -> int:
    return db.lay_nhom(con, ten)


def nhom_hop(con, ten: str) -> dict[str, float] | None:
    return db.doc_hop(con, db.lay_nhom(con, ten))


def nhom_thuat_ngu(con, ten: str) -> dict[str, str]:
    return db.doc_thuat_ngu(con, db.lay_nhom(con, ten))


def nhom_dat_thuat_ngu(con, ten: str, goc: str, dich: str, khoa: bool = False) -> None:
    db.dat_thuat_ngu(con, db.lay_nhom(con, ten), goc, dich, khoa)


def nhom_dat_hop(con, ten: str, hop: dict, W: int = 1920, H: int = 1080) -> dict:
    """Hop luon qua validator dung chung cua markbox, du den tu CLI hay API."""
    hop = _nap("markbox").kiem_hop(hop, W, H)
    db.ghi_hop(con, db.lay_nhom(con, ten), hop)
    return hop


# ---------------------------------------------------------------- batch

def dich_batch(thu_muc: Path) -> list[tuple[Path, Path]]:
    """Tinh truoc moi dich; trung dich hoac trung input thi tu choi truoc khi ghi."""
    duoi = {".mp4", ".mkv", ".mov", ".webm", ".avi", ".ts"}
    nguon = sorted(p for p in Path(thu_muc).iterdir()
                   if p.is_file() and p.suffix.lower() in duoi
                   and not p.name.endswith(HAU_TO))
    if not nguon:
        raise ValueError(f"Khong co video nao trong {thu_muc}")
    cap = [(p, p.with_name(p.stem + HAU_TO)) for p in nguon]
    dich = [r for _, r in cap]
    trung = {r for r in dich if dich.count(r) > 1}
    if trung:
        raise ValueError("Trung dich dau ra: " + ", ".join(sorted(r.name for r in trung)))
    va_cham = [v.name for v, r in cap if v.resolve() == r.resolve()]
    if va_cham:
        raise ValueError("Dau ra trung dau vao: " + ", ".join(va_cham))
    return cap
