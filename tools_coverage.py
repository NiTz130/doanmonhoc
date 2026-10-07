"""Do do phu dong lenh cua bo test offline, khong them thu vien (dung sys.monitoring, Python 3.12).

    python tools_coverage.py                 # chay test_pipeline.py, in bang do phu
    python tools_coverage.py --min 90        # thoat ma 1 neu tong do phu < 90%
    python tools_coverage.py -- --smoke      # moi thu sau `--` chuyen cho test_pipeline.py

Pham vi: pipeline/, api/, main.py va tools_tai_video.py, TRONG tien trinh nay. Khong do duoc tien trinh con
(test/runtime_logic.py chay uvicorn rieng) va khong do nhanh (branch), chi do dong.
Dong "thuc thi duoc" lay tu bang dong cua ma bien dich, nen comment/docstring khong tinh.
Con so nay do muc test CHAM toi dong ma, khong chung minh dong ma dung.
"""
from __future__ import annotations

import argparse
import dis
import runpy
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent
PHAM_VI = ("pipeline", "api")
FILE_LE = ("main.py", "tools_tai_video.py")
TOOL = sys.monitoring.COVERAGE_ID


def tep_trong_pham_vi() -> list[Path]:
    ds = [p for d in PHAM_VI for p in sorted((GOC / d).glob("*.py")) if p.name != "__init__.py"]
    return ds + [GOC / f for f in FILE_LE]


def dong_thuc_thi(tep: Path) -> set[int]:
    """Moi dong co lenh may trong ma bien dich cua tep (de quy vao ham, lop, lambda)."""
    ra: set[int] = set()
    cho = [compile(tep.read_text(encoding="utf-8"), str(tep), "exec")]
    while cho:
        ma = cho.pop()
        ra.update(d for _, d in dis.findlinestarts(ma) if d is not None and d > 0)
        cho.extend(c for c in ma.co_consts if hasattr(c, "co_code"))
    return ra


def khoang(dong: list[int]) -> str:
    """[3,4,5,9] -> '3-5, 9'."""
    ra, dau = [], None
    for i, d in enumerate(dong):
        if dau is None:
            dau = d
        if i + 1 == len(dong) or dong[i + 1] != d + 1:
            ra.append(str(dau) if dau == d else f"{dau}-{d}")
            dau = None
    return ", ".join(ra)


def do(chay, tep: list[Path]) -> tuple[dict[Path, set[int]], int]:
    """Chay `chay()` duoi do dac; tra (dong da chay moi tep, ma thoat)."""
    can = {str(p): p for p in tep}
    da_chay: dict[Path, set[int]] = {p: set() for p in tep}

    def ghi(ma, dong):
        p = can.get(ma.co_filename)
        if p is not None:
            da_chay[p].add(dong)
        return sys.monitoring.DISABLE           # moi dong chi can ghi mot lan: gan nhu khong ton thoi gian

    sys.monitoring.use_tool_id(TOOL, "dich-phu-de-do-phu")
    sys.monitoring.register_callback(TOOL, sys.monitoring.events.LINE, ghi)
    sys.monitoring.set_events(TOOL, sys.monitoring.events.LINE)
    ma_thoat = 0
    try:
        chay()
    except SystemExit as exc:
        ma_thoat = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
    finally:
        sys.monitoring.set_events(TOOL, 0)
        sys.monitoring.free_tool_id(TOOL)
    return da_chay, ma_thoat


def bao_cao(da_chay: dict[Path, set[int]]) -> float:
    tong_ma = tong_chay = 0
    print(f"\n{'Tep':<26}{'Dong':>6}{'Chua chay':>11}{'Phu':>7}  Dong chua chay")
    for p, chay in da_chay.items():
        can = dong_thuc_thi(p)
        thieu = sorted(can - chay)
        tong_ma += len(can)
        tong_chay += len(can) - len(thieu)
        phu = 100.0 * (len(can) - len(thieu)) / len(can) if can else 100.0
        rut = khoang(thieu)
        print(f"{p.relative_to(GOC).as_posix():<26}{len(can):>6}{len(thieu):>11}{phu:>6.1f}%  "
              f"{rut if len(rut) < 60 else rut[:57] + '...'}")
    tong = 100.0 * tong_chay / tong_ma if tong_ma else 100.0
    print(f"{'TONG':<26}{tong_ma:>6}{tong_ma - tong_chay:>11}{tong:>6.1f}%")
    return tong


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--min", type=float, default=0.0, help="thoat ma 1 neu tong do phu thap hon")
    ap.add_argument("test_args", nargs="*", help="sau `--`: doi so cho test_pipeline.py")
    a = ap.parse_args(sys.argv[1:] if argv is None else argv)
    sys.path.insert(0, str(GOC))
    sys.argv = ["test_pipeline.py", *a.test_args]
    # Phai bat do TRUOC khi test_pipeline import pipeline/api, neu khong cac dong cap
    # module (def, import, hang so) da chay xong ma khong ai thay.
    da_chay, ma = do(lambda: runpy.run_path(str(GOC / "test_pipeline.py"), run_name="__main__"),
                     tep_trong_pham_vi())
    tong = bao_cao(da_chay)
    if ma:
        print(f"\nTEST THAT BAI (ma thoat {ma}): do phu o tren khong dang tin cho den khi test qua.")
        return ma
    if tong < a.min:
        print(f"\nDO PHU {tong:.1f}% < nguong {a.min:g}%")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
