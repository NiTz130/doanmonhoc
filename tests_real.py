"""V-13: kiem tra THAT voi GPU, Whisper, NLLB va ffmpeg. Chay: python test_pipeline.py --real

Khac moi test khac trong repo: khong co callable gia. Ton thoi gian (vai chuc giay) va can
GPU NVIDIA + model da nam trong cache HuggingFace. Thieu dieu kien nao thi test do bao
NOT RUN kem ly do, khong tu pass. Khong bao gio tu tai model (3 GB cho large-v3).

Video mau: test/video_2.mp4 (loi thoai tieng Anh ro, 30 giay dau).
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
from contextlib import closing, contextmanager
from pathlib import Path

GOC = Path(__file__).resolve().parent
MAU = GOC / "test" / "video_2.mp4"
DAU_VIET = re.compile(r"[ăâđêôơưàáạảãèéẹẻẽìíịỉĩòóọỏõùúụủũỳýỵỷỹ]", re.I)


class KhongChay(Exception):
    """Thieu dieu kien moi truong: khong phai loi cua ma, khong phai pass."""


def _can(dieu_kien: bool, ly_do: str) -> None:
    if not dieu_kien:
        raise KhongChay(ly_do)


def _co_cuda() -> bool:
    try:
        import ctranslate2
        return ctranslate2.get_cuda_device_count() > 0
    except Exception:
        return False


def _can_gpu() -> None:
    _can(_co_cuda(), "khong co GPU CUDA ma ctranslate2 thay duoc")


def _can_model(repo: str) -> None:
    """Model phai co san trong cache; khong tai ngam.

    Kiem file trong so do `model.bin`, khong dung snapshot_download(local_files_only):
    faster-whisper chi tai vai file can dung nen snapshot bi coi la "chua du" du dung duoc.
    """
    from huggingface_hub import try_to_load_from_cache
    if not isinstance(try_to_load_from_cache(repo, "model.bin"), str):
        raise KhongChay(f"chua tai model {repo} (khong tu tai trong test)")


def _can_ffmpeg() -> None:
    _can(shutil.which("ffmpeg") and shutil.which("ffprobe"), "thieu ffmpeg/ffprobe trong PATH")
    _can(MAU.is_file(), f"thieu video mau {MAU}")


@contextmanager
def _tam():
    with tempfile.TemporaryDirectory() as d:
        cu = Path.cwd()
        os.chdir(d)
        try:
            yield Path(d)
        finally:
            os.chdir(cu)


def _cat(d: Path, **kw) -> tuple[Path, Path]:
    """30 giay dau cua video mau: (mp4, wav 16 kHz mono)."""
    mp4, wav = d / "clip.mp4", d / "clip.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-t", "30", "-i", str(MAU), "-c", "copy", "-y", str(mp4)], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp4), "-vn", "-ac", "1", "-ar", "16000",
                    "-y", str(wav)], check=True)
    return mp4, wav


def _whisper(model: str) -> None:
    from faster_whisper import WhisperModel
    from pipeline import asr
    from pipeline.srt import doc_srt
    _can_gpu()
    _can_model(f"Systran/faster-whisper-{model}")
    _can_ffmpeg()
    with _tam() as d:
        _, wav = _cat(d)
        thiet_bi: list[tuple[str, str]] = []

        def tao(ten, device, compute_type):
            thiet_bi.append((device, compute_type))
            return WhisperModel(ten, device=device, compute_type=compute_type)

        t0 = time.time()
        asr.nhan_dang(wav, d / "o.srt", "en", model, tao_model=tao)
        giay = time.time() - t0
        # asr.nhan_dang lui ve CPU im lang khi CUDA loi: phai chung minh khong lui.
        assert thiet_bi == [("cuda", "int8_float16")], f"khong chay tron tren GPU: {thiet_bi}"
        cues = doc_srt(d / "o.srt")
        assert len(cues) >= 2, f"qua it cue: {len(cues)}"
        assert all(c.ket_thuc > c.bat_dau and c.text.strip() for c in cues)
        assert all(a.ket_thuc <= b.bat_dau + 1e-6 for a, b in zip(cues, cues[1:])), "cue chong lan"
        assert cues[-1].ket_thuc <= 31, "moc thoi gian vuot do dai clip"
        van = " ".join(c.text for c in cues).lower()
        assert "minecraft" in van, f"khong nhan ra tu khoa trong loi thoai: {van[:200]!r}"
        print(f"      {model}: {len(cues)} cue, {giay:.1f}s, {thiet_bi[0]}")


# ----------------------------------------------------------------- GPU

def real_gpu_ctranslate2_cuda():
    import ctranslate2
    _can_gpu()
    kieu = set(ctranslate2.get_supported_compute_types("cuda"))
    assert "int8_float16" in kieu, f"GPU khong ho tro int8_float16 ma asr.py dung: {sorted(kieu)}"
    r = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                       capture_output=True, text=True)
    print(f"      {r.stdout.strip() if r.returncode == 0 else 'nvidia-smi khong co'}")


# ----------------------------------------------------------------- Whisper

def real_whisper_base_tren_gpu():
    _whisper("base")


def real_whisper_large_v3_tren_gpu():
    """Model mac dinh cua ung dung: phai vua 6 GB VRAM voi int8_float16."""
    _whisper("large-v3")


# ----------------------------------------------------------------- NLLB

def real_nllb_dich_tren_gpu_va_ep_thuat_ngu():
    import ctranslate2
    from pipeline import translate
    _can_gpu()
    _can_model(translate.MODEL_CUC_BO)
    dung: list = []

    class Do(ctranslate2.Translator):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            dung.append(self)

    goc = ctranslate2.Translator
    ctranslate2.Translator = Do
    try:
        goi = translate.tao_goi_cuc_bo()
        t0 = time.time()
        kq = goi({"lines": {"1": "Hello, how are you today?", "2": "Ironhold is a great city.",
                            "3": "We leave at 9:30 tomorrow.", "4": "Ironhold fell. Ironhold will rise again."},
                  "glossary": {"Ironhold": "Thành Sắt"}})
        giay = time.time() - t0
    finally:
        ctranslate2.Translator = goc
    assert dung and dung[-1].device == "cuda", f"NLLB khong chay tren GPU: {[t.device for t in dung]}"
    ra = kq.content["lines"]
    assert list(ra) == ["1", "2", "3", "4"], "CS-1: mot cue vao phai ra dung mot cue, giu khoa"
    for k, v in ra.items():
        assert v.strip() and DAU_VIET.search(v), f"cue {k} khong phai tieng Viet: {v!r}"
    assert "Thành Sắt" in ra["2"] and ra["4"].count("Thành Sắt") == 2, ra
    assert "9:30" in ra["3"] and "zq" not in " ".join(ra.values()).lower(), "the giu cho lot ra ngoai"
    assert kq.token_vao > 0
    print(f"      NLLB: {giay:.1f}s, device={dung[-1].device}")


def real_dich_giu_dung_so_cue_khi_goi_model_that():
    from pipeline import translate
    _can_gpu()
    _can_model(translate.MODEL_CUC_BO)
    dong = ["Welcome back.", "Today we are going to talk about Minecraft, a game released in 2009.",
            "Why? Because it is fun!", "I mean it.", "Subscribe!"]
    kq = translate.dich([d for d in dong], {"Minecraft": "Minecraft"}, translate.tao_goi_cuc_bo(), lo=3)
    assert len(kq.ban) == len(dong), "CS-1: so cue ra phai bang so cue vao"
    assert len(kq.giu_nguon) < len(dong), f"model that ma khong dich duoc cue nao: {kq.giu_nguon}"
    assert all(kq.ban[i].strip() for i in range(len(dong)))
    assert DAU_VIET.search(" ".join(kq.ban)), kq.ban


# ----------------------------------------------------------------- dau-cuoi

def real_dau_cuoi_whisper_nllb_ffmpeg():
    """Video that -> Whisper (GPU) -> NLLB (GPU) -> ffmpeg ra mp4 co phu de Viet chay vao hinh."""
    import numpy as np
    from pipeline import dieu_phoi, translate
    from pipeline.dieu_phoi import TuyChon
    from pipeline.srt import doc_srt
    _can_gpu()
    _can_model("Systran/faster-whisper-base")
    _can_model(translate.MODEL_CUC_BO)
    _can_ffmpeg()
    with _tam() as d:
        mp4, _ = _cat(d)
        tc = TuyChon(model="base", blur="off", ra=d / "ra_vi.mp4")
        buoc: list[str] = []
        from pipeline import db
        with closing(db.mo(d / "s.db")) as con:
            kq = dieu_phoi.chay(mp4, tc, lambda b, t: buoc.append(b), con=con,
                                goi=dieu_phoi.tao_goi(tc.model_dich))
            assert kq.trang_thai == "xong", (kq.trang_thai, kq.canh_bao)
            assert db.liet_ke_nhat_ky(con)[1] >= 3, "khong ghi nhat ky"
        assert "sub_goc" in buoc and len(buoc) >= 3, buoc
        goc, vi = doc_srt(kq.work / "sub_goc.srt"), doc_srt(kq.work / "sub_vi.srt")
        assert len(goc) == len(vi) >= 2, "CS-1: so cue sau dich phai bang so cue goc"
        assert [(c.bat_dau, c.ket_thuc) for c in goc] == [(c.bat_dau, c.ket_thuc) for c in vi]
        assert DAU_VIET.search(" ".join(c.text for c in vi)), "ban dich khong phai tieng Viet"

        info = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type:format=duration",
                               "-of", "csv=p=0", str(kq.ra)], capture_output=True, text=True, check=True).stdout
        assert "video" in info and "audio" in info, info
        assert abs(float(info.split()[-1]) - 30) < 1.5, f"do dai sai: {info!r}"

        # Phu de phai thuc su duoc ve vao hinh: sai khac so voi ban goc phai don ve phan day khung.
        dai = max(vi, key=lambda c: c.ket_thuc - c.bat_dau)
        giay = (dai.bat_dau + dai.ket_thuc) / 2

        def xam(v: Path):
            r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{giay:.3f}", "-i", str(v), "-frames:v", "1",
                                "-vf", "scale=320:180,format=gray", "-f", "rawvideo", "-"],
                               capture_output=True, check=True)
            return np.frombuffer(r.stdout, np.uint8).reshape(180, 320).astype(int)
        lech = np.abs(xam(kq.ra) - xam(mp4))
        day, dinh = lech[120:].mean(), lech[:60].mean()
        assert day > 1.0 and day > 2 * dinh, f"khong thay phu de tren hinh: day={day:.2f} dinh={dinh:.2f}"
        print(f"      {len(vi)} cue, {len(buoc)} lan bao tien do, lech day/dinh = {day:.1f}/{dinh:.1f}")


# ----------------------------------------------------------------- runner

def chay_that() -> int:
    ds = [(n, f) for n, f in globals().items() if n.startswith("real_") and callable(f)]
    qua = loi = khong = 0
    for ten, ham in ds:                                   # theo thu tu khai bao: GPU truoc
        t0 = time.time()
        try:
            ham()
            qua += 1
            print(f"PASS     {ten}  ({time.time() - t0:.1f}s)")
        except KhongChay as exc:
            khong += 1
            print(f"NOT RUN  {ten}: {exc}")
        except Exception:
            loi += 1
            print(f"FAIL     {ten}")
            traceback.print_exc()
    print(f"\nTest that: chay {qua + loi} / qua {qua} / loi {loi} / NOT RUN {khong}")
    return 1 if loi else 0


if __name__ == "__main__":
    sys.path.insert(0, str(GOC))
    raise SystemExit(chay_that())
