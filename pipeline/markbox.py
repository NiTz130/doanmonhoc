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


def kiem_vung(vung: object, W: int | None = None, H: int | None = None,
              so_cue: int | None = None) -> list[dict]:
    """Chuan hoa danh sach vung mo; van di qua kiem_hop nen hinh hoc chi mot cho kiem.

    Moi phan tu co x, y, w, h va `cue`: danh sach chi so cau thoai hop nay ap vao,
    hoac None nghia la moi cau. Mot dict tran duoc coi la mot hop cho moi cau, nen
    CLI, khung mac dinh cua nhom va JSON cu deu di duoc duong nay.
    """
    if isinstance(vung, dict):
        vung = [vung]
    if not isinstance(vung, list) or not vung:
        raise ValueError("Vung lam mo phai la danh sach khong rong")
    ra = []
    for m in vung:
        if not isinstance(m, dict):
            raise ValueError("Moi vung lam mo phai la object co x, y, w, h")
        hop = kiem_hop(m, W, H)
        cue = m.get("cue")
        if cue is not None:
            if not isinstance(cue, list) or not cue:
                raise ValueError("cue phai la danh sach chi so khong rong, hoac vang mat")
            for i in cue:
                if isinstance(i, bool) or not isinstance(i, int) or i < 0:
                    raise ValueError(f"Chi so cau thoai phai la so nguyen khong am, nhan {i!r}")
                if so_cue is not None and i >= so_cue:
                    raise ValueError(f"Khong co cau thoai {i}; video chi co {so_cue} cau")
            cue = sorted(set(cue))
        ra.append({**hop, "cue": cue})
    return ra


def hop_chinh(vung: list[dict]) -> dict:
    """Hop dai dien cho vi tri phu de goc chinh trong mot danh sach vung.

    Kieu chu cua phu de Viet va khung mac dinh cua nhom deu phai chon MOT hop, va
    phai chon giong nhau — nen quy tac nam o day chu khong chep hai ban.
    Hop ap cho moi cau thang; khong co thi lay hop phu nhieu cau nhat.
    """
    if not vung:
        raise ValueError("Danh sach vung rong, khong co hop nao de chon")
    return next((v for v in vung if v.get("cue") is None),
                max(vung, key=lambda v: len(v.get("cue") or ())))


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


def trich_khung(video: Path, cues: list[Cue], work: Path) -> list[Path]:
    """Mot khung cho MOI cau thoai, khong lay mau.

    Lay mau 8 khung thi khong ai kiem duoc hop da phu het chua: phu de nhay cho o
    dung cau khong nam trong mau la lot luoi, ma do moi la cau can nhin.
    Khung lay tai dau cau chu khong rai deu theo thoi gian: khung nao cung co chu.
    """
    # ponytail: tuan tu mot ffmpeg seek moi cue (~0.2s o 640x360, ~9s cho 43 cue).
    # Phim hai tieng ~2000 cue thi mat vai phut va vai tram MB PNG; luc do hay
    # trich theo yeu cau tung khung trong api/app.py thay vi trich truoc ca loat.
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    ra = []
    for i, c in enumerate(cues):
        path = work / f"khung_{i}.png"
        subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{c.bat_dau + 0.3:.3f}",
                        "-i", str(Path(video).resolve()), "-frames:v", "1", "-y", str(path)],
                       check=True, capture_output=True, text=True)
        ra.append(path)
    return ra


def moc_khung(cues: list[Cue]) -> list[dict]:
    """Mo ta cac khung da trich cho frontend: thu tu khop voi trich_khung."""
    return [{"i": i, "giay": round(c.bat_dau + 0.3, 3), "text": c.text}
            for i, c in enumerate(cues)]
