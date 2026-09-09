"""Ket xuat MOT lan encode: crop -> gblur -> overlay -> subtitles."""
from __future__ import annotations

import functools
import json
import logging
import shutil
import subprocess
from pathlib import Path

from pipeline.markbox import hop_sang_pixel     # LD-8: mot validator hinh hoc duy nhat
from pipeline.srt import Cue, doc_srt, file_tam

__all__ = ["hop_sang_pixel", "cue_thanh_khoang", "khoang_mo", "kieu_chu", "ket_xuat"]

NGHI = 0.4          # noi bien moi phia; hardsub thuong hien som/tat muon hon cue
GAP = 1.0           # gop hai khoang cach nhau duoi nguong nay
TOI_DA = 50         # chuoi enable dai hon lam vo filtergraph


def cue_thanh_khoang(cues: list[Cue], thoi_luong: float | None = None,
                     nghi: float = NGHI, gap: float = GAP,
                     toi_da: int = TOI_DA) -> list[tuple[float, float]]:
    """Cau -> khoang lam mo, noi +-nghi roi gop; qua dong thi noi rong nguong gop."""
    if not cues:
        return []
    if not (nghi >= 0 and gap > 0 and toi_da >= 1):
        raise ValueError("Tham so gop khoang khong hop le")
    het = thoi_luong if thoi_luong else max(c.ket_thuc for c in cues) + nghi
    tho = sorted((max(0.0, c.bat_dau - nghi), min(het, c.ket_thuc + nghi)) for c in cues)
    while True:
        gop: list[list[float]] = []
        for a, b in tho:
            if gop and a - gop[-1][1] <= gap:
                gop[-1][1] = max(gop[-1][1], b)
            else:
                gop.append([a, b])
        if len(gop) <= toi_da:
            return [(a, b) for a, b in gop]
        if gap >= het:                      # noi rong het co van du: lam mo ca phim
            return [(0.0, het)]
        gap *= 2


khoang_mo = cue_thanh_khoang                # ten dieu_phoi.py dang goi


def kieu_chu(W: int, H: int, px: tuple[int, int, int, int] | None = None,
             font_scale: float = 0.42, du_phong: dict | None = None) -> dict:
    """Co hop thi suy kieu chu tu hop; khong thi dung ho so hinh hoc."""
    if (isinstance(font_scale, bool) or not isinstance(font_scale, (int, float))
            or not font_scale > 0):
        raise ValueError("font-scale phai la so duong")
    if px is None:
        ngang = W / H >= 1.2
        du_phong = du_phong or {}
        style = {"FontSize": du_phong.get("FontSize", 22 if ngang else 16),
                 "MarginV": du_phong.get("MarginV", 30 if ngang else 90)}
    else:
        # Chu Viet roi dung day hop mo va che gan het no; xem thiet ke buoc 5.
        style = {"FontSize": max(8, round(px[3] * font_scale)),
                 "MarginV": max(0, H - px[1] - px[3])}
    return {"PlayResX": W, "PlayResY": H, "FontName": "Arial", **style}


def _moc_ass(t: float) -> str:
    gio, con = divmod(round(t * 100), 360000)
    phut, con = divmod(con, 6000)
    giay, tram = divmod(con, 100)
    return f"{gio:d}:{phut:02d}:{giay:02d}.{tram:02d}"


def viet_ass(cues: list[Cue], style: dict, path: Path) -> None:
    """Tu sinh ASS de PlayResX/Y bang kich thuoc video: FontSize/MarginV theo pixel.

    ffmpeg doi SRT sang ASS voi PlayRes mac dinh 384x288, nen cong thuc pixel o
    thiet ke buoc 5 chi dung khi ta tu ghi header nay.
    """
    dau = ("[Script Info]\nScriptType: v4.00+\nWrapStyle: 0\n"
           "ScaledBorderAndShadow: yes\n"
           f"PlayResX: {style['PlayResX']}\nPlayResY: {style['PlayResY']}\n\n"
           "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, "
           "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
           "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
           f"Style: Default,{style['FontName']},{style['FontSize']},&H00FFFFFF,&H00000000,"
           f"&H80000000,0,0,0,0,100,100,0,0,1,2,1,2,20,20,{style['MarginV']},1\n\n"
           "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, "
           "Effect, Text\n")
    dong = "".join(
        f"Dialogue: 0,{_moc_ass(c.bat_dau)},{_moc_ass(c.ket_thuc)},Default,,0,0,0,,"
        + c.text.replace("{", "(").replace("}", ")").replace("\n", "\\N") + "\n"
        for c in cues)
    with file_tam(path) as tmp:
        tmp.write_text(dau + dong, encoding="utf-8")


def _thoat(v: object) -> str:
    """Escape gia tri trong mot doi so filter: dau , va : la ky tu phan cach."""
    return str(v).replace("\\", "\\\\").replace(",", "\\,").replace(":", "\\:")


@functools.lru_cache(maxsize=1)
def bo_ma_hoa() -> tuple[str, ...]:
    """Kiem NVENC bang encode that; liet ke encoder khong chung minh chay duoc."""
    # 256x256: duoi kich thuoc toi thieu cua NVENC thi phep thu tu hong, va ta se
    # bao GPU khong dung duoc tren may thuc ra dung duoc.
    thu = subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=s=256x256:d=0.1",
                          "-c:v", "h264_nvenc", "-f", "null", "-"], capture_output=True, text=True)
    if thu.returncode == 0:
        return ("-c:v", "h264_nvenc", "-preset", "p5", "-cq", "23")
    logging.warning("h264_nvenc khong encode duoc, chuyen sang libx264 (cham hon):\n%s",
                    thu.stderr.strip())
    return ("-c:v", "libx264", "-preset", "medium", "-crf", "23")


def ket_xuat(video: Path, srt: Path, hop: dict | None, khoang: list[tuple[float, float]],
             style: dict, ra: Path) -> Path:
    """Mot lan encode duy nhat; audio copy nguyen, output tam roi probe roi replace."""
    for tool in ("ffmpeg", "ffprobe"):
        if shutil.which(tool) is None:
            raise RuntimeError(f"Thieu {tool} trong PATH")
    video, srt, ra = Path(video).resolve(), Path(srt), Path(ra)
    W, H = int(style["W"]), int(style["H"])
    px = hop_sang_pixel(hop, W, H) if hop else None
    ass = srt.with_suffix(".ass")
    viet_ass(doc_srt(srt), kieu_chu(W, H, px, style.get("font_scale", 0.42), style), ass)

    # cwd dat tai thu muc chua phu de va truyen ten tuong doi: duong dan Windows
    # tuyet doi trong filtergraph phai escape thanh C\:/... , sai mot dau la loi la.
    phu_de = "subtitles=" + _thoat(ass.name)
    if px and khoang:
        bat = "+".join(f"between(t\\,{a:.3f}\\,{b:.3f})" for a, b in khoang)
        loc = (f"[0:v]split[base][tmp];"
               f"[tmp]crop={px[2]}:{px[3]}:{px[0]}:{px[1]},gblur=sigma=25[blur];"
               f"[base][blur]overlay={px[0]}:{px[1]}:enable={bat}[bl];"
               f"[bl]{phu_de}[v]")
    else:
        loc = f"[0:v]{phu_de}[v]"

    with file_tam(ra) as tmp:
        lenh = ["ffmpeg", "-v", "error", "-y", "-i", str(video), "-filter_complex", loc,
                "-map", "[v]", "-map", "0:a?", *bo_ma_hoa(), "-c:a", "copy",
                "-f", "mp4", str(tmp.resolve())]
        ket = subprocess.run(lenh, cwd=str(srt.parent.resolve()), capture_output=True, text=True)
        if ket.returncode != 0:
            raise RuntimeError(f"ffmpeg loi khi ket xuat {video.name}:\n{ket.stderr.strip()}")
        _kiem_ra(tmp)
    return ra


def _kiem_ra(path: Path) -> None:
    """Kich thuoc file khong phai bang chung: hoi ffprobe co luong video that khong."""
    ket = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                          "-show_entries", "stream=width,height", "-show_entries",
                          "format=duration", "-of", "json", str(path)],
                         capture_output=True, text=True)
    d = json.loads(ket.stdout or "{}")
    if ket.returncode != 0 or not d.get("streams") or float(d["format"]["duration"]) <= 0:
        raise RuntimeError("Output khong co luong video hop le; giu nguyen ban cu")
