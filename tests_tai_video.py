"""Kiem tai mau khi cai dat: mang gia, khong cham video that trong repo."""
from contextlib import ExitStack, redirect_stdout
import hashlib
import io
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from unittest.mock import patch
from urllib.error import HTTPError, URLError


def _gia(mau: bytes, phan_hoi=None):
    import tools_tai_video as tai
    stack = ExitStack()
    stack.enter_context(patch.object(tai, "SO_BYTE", len(mau)))
    stack.enter_context(patch.object(tai, "SHA256", hashlib.sha256(mau).hexdigest()))
    mang = stack.enter_context(patch.object(tai, "urlopen", return_value=phan_hoi or io.BytesIO(mau)))
    return stack, mang


def test_tai_video_thieu_va_lap_lai_khong_mang():
    import tools_tai_video as tai
    mau = b"video" * 250000
    stack, mang = _gia(mau)
    with stack, tempfile.TemporaryDirectory() as d:
        dich = Path(d) / "test" / "video_3.mp4"
        assert tai.tai_video_mau(dich) == dich
        assert dich.read_bytes() == mau
        assert tai.tai_video_mau(dich) == dich
        assert mang.call_count == 1
        assert list(dich.parent.iterdir()) == [dich]


def test_tai_video_khong_ghi_de_tep_da_co():
    import tools_tai_video as tai
    stack, mang = _gia(b"video")
    with stack, tempfile.TemporaryDirectory() as d:
        dich = Path(d) / "video_3.mp4"
        for cu in (b"khac", b"sai!!", b""):
            dich.write_bytes(cu)
            try:
                tai.tai_video_mau(dich)
            except ValueError:
                pass
            else:
                raise AssertionError("Tep cu khong hop le bi chap nhan")
            assert dich.read_bytes() == cu
        mang.assert_not_called()


def test_tai_video_tu_choi_tep_thieu_thua_va_sai_hash():
    import tools_tai_video as tai
    for xau in (b"", b"vid", b"video-thua", b"sai!!", b"<html>login</html>"):
        stack, _ = _gia(b"video", io.BytesIO(xau))
        with stack, tempfile.TemporaryDirectory() as d:
            dich = Path(d) / "video_3.mp4"
            try:
                tai.tai_video_mau(dich)
            except ValueError:
                pass
            else:
                raise AssertionError("Noi dung tai ve khong hop le duoc luu")
            assert not dich.exists() and not list(Path(d).iterdir())


def test_tai_video_loi_mang_khong_de_tep_do():
    import tools_tai_video as tai
    for loi in (URLError("mat mang"), HTTPError("https://drive.google.com", 403, "cam", {}, None),
                TimeoutError("qua han")):
        with tempfile.TemporaryDirectory() as d, patch.object(tai, "urlopen", side_effect=loi):
            dich = Path(d) / "video_3.mp4"
            try:
                tai.tai_video_mau(dich)
            except (OSError, URLError):
                pass
            else:
                raise AssertionError("Nuot loi mang")
            assert not dich.exists() and not list(Path(d).iterdir())


def test_tai_video_ngat_giua_luot_don_tep_tam():
    import tools_tai_video as tai

    class Ngat(io.BytesIO):
        def read(self, n=-1):
            if self.tell():
                raise KeyboardInterrupt
            return super().read(n)

    stack, _ = _gia(b"video", Ngat(b"vid"))
    with stack, tempfile.TemporaryDirectory() as d:
        dich = Path(d) / "video_3.mp4"
        try:
            tai.tai_video_mau(dich)
        except KeyboardInterrupt:
            pass
        else:
            raise AssertionError("Ngat khong duoc truyen ra")
        assert not dich.exists() and not list(Path(d).iterdir())


def test_tai_video_khong_ghi_de_tep_xuat_hien_khi_dang_tai():
    import tools_tai_video as tai
    with tempfile.TemporaryDirectory() as d:
        dich = Path(d) / "video_3.mp4"

        def mang(*args, **kwargs):
            dich.write_bytes(b"tep cua nguoi dung")
            return io.BytesIO(b"video")

        stack, _ = _gia(b"video")
        with stack, patch.object(tai, "urlopen", mang):
            try:
                tai.tai_video_mau(dich)
            except FileExistsError:
                pass
            else:
                raise AssertionError("Tep cua nguoi dung bi ghi de")
        assert dich.read_bytes() == b"tep cua nguoi dung"
        assert list(Path(d).iterdir()) == [dich]


def test_tai_video_loi_o_dia_va_thu_muc_dich():
    import tools_tai_video as tai
    stack, mang = _gia(b"video")
    with stack, tempfile.TemporaryDirectory() as d:
        dich = Path(d) / "video_3.mp4"
        with patch.object(tai.os, "link", side_effect=OSError("het dung luong")):
            try:
                tai.tai_video_mau(dich)
            except OSError:
                pass
            else:
                raise AssertionError("Nuot loi o dia")
        assert not dich.exists() and not list(Path(d).iterdir())
        mang.reset_mock()
        dich.mkdir()
        try:
            tai.tai_video_mau(dich)
        except ValueError:
            pass
        else:
            raise AssertionError("Chap nhan thu muc lam video")
        mang.assert_not_called()


def test_tai_video_cli_thanh_cong_loi_va_ngat():
    import tools_tai_video as tai
    stack, _ = _gia(b"video")
    with stack, tempfile.TemporaryDirectory() as d, redirect_stdout(io.StringIO()) as out:
        dich = Path(d) / "video_3.mp4"
        assert tai.main(["--dich", str(dich)]) == 0
        assert dich.read_bytes() == b"video"
        assert tai.main(["--dich", str(dich)]) == 0
        for loi, ma in ((URLError("403"), 1), (ValueError("hash sai"), 1),
                       (OSError("khong ghi duoc"), 1), (KeyboardInterrupt(), 130)):
            with patch.object(tai, "tai_video_mau", side_effect=loi):
                assert tai.main([]) == ma
        assert "LỖI" in out.getvalue()
    try:
        tai.main(["--khong-co"])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("CLI chap nhan tham so la")


def test_cai_dat_goi_tai_mau_dung_thu_muc_va_truyen_ma_loi():
    if os.name != "nt":
        print("NOT RUN cai_dat.bat: chỉ dành cho Windows")
        return
    with tempfile.TemporaryDirectory() as d:
        goc = Path(d)
        du_an = goc / "project space"
        bin_dir = goc / "bin"
        du_an.mkdir()
        bin_dir.mkdir()
        shutil.copyfile(Path(__file__).with_name("cai_dat.bat"), du_an / "cai_dat.bat")
        trace = goc / "trace.txt"
        env = {**os.environ, "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"],
               "TEST_INSTALL_TRACE": str(trace)}
        for ma in (0, 7):
            (bin_dir / "uv.cmd").write_text(
                '@echo off\necho %CD%>"%TEST_INSTALL_TRACE%"\n'
                'echo %*>>"%TEST_INSTALL_TRACE%"\n' + f"exit /b {ma}\n", encoding="ascii")
            kq = subprocess.run(["cmd", "/d", "/c", str(du_an / "cai_dat.bat")],
                                cwd=goc, env=env, capture_output=True)
            assert kq.returncode == ma, kq.stderr
            dong = trace.read_text().splitlines()
            assert Path(dong[0]) == du_an
            assert dong[1] == "run --locked python tools_tai_video.py"
