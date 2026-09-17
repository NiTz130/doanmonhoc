"""V-9: route va trang thai cong viec. TestClient, khong mo cong mang, khong nap model."""
from collections import Counter
from contextlib import closing, contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import os
import tempfile

from pipeline.srt import Cue, ghi_srt


def _srt(path, so=3):
    ghi_srt([Cue(i + 1, i * 2.0, i * 2.0 + 1.5, f"line {i + 1}") for i in range(so)], path)


@contextmanager
def _san(co_sidecar=True, dich_loi=False, dem: Counter | None = None,
         raise_server_exceptions=True):
    """Thu muc tam + pipeline gia: khong ffmpeg, khong mang, khong model."""
    from fastapi.testclient import TestClient
    from pipeline import dieu_phoi

    def tim_sidecar(video, lang="en"):
        # Tai len chi mang mot file, nen sidecar nam canh ban goc chu khong canh
        # ban da tai len; test tra thang duong dan do.
        p = Path("phim.en.srt").resolve()
        return p if co_sidecar and p.is_file() else None

    def tim_phu_de(video, ra, lang="en"):
        if dem is not None:
            dem["subs"] += 1
        _srt(ra)
        return True

    def dich(lines, glossary, goi, lo=400):
        if dem is not None:
            dem["dich"] += 1
        if dich_loi:
            raise RuntimeError("API dich hong")
        return SimpleNamespace(ban=[f"vi {s}" for s in lines], thuat_ngu_moi={},
                               giu_nguon=[], token_vao=0, token_ra=0)

    def trich_khung(video, cues, work):
        if dem is not None:
            dem["khung"] += 1
        ra = []
        for i in range(len(cues)):
            p = Path(work) / f"khung_{i}.png"
            p.write_bytes(b"\x89PNG")
            ra.append(p)
        return ra

    def tach(v, ra, separate=False):
        if dem is not None:
            dem["audio"] += 1
        p = Path(ra).with_name("vocals.wav") if separate else Path(ra)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"wav")
        return p

    def nhan_dang(*args, **kwargs):
        if dem is not None:
            dem["asr"] += 1
        _srt(args[1])

    def ket_xuat(v, s, vg, st, out, *, loai_tru_chung=None):
        if dem is not None:
            dem["render"] += 1
        Path(out).write_bytes(b"mp4")

    from pipeline.markbox import kiem_vung, moc_khung
    from pipeline.render import gop_khoang
    mods = {
        "audio": SimpleNamespace(tach=tach),
        "subs": SimpleNamespace(CODEC_CHU={"subrip"}, probe_subs=lambda v: [],
                                tim_sidecar=tim_sidecar, tim_phu_de=tim_phu_de),
        "asr": SimpleNamespace(nhan_dang=nhan_dang),
        "translate": SimpleNamespace(dich=dich),
        "markbox": SimpleNamespace(kiem_vung=kiem_vung, moc_khung=moc_khung,
                                   trich_khung=trich_khung),
        "render": SimpleNamespace(khoang_mo=lambda cues, dur: [(0.0, 1.9)],
                                  gop_khoang=gop_khoang, ket_xuat=ket_xuat),
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
                with TestClient(app, raise_server_exceptions=raise_server_exceptions) as client:
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
        # Mot khung moi cue: lay mau thi khong kiem duoc hop da phu het phu de chua.
        assert len(khung) == 3 and khung[0]["giay"] == 0.3, khung
        assert [k["i"] for k in khung] == [0, 1, 2], khung
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
        # Nguon xu ly la ban canonical theo noi dung + nhom (LD-1), khong phai
        # duong dan theo CID: CID chi so huu output va khung mau.
        from api import viec as _viec
        qua_api = (thu_muc_lam_viec(_viec.lay(cid).video)
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


def test_api_concurrent_requests_share_no_sqlite_connection():
    """V-01: cac request that khong duoc dung chung connection sqlite cua nhau."""
    from concurrent.futures import ThreadPoolExecutor

    with _san() as (client, video):
        def doc(_):
            try:
                r = client.get("/api/nhom")
                return r.status_code, r.text
            except BaseException as exc:
                return None, repr(exc)

        with ThreadPoolExecutor(max_workers=8) as pool:
            ket = list(pool.map(doc, range(40)))
        assert all(status == 200 for status, _ in ket), ket


def test_api_sqlite_connection_lifecycle_and_rollback():
    """V-01: dependency dong connection khi route ket thuc va rollback loi."""
    import sqlite3
    from api.viec import ket_noi

    with _san() as (client, video):
        generator = ket_noi()
        con = next(generator)
        assert con.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        generator.close()
        try:
            con.execute("SELECT 1")
        except sqlite3.ProgrammingError:
            pass
        else:
            raise AssertionError("connection dependency khong dong sau request")

        before = client.get("/api/nhom").json()
        invalid = client.post("/api/nhom/rollback/thuat-ngu",
                              json={"goc": "", "dich": "khong duoc ghi"})
        assert invalid.status_code == 400, invalid.text
        assert client.get("/api/nhom").json() == before


def test_api_canonical_identity_cache_and_no_overwrite():
    """V-03/LD-1: cung hash+nhom dung cache, CID va output van rieng."""
    from pipeline.srt import bam_file, chu_ky
    from api import viec

    dem = Counter()
    with _san(dem=dem) as (client, video):
        one = _tai_len(client, video, nhom="A", blur="off")
        assert one.status_code == 202, one.text
        cid1 = one.json()["id"]
        h1 = viec.lay(cid1)
        assert h1 is not None
        source = h1.video
        assert source.name == "nguon.media" and bam_file(source) == bam_file(video)
        assert source.parent.parent.name == chu_ky(["nhom", "A"])[:16]
        counts = dem.copy()

        renamed = Path("renamed.mkv")
        renamed.write_bytes(video.read_bytes())
        two = _tai_len(client, renamed, nhom="A", blur="off")
        assert two.status_code == 202, two.text
        h2 = viec.lay(two.json()["id"])
        assert h2 is not None and h2.video == source
        assert h2.tc.ra != h1.tc.ra and h2.tc.ra.name == "renamed_vi.mp4"
        assert dem["subs"] == counts["subs"] and dem["dich"] == counts["dich"]

        # Khong duoc ghi de canonical da ton tai neu noi dung ben trong bi sai.
        source.write_bytes(b"canonical-do-not-overwrite")
        assert _tai_len(client, video, nhom="A", blur="off").status_code == 409
        assert source.read_bytes() == b"canonical-do-not-overwrite"

        # Doi nhom hoac doi bytes tao namespace/work khac; "None" la ten nhom that.
        other_group = _tai_len(client, video, nhom="B", blur="off")
        no_group = _tai_len(client, video, blur="off")
        literal_none = _tai_len(client, video, nhom="None", blur="off")
        assert other_group.status_code == no_group.status_code == literal_none.status_code == 202
        assert viec.lay(other_group.json()["id"]).video != source
        assert viec.lay(no_group.json()["id"]).video != viec.lay(literal_none.json()["id"]).video


def test_api_upload_and_resume_claim_is_single_winner():
    """V-04/LD-6: race cung resource co mot claim, ben con lai 409 va khong rac."""
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from pipeline import db
    from api import viec
    from pipeline.srt import thu_muc_lam_viec

    started = Event()
    release = Event()
    dem = Counter()
    with _san(dem=dem) as (client, video):
        real = viec.chay_nen

        def dung(cid):
            started.set()
            assert release.wait(5), "background admission khong duoc giai phong"
            real(cid)

        with patch.object(viec, "chay_nen", dung):
            pool = ThreadPoolExecutor(max_workers=2)
            first = pool.submit(_tai_len, client, video, nhom="race", blur="off")
            assert started.wait(5), "upload dau chua claim xong"
            second = pool.submit(_tai_len, client, video, nhom="race", blur="off")
            r2 = second.result(timeout=10)
            assert r2.status_code == 409, r2.text
            release.set()
            r1 = first.result(timeout=10)
            pool.shutdown(wait=True)
        assert r1.status_code == 202, r1.text

        with closing(db.mo(Path("work") / "subtitles.db")) as con:
            assert con.execute("SELECT COUNT(*) FROM cong_viec").fetchone()[0] == 1
        assert not list(Path("work").glob("**/*.tmp"))
        ho_so = viec.lay(r1.json()["id"])
        assert ho_so is not None and ho_so.khoa is None
        assert not thu_muc_lam_viec(ho_so.video).joinpath(".lock").exists()


def test_api_resume_claim_is_single_winner():
    """V-04/LD-6: hai POST cung CID khong duoc cung qua admission."""
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from api import viec

    entered = Event()
    release = Event()
    with _san() as (client, video):
        cid = _tai_len(client, video, blur="on").json()["id"]
        real_claim = viec.gianh_khoa

        def hold_claim(work):
            path = real_claim(work)
            entered.set()
            assert release.wait(5), "claim dau khong duoc giai phong"
            return path

        body = {"x": 0.3, "y": 0.85, "w": 0.4, "h": 0.09,
                "che_do_vung": "thay_the"}
        with patch.object(viec, "gianh_khoa", hold_claim):
            with ThreadPoolExecutor(max_workers=2) as pool:
                first = pool.submit(client.post, f"/api/cong-viec/{cid}/hop", json=body)
                assert entered.wait(5), "POST dau chua claim work"
                second = pool.submit(client.post, f"/api/cong-viec/{cid}/hop", json=body)
                try:
                    r2 = second.result(timeout=10)
                finally:
                    release.set()
                r1 = first.result(timeout=10)
        assert r2.status_code == 409, r2.text
        assert r1.status_code == 200, r1.text
        assert client.get(f"/api/cong-viec/{cid}").json()["trang_thai"] != "loi"


def test_api_scheduler_failure_cleans_admission():
    """V-04: loi truoc add_task khong de queued job/lock so huu bi ro."""
    from pipeline import db
    from api import viec
    from pipeline.srt import thu_muc_lam_viec

    with _san(raise_server_exceptions=False) as (client, video):
        with patch("api.app.BackgroundTasks.add_task",
                   side_effect=RuntimeError("scheduler down")):
            response = _tai_len(client, video, nhom="scheduler", blur="off")
        assert response.status_code == 500, response.text

        with closing(db.mo(Path("work") / "subtitles.db")) as con:
            rows = con.execute("SELECT id, trang_thai FROM cong_viec").fetchall()
        assert all(row[1] != "cho" for row in rows), \
            [(row["id"], row["trang_thai"]) for row in rows]
        assert not list(Path("work").glob("**/*.tmp"))
        for cid in viec.dang_theo_doi():
            ho_so = viec.lay(cid)
            assert ho_so is not None and ho_so.khoa is None, (cid, ho_so)
            assert not thu_muc_lam_viec(ho_so.video).joinpath(".lock").exists()


def test_api_cue_index_out_of_range_is_rejected():
    """V-02/IC-5: HTTP khong duoc bo qua cue index ngoai pham vi."""
    from api import viec

    with _san() as (client, video):
        cid = _tai_len(client, video, blur="on").json()["id"]
        ho_so = viec.lay(cid)
        assert ho_so is not None and ho_so.checkpoint
        checkpoint = ho_so.checkpoint.copy()
        response = client.post(
            f"/api/cong-viec/{cid}/hop",
            json={"che_do_vung": "thay_the",
                  "vung": [{"x": 0.3, "y": 0.85, "w": 0.4, "h": 0.09,
                            "cue": [99]}]},
        )
        assert response.status_code == 400, response.text
        assert viec.lay(cid).checkpoint == checkpoint
        assert client.get(f"/api/cong-viec/{cid}").json()["trang_thai"] == "cho_chon_khung"


def test_api_mode_validation_before_mutation():
    """V-02/LD-7a: mode co mat nhung loi bi tu choi truoc khi doi job."""
    from api import viec

    for value in (None, True, 1, "THAY_THE"):
        with _san() as (client, video):
            cid = _tai_len(client, video, blur="on").json()["id"]
            ho_so = viec.lay(cid)
            assert ho_so is not None and ho_so.checkpoint
            before = ho_so.checkpoint.copy()
            body = {"co_blur": False, "che_do_vung": value}
            r = client.post(f"/api/cong-viec/{cid}/hop", json=body)
            assert r.status_code == 400, (value, r.status_code, r.text)
            assert viec.lay(cid).checkpoint == before
            assert client.get(f"/api/cong-viec/{cid}").json()["trang_thai"] == "cho_chon_khung"


def test_api_stale_cid_snapshot():
    """V-06/LD-4: cue snapshot CID cu khong duoc chay voi sub da doi."""
    from api import viec
    from pipeline.srt import bam_file, thu_muc_lam_viec

    with _san() as (client, video):
        cid = _tai_len(client, video, blur="on").json()["id"]
        ho_so = viec.lay(cid)
        assert ho_so is not None and ho_so.checkpoint
        snap = Path("work") / "tai_len" / cid / "khung" / "sub_goc.srt"
        old_snapshot_hash = bam_file(snap)
        assert len(client.get(f"/api/cong-viec/{cid}/khung").json()) == 3
        _srt(thu_muc_lam_viec(ho_so.video) / "sub_goc.srt", so=4)
        assert bam_file(snap) == old_snapshot_hash
        stale = client.post(f"/api/cong-viec/{cid}/hop",
                            json={"x": 0.3, "y": 0.85, "w": 0.4, "h": 0.09,
                                  "che_do_vung": "thay_the"})
        assert stale.status_code == 409, stale.text
        assert len(client.get(f"/api/cong-viec/{cid}/khung").json()) == 3
        assert client.get(f"/api/cong-viec/{cid}").json()["trang_thai"] == "cho_chon_khung"


def test_api_restart_marks_only_orphans_and_keeps_completed_output():
    """V-07/LD-5: restart chi loi job mat ho so; terminal va lock duoc giu."""
    from contextlib import closing
    from fastapi.testclient import TestClient
    from pipeline import db
    from api import viec
    from api.app import app

    with _san() as (_client, _video):
        done = Path("work") / "done.mp4"
        done.parent.mkdir(parents=True, exist_ok=True)
        done.write_bytes(b"done")
        ids = {status: f"restart-{status}" for status in
               ("cho", "dang_chay", "cho_chon_khung", "xong", "suy_giam", "loi")}
        with closing(db.mo(Path("work") / "subtitles.db")) as con:
            for status, cid in ids.items():
                db.tao_cong_viec(con, cid)
                db.cap_nhat_cong_viec(con, cid, trang_thai=status,
                                      loi="old error" if status == "loi" else None,
                                      **({"duong_dan_ra": str(done)} if status == "xong" else {}))
            con.commit()
        lock = Path("work") / "orphan" / ".lock"
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text("left by crashed operator", encoding="utf-8")
        with viec._KHOA:
            viec._HO_SO.clear()

        with TestClient(app) as restarted:
            for status in ("cho", "dang_chay", "cho_chon_khung"):
                r = restarted.get(f"/api/cong-viec/{ids[status]}")
                assert r.status_code == 200 and r.json()["trang_thai"] == "loi", r.text
                assert "khởi động lại" in r.json()["loi"]
                assert restarted.post(f"/api/cong-viec/{ids[status]}/hop",
                                      json={"co_blur": False}).status_code == 409
            assert restarted.get(f"/api/cong-viec/{ids['xong']}/ket-qua").content == b"done"
            assert restarted.get("/api/cong-viec/no-such-id").status_code == 404
            assert restarted.get(f"/api/cong-viec/{ids['suy_giam']}").json()["trang_thai"] == "suy_giam"
            assert restarted.get(f"/api/cong-viec/{ids['loi']}").json()["loi"] == "old error"
        assert lock.read_text(encoding="utf-8") == "left by crashed operator"


def test_api_force_resume_keeps_source_and_does_not_repeat_asr():
    """V-05/LD-3: force-asr chay moi, POST vung chi tiep tuc checkpoint da ghim."""
    from api import viec

    dem = Counter()
    with _san(dem=dem) as (client, video):
        first = _tai_len(client, video, blur="on", force_asr="true", separate="true")
        assert first.status_code == 202, first.text
        cid = first.json()["id"]
        assert (dem["audio"], dem["asr"], dem["dich"]) == (1, 1, 0)
        cp = viec.lay(cid).checkpoint
        assert cp["nguon_sub"] == "asr" and cp["force_dich"] is True

        resumed = client.post(
            f"/api/cong-viec/{cid}/hop",
            json={"x": 0.3, "y": 0.85, "w": 0.4, "h": 0.09,
                  "che_do_vung": "thay_the"})
        assert resumed.status_code == 200, resumed.text
        assert (dem["audio"], dem["asr"], dem["dich"], dem["render"]) == (1, 1, 1, 1), \
            (dem, client.get(f"/api/cong-viec/{cid}").text)
        assert viec.lay(cid).tc.nguon_sub == "asr"

    # A new forced invocation is different from the resume POST: every dependent
    # cached stage is actually refreshed, even though fake ASR returns same cues.
    dem = Counter()
    with _san(co_sidecar=False, dem=dem) as (client, video):
        assert _tai_len(client, video, blur="off").status_code == 202
        assert (dem["audio"], dem["asr"], dem["dich"]) == (1, 1, 1)
        assert _tai_len(client, video, blur="off", force="true").status_code == 202
        assert (dem["audio"], dem["asr"], dem["dich"]) == (2, 2, 2)


if __name__ == "__main__":
    for ten, ham in list(globals().items()):
        if ten.startswith("test_"):
            ham()
            print("PASS", ten)
