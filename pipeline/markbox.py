"""Trich khung mau va validator hop duy nhat cho CLI, API, JSON va DB (LD-8)."""
from __future__ import annotations

import math
import subprocess
from pathlib import Path

from pipeline.srt import Cue


def _so(v: object) -> float:
    """Bool khong phai toa do: True lot qua isinstance(int) neu khong chan o day."""
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        raise ValueError(f"Toa do hop phai la so huu han, nhan duoc {v!r}")
    return float(v)


def kiem_hop(hop: dict, W: int | None = None, H: int | None = None) -> dict[str, float]:
    """Tra hop da chuan hoa; co W/H thi kiem luon phan lam tron ra pixel."""
    if not isinstance(hop, dict):
        raise ValueError("Hop phai la object co bon khoa x, y, w, h")
    thieu = {"x", "y", "w", "h"} - hop.keys()
    if thieu:
        raise ValueError(f"Hop thieu khoa: {sorted(thieu)}")
    x, y, w, h = (_so(hop[k]) for k in "xywh")
    if not (0 <= x < 1 and 0 <= y < 1):
        raise ValueError("x va y phai trong [0, 1)")
    if not (w > 0 and h > 0):
        raise ValueError("w va h phai duong")
    if x + w > 1 or y + h > 1:
        raise ValueError("Hop vuot ra ngoai khung hinh")
    sach = {"x": x, "y": y, "w": w, "h": h}
    if W is not None and H is not None:
        hop_sang_pixel(sach, W, H)
    return sach


def tach_hop(text: str) -> dict[str, float]:
    """Chi tach chuoi 'x,y,w,h'; kiem_hop van la validator duy nhat."""
    phan = str(text).split(",")
    if len(phan) != 4:
        raise ValueError("Hop phai co dang x,y,w,h")
    try:
        return dict(zip("xywh", (float(p) for p in phan)))
    except ValueError:
        raise ValueError("Hop phai gom bon so") from None


def hop_sang_pixel(hop: dict, W: int, H: int) -> tuple[int, int, int, int]:
    """Phan tram -> pixel chan, toi thieu 2x2 va nam tron trong anh."""
    x, y, w, h = (_so(hop[k]) for k in "xywh")
    bx, by = int(x * W) // 2 * 2, int(y * H) // 2 * 2
    bw = min(W - bx, -(-round(w * W) // 2) * 2) // 2 * 2
    bh = min(H - by, -(-round(h * H) // 2) * 2) // 2 * 2
    if bw < 2 or bh < 2:
        raise ValueError(f"Hop lam tron con {bw}x{bh} pixel, khong du de lam mo")
    return bx, by, bw, bh


def trich_khung(video: Path, cues: list[Cue], work: Path, n: int = 8) -> list[Path]:
    """Lay khung tai dau cau thoai, khong rai deu theo thoi gian: khung nao cung co chu."""
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    chon = [cues[round(i * (len(cues) - 1) / max(1, min(n, len(cues)) - 1))]
            for i in range(min(n, len(cues)))]
    ra = []
    for i, c in enumerate(chon):
        path = work / f"khung_{i}.png"
        subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{c.bat_dau + 0.3:.3f}",
                        "-i", str(Path(video).resolve()), "-frames:v", "1", "-y", str(path)],
                       check=True, capture_output=True, text=True)
        ra.append(path)
    return ra


def moc_khung(cues: list[Cue], n: int = 8) -> list[dict]:
    """Mo ta cac khung da trich cho frontend: thu tu khop voi trich_khung."""
    chon = [cues[round(i * (len(cues) - 1) / max(1, min(n, len(cues)) - 1))]
            for i in range(min(n, len(cues)))]
    return [{"i": i, "giay": round(c.bat_dau + 0.3, 3), "text": c.text}
            for i, c in enumerate(chon)]
