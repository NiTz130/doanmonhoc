"""Tai video mau de kiem thu tren may moi; khong ghi de tep da co."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import tempfile
from urllib.error import URLError
from urllib.request import urlopen

from pipeline.srt import bam_file

GOC = Path(__file__).resolve().parent
URL = "https://drive.google.com/uc?export=download&id=16sh5oYQUdVYngAkxV-8d_rh4v5B-4ngV"
SO_BYTE = 5732135
SHA256 = "48b89db16a49a6c8cf2c52dfe88d6b90d16320c9d296715518e42f3832d4d4fb"


def _kiem_mau(tep: Path) -> None:
    if not tep.is_file() or tep.stat().st_size != SO_BYTE or bam_file(tep) != SHA256:
        raise ValueError(f"{tep}: không đúng video mẫu. Giữ nguyên tệp; chuyển tệp đi rồi tải lại.")


def tai_video_mau(dich: Path = GOC / "test" / "video_3.mp4") -> Path:
    """Tai khi thieu; kiem so byte va SHA-256 truoc khi cong bo tep."""
    dich = Path(dich)
    if dich.exists() or dich.is_symlink():
        _kiem_mau(dich)
        return dich
    dich.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".tai-video-", dir=dich.parent) as d:
        tam = Path(d) / "video_3.mp4"
        with urlopen(URL, timeout=60) as nguon, tam.open("wb") as ra:
            so_byte = 0
            while khoi := nguon.read(1024 * 1024):
                so_byte += len(khoi)
                if so_byte > SO_BYTE:
                    raise ValueError("Tệp tải về lớn hơn video mẫu; kiểm tra quyền tải trên Drive.")
                ra.write(khoi)
        _kiem_mau(tam)
        # file_tam dung os.replace; hard link giu ca tep xuat hien giua luot tai.
        os.link(tam, dich)
    return dich


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Tải video mẫu để kiểm thử hệ thống.")
    ap.add_argument("--dich", type=Path, default=GOC / "test" / "video_3.mp4",
                    help="đường dẫn lưu mẫu (mặc định test/video_3.mp4)")
    a = ap.parse_args(argv)
    try:
        tep = tai_video_mau(a.dich)
    except (OSError, URLError, ValueError) as exc:
        print(f"LỖI: Không tải được video mẫu: {exc}")
        print("Kiểm tra mạng và quyền xem/tải bằng liên kết trên Google Drive, rồi chạy lại.")
        return 1
    except KeyboardInterrupt:
        print("Đã ngắt tải video mẫu.")
        return 130
    print(f"Video kiểm thử đã sẵn sàng: {tep}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
