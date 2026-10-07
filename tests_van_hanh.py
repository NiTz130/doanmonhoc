"""V-12: van hanh — tra cuu, xoa, nhat ky, sao luu/khoi phuc, don dep, kiem tuy chon.

Offline, khong mang, khong GPU, khong nap model (dung `_san` cua tests_api).
Moi test bao gom duong chinh, bien va loi; test hoi quy ghi ro loi nao no giu.
"""
from __future__ import annotations

import math
import os
import sqlite3
import subprocess
import tempfile
import time
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from pipeline import db
from tests_api import _san, _tai_len


def _loi(ham, loai=ValueError, *a, **kw):
    try:
        ham(*a, **kw)
    except loai as exc:
        return exc
    raise AssertionError(f"{ham} khong nem {loai.__name__}")


# --------------------------------------------------------------- db: tra cuu chi doc

def test_get_khong_tao_nhom_va_gioi_han_do_dai():
    """Hoi quy: GET thuat-ngu/hop cua ten go sai tung INSERT mot nhom rac."""
    with closing(db.mo(":memory:")) as con:
        _loi(db.tim_nhom, db.KhongCo, con, "go_sai")
        assert con.execute("SELECT count(*) FROM nhom").fetchone()[0] == 0
        with con:
            nid = db.lay_nhom(con, "A" * db.TEN_NHOM_TOI_DA)
        assert db.tim_nhom(con, "A" * db.TEN_NHOM_TOI_DA) == nid
        for xau in ("A" * (db.TEN_NHOM_TOI_DA + 1), "", "   ", None, 5):
            _loi(db.lay_nhom, ValueError, con, xau)
            _loi(db.tim_nhom, ValueError, con, xau)
        db.ghi_thuat_ngu(con, nid, {"g" * db.THUAT_NGU_TOI_DA: "d" * db.THUAT_NGU_TOI_DA})
        for xau in ({"g" * 201: "d"}, {"g": "d" * 201}):
            _loi(db.ghi_thuat_ngu, ValueError, con, nid, xau)
            _loi(db.dat_thuat_ngu, ValueError, con, nid, *next(iter(xau.items())))
        assert con.execute("SELECT count(*) FROM nhom").fetchone()[0] == 1


def test_wal_chi_muc_va_khoa_ngoai():
    with tempfile.TemporaryDirectory() as d:
        with closing(db.mo(Path(d) / "x.db")) as con:
            assert con.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
            assert con.execute("PRAGMA foreign_keys").fetchone()[0] == 1
            chi_muc = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='index'")}
            assert {"ix_nhat_ky_video", "ix_cong_viec_tt", "ix_lich_su_nhom", "ix_video_nhom"} <= chi_muc
        with closing(db.mo(Path(d) / "x.db")) as con:           # mo lai: schema idempotent
            assert con.execute("SELECT count(*) FROM lich_su").fetchone()[0] == 0
    with closing(db.mo(":memory:")) as con:                      # :memory: khong co WAL, van chay
        assert con.execute("PRAGMA journal_mode").fetchone()[0] == "memory"


def test_trigger_lich_su_moi_duong_ghi():
    with closing(db.mo(":memory:")) as con:
        with con:
            nid = db.lay_nhom(con, "Phim")
            db.dat_thuat_ngu(con, nid, "Ironhold", "Thành Sắt")
            db.dat_thuat_ngu(con, nid, "Ironhold", "Thành Sắt")        # khong doi: khong ghi them
        ls, tong = db.liet_ke_lich_su(con)
        assert tong == 2 and {(r["doi_tuong"], r["hanh_dong"]) for r in ls} == {
            ("nhom", "tao"), ("thuat_ngu", "tao")}, ls
        with con:
            db.dat_thuat_ngu(con, nid, "Ironhold", "Thành Thép")
            db.ghi_hop(con, nid, {"x": 0.1, "y": 0.2, "w": 0.3, "h": 0.4})
            db.ghi_hop(con, nid, {"x": 0.1, "y": 0.2, "w": 0.3, "h": 0.4})   # trung: khong ghi
            db.ghi_hop(con, nid, {"x": 0.1, "y": 0.2, "w": 0.3, "h": 0.5})
            # Duong ghi khong qua dat_thuat_ngu (hoc thuat ngu trong job) cung de lai dau vet.
            db.ghi_thuat_ngu(con, nid, {"Castle": "Lâu đài"})
        sua = db.liet_ke_lich_su(con, nid, hanh_dong="sua")[0]
        assert [(r["doi_tuong"], r["cu"], r["moi"]) for r in sua] == [
            ("nhom", "0.1,0.2,0.3,0.4", "0.1,0.2,0.3,0.5"),
            ("nhom", None, "0.1,0.2,0.3,0.4"),
            ("thuat_ngu", "Thành Sắt", "Thành Thép")], sua
        assert db.liet_ke_lich_su(con, nid, doi_tuong="thuat_ngu", hanh_dong="tao")[1] == 2
        with con:
            db.xoa_thuat_ngu(con, nid, "Castle")
        assert db.liet_ke_lich_su(con, nid, hanh_dong="xoa")[0][0]["cu"] == "Lâu đài"
        with con:
            db.xoa_nhom(con, nid)
        # Xoa nhom keo thuat ngu theo; dau vet nhom bi xoa phai con de truy nguoc.
        xoa = db.liet_ke_lich_su(con, nid, doi_tuong="nhom", hanh_dong="xoa")
        assert xoa[1] == 1 and xoa[0][0]["khoa"] == "Phim"
        # Lich su khong co khoa ngoai: khong bi xoa day chuyen cung nhom.
        assert db.liet_ke_lich_su(con, nid)[1] >= 8


def test_hop_nhom_ghi_roi_xoa_khong_vo_trigger_khi_hop_rong():
    """Hop tu NULL ve NULL khong ghi, hop dang NULL doi sang gia tri thi cu = NULL."""
    with closing(db.mo(":memory:")) as con:
        with con:
            nid = db.lay_nhom(con, "N")
            con.execute("UPDATE nhom SET blur_x=NULL WHERE id=?", (nid,))
        assert db.liet_ke_lich_su(con, nid, hanh_dong="sua")[1] == 0


# --------------------------------------------------------------- db: liet ke, tim, phan trang

def test_liet_ke_nhom_tim_khong_dau_sap_xep_phan_trang():
    with closing(db.mo(":memory:")) as con:
        with con:
            for ten in ("Thành Sắt", "Ironhold", "100%_xong", "Đất Nước", "abc"):
                db.lay_nhom(con, ten)
        ten = lambda ds: [r["ten"] for r in ds]
        ds, tong = db.liet_ke_nhom(con, q="thanh sat")                  # khong dau, khong hoa/thuong
        assert ten(ds) == ["Thành Sắt"] and tong == 1
        assert ten(db.liet_ke_nhom(con, q="dat nuoc")[0]) == ["Đất Nước"]   # đ -> d
        assert ten(db.liet_ke_nhom(con, q="%")[0]) == ["100%_xong"]         # % la ky tu thuong
        # Sap theo chu khong dau: "Đất" xep o D (giua abc va Ironhold), khong roi xuong sau Z.
        assert ten(db.liet_ke_nhom(con)[0]) == ["100%_xong", "abc", "Đất Nước", "Ironhold", "Thành Sắt"]
        assert ten(db.liet_ke_nhom(con, q="_")[0]) == ["100%_xong"]
        assert db.liet_ke_nhom(con, q="khong-co")[1] == 0
        assert db.liet_ke_nhom(con, q="   ")[1] == 5                         # q rong = khong loc
        assert ten(db.liet_ke_nhom(con, sap_xep="ten", thu_tu="desc")[0])[0] == "Thành Sắt"
        trang1, tong = db.liet_ke_nhom(con, moi_trang=2, trang=1)
        trang3, _ = db.liet_ke_nhom(con, moi_trang=2, trang=3)
        assert (len(trang1), len(trang3), tong) == (2, 1, 5)                # tong dem truoc khi cat
        assert db.liet_ke_nhom(con, moi_trang=2, trang=9)[0] == []           # qua trang cuoi: rong, khong loi
        for xau in ({"trang": 0}, {"trang": -1}, {"moi_trang": 0}, {"moi_trang": 201},
                    {"trang": True}, {"moi_trang": "5"}, {"sap_xep": "id; DROP TABLE nhom"},
                    {"thu_tu": "up"}):
            _loi(db.liet_ke_nhom, ValueError, con, **xau)
        assert con.execute("SELECT count(*) FROM nhom").fetchone()[0] == 5


def test_liet_ke_thuat_ngu_cong_viec_nhat_ky():
    with closing(db.mo(":memory:")) as con:
        with con:
            nid = db.lay_nhom(con, "P")
            db.ghi_thuat_ngu(con, nid, {"Ironhold": "Thành Sắt", "King": "Vua", "Queen": "Nữ hoàng"})
            vid = db.ghi_video(con, "a.mp4", "work/a-1", nid, 1280, 720, 5.0)
            db.ghi_nhat_ky(con, vid, "asr", "xong", giay=1.5)
            db.ghi_nhat_ky(con, vid, "translate", "suy_giam", loi="cue 1")
            db.ghi_nhat_ky(con, vid, "translate_apply", "xong")
            for i, tt in enumerate(("cho", "dang_chay", "xong", "loi")):
                db.tao_cong_viec(con, f"c{i}")
                db.cap_nhat_cong_viec(con, f"c{i}", trang_thai=tt)
        tn, tong = db.liet_ke_thuat_ngu(con, nid, q="vua")                 # tim ca ve dich, khong dau
        assert tn == {"King": "Vua"} and tong == 1
        assert db.liet_ke_thuat_ngu(con, nid, q="iron")[0] == {"Ironhold": "Thành Sắt"}
        assert list(db.liet_ke_thuat_ngu(con, nid, sap_xep="dich", thu_tu="desc")[0])[0] == "King"
        assert list(db.liet_ke_thuat_ngu(con, nid, moi_trang=1, trang=2)[0]) == ["King"]
        _loi(db.liet_ke_thuat_ngu, ValueError, con, nid, sap_xep="x")

        cv, tong = db.liet_ke_cong_viec(con, trang_thai="xong")
        assert [r["id"] for r in cv] == ["c2"] and tong == 1 and cv[0]["co_ket_qua"] is False
        assert db.liet_ke_cong_viec(con)[1] == 4
        _loi(db.liet_ke_cong_viec, ValueError, con, trang_thai="hu")
        _loi(db.liet_ke_cong_viec, ValueError, con, sap_xep="loi")

        nk, tong = db.liet_ke_nhat_ky(con)
        # Dau 'translate_apply' la khoa idempotency noi bo: an di tru khi hoi dung buoc do.
        assert [r["buoc"] for r in nk] == ["translate", "asr"] and tong == 2
        assert db.liet_ke_nhat_ky(con, buoc="translate_apply")[1] == 1
        assert db.liet_ke_nhat_ky(con, ket_qua="suy_giam")[0][0]["loi"] == "cue 1"
        assert db.liet_ke_nhat_ky(con, video_id=vid + 99)[1] == 0
        assert nk[0]["thu_muc_work"] == "a-1"                              # chi ten, khong lo duong dan
        _loi(db.liet_ke_lich_su, ValueError, con, doi_tuong="khac")
        _loi(db.liet_ke_lich_su, ValueError, con, hanh_dong="khac")


# --------------------------------------------------------------- db: xoa

def test_xoa_nhom_thuat_ngu_va_chan_khi_dang_chay():
    with closing(db.mo(":memory:")) as con:
        with con:
            nid = db.lay_nhom(con, "P")
            db.ghi_thuat_ngu(con, nid, {"a": "b"})
            db.tao_cong_viec(con, "j")
        for tt in ("cho", "dang_chay"):
            with con:
                db.cap_nhat_cong_viec(con, "j", trang_thai=tt)
            _loi(db.xoa_nhom, db.DangBan, con, nid)
            _loi(db.xoa_thuat_ngu, db.DangBan, con, nid, "a")
        assert db.doc_thuat_ngu(con, nid) == {"a": "b"}                      # khong doi gi
        with con:
            db.cap_nhat_cong_viec(con, "j", trang_thai="cho_chon_khung")      # dung yen: khong chan
        with con:
            db.xoa_thuat_ngu(con, nid, "a")
        _loi(db.xoa_thuat_ngu, db.KhongCo, con, nid, "a")
        with con:
            db.xoa_nhom(con, nid)
        assert con.execute("SELECT count(*) FROM nhom").fetchone()[0] == 0


# --------------------------------------------------------------- sao luu, khoi phuc

def test_sao_luu_khoi_phuc_va_tu_choi_file_hong():
    from pipeline import dieu_phoi
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        with closing(db.mo(d / "s.db")) as con:
            with con:
                nid = db.lay_nhom(con, "Phim")
                db.ghi_thuat_ngu(con, nid, {"Ironhold": "Thành Sắt"})
            ban = dieu_phoi.sao_luu(con, d / "bk")
            assert ban.is_file() and not list((d / "bk").glob("*.tmp")), "con file tam"
            db._kiem_file_db(ban)
            with con:
                db.xoa_nhom(con, nid)
                db.lay_nhom(con, "Khac")
            an_toan = dieu_phoi.khoi_phuc(con, ban, d / "bk")
            assert db.doc_thuat_ngu(con, db.tim_nhom(con, "Phim")) == {"Ironhold": "Thành Sắt"}
            _loi(db.tim_nhom, db.KhongCo, con, "Khac")
            # Ban chup truoc khi khoi phuc giu trang thai TRUOC do: khoi phuc nham van quay lai duoc.
            with closing(db.mo(an_toan)) as cu:
                assert db.tim_nhom(cu, "Khac") and _loi(db.tim_nhom, db.KhongCo, cu, "Phim")

            # File khong phai SQLite, file rong, file thieu bang, file khong ton tai: tu choi,
            # CSDL dang dung nguyen ven.
            rac = d / "rac.db"
            rac.write_bytes(b"day khong phai sqlite" * 50)
            rong = d / "rong.db"
            rong.write_bytes(b"")
            thieu = d / "thieu.db"
            with closing(sqlite3.connect(thieu)) as r:
                r.execute("CREATE TABLE x(a)")
            for xau in (rac, rong, thieu):
                _loi(dieu_phoi.khoi_phuc, ValueError, con, xau, d / "bk")
            _loi(dieu_phoi.khoi_phuc, (ValueError, FileNotFoundError, sqlite3.DatabaseError),
                 con, d / "khong-co.db", d / "bk")
            assert db.doc_thuat_ngu(con, db.tim_nhom(con, "Phim")) == {"Ironhold": "Thành Sắt"}

            # Dang co cong viec chay: khong duoc doi nen CSDL duoi chan no.
            with con:
                db.tao_cong_viec(con, "j")
                db.cap_nhat_cong_viec(con, "j", trang_thai="dang_chay")
            _loi(db.khoi_phuc, db.DangBan, con, ban)
            with con:
                db.cap_nhat_cong_viec(con, "j", trang_thai="xong")


def test_khoi_phuc_don_cong_viec_mat_ho_so_va_ban_cu_thieu_trigger():
    """Khoi phuc ban cu: bang/trigger moi duoc bo sung; cong viec dang do cua ban sao bi bao loi."""
    from pipeline import dieu_phoi
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        cu = d / "cu.db"
        with closing(db.mo(cu)) as con:
            with con:
                db.tao_cong_viec(con, "treo")
                db.cap_nhat_cong_viec(con, "treo", trang_thai="dang_chay")
        # Mo phong ban sao luu doi cu: khong co bang lich_su.
        with closing(sqlite3.connect(cu)) as raw:
            for tg in [r[0] for r in raw.execute("SELECT name FROM sqlite_master WHERE type='trigger'")]:
                raw.execute(f"DROP TRIGGER {tg}")
            raw.execute("DROP TABLE lich_su")
            raw.commit()
        with closing(db.mo(d / "s.db")) as con:
            # cong viec dang_chay trong ban sao => job nay khong con chu o tien trinh nay.
            # Chi khoi phuc duoc sau khi CSDL hien tai khong co viec chay.
            dieu_phoi.khoi_phuc(con, cu, d / "bk")
            row = db.doc_cong_viec(con, "treo")
            assert row["trang_thai"] == "loi" and row["loi"], dict(row)
            with con:
                nid = db.lay_nhom(con, "moi")
            assert db.liet_ke_lich_su(con, nid)[1] == 1, "trigger khong duoc bo sung sau khoi phuc"


def test_sao_luu_tu_dong_giu_5_ban_va_khong_xoa_ban_an_toan():
    from pipeline import dieu_phoi
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        for i in range(8):
            (d / f"subtitles-2020010{i}-000000.db").write_bytes(b"cu")
        (d / "truoc-khoi-phuc-20200101-000000.db").write_bytes(b"giu")
        with closing(db.mo(":memory:")) as con:
            moi = dieu_phoi.sao_luu_tu_dong(con, d)
        con_lai = sorted(p.name for p in d.glob("subtitles-*.db"))
        assert len(con_lai) == dieu_phoi.GIU_SAO_LUU and moi.name in con_lai, con_lai
        assert con_lai[0] == "subtitles-20200104-000000.db", "xoa nham ban moi thay vi ban cu"
        assert (d / "truoc-khoi-phuc-20200101-000000.db").is_file()


# --------------------------------------------------------------- don dep

def test_don_dep_chi_xoa_cu_khong_xoa_dang_chay_va_ngoai_work():
    from pipeline import dieu_phoi
    with tempfile.TemporaryDirectory() as d:
        goc = Path(d) / "work"
        tai = goc / "tai_len"
        gia = time.time() - 30 * 86400

        def tao(ten, cu=True):
            p = tai / ten
            (p / "khung").mkdir(parents=True)
            (p / "khung" / "khung_0.png").write_bytes(b"x" * 100)
            (p / "ra_vi.mp4").write_bytes(b"y" * 1000)
            if cu:
                for q in (p / "khung" / "khung_0.png", p / "ra_vi.mp4", p / "khung", p):
                    os.utime(q, (gia, gia))
            return p
        cu_xong, cu_chay, moi = tao("cu-xong"), tao("cu-chay"), tao("moi", cu=False)
        (goc / "subtitles.db").write_bytes(b"db")
        ngoai = Path(d) / "ngoai.txt"
        ngoai.write_text("khong duoc dong toi", encoding="utf-8")
        with closing(db.mo(":memory:")) as con:
            with con:
                for cid, tt in (("cu-xong", "xong"), ("cu-chay", "dang_chay")):
                    db.tao_cong_viec(con, cid)
                    db.cap_nhat_cong_viec(con, cid, trang_thai=tt)
            muc = dieu_phoi.don_dep(goc, ngay=7, con=con)                 # mac dinh chi liet ke
            assert [p.name for p, _ in muc] == ["cu-xong"] and muc[0][1] == 1100, muc
            assert cu_xong.exists(), "mac dinh khong duoc xoa that"
            dieu_phoi.don_dep(goc, ngay=7, thuc_hien=True, con=con)
            assert not cu_xong.exists() and cu_chay.exists() and moi.exists()
            assert (goc / "subtitles.db").exists() and ngoai.exists()
            assert dieu_phoi.don_dep(goc, ngay=0, con=con)[0][0].name == "moi"   # ngay=0: moi thu da cu
        for xau in (-1, "7", True, float("nan"), None):
            _loi(dieu_phoi.don_dep, ValueError, goc, ngay=xau)
        assert dieu_phoi.don_dep(Path(d) / "khong-co") == []                   # chua co work/: rong, khong loi


# --------------------------------------------------------------- kiem tuy chon

def test_kiem_tuy_chon_cua_web_va_cli():
    from pipeline.dieu_phoi import TuyChon, kiem_tuy_chon
    kiem_tuy_chon(TuyChon(), chat=True)                                # mac dinh hop le
    kiem_tuy_chon(TuyChon(lang="pt-BR", model="tiny.en", font_scale=5), chat=True)
    kiem_tuy_chon(TuyChon(model="D:/models/ban-rieng"))                 # CLI khong bi whitelist
    for xau in ({"blur": "mo"}, {"font_scale": 0}, {"font_scale": -1}, {"font_scale": math.nan},
                {"font_scale": math.inf}, {"font_scale": True}, {"font_scale": "1"},
                {"font_scale": 5.01}, {"lang": ""}, {"lang": None}, {"lang": "english"},
                {"lang": "e n"}, {"lang": "../x"}, {"nhom": "N" * 101}, {"nhom": "  "}):
        _loi(kiem_tuy_chon, ValueError, TuyChon(**xau))
    for xau in ({"model": "org/repo"}, {"model": "../../etc"}, {"model": ""},
                {"model_dich": "gpt"}, {"model_dich": "org/nllb"}):
        _loi(kiem_tuy_chon, ValueError, TuyChon(**xau), chat=True)


# --------------------------------------------------------------- trich khung song song

def test_trich_khung_song_song_giu_thu_tu_va_nem_loi():
    from pipeline import markbox
    from pipeline.srt import Cue
    cues = [Cue(i + 1, i * 3.0, i * 3.0 + 2, f"c{i}") for i in range(9)]
    goi = []

    def gia(cmd, **kw):
        goi.append(cmd)
        time.sleep(max(0.0, 0.02 * (9 - len(goi))))                 # cue sau xong truoc cue truoc
        Path(cmd[-1]).write_bytes(b"png")
        return subprocess.CompletedProcess(cmd, 0)

    with tempfile.TemporaryDirectory() as d, patch("pipeline.markbox.subprocess.run", gia):
        ra = markbox.trich_khung(Path(d) / "v.mp4", cues, Path(d) / "k")
        assert [p.name for p in ra] == [f"khung_{i}.png" for i in range(9)], "sai thu tu"
        assert all(p.is_file() for p in ra) and len(goi) == 9
        assert sorted(float(c[c.index("-ss") + 1]) for c in goi) == [i * 3.0 + 0.3 for i in range(9)]
        assert markbox.trich_khung(Path(d) / "v.mp4", [], Path(d) / "k2") == []

        def hong(cmd, **kw):
            if "6.300" in cmd:
                raise subprocess.CalledProcessError(1, cmd, stderr="loi ffmpeg")
            return gia(cmd)
        with patch("pipeline.markbox.subprocess.run", hong):
            _loi(markbox.trich_khung, subprocess.CalledProcessError, Path(d) / "v.mp4", cues, Path(d) / "k3")


# --------------------------------------------------------------- api

def test_api_get_khong_tao_nhom_va_404_409():
    from pipeline import dieu_phoi, markbox
    with _san() as (client, video):
        # `_san` thay markbox bang ban gia khong co kiem_hop; hop cua nhom can validator that.
        goc = dieu_phoi._nap
        patcher = patch.object(dieu_phoi, "_nap", lambda n: markbox if n == "markbox" else goc(n))
        patcher.start()
        for duong in ("/thuat-ngu", "/hop"):
            r = client.get(f"/api/nhom/go_sai{duong}")
            assert r.status_code == 404, (duong, r.status_code)
        assert client.get("/api/nhom").json() == [], "GET da tao nhom rac"
        assert client.post("/api/nhom", json={"ten": "Phim"}).status_code == 201
        assert client.get("/api/nhom/Phim/thuat-ngu").json() == {}
        assert client.get("/api/nhom/Phim/hop").json() is None
        assert client.post("/api/nhom", json={"ten": "N" * 101}).status_code == 400
        assert client.post("/api/nhom", json={"ten": " "}).status_code == 400
        assert client.post("/api/nhom/Phim/thuat-ngu", json={"goc": "g" * 201, "dich": "d"}).status_code == 400
        assert client.post("/api/nhom/Phim/thuat-ngu", json={"goc": "a"}).status_code == 400
        assert client.post("/api/nhom/Phim/thuat-ngu", json={"goc": "Ironhold", "dich": "Thành Sắt"}
                           ).json() == {"Ironhold": "Thành Sắt"}
        assert client.post("/api/nhom/Phim/hop", json={"x": 2, "y": 0, "w": 1, "h": 1}).status_code == 400
        assert client.post("/api/nhom/Phim/hop", json={"x": 0.1, "y": 0.8, "w": 0.5, "h": 0.1}
                           ).status_code == 200
        assert client.get("/api/nhom").json()[0]["blur_x"] == 0.1
        patcher.stop()


def test_api_tim_loc_sap_xep_phan_trang_va_header_tong():
    with _san() as (client, video):
        for ten in ("Thành Sắt", "Ironhold", "abc", "Đất"):
            client.post("/api/nhom", json={"ten": ten})
        r = client.get("/api/nhom", params={"moi_trang": 2, "trang": 2})
        assert r.status_code == 200 and len(r.json()) == 2 and r.headers["X-Tong-So"] == "4"
        r = client.get("/api/nhom", params={"q": "thanh"})
        assert [x["ten"] for x in r.json()] == ["Thành Sắt"] and r.headers["X-Tong-So"] == "1"
        assert [x["ten"] for x in client.get("/api/nhom", params={"thu_tu": "desc"}).json()][0] == "Thành Sắt"
        for xau in ({"trang": 0}, {"moi_trang": 999}, {"sap_xep": "x"}, {"thu_tu": "up"}):
            assert client.get("/api/nhom", params=xau).status_code == 400, xau
        assert client.get("/api/nhom", params={"trang": "a"}).status_code == 422   # khong phai so
        client.post("/api/nhom/Ironhold/thuat-ngu", json={"goc": "King", "dich": "Vua"})
        client.post("/api/nhom/Ironhold/thuat-ngu", json={"goc": "Queen", "dich": "Nữ hoàng"})
        r = client.get("/api/nhom/Ironhold/thuat-ngu", params={"q": "vua"})
        assert r.json() == {"King": "Vua"} and r.headers["X-Tong-So"] == "1"
        assert client.get("/api/nhom/khong-co/thuat-ngu", params={"q": "x"}).status_code == 404

        cid = _tai_len(client, video, blur="off").json()["id"]
        r = client.get("/api/cong-viec", params={"trang_thai": "xong"})
        assert [x["id"] for x in r.json()] == [cid] and r.headers["X-Tong-So"] == "1"
        assert client.get("/api/cong-viec", params={"trang_thai": "hu"}).status_code == 400
        assert client.get("/api/cong-viec", params={"trang_thai": "loi"}).json() == []
        assert client.get(f"/api/cong-viec/{cid}").status_code == 200         # route cu van chay
        assert client.get("/api/nhat-ky").status_code == 200
        assert client.get("/api/nhat-ky", params={"moi_trang": 0}).status_code == 400
        ls = client.get("/api/lich-su", params={"nhom": "Ironhold"})
        assert ls.status_code == 200 and ls.headers["X-Tong-So"] == "3", ls.text
        assert client.get("/api/lich-su", params={"nhom": "khong-co"}).status_code == 404
        assert client.get("/api/lich-su", params={"hanh_dong": "x"}).status_code == 400


def test_api_xoa_nhom_thuat_ngu_va_409_khi_dang_chay():
    from api import viec
    with _san() as (client, video):
        client.post("/api/nhom/P/thuat-ngu", json={"goc": "a", "dich": "b"})
        with closing(db.mo(viec.DB)) as con, con:
            db.tao_cong_viec(con, "treo")
            db.cap_nhat_cong_viec(con, "treo", trang_thai="dang_chay")
        assert client.delete("/api/nhom/P/thuat-ngu/a").status_code == 409
        assert client.delete("/api/nhom/P").status_code == 409
        assert client.get("/api/nhom/P/thuat-ngu").json() == {"a": "b"}
        with closing(db.mo(viec.DB)) as con, con:
            db.cap_nhat_cong_viec(con, "treo", trang_thai="xong")
        assert client.delete("/api/nhom/P/thuat-ngu/a").status_code == 204
        assert client.delete("/api/nhom/P/thuat-ngu/a").status_code == 404
        assert client.delete("/api/nhom/P").status_code == 204
        assert client.delete("/api/nhom/P").status_code == 404
        assert client.delete("/api/nhom/%20").status_code in (400, 404)
        ls = client.get("/api/lich-su", params={"hanh_dong": "xoa"})
        assert ls.headers["X-Tong-So"] == "2", ls.text                         # nhom + thuat ngu


def test_api_tuy_chon_sai_la_400_khong_de_rac():
    from api import viec
    with _san() as (client, video):
        for xau in ({"lang": "xx yy"}, {"font_scale": "0"}, {"font_scale": "nan"},
                    {"font_scale": "99"}, {"model": "evil/repo"}, {"model_dich": "gpt-x"},
                    {"nhom": "N" * 101}, {"model": "../.."}):
            r = _tai_len(client, video, **xau)
            assert r.status_code == 400, (xau, r.status_code, r.text)
        assert sorted(Path("work/tai_len").glob("**/*")) == [], "tuy chon sai van de lai file"
        with closing(db.mo(viec.DB)) as con:
            assert con.execute("SELECT count(*) FROM cong_viec").fetchone()[0] == 0
        assert _tai_len(client, video, lang="pt-BR", model="tiny", blur="off").status_code == 202


def test_api_tu_choi_file_qua_lon_tu_tieu_de():
    from api import app as m
    with _san() as (client, video):
        r = client.post("/api/video", content=b"x", headers={
            "content-length": str(m.TOI_DA_BYTE + (2 << 20)),
            "content-type": "multipart/form-data; boundary=b"})
        assert r.status_code == 413, r.text
        # Header rac khong duoc lam sap middleware; request van di tiep vao validate binh thuong.
        r = client.post("/api/video", content=b"x", headers={
            "content-length": "1", "content-type": "multipart/form-data; boundary=b"})
        assert r.status_code in (400, 422)
        assert sorted(Path("work/tai_len").glob("**/*")) == []


def test_api_sao_luu_va_tu_sao_luu_khi_khoi_dong():
    with _san() as (client, video):
        client.post("/api/nhom", json={"ten": "Phim"})
        tu_dong = list(Path("work/sao_luu").glob("subtitles-*.db"))
        assert len(tu_dong) >= 1, "khong sao luu luc khoi dong"
        r = client.post("/api/sao-luu")
        assert r.status_code == 201, r.text
        ban = Path("work/sao_luu") / r.json()["tep"]
        with closing(db.mo(ban)) as con:
            assert db.tim_nhom(con, "Phim")
        assert "work" not in r.text and os.sep not in r.json()["tep"]          # chi ten tep


def test_api_don_ho_so_xong_va_khung_mau_sau_khi_ket_thuc():
    from api import viec
    from pipeline.dieu_phoi import TuyChon
    viec._HO_SO.clear()
    try:
        for i in range(viec.GIU_XONG + 15):
            viec.dat(f"x{i}", Path("v.mp4"), TuyChon())
            viec._cap_nhat(f"x{i}", xong=True)
        viec.dat("dang-chay", Path("v.mp4"), TuyChon())
        viec.dat("moi", Path("v.mp4"), TuyChon())
        ids = viec.dang_theo_doi()
        assert len(ids) <= viec.GIU_XONG + 2 and {"dang-chay", "moi"} <= ids, len(ids)
        assert "x0" not in ids and f"x{viec.GIU_XONG + 14}" in ids, "don nham ho so moi nhat"
    finally:
        viec._HO_SO.clear()

    with _san() as (client, video):
        # Cho ve hop: khung mau con de nguoi dung ve.
        cid = _tai_len(client, video, blur="on").json()["id"]
        assert list((Path("work/tai_len") / cid / "khung").glob("khung_*.png"))
        # Gui hop -> xong: khung mau (mot PNG moi cue) bi xoa, ket qua con de tai.
        client.post(f"/api/cong-viec/{cid}/hop", json={"x": 0.3, "y": 0.85, "w": 0.4, "h": 0.09})
        assert client.get(f"/api/cong-viec/{cid}").json()["trang_thai"] == "xong"
        assert not (Path("work/tai_len") / cid / "khung").exists()
        assert client.get(f"/api/cong-viec/{cid}/ket-qua").status_code == 200
        # Cong viec loi cung don khung mau.
    with _san(dich_loi=True) as (client, video):
        cid = _tai_len(client, video, blur="off").json()["id"]
        assert client.get(f"/api/cong-viec/{cid}").json()["trang_thai"] == "loi"
        assert not (Path("work/tai_len") / cid / "khung").exists()


def test_don_khung_mo_coi_chi_xoa_luot_khong_con_theo_doi():
    from api import viec
    from pipeline.dieu_phoi import TuyChon
    with tempfile.TemporaryDirectory() as d:
        tai = Path(d) / "tai_len"
        for ten in ("mo-coi", "dang-theo", "nguon"):
            (tai / ten / "khung").mkdir(parents=True)
            (tai / ten / "khung" / "khung_0.png").write_bytes(b"x")
        (tai / "mo-coi" / "ra_vi.mp4").write_bytes(b"giu ket qua")
        viec._HO_SO.clear()
        try:
            viec.dat("dang-theo", Path("v.mp4"), TuyChon())
            assert viec.don_khung_mo_coi(tai) == 1
        finally:
            viec._HO_SO.clear()
        assert not (tai / "mo-coi" / "khung").exists() and (tai / "mo-coi" / "ra_vi.mp4").exists()
        assert (tai / "dang-theo" / "khung").exists() and (tai / "nguon" / "khung").exists()
        assert viec.don_khung_mo_coi(Path(d) / "khong-co") == 0


# --------------------------------------------------------------- cli

def test_cli_sao_luu_khoi_phuc_don_dep_lich_su_xoa():
    import main as cli
    cu = Path.cwd()
    with tempfile.TemporaryDirectory() as d:
        os.chdir(d)
        try:
            (Path(d) / "work").mkdir()
            assert cli.main(["nhom", "set-term", "Phim", "Ironhold", "Thành Sắt"]) == 0
            assert cli.main(["sao-luu", "--dich", str(Path(d) / "bk" / "a.db")]) == 0
            assert (Path(d) / "bk" / "a.db").is_file()
            assert cli.main(["sao-luu"]) == 0 and list((Path(d) / "work/sao_luu").glob("subtitles-*.db"))
            assert cli.main(["lich-su", "--nhom", "Phim"]) == 0
            assert cli.main(["lich-su", "--nhom", "khong-co"]) == 1
            assert cli.main(["nhom", "del-term", "Phim", "Ironhold"]) == 0
            assert cli.main(["nhom", "del-term", "Phim", "Ironhold"]) == 1          # da xoa roi
            assert cli.main(["nhom", "delete", "Phim"]) == 0
            assert cli.main(["nhom", "delete", "Phim"]) == 1
            assert cli.main(["khoi-phuc", str(Path(d) / "bk" / "a.db")]) == 0
            assert cli.main(["nhom", "glossary", "Phim"]) == 0                      # da khoi phuc
            (Path(d) / "rac.db").write_bytes(b"khong phai sqlite")
            assert cli.main(["khoi-phuc", str(Path(d) / "rac.db")]) == 1
            assert cli.main(["khoi-phuc", str(Path(d) / "khong-co.db")]) == 1
            assert cli.main(["don-dep"]) == 0
            assert cli.main(["don-dep", "--ngay", "-3"]) == 1
        finally:
            os.chdir(cu)


# --------------------------------------------------------------- phan con ho cua ma van hanh

def test_don_dep_nguon_cu_khong_lock_bi_don_con_lock_hoac_moi_thi_giu():
    from pipeline import dieu_phoi
    from pipeline.srt import thu_muc_lam_viec
    with tempfile.TemporaryDirectory() as d:
        goc = Path(d).resolve() / "work"
        gia = time.time() - 30 * 86400

        def nguon(ten, cu=True, lock=False):
            h = goc / "tai_len" / "nguon" / "nhom" / ten
            h.mkdir(parents=True)
            (h / "nguon.media").write_bytes(b"v" * 500)
            w = goc / thu_muc_lam_viec(h / "nguon.media", goc).name
            w.mkdir(parents=True)
            (w / "trang_thai.json").write_text("{}", encoding="utf-8")
            if lock:
                (w / ".lock").write_text("1", encoding="utf-8")
            if cu:
                for p in (h / "nguon.media", h, w / "trang_thai.json", w):
                    os.utime(p, (gia, gia))
            return h, w
        cu_h, cu_w = nguon("cu")
        khoa_h, khoa_w = nguon("khoa", lock=True)
        moi_h, moi_w = nguon("moi", cu=False)
        muc = dieu_phoi.don_dep(goc, ngay=7)
        assert {p for p, _ in muc} == {cu_h, cu_w}, muc
        dieu_phoi.don_dep(goc, ngay=7, thuc_hien=True)
        assert not cu_h.exists() and not cu_w.exists()
        assert khoa_h.exists() and khoa_w.exists() and moi_h.exists() and moi_w.exists()


def test_don_dep_tu_choi_xoa_qua_lien_ket_ra_ngoai_work():
    from pipeline import dieu_phoi
    with tempfile.TemporaryDirectory() as d:
        goc = Path(d).resolve() / "work"
        ngoai = Path(d).resolve() / "ngoai"
        ngoai.mkdir()
        (ngoai / "quan-trong.txt").write_text("giu", encoding="utf-8")
        (goc / "tai_len").mkdir(parents=True)
        try:
            os.symlink(ngoai, goc / "tai_len" / "lien-ket", target_is_directory=True)
        except (OSError, NotImplementedError):
            return          # Windows khong cap quyen tao symlink: khong kiem duoc o may nay
        gia = time.time() - 30 * 86400
        os.utime(ngoai / "quan-trong.txt", (gia, gia))
        os.utime(ngoai, (gia, gia))
        _loi(dieu_phoi.don_dep, RuntimeError, goc, ngay=7, thuc_hien=True)
        assert (ngoai / "quan-trong.txt").read_text(encoding="utf-8") == "giu"


def test_khoi_phuc_tu_choi_khi_thieu_file_hoac_dang_co_giao_dich():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        with closing(db.mo(d / "a.db")) as con:
            with con:
                db.lay_nhom(con, "A")
            ban = db.sao_luu(con, d / "bk.db")
            _loi(db.khoi_phuc, FileNotFoundError, con, d / "khong-co.db")
            con.execute("INSERT INTO nhom(ten) VALUES ('B')")             # mo giao dich ngam
            assert con.in_transaction
            _loi(db.khoi_phuc, RuntimeError, con, ban)
            con.rollback()
            assert [r["ten"] for r in db.liet_ke_nhom(con)[0]] == ["A"]


def test_api_content_length_rac_khong_lam_sap_middleware():
    with _san() as (client, video):
        r = client.post("/api/video", content=b"x", headers={
            "content-length": "abc", "content-type": "multipart/form-data; boundary=b"})
        assert r.status_code < 500, r.status_code


def test_chay_nen_tranh_khoa_thi_bao_loi_va_don_khung_mau():
    """Lenh chay tiep gianh lai claim ma work dir dang bi giu: bao loi, khong treo, don khung mau."""
    from api import viec
    from pipeline.dieu_phoi import TuyChon
    from pipeline.srt import thu_muc_lam_viec
    cu = Path.cwd()
    with tempfile.TemporaryDirectory() as d:
        os.chdir(d)
        try:
            video = Path(d) / "v.mp4"
            video.write_bytes(b"v")
            khung = Path("work/tai_len/c1/khung")
            khung.mkdir(parents=True)
            (khung / "khung_0.png").write_bytes(b"x")
            thu_muc_lam_viec(video).mkdir(parents=True)
            (thu_muc_lam_viec(video) / ".lock").write_text("1", encoding="utf-8")
            viec._HO_SO.clear()
            viec.dat("c1", video, TuyChon(thu_muc_khung=khung))      # khoa=None: phai tu gianh
            with closing(db.mo(viec.DB)) as con, con:
                db.tao_cong_viec(con, "c1")
            viec.chay_nen("c1")
            with closing(db.mo(viec.DB)) as con:
                row = db.doc_cong_viec(con, "c1")
            assert row["trang_thai"] == "loi" and ".lock" in row["loi"], dict(row)
            assert not khung.exists() and viec.lay("c1").xong
            viec.chay_nen("khong-co")                                 # cid la: khong nem, khong ghi gi
        finally:
            viec._HO_SO.clear()
            os.chdir(cu)
