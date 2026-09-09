"""Cong cu noi bo: chay pipeline bang dong lenh. San pham chinh la web app."""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from contextlib import closing
from pathlib import Path

from pipeline import db, dieu_phoi  # db chi de mo ket noi; moi truy van qua dieu_phoi
from pipeline.dieu_phoi import TuyChon


# Console Windows mac dinh cp1252 lam vo moi ban dich tieng Viet in ra.
for _luong in (sys.stdout, sys.stderr):
    _luong.reconfigure(encoding="utf-8", errors="replace")


def _hop(text: str) -> dict[str, float]:
    """Chi tach chuoi; markbox.kiem_hop moi la validator duy nhat (LD-8)."""
    phan = text.split(",")
    if len(phan) != 4:
        raise argparse.ArgumentTypeError("Hop phai co dang x,y,w,h")
    try:
        return dict(zip("xywh", (float(p) for p in phan)))
    except ValueError:
        raise argparse.ArgumentTypeError("Hop phai gom bon so") from None


def _co_chung(p: argparse.ArgumentParser) -> None:
    p.add_argument("--nhom")
    p.add_argument("--lang", default="en")
    p.add_argument("--model", default="large-v3")
    p.add_argument("--model-dich", default="deepseek-v4-flash")
    p.add_argument("--blur", choices=("auto", "on", "off"), default="auto")
    p.add_argument("--blur-box", type=_hop)
    p.add_argument("--font-scale", type=float, default=0.42)
    p.add_argument("--separate", action="store_true")
    p.add_argument("--vad", choices=("on", "off"), default="on",
                   help="tat khi video ca nhac: VAD coi nhac nen la khong phai tieng noi")
    p.add_argument("--force-asr", action="store_true")
    p.add_argument("--force", action="store_true")


def _tuy_chon(a: argparse.Namespace, ra: Path | None = None) -> TuyChon:
    return TuyChon(nhom=a.nhom, lang=a.lang, model=a.model, model_dich=a.model_dich,
                   blur=a.blur, blur_box=a.blur_box, font_scale=a.font_scale,
                   separate=a.separate, vad=a.vad == "on",
                   force_asr=a.force_asr, force=a.force, ra=ra)


def _tien_do(buoc: str, ti_le: float) -> None:
    print(f"[{ti_le:5.0%}] {buoc}", flush=True)


def _preflight(tc: TuyChon):
    """Loi cau hinh chung kiem truoc vong batch, khong de vao giua chung."""
    for tool in ("ffmpeg", "ffprobe"):
        if shutil.which(tool) is None:
            raise RuntimeError(f"Thieu {tool} trong PATH")
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not key.strip():
        raise RuntimeError("Thieu DEEPSEEK_API_KEY trong .env hoac bien moi truong")
    from pipeline.translate import tao_goi
    return tao_goi(key, tc.model_dich)


def _mot_video(video: Path, tc: TuyChon, con, goi) -> str:
    kq = dieu_phoi.chay(video, tc, _tien_do, con=con, goi=goi)
    if kq.trang_thai == "cho_chon_khung":
        print(f"DUNG LAI: {video.name} chua co vung lam mo. Da trich {len(kq.khung)} khung "
              f"trong {kq.work}.\n  Chay lai voi --blur-box x,y,w,h hoac --blur off.",
              file=sys.stderr)
    elif kq.trang_thai == "suy_giam":
        print(f"SUY GIAM: {len(kq.giu_nguon)} cue giu nguyen ban goc -> {kq.ra}", file=sys.stderr)
    else:
        print(f"XONG: {kq.ra}")
    return kq.trang_thai


def _chay_video(a: argparse.Namespace) -> int:
    video = Path(a.video)
    if not video.is_file():                          # bao truoc khi doi hoi khoa API
        raise FileNotFoundError(f"Khong tim thay video: {video}")
    tc = _tuy_chon(a, Path(a.output) if a.output else None)
    goi = _preflight(tc)
    with closing(db.mo(Path("work") / "subtitles.db")) as con:
        return 0 if _mot_video(video, tc, con, goi) == "xong" else 1


def _chay_batch(a: argparse.Namespace) -> int:
    tc = _tuy_chon(a)
    cap = dieu_phoi.dich_batch(Path(a.thu_muc))       # tinh dich truoc moi side effect
    goi = _preflight(tc)
    dem = {"xong": 0, "suy_giam": 0, "cho_chon_khung": 0, "loi": 0}
    with closing(db.mo(Path("work") / "subtitles.db")) as con:
        for video, ra in cap:                        # tuan tu: thuat ngu tich luy dan
            try:
                dem[_mot_video(video, _tuy_chon(a, ra), con, goi)] += 1
            except KeyboardInterrupt:
                raise
            except Exception as exc:                 # loi mot video khong dung ca lo
                dem["loi"] += 1
                print(f"LOI {video.name}: {exc}", file=sys.stderr)
    print("Tong ket: " + ", ".join(f"{k}={v}" for k, v in dem.items()))
    return 1 if dem["loi"] or dem["suy_giam"] or dem["cho_chon_khung"] else 0


def _chay_nhom(a: argparse.Namespace) -> int:
    with closing(db.mo(Path("work") / "subtitles.db")) as con, con:
        if a.viec == "list":
            for row in con.execute("SELECT ten,blur_x,blur_y,blur_w,blur_h FROM nhom ORDER BY ten"):
                hop = "chua co hop" if row["blur_x"] is None else \
                    "hop " + ",".join(f"{row[k]:g}" for k in ("blur_x", "blur_y", "blur_w", "blur_h"))
                print(f"{row['ten']}\t{hop}")
        elif a.viec == "glossary":
            for goc, dich in db.doc_thuat_ngu(con, db.lay_nhom(con, a.ten)).items():
                print(f"{goc}\t{dich}")
        elif a.viec == "set-term":
            db.dat_thuat_ngu(con, db.lay_nhom(con, a.ten), a.goc, a.dich, a.lock)
        else:
            from pipeline.dieu_phoi import _nap
            db.ghi_hop(con, db.lay_nhom(con, a.ten), _nap("markbox").kiem_hop(a.hop, 1920, 1080))
    return 0


def tao_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="main.py", description="Dich phu de video Anh -> Viet")
    sub = p.add_subparsers(dest="lenh")

    mot = sub.add_parser("video", help="chay mot video")
    mot.add_argument("video")
    mot.add_argument("-o", "--output")
    _co_chung(mot)
    mot.set_defaults(ham=_chay_video)

    lo = sub.add_parser("batch", help="chay ca thu muc, tuan tu")
    lo.add_argument("thu_muc")
    _co_chung(lo)                                    # khong co -o: LD-3
    lo.set_defaults(ham=_chay_batch)

    nhom = sub.add_parser("nhom", help="quan ly nhom va thuat ngu")
    viec = nhom.add_subparsers(dest="viec", required=True)
    viec.add_parser("list")
    g = viec.add_parser("glossary")
    g.add_argument("ten")
    t = viec.add_parser("set-term")
    t.add_argument("ten")
    t.add_argument("goc")
    t.add_argument("dich")
    t.add_argument("--lock", action="store_true")
    b = viec.add_parser("set-box")
    b.add_argument("ten")
    b.add_argument("hop", type=_hop)
    nhom.set_defaults(ham=_chay_nhom)
    return p


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] not in {"video", "batch", "nhom", "-h", "--help"}:
        argv.insert(0, "video")                      # main.py <video> nhu spec §8
    a = tao_parser().parse_args(argv)
    if not getattr(a, "ham", None):
        tao_parser().print_help()
        return 2
    try:
        return a.ham(a)
    except KeyboardInterrupt:
        print("\nDa dung theo yeu cau nguoi dung.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"LOI: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
