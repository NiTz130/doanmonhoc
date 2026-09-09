"""V-9: route va trang thai cong viec. TestClient, khong mo cong mang, khong nap model."""
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import os
import tempfile

from pipeline.srt import Cue, ghi_srt


def _srt(path, so=3):
    ghi_srt([Cue(i + 1, i * 2.0, i * 2.0 + 1.5, f"line {i + 1}") for i in range(so)], path)


@contextmanager
def _san(co_sidecar=True, dich_loi=False):
    """Thu muc tam + pipeline gia: khong ffmpeg, khong mang, khong model."""
    from fastapi.testclient import TestClient
    from pipeline import dieu_phoi

    def tim_sidecar(video, lang="en"):
        # Tai len chi mang mot file, nen sidecar nam canh ban goc chu khong canh
        # ban da tai len; test tra thang duong dan do.
        p = Path("phim.en.srt").resolve()
        return p if co_sidecar and p.is_file() else None

    def tim_phu_de(video, ra, lang="en"):
        _srt(ra)
        return True

    def dich(lines, glossary, goi, lo=400):
        if dich_loi:
            raise RuntimeError("API dich hong")
        return SimpleNamespace(ban=[f"vi {s}" for s in lines], thuat_ngu_moi={},
                               giu_nguon=[], token_vao=0, token_ra=0)

    def trich_khung(video, cues, work, n=8):
        ra = []
        for i in range(min(n, len(cues))):
            p = Path(work) / f"khung_{i}.png"
            p.write_bytes(b"\x89PNG")
            ra.append(p)
        return ra

    from pipeline.markbox import kiem_hop, moc_khung
    mods = {
        "audio": SimpleNamespace(tach=lambda v, ra, separate=False:
                                 (Path(ra).write_bytes(b"wav"), Path(ra))[1]),
        "subs": SimpleNamespace(CODEC_CHU={"subrip"}, probe_subs=lambda v: [],
                                tim_sidecar=tim_sidecar, tim_phu_de=tim_phu_de),
        "asr": SimpleNamespace(nhan_dang=lambda *a, **k: None),
        "translate": SimpleNamespace(dich=dich),
        "markbox": SimpleNamespace(kiem_hop=kiem_hop, moc_khung=moc_khung,
                                   trich_khung=trich_khung),
        "render": SimpleNamespace(khoang_mo=lambda cues, dur: [(0.0, 1.9)],
                                  ket_xuat=lambda v, s, h, k, st, out: Path(out).write_bytes(b"mp4")),
    }
    with tempfile.TemporaryDirectory() as d:
        cu = Path.cwd()
        os.chdir(d)
        try:
            video = Path(d) / "phim.mp4"
            video.write_bytes(b"video")
            _srt(video.with_suffix(".en.srt"))
            # Khong doc .env, khong dung khoa that: tang dich da thay bang ban gia.
            with patch.object(dieu_phoi, "_nap", mods.__getitem__), \
                    patch.object(dieu_phoi, "nhan_dien", lambda v: (1920, 1080, 10.0)), \
                    patch("api.viec.tao_goi", lambda tc: (lambda payload: None)):
                from api.app import app
                with TestClient(app) as client:
                    yield client, video
        finally:
            os.chdir(cu)


def _tai_len(client, video, **truong):
    with open(video, "rb") as f:
        return client.post("/api/video", files={"file": (video.name, f, "video/mp4")},
                           data=truong)


def test_api_tai_len_va_ma_loi():
    with _san() as (client, video):
        def da_tai_len():
            return sorted(Path("work/tai_len").glob("**/*"))

        # File khong phai video: 400 va khong de lai rac trong work/.
        rac = Path("ghi_chu.txt")
        rac.write_text("khong phai video", encoding="utf-8")
        with open(rac, "rb") as f:
            kq = client.post("/api/video", files={"file": ("ghi_chu.txt", f, "text/plain")})
        assert kq.status_code == 400, kq.text
        assert da_tai_len() == [], "file khong hop le van de lai rac trong work/"

        # Duoi hop le nhung ffprobe tu choi: van 400, van khong ghi vao work/.
        with patch("pipeline.dieu_phoi.nhan_dien", side_effect=ValueError("khong co luong video")):
            with open(rac, "rb") as f:
                kq = client.post("/api/video", files={"file": ("gia.mp4", f, "video/mp4")})
        assert kq.status_code == 400, kq.text
        assert da_tai_len() == [], "file khong hop le van de lai rac trong work/"

        # Id khong ton tai: 404 va khong lo duong dan he thong.
        for duong in ("", "/khung", "/khung/0", "/ket-qua"):
            kq = client.get(f"/api/cong-viec/khong-co-that{duong}")
            assert kq.status_code == 404, (duong, kq.status_code)
            assert "work" not in kq.text and os.sep not in kq.json()["detail"]

        # blur khong hop le va hop khong hop le deu bi tu choi ngay o tang HTTP.
        assert _tai_len(client, video, blur="mo-het").status_code == 400
        assert _tai_len(client, video, blur_box="0.3,0.8,0.9,0.1").status_code == 400
        assert _tai_len(client, video, blur_box="mot,hai").status_code == 400


def test_api_cho_chon_khung_roi_chay_tiep():
    with _san() as (client, video):
        kq = _tai_len(client, video, blur="on")
        assert kq.status_code == 202, kq.text
        cid = kq.json()["id"]

        # Thieu khung mo la trang thai cho, khong phai loi.
        tt = client.get(f"/api/cong-viec/{cid}").json()
        assert tt["trang_thai"] == "cho_chon_khung" and tt["loi"] is None, tt

        khung = client.get(f"/api/cong-viec/{cid}/khung").json()
        assert len(khung) == 3 and khung[0]["giay"] == 0.3, khung
        assert client.get(f"/api/cong-viec/{cid}/khung/0").status_code == 200
        assert client.get(f"/api/cong-viec/{cid}/khung/99").status_code == 404
        assert client.get(f"/api/cong-viec/{cid}/ket-qua").status_code == 404

        # Hop sai bi tu choi bang dung validator LD-8 cua CLI.
        for xau in ({"x": -0.1, "y": 0.8, "w": 0.4, "h": 0.1},
                    {"x": 0.3, "y": 0.8, "w": 0.9, "h": 0.1},
                    {"x": 0.3, "y": 0.8, "w": 0.4}):
            r = client.post(f"/api/cong-viec/{cid}/hop", json=xau)
            assert r.status_code == 400, (xau, r.status_code)
        assert client.get(f"/api/cong-viec/{cid}").json()["trang_thai"] == "cho_chon_khung"

        # Hop dung: chay tiep tu buoc ket xuat va ve xong.
        r = client.post(f"/api/cong-viec/{cid}/hop",
                        json={"x": 0.3, "y": 0.85, "w": 0.4, "h": 0.09})
        assert r.status_code == 200, r.text
        tt = client.get(f"/api/cong-viec/{cid}").json()
        assert tt["trang_thai"] == "xong" and tt["tien_do"] == 1.0, tt
        assert client.get(f"/api/cong-viec/{cid}/ket-qua").status_code == 200

        # Bo qua ve hop = blur off, van ra video.
        cid2 = _tai_len(client, video, blur="on").json()["id"]
        client.post(f"/api/cong-viec/{cid2}/hop", json={"co_blur": False})
        assert client.get(f"/api/cong-viec/{cid2}").json()["trang_thai"] == "xong"


def test_api_loi_nen_va_lock():
    # Ngoai le trong tac vu nen phai thanh trang thai loi, khong treo o dang_chay.
    with _san(dich_loi=True) as (client, video):
        cid = _tai_len(client, video, blur="off").json()["id"]
        tt = client.get(f"/api/cong-viec/{cid}").json()
        assert tt["trang_thai"] == "loi" and "API dich hong" in tt["loi"], tt

    # Cong viec thu hai tren cung work directory bi tu choi bang 409.
    with _san() as (client, video):
        from pipeline.srt import thu_muc_lam_viec
        with patch("api.app.thu_muc_lam_viec", lambda v: Path("work") / "dung-chung") as _:
            (Path("work") / "dung-chung").mkdir(parents=True, exist_ok=True)
            (Path("work") / "dung-chung" / ".lock").write_text("1234", encoding="utf-8")
            assert _tai_len(client, video).status_code == 409
        assert thu_muc_lam_viec(video).name.startswith("phim-")


def test_api_va_cli_cung_ket_qua():
    """AC-9: hai duong vao dung chung dieu_phoi nen phai cho ra cung artifact."""
    from contextlib import closing
    from pipeline import db, dieu_phoi
    from pipeline.dieu_phoi import TuyChon
    from pipeline.srt import thu_muc_lam_viec
    hop = {"x": 0.3, "y": 0.85, "w": 0.4, "h": 0.09}
    with _san() as (client, video):
        cid = _tai_len(client, video, blur="on",
                       blur_box="0.3,0.85,0.4,0.09").json()["id"]
        assert client.get(f"/api/cong-viec/{cid}").json()["trang_thai"] == "xong"
        qua_api = (thu_muc_lam_viec(Path("work") / "tai_len" / cid / "phim.mp4")
                   / "sub_vi.srt").read_text(encoding="utf-8")

        ban_sao = Path("ban_sao.mp4")
        ban_sao.write_bytes(video.read_bytes())
        _srt(ban_sao.with_suffix(".en.srt"))
        with closing(db.mo(Path("work") / "subtitles.db")) as con:
            kq = dieu_phoi.chay(ban_sao, TuyChon(blur="on", blur_box=hop), con=con,
                                goi=lambda p: None)
        assert kq.trang_thai == "xong"
        qua_cli = (kq.work / "sub_vi.srt").read_text(encoding="utf-8")
        assert qua_api == qua_cli, "API va CLI cho ban dich khac nhau"


if __name__ == "__main__":
    for ten, ham in list(globals().items()):
        if ten.startswith("test_"):
            ham()
            print("PASS", ten)
