"""Chay assert offline: python test_pipeline.py; media: them --smoke.

Diem vao duy nhat cua ca nhom: import test cua tung nguoi roi chay runner o cuoi.
"""
from collections import Counter
from contextlib import closing, contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import os
import tempfile

from tests_api import *         # noqa: F401,F403  V-9
from tests_db import *          # noqa: F401,F403  V-3
from tests_media import *       # noqa: F401,F403  V-4, V-6
from tests_translate import *   # noqa: F401,F403  V-5


def test_srt_roundtrip_validation():
    from pipeline.srt import Cue, doc_srt, ghi_srt
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "sub.srt"
        cues = [Cue(1, 1.12, 3.45, "Xin chào\nthế giới")]
        ghi_srt(cues, p)
        assert doc_srt(p) == cues
        assert not p.read_bytes().startswith(b"\xef\xbb\xbf")
        for text in ("", "broken", "1\n00:00:03,000 --> 00:00:01,000\nx"):
            p.write_text(text, encoding="utf-8")
            try:
                doc_srt(p)
            except ValueError:
                pass
            else:
                raise AssertionError(text)


def test_atomic_write_and_lock():
    from pipeline.srt import file_tam, khoa_work
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "good.txt"
        p.write_text("good", encoding="utf-8")
        try:
            with file_tam(p) as tmp:
                tmp.write_text("bad", encoding="utf-8")
                raise ValueError("interrupted")
        except ValueError:
            pass
        assert p.read_text(encoding="utf-8") == "good"
        with khoa_work(Path(d)):
            try:
                with khoa_work(Path(d)):
                    raise AssertionError("lock accepted twice")
            except FileExistsError:
                pass
        assert not (Path(d) / ".lock").exists()


# ------------------------------------------------------- gia lap cho V-2, V-6

def _srt(path, so=2):
    from pipeline.srt import Cue, ghi_srt
    ghi_srt([Cue(i + 1, i * 2.0, i * 2.0 + 1.5, f"line {i + 1}") for i in range(so)], path)


@contextmanager
def _pipeline_gia(dem: Counter, sidecar: Path | None):
    """Thay sau module xu ly bang ban gia dem so lan goi; khong ffmpeg, khong mang."""
    def tach(video, ra, separate=False):
        dem["audio"] += 1
        p = Path(ra).with_name("vocals.wav") if separate else Path(ra)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"vocals" if separate else b"wav")
        return p

    def tim_phu_de(video, ra, lang="en"):
        dem["subs"] += 1
        _srt(ra)
        return True

    def nhan_dang(wav, ra, lang="en", model="large-v3", tao_model=None, vad=True):
        dem["asr"] += 1
        dem["wav:" + Path(wav).name] += 1
        dem["vad:" + str(vad)] += 1
        _srt(ra)

    def dich(lines, glossary, goi, lo=400):
        dem["dich"] += 1
        return SimpleNamespace(ban=[f"vi {s}" for s in lines], thuat_ngu_moi={"Hero": "Anh hùng"},
                               giu_nguon=[], token_vao=1, token_ra=1)

    def ket_xuat(video, srt, hop, khoang, style, out):
        dem["render"] += 1
        Path(out).write_bytes(b"mp4")

    mods = {
        "audio": SimpleNamespace(tach=tach),
        "subs": SimpleNamespace(CODEC_CHU={"subrip"}, probe_subs=lambda v: [],
                                tim_sidecar=lambda v, lang="en": (
                                    sidecar if sidecar and sidecar.is_file() else None),
                                tim_phu_de=tim_phu_de),
        "asr": SimpleNamespace(nhan_dang=nhan_dang),
        "translate": SimpleNamespace(dich=dich),
        "markbox": SimpleNamespace(kiem_hop=lambda hop, W, H: dict(hop),
                                   trich_khung=lambda v, cues, work: [Path(work) / "khung_0.png"]),
        "render": SimpleNamespace(ket_xuat=ket_xuat, khoang_mo=lambda cues, dur: [[0.0, 1.9]]),
    }
    from pipeline import dieu_phoi
    with patch.object(dieu_phoi, "_nap", mods.__getitem__), \
            patch.object(dieu_phoi, "nhan_dien", lambda v: (1920, 1080, 10.0)):
        yield


@contextmanager
def _san(sidecar: bool = True):
    """Thu muc lam viec rieng: work/ sinh ra canh video, khong dung vao repo."""
    with tempfile.TemporaryDirectory() as d:
        cu = Path.cwd()
        os.chdir(d)
        try:
            video = Path(d) / "phim.mp4"
            video.write_bytes(b"video-v1")
            phu = Path(d) / "phim.en.srt"
            if sidecar:
                _srt(phu)
            yield video, (phu if sidecar else None)
        finally:
            os.chdir(cu)


def test_resume_dependencies_and_atomic_write():
    from pipeline import db, dieu_phoi
    from pipeline.dieu_phoi import TuyChon
    from pipeline.srt import Cue, doc_srt, doc_json, ghi_json, ghi_srt, thu_muc_lam_viec
    hop = {"x": 0.3, "y": 0.85, "w": 0.4, "h": 0.09}
    dem = Counter()
    with _san() as (video, sidecar), closing(db.mo(":memory:")) as con, _pipeline_gia(dem, sidecar):
        def chay(**kw):
            return dieu_phoi.chay(video, TuyChon(blur_box=hop, **kw), con=con, goi=lambda p: None)

        assert chay().trang_thai == "xong"
        assert dem["audio"] == 0 and dem["asr"] == 0, "co sidecar thi khong duoc goi ASR"
        assert (dem["dich"], dem["render"]) == (1, 1)

        # Luot y nguyen: moi thu tu cache, chi render chay lai.
        chay()
        assert (dem["dich"], dem["render"]) == (1, 2)

        # Doi co blur va font khong duoc keo theo dich hay ASR.
        dieu_phoi.chay(video, TuyChon(blur="off"), con=con, goi=None)
        dieu_phoi.chay(video, TuyChon(blur_box=hop, font_scale=0.5), con=con, goi=lambda p: None)
        assert (dem["dich"], dem["asr"]) == (1, 0)

        # Sua tay sub_vi hop le duoc giu khi upstream khong doi.
        work = thu_muc_lam_viec(video)
        goc = doc_srt(work / "sub_goc.srt")
        ghi_srt([Cue(c.idx, c.bat_dau, c.ket_thuc, "sua tay") for c in goc], work / "sub_vi.srt")
        chay()
        assert dem["dich"] == 1 and doc_srt(work / "sub_vi.srt")[0].text == "sua tay"

        # Ngat giua artifact va manifest: khong duoc tinh la cache hit.
        m = doc_json(work / "trang_thai.json")
        m.pop("sub_vi")
        ghi_json(work / "trang_thai.json", m)
        chay()
        assert dem["dich"] == 2

        # --force-asr bo qua ca sidecar lan cache, va lam moi ban dich.
        chay(force_asr=True, separate=True)
        assert (dem["asr"], dem["audio"], dem["dich"]) == (1, 1, 3)
        assert dem["wav:vocals.wav"] == 1, "resume --separate phai nhan dang tren vocals"

        # Thay noi dung tai cung duong dan phai lam moi cac buoc phu thuoc.
        video.write_bytes(b"video-v2")
        chay(force_asr=True, separate=True)
        assert (dem["audio"], dem["asr"], dem["dich"]) == (2, 2, 4)
        assert dem["vad:True"] == 2 and dem["vad:False"] == 0

        # Doi --vad phai nhan dang lai: VAD sai lam mat 90% phu de nen cache cu vo dung.
        sidecar.unlink()                                # bo sidecar de di duong ASR that
        chay(vad=False)
        assert (dem["asr"], dem["vad:False"]) == (3, 1)
        chay(vad=False)                                 # cung vad: dung cache, khong goi lai
        assert dem["asr"] == 3
        chay(vad=True)                                  # doi vad: phai nhan dang lai
        assert dem["asr"] == 4

    # Chua co hop nao: dung o cho_chon_khung chu khong phai loi.
    dem = Counter()
    with _san() as (video, sidecar), closing(db.mo(":memory:")) as con, _pipeline_gia(dem, sidecar):
        kq = dieu_phoi.chay(video, TuyChon(blur="on"), con=con, goi=lambda p: None)
        assert kq.trang_thai == "cho_chon_khung" and kq.khung and dem["render"] == 0


def test_batch_targets_and_cli():
    import main as cli
    from pipeline.dieu_phoi import dich_batch
    with tempfile.TemporaryDirectory() as d:
        thu_muc = Path(d)
        for ten in ("a.mp4", "b.mkv", "a_vi.mp4"):
            (thu_muc / ten).write_bytes(b"v")
        cap = dich_batch(thu_muc)
        assert [v.name for v, _ in cap] == ["a.mp4", "b.mkv"], "output _vi khong duoc lam input"
        assert [r.name for _, r in cap] == ["a_vi.mp4", "b_vi.mp4"]

        (thu_muc / "a.mov").write_bytes(b"v")        # a.mp4 va a.mov cung dich a_vi.mp4
        try:
            dich_batch(thu_muc)
        except ValueError as exc:
            assert "Trung dich" in str(exc)
        else:
            raise AssertionError("trung dich dau ra duoc chap nhan")

        try:                                          # -o bi tu choi truoc moi side effect
            cli.main(["batch", str(thu_muc), "-o", "x.mp4"])
        except SystemExit as exc:
            assert exc.code == 2
        else:
            raise AssertionError("batch nhan -o")


if __name__ == "__main__":
    import sys
    import traceback
    if "--smoke" in sys.argv:
        # V-7: can ffmpeg that, sinh video bang lavfi. Khong phai end-to-end (V-8).
        from tests_smoke import smoke_media
        smoke_media()
        print("smoke media: OK")
        raise SystemExit(0)
    # Chay het roi moi bao: mot phan chua lam khong duoc che ket qua cac phan khac.
    that_bai = []
    for ten, ham in sorted(list(globals().items())):
        if ten.startswith("test_"):
            try:
                ham()
                print("PASS", ten)
            except BaseException:
                that_bai.append(ten)
                print("FAIL", ten)
                traceback.print_exc()
    print(f"FAIL: {', '.join(that_bai)}" if that_bai else "Tat ca PASS")
    raise SystemExit(1 if that_bai else 0)
