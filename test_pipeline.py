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
    # Validator that: hinh hoc phai duoc kiem that chu khong phai ban gia de lot.
    from pipeline.markbox import hop_chinh, kiem_hop, kiem_vung
    from pipeline.render import cue_thanh_khoang, gop_khoang
    from pipeline.srt import ghi_json

    def tach(video, ra, separate=False):
        dem["audio"] += 1
        p = Path(ra).with_name("vocals.wav") if separate else Path(ra)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"vocals" if separate else b"wav")
        return p

    def tim_phu_de(video, ra, lang="en"):
        dem["subs"] += 1
        if sidecar and sidecar.is_file():
            Path(ra).write_bytes(sidecar.read_bytes())
        else:
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

    def ket_xuat(video, srt, vung, style, out, *, loai_tru_chung=None):
        dem["render"] += 1
        Path(out).write_bytes(b"mp4")
        # Ghi lai de test doi chieu tung hop voi khoang thoi gian no duoc gan.
        ghi_json(Path(srt).with_name("render_vung.json"),
                 {"vung": vung, "loai_tru_chung": loai_tru_chung,
                  "hop_chinh": style.get("hop_chinh")})

    mods = {
        "audio": SimpleNamespace(tach=tach),
        "subs": SimpleNamespace(CODEC_CHU={"subrip"}, probe_subs=lambda v: [],
                                tim_sidecar=lambda v, lang="en": (
                                    sidecar if sidecar and sidecar.is_file() else None),
                                tim_phu_de=tim_phu_de),
        "asr": SimpleNamespace(nhan_dang=nhan_dang),
        "translate": SimpleNamespace(dich=dich),
        "markbox": SimpleNamespace(kiem_vung=kiem_vung, kiem_hop=kiem_hop,
                                   hop_chinh=hop_chinh,
                                   trich_khung=lambda v, cues, work: [Path(work) / "khung_0.png"]),
        # khoang_mo that: no thuan tuy tinh toan, va test can thay dung cue nao vao hop nao.
        "render": SimpleNamespace(ket_xuat=ket_xuat, khoang_mo=cue_thanh_khoang,
                                  gop_khoang=gop_khoang),
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

    # Chua co hop nao: dung o cho_chon_khung chu khong phai loi, va dung TRUOC buoc
    # dich — bo cuoc o man ve hop thi khong duoc mat tien API dich.
    dem = Counter()
    with _san() as (video, sidecar), closing(db.mo(":memory:")) as con, _pipeline_gia(dem, sidecar):
        kq = dieu_phoi.chay(video, TuyChon(blur="on"), con=con, goi=lambda p: None)
        assert kq.trang_thai == "cho_chon_khung" and kq.khung
        assert (dem["dich"], dem["render"]) == (0, 0), "cho ve hop khong duoc ton token dich"

        # Ve hop xong chay tiep: bay gio moi dich, roi ket xuat.
        kq = dieu_phoi.chay(video, TuyChon(blur="on", blur_box=hop), con=con, goi=lambda p: None)
        assert kq.trang_thai == "xong" and (dem["dich"], dem["render"]) == (1, 1)


def test_hop_nhom_khong_bi_ghi_de_am_tham():
    from pipeline import db, dieu_phoi
    from pipeline.dieu_phoi import TuyChon
    from pipeline.srt import doc_json, thu_muc_lam_viec
    hop = {"x": 0.3, "y": 0.85, "w": 0.4, "h": 0.09}
    mac_dinh = {"x": 0.1, "y": 0.80, "w": 0.3, "h": 0.10}
    dem = Counter()
    with _san() as (video, sidecar), closing(db.mo(":memory:")) as con, _pipeline_gia(dem, sidecar):
        def chay(**kw):
            return dieu_phoi.chay(video, TuyChon(nhom="Phim", **kw), con=con, goi=lambda p: None)

        chay(blur_box=hop)
        assert dieu_phoi.nhom_hop(con, "Phim") is None, "ve hop mot video khong duoc doi ca nhom"

        chay(blur_box=hop, luu_hop_nhom=True)           # chon ro rang thi moi ghi
        assert dieu_phoi.nhom_hop(con, "Phim") == hop

        # Hop rieng cua video thang hop mac dinh cua nhom: no ve tren dung khung hinh nay.
        dieu_phoi.nhom_dat_hop(con, "Phim", mac_dinh)
        chay()
        luu = doc_json(thu_muc_lam_viec(video) / "vung_blur.json")
        assert [{k: v[k] for k in "xywh"} for v in luu["vung"]] == [hop], \
            "hop rieng phai thang hop mac dinh nhom"


def test_vung_mo_gan_tung_cau_thoai():
    """Phu de nhay cho: moi hop chi lam mo dung nhung cau duoc gan cho no."""
    from pipeline import db, dieu_phoi
    from pipeline.dieu_phoi import TuyChon
    from pipeline.srt import doc_json, thu_muc_lam_viec
    duoi = {"x": 0.3, "y": 0.85, "w": 0.4, "h": 0.09}       # phu de goc, o day
    tren = {"x": 0.3, "y": 0.05, "w": 0.4, "h": 0.09}       # vai cau nhay len dinh
    dem = Counter()
    with _san() as (video, sidecar), closing(db.mo(":memory:")) as con, _pipeline_gia(dem, sidecar):
        # Ban gia sinh 2 cue: cue 0 o 0.0-1.5s, cue 1 o 2.0-3.5s.
        vung = [{**duoi, "cue": None}, {**tren, "cue": [1]}]
        kq = dieu_phoi.chay(video, TuyChon(nhom="Phim", blur_box=vung, luu_hop_nhom=True),
                            con=con, goi=lambda p: None)
        assert kq.trang_thai == "xong"

        work = thu_muc_lam_viec(video)
        luu = doc_json(work / "vung_blur.json")["vung"]
        assert [v["cue"] for v in luu] == [None, [1]]

        # Hop chung phu ca hai cau; hop tren chi phu cue 1, nen bat muon hon.
        goi = doc_json(work / "render_vung.json")["vung"]
        assert len(goi) == 2
        (h1, k1), (h2, k2) = goi
        assert {k: h1[k] for k in "xywh"} == duoi and {k: h2[k] for k in "xywh"} == tren
        assert k1 == [[0.0, 3.9]], k1              # cue 0 + cue 1, gop lai
        assert k2 == [[1.6, 3.9]], k2              # chi cue 1: khong mo tu giay 0

        # Khung mac dinh cua nhom lay hop dung cho MOI cau, khong lay hop gan rieng.
        assert dieu_phoi.nhom_hop(con, "Phim") == duoi

        # Gan vao cau khong ton tai thi tu choi, khong lang le bo qua.
        for xau in ([{**duoi, "cue": [99]}], [{**duoi, "cue": []}], [{**duoi, "cue": [-1]}]):
            try:
                dieu_phoi.chay(video, TuyChon(blur_box=xau), con=con, goi=lambda p: None)
                assert False, xau
            except ValueError:
                pass


def test_vung_rieng_thay_vung_chung():
    """LD-7: che do thay_the tru cue rieng khoi vung chung, ca theo cue lan theo thoi gian."""
    from pipeline import db, dieu_phoi
    from pipeline.dieu_phoi import TuyChon
    from pipeline.markbox import kiem_che_do, kiem_vung
    from pipeline.render import gop_khoang
    from pipeline.srt import doc_json, thu_muc_lam_viec

    # Discriminator: vang mat la legacy, moi gia tri khac hai chuoi cho phep la loi.
    # Vang mat la legacy; `null` tuong minh la loi chu khong phai vang mat (LD-7a).
    assert kiem_che_do() == "cong_them" and kiem_che_do("thay_the") == "thay_the"
    for xau in (None, "THAY_THE", "", True, 1, "replace"):
        try:
            kiem_che_do(xau)
            assert False, xau
        except ValueError:
            pass

    duoi = {"x": 0.3, "y": 0.85, "w": 0.4, "h": 0.09}
    tren = {"x": 0.3, "y": 0.05, "w": 0.4, "h": 0.09}
    # Rang buoc duy nhat chi ap cho thay_the; legacy van duoc cong don tu do.
    hai_chung = [{**duoi, "cue": None}, {**tren, "cue": None}]
    cheo = [{**duoi, "cue": [0]}, {**tren, "cue": [0, 1]}]
    for xau in (hai_chung, cheo):
        assert len(kiem_vung(xau, so_cue=2, che_do="cong_them")) == 2
        try:
            kiem_vung(xau, so_cue=2, che_do="thay_the")
            assert False, xau
        except ValueError:
            pass

    # Gop mat na chi gop khi cham/chong nhau, khong noi them gap nhu buoc gop cue.
    assert gop_khoang([(2.0, 3.0), (0.0, 1.0), (1.0, 1.5)]) == [(0.0, 1.5), (2.0, 3.0)]

    dem = Counter()
    with _san() as (video, sidecar), closing(db.mo(":memory:")) as con, _pipeline_gia(dem, sidecar):
        # Ban gia sinh 2 cue: cue 0 o 0.0-1.5s, cue 1 o 2.0-3.5s.
        vung = [{**duoi, "cue": None}, {**tren, "cue": [1]}]
        kq = dieu_phoi.chay(video, TuyChon(nhom="Phim", blur_box=vung, luu_hop_nhom=True,
                                           che_do_vung="thay_the"),
                            con=con, goi=lambda p: None)
        assert kq.trang_thai == "xong"

        work = thu_muc_lam_viec(video)
        luu = doc_json(work / "vung_blur.json")
        # Mode nam trong artifact: lan chay sau khong doc lai vung nay bang nghia khac.
        assert luu["che_do_vung"] == "thay_the" and [v["cue"] for v in luu["vung"]] == [None, [1]]

        goi = doc_json(work / "render_vung.json")
        (h1, k1), (h2, k2) = goi["vung"]
        assert {k: h1[k] for k in "xywh"} == duoi and {k: h2[k] for k in "xywh"} == tren
        # Vung chung chi con cue 0; o che do cong_them no phu ca 0.0-3.9.
        assert k1 == [[0.0, 1.9]], k1
        assert k2 == [[1.6, 3.9]], k2
        # Noi +-0.4s cua cue 0 cham vao khoang cua cue 1, nen phai co mat na thoi gian.
        assert goi["loai_tru_chung"] == [[1.6, 3.9]], goi["loai_tru_chung"]
        # Hop dai dien chon tren danh sach THO: tru cue khong duoc lam chu nhay cho.
        assert {k: goi["hop_chinh"][k] for k in "xywh"} == duoi
        assert dieu_phoi.nhom_hop(con, "Phim") == duoi


def test_vung_edge_cases_and_raw_primary():
    """V-02/LD-7: edge semantics, >50 exclusions, and primary before subtraction."""
    import math
    from pipeline import db, dieu_phoi
    from pipeline.dieu_phoi import TuyChon
    from pipeline.markbox import kiem_vung
    from pipeline.render import gop_khoang
    from pipeline.srt import Cue, doc_json, thu_muc_lam_viec

    cues = [Cue(1, 0.0, 0.5, "zero"), Cue(2, 10.0, 10.5, "ten")]
    common = {"x": 0.1, "y": 0.8, "w": 0.2, "h": 0.1, "cue": None}
    private = {"x": 0.6, "y": 0.1, "w": 0.2, "h": 0.1, "cue": [1]}
    assert [len(x) for _, x in dieu_phoi._phan_cue([common, private], cues, "thay_the")] == [1, 1]
    assert [len(x) for _, x in dieu_phoi._phan_cue([private], cues, "thay_the")] == [1]
    assert [len(x) for _, x in dieu_phoi._phan_cue(
        [{**common, "cue": None}, {**private, "cue": [0, 1]}], cues, "thay_the")] == [0, 2]
    assert [len(x) for _, x in dieu_phoi._phan_cue([common, private], cues, "cong_them")] == [2, 1]
    assert len(gop_khoang([(i * 2.0, i * 2.0 + 0.5) for i in range(60)])) == 60

    for bad in (math.nan, math.inf, -math.inf):
        try:
            kiem_vung([{**common, "x": bad}], 1920, 1080, 2)
        except ValueError:
            pass
        else:
            raise AssertionError(bad)

    # Common is raw primary even when replacement removes all its effective cues.
    dem = Counter()
    with _san() as (video, sidecar), closing(db.mo(":memory:")) as con, _pipeline_gia(dem, sidecar):
        vung = [common, {**private, "cue": [0, 1]}]
        assert dieu_phoi.chay(
            video, TuyChon(blur_box=vung, che_do_vung="thay_the"),
            con=con, goi=lambda p: None).trang_thai == "xong"
        luu = doc_json(thu_muc_lam_viec(video) / "render_vung.json")
        assert luu["vung"][0][1] == [] and luu["vung"][1][1]
        assert {k: luu["hop_chinh"][k] for k in "xywh"} == \
               {k: common[k] for k in "xywh"}


def test_vung_cue_source_invalidation_before_side_effect():
    """V-06: checkpoint cue lech phai chan pipeline truoc khi doi artifact/DB."""
    from pipeline import db, dieu_phoi
    from pipeline.dieu_phoi import TuyChon
    from pipeline.srt import bam_file, thu_muc_lam_viec

    dem = Counter()
    with _san() as (video, sidecar), closing(db.mo(":memory:")) as con, _pipeline_gia(dem, sidecar):
        assert dieu_phoi.chay(video, TuyChon(blur="off"), con=con,
                              goi=lambda p: None).trang_thai == "xong"
        work = thu_muc_lam_viec(video)
        old_cue = bam_file(work / "sub_goc.srt")
        before_video = [tuple(row) for row in con.execute(
            "SELECT duong_dan,thu_muc_work,xong_luc FROM video")]
        before_log = con.execute("SELECT COUNT(*) FROM nhat_ky").fetchone()[0]
        _srt(sidecar, so=3)

        try:
            dieu_phoi.chay(video, TuyChon(blur="off", ky_cue=old_cue),
                           con=con, goi=lambda p: None)
        except RuntimeError as exc:
            assert "Phu de goc da doi" in str(exc)
        else:
            raise AssertionError("stale ky_cue duoc chap nhan")

        assert dem["subs"] == 1, "stale checkpoint khong duoc chay lai buoc sub"
        assert [tuple(row) for row in con.execute(
            "SELECT duong_dan,thu_muc_work,xong_luc FROM video")] == before_video
        assert con.execute("SELECT COUNT(*) FROM nhat_ky").fetchone()[0] == before_log
        assert bam_file(work / "sub_goc.srt") == old_cue


def test_vung_cue_signature_tracks_content_not_count():
    """V-06/LD-4: text, moc thoi gian va thu tu doi thi cache sub/vung cung doi."""
    from pipeline import db, dieu_phoi
    from pipeline.dieu_phoi import TuyChon
    from pipeline.srt import Cue, doc_srt, thu_muc_lam_viec, ghi_srt

    dem = Counter()
    with _san() as (video, sidecar), closing(db.mo(":memory:")) as con, _pipeline_gia(dem, sidecar):
        assert dieu_phoi.chay(video, TuyChon(blur="off"), con=con,
                              goi=lambda p: None).trang_thai == "xong"
        base_subs = dem["subs"]
        variants = (
            [Cue(1, 0.0, 1.5, "changed text"), Cue(2, 2.0, 3.5, "line 2")],
            [Cue(1, 0.2, 1.7, "changed text"), Cue(2, 2.0, 3.5, "line 2")],
            [Cue(1, 2.0, 3.5, "line 2"), Cue(2, 0.2, 1.7, "changed text")],
        )
        for cues in variants:
            ghi_srt(cues, sidecar)
            assert dieu_phoi.chay(video, TuyChon(blur="off"), con=con,
                                  goi=lambda p: None).trang_thai == "xong"
        assert dem["subs"] == base_subs + len(variants)
        assert len(doc_srt(thu_muc_lam_viec(video) / "sub_goc.srt")) == 2


def test_cached_region_mode_is_authoritative():
    """V-02/LD-7b: mode da luu duoc dung lai, khong bi default upload ghi de."""
    from pipeline import db, dieu_phoi
    from pipeline.dieu_phoi import TuyChon
    from pipeline.srt import bam_file, doc_json, doc_srt, thu_muc_lam_viec

    vung = [{"x": 0.3, "y": 0.85, "w": 0.4, "h": 0.09, "cue": None},
            {"x": 0.3, "y": 0.05, "w": 0.4, "h": 0.09, "cue": [1]}]
    with _san() as (video, sidecar), closing(db.mo(":memory:")) as con, _pipeline_gia(Counter(), sidecar):
        dieu_phoi.chay(video, TuyChon(blur_box=vung, che_do_vung="thay_the"),
                       con=con, goi=lambda p: None)
        work = thu_muc_lam_viec(video)
        assert doc_json(work / "vung_blur.json")["che_do_vung"] == "thay_the"
        cues = doc_srt(work / "sub_goc.srt")
        try:
            got = dieu_phoi._buoc_hop(
                video, work, TuyChon(blur="on", che_do_vung="cong_them"),
                1920, 1080, cues, bam_file(work / "sub_goc.srt"), bam_file,
                None, lambda hop: None)
        except dieu_phoi.ChoChonKhung as exc:
            raise AssertionError("cache mode thay_the bi default cong_them che") from exc
        assert got[1] == "thay_the" and got[0] == vung


def test_legacy_region_without_mode_is_not_valid_cache():
    """V-02/LD-7b: artifact cu thieu mode phai chon lai, khong default cache im lang."""
    from pipeline import db, dieu_phoi
    from pipeline.dieu_phoi import TuyChon
    from pipeline.srt import bam_file, chu_ky, doc_json, doc_srt, ghi_json, thu_muc_lam_viec

    vung = [{"x": 0.3, "y": 0.85, "w": 0.4, "h": 0.09, "cue": None},
            {"x": 0.3, "y": 0.05, "w": 0.4, "h": 0.09, "cue": [1]}]
    with _san() as (video, sidecar), closing(db.mo(":memory:")) as con, _pipeline_gia(Counter(), sidecar):
        dieu_phoi.chay(video, TuyChon(blur_box=vung), con=con, goi=lambda p: None)
        work = thu_muc_lam_viec(video)
        artifact = work / "vung_blur.json"
        luu = doc_json(artifact)
        luu.pop("che_do_vung")
        ghi_json(artifact, luu)
        _key = chu_ky(["vung_blur", bam_file(video), 1920, 1080,
                       bam_file(work / "sub_goc.srt"), "cong_them"])
        dieu_phoi._ghi_manifest(work, "vung_blur", _key, artifact)
        cues = doc_srt(work / "sub_goc.srt")
        try:
            dieu_phoi._buoc_hop(
                video, work, TuyChon(blur="on"), 1920, 1080, cues,
                bam_file(work / "sub_goc.srt"), bam_file, None, lambda hop: None)
        except dieu_phoi.ChoChonKhung:
            pass
        else:
            raise AssertionError("artifact thieu mode bi coi la cache hop le")


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
