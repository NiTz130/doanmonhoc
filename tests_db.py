"""Offline SQLite checks: run with python tests_db.py."""
from __future__ import annotations

import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path

from pipeline import db


def test_glossary_transaction_resume() -> None:
    with closing(db.mo(":memory:")) as con:
        with con:
            nid = db.lay_nhom(con, "Series")
            vid = db.ghi_video(con, "input.mp4", "work/input", nid, 1280, 720, 10.0)
            db.dat_thuat_ngu(con, nid, "Hero", "Anh hùng")
        assert db.ap_dung_dich(con, vid, nid, "hash-1", {"Hero": "Sai", "Castle": "Lâu đài"}) == 2
        assert db.ap_dung_dich(con, vid, nid, "hash-1", {"Castle": "Sai"}) == 0
        assert db.doc_thuat_ngu(con, nid) == {"Hero": "Anh hùng", "Castle": "Lâu đài"}
        # A marker failure must roll back the terms in the same operation.
        con.execute("CREATE TRIGGER reject_marker BEFORE INSERT ON nhat_ky BEGIN SELECT RAISE(ABORT, 'injected'); END")
        try:
            db.ap_dung_dich(con, vid, nid, "hash-2", {"New": "Mới"})
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError("Expected injected journal failure")
        assert "New" not in db.doc_thuat_ngu(con, nid)
        con.execute("DROP TRIGGER reject_marker")
        assert db.ap_dung_dich(con, vid, nid, "hash-2", {"New": "Mới"}) == 1
        # Nested writes must not commit their caller's transaction.
        try:
            with con:
                db.ghi_thuat_ngu(con, nid, {"Outer": "Ngoài"})
                db.ap_dung_dich(con, vid, nid, "hash-3", {"Inner": "Trong"})
                raise RuntimeError("abort caller")
        except RuntimeError:
            pass
        assert "Outer" not in db.doc_thuat_ngu(con, nid)
        assert "Inner" not in db.doc_thuat_ngu(con, nid)
        with con:
            db.ghi_nhat_ky(con, vid, "translate", "suy_giam", loi="cue 1")
            db.ghi_nhat_ky(con, vid, "render", "xong")
        assert con.execute("SELECT xong_luc FROM video WHERE id=?", (vid,)).fetchone()[0]
        with con:
            assert db.ghi_video(con, "input.mp4", "work/input", nid, 1920, 1080, 12.0) == vid
        row = con.execute("SELECT rong,cao,thoi_luong,xong_luc FROM video WHERE id=?", (vid,)).fetchone()
        assert tuple(row) == (1920, 1080, 12.0, None)
        assert con.execute("SELECT count(*) FROM nhat_ky WHERE ket_qua='suy_giam'").fetchone()[0] == 1
        with con:
            con.execute("DELETE FROM nhom WHERE id=?", (nid,))
        assert con.execute("SELECT nhom_id FROM video WHERE id=?", (vid,)).fetchone()[0] is None
        assert not con.execute("SELECT * FROM thuat_ngu").fetchall()
        try:
            with con:
                db.ghi_thuat_ngu(con, 999, {"No": "Không"})
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError("Foreign keys must be enforced")


# Nguyen van hai CREATE TABLE cua lop cu (git show HEAD~ truoc dot 4): con 5 cot da go.
SCHEMA_CU = """
CREATE TABLE nhom (
 id INTEGER PRIMARY KEY, ten TEXT NOT NULL UNIQUE,
 ngon_ngu_goc TEXT NOT NULL DEFAULT 'en', sub_style TEXT,
 blur_x REAL, blur_y REAL, blur_w REAL, blur_h REAL,
 tao_luc TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE thuat_ngu (
 id INTEGER PRIMARY KEY,
 nhom_id INTEGER NOT NULL REFERENCES nhom(id) ON DELETE CASCADE,
 goc TEXT NOT NULL, dich TEXT NOT NULL,
 loai TEXT NOT NULL DEFAULT 'thuat_ngu'
 CHECK (loai IN ('ten_nguoi','dia_danh','thuat_ngu')),
 so_lan INTEGER NOT NULL DEFAULT 1, khoa INTEGER NOT NULL DEFAULT 0,
 UNIQUE (nhom_id,goc)
);
"""


def test_db_cu_con_cot_thua_van_chay() -> None:
    """AC-7/LD-5: CSDL tao bang luoc do cu chay dung voi ma moi, khong can migration."""
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "cu.db"
        with closing(sqlite3.connect(path)) as raw:
            raw.executescript(SCHEMA_CU)
            raw.execute("INSERT INTO nhom(ten) VALUES ('Phim')")
            nid_cu = raw.execute("SELECT id FROM nhom WHERE ten='Phim'").fetchone()[0]
            raw.executemany(
                "INSERT INTO thuat_ngu(nhom_id,goc,dich,khoa,so_lan) VALUES (?,?,?,?,?)",
                [(nid_cu, "Hero", "Anh hung", 1, 5), (nid_cu, "Castle", "Lau dai", 0, 2)])
            raw.commit()
        with closing(db.mo(path)) as con:
            with con:
                assert db.lay_nhom(con, "Phim") == nid_cu
                db.dat_thuat_ngu(con, nid_cu, "Hero", "Vi anh hung")
                assert db.ghi_thuat_ngu(con, nid_cu, {"Castle": "Sai", "King": "Vua"}) == 2
                db.ghi_hop(con, nid_cu, {"x": 0.1, "y": 0.2, "w": 0.3, "h": 0.4})
            assert db.doc_hop(con, nid_cu) == {"x": 0.1, "y": 0.2, "w": 0.3, "h": 0.4}
            assert db.doc_thuat_ngu(con, nid_cu) == {
                "Castle": "Lau dai", "Hero": "Vi anh hung", "King": "Vua"}


if __name__ == "__main__":
    test_glossary_transaction_resume()
    test_db_cu_con_cot_thua_van_chay()
    print("SQLite checks passed")
