"""SRT, chu ky noi dung va ghi file nguyen tu bang thu vien chuan."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import tempfile
from collections.abc import Iterator


@dataclass(frozen=True)
class Cue:
    idx: int
    bat_dau: float
    ket_thuc: float
    text: str


def kiem_cue(cues: list[Cue]) -> None:
    if not cues:
        raise ValueError("Phu de rong, khong co cue hop le")
    for c in cues:
        if not (math.isfinite(c.bat_dau) and math.isfinite(c.ket_thuc)
                and 0 <= c.bat_dau < c.ket_thuc):
            raise ValueError(f"Moc thoi gian khong hop le o cue {c.idx}")
        if not isinstance(c.text, str) or not c.text.strip() or any(
            not dong.strip() for dong in c.text.splitlines()
        ):
            raise ValueError(f"Noi dung phu de khong hop le o cue {c.idx}")


def _doc_moc(s: str) -> float:
    m = re.fullmatch(r"(\d{2,}):([0-5]\d):([0-5]\d)[,.](\d{3})", s.strip())
    if m is None:
        raise ValueError(f"Moc SRT khong hop le: {s}")
    gio, phut, giay, mili = map(int, m.groups())
    return gio * 3600 + phut * 60 + giay + mili / 1000


def _ghi_moc(t: float) -> str:
    gio, con = divmod(round(t * 1000), 3600000)
    phut, con = divmod(con, 60000)
    giay, mili = divmod(con, 1000)
    return f"{gio:02d}:{phut:02d}:{giay:02d},{mili:03d}"


def doc_srt(path: Path) -> list[Cue]:
    noi_dung = Path(path).read_text(encoding="utf-8-sig").strip()
    cues = []
    for khoi in re.split(r"\n\s*\n", noi_dung):
        dong = khoi.splitlines()
        if dong and dong[0].strip().isdigit():
            dong = dong[1:]
        if len(dong) < 2 or dong[0].count("-->") != 1:
            raise ValueError("Khoi SRT hong hoac rong")
        a, b = dong[0].split("-->")
        cues.append(Cue(len(cues) + 1, _doc_moc(a), _doc_moc(b.strip().split()[0]),
                        "\n".join(dong[1:])))
    kiem_cue(cues)
    return cues


@contextmanager
def file_tam(path: Path) -> Iterator[Path]:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, ten = tempfile.mkstemp(prefix=f".{path.stem}-", suffix=path.suffix, dir=path.parent)
    os.close(fd)
    tmp = Path(ten)
    try:
        yield tmp
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def ghi_srt(cues: list[Cue], path: Path) -> None:
    kiem_cue(cues)
    text = "\n\n".join(f"{i}\n{_ghi_moc(c.bat_dau)} --> {_ghi_moc(c.ket_thuc)}\n{c.text}"
                        for i, c in enumerate(cues, 1)) + "\n"
    with file_tam(path) as tmp:
        tmp.write_text(text, encoding="utf-8")
        doc_srt(tmp)


def ghi_json(path: Path, du_lieu: dict) -> None:
    with file_tam(path) as tmp:
        tmp.write_text(json.dumps(du_lieu, ensure_ascii=False, sort_keys=True,
                                  allow_nan=False), encoding="utf-8")


def doc_json(path: Path) -> dict:
    try:
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (FileNotFoundError, UnicodeError, json.JSONDecodeError):
        return {}


def bam_file(path: Path) -> str:
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def chu_ky(du_lieu: object) -> str:
    return hashlib.sha256(json.dumps(du_lieu, sort_keys=True, ensure_ascii=False,
                                     allow_nan=False).encode("utf-8")).hexdigest()


def thu_muc_lam_viec(video: Path, goc: Path = Path("work")) -> Path:
    p = Path(video).resolve()
    return Path(goc) / f"{p.stem}-{chu_ky(str(p))[:8]}"


def gianh_khoa(work: Path) -> Path:
    """Claim nguyen tu mot work directory; caller giu path va tu nha (LD-2, LD-6).

    Tach khoi `khoa_work` vi web can giu claim tu luc nhan upload den khi tac vu
    nen chay xong: kiem `.lock.exists()` roi tao sau la mot khe ho, khong phai claim.
    """
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    path = work / ".lock"
    try:
        f = path.open("x", encoding="utf-8")
    except FileExistsError:
        raise FileExistsError(f"Dang co lock {path}. Chi xoa sau khi xac minh tien trinh da dung.") from None
    with f:
        f.write(str(os.getpid()))
    return path


@contextmanager
def khoa_work(work: Path) -> Iterator[None]:
    path = gianh_khoa(work)
    try:
        yield
    finally:
        path.unlink(missing_ok=True)
