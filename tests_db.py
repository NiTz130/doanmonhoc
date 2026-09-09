"""Offline SQLite checks: run with python tests_db.py."""
from __future__ import annotations

import sqlite3
from contextlib import closing

from pipeline import db


def test_glossary_transaction_resume() -> None:
    with closing(db.mo(":memory:")) as con:
        with con:
            nid = db.lay_nhom(con, "Series")
            vid = db.ghi_video(con, "input.mp4", "work/input", nid, 1280, 720, 10.0)
            db.dat_thuat_ngu(con, nid, "Hero", "Anh hùng", True)
        assert db.ap_dung_dich(con, vid, nid, "hash-1", {"Hero": "Sai", "Castle": "Lâu đài"}) == 2
        assert db.ap_dung_dich(con, vid, nid, "hash-1", {"Castle": "Sai"}) == 0
        assert db.doc_thuat_ngu(con, nid) == {"Hero": "Anh hùng", "Castle": "Lâu đài"}
        assert con.execute("SELECT so_lan FROM thuat_ngu WHERE goc='Castle'").fetchone()[0] == 1
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


if __name__ == "__main__":
    test_glossary_transaction_resume()
    print("SQLite checks passed")
