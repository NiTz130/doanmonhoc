"""SQLite memory and journal; ordinary writes commit in the caller's transaction."""
from __future__ import annotations

import sqlite3
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS nhom (
 id INTEGER PRIMARY KEY, ten TEXT NOT NULL UNIQUE,
 ngon_ngu_goc TEXT NOT NULL DEFAULT 'en', sub_style TEXT,
 blur_x REAL, blur_y REAL, blur_w REAL, blur_h REAL,
 tao_luc TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS video (
 id INTEGER PRIMARY KEY,
 nhom_id INTEGER REFERENCES nhom(id) ON DELETE SET NULL,
 duong_dan TEXT NOT NULL UNIQUE, thu_muc_work TEXT NOT NULL UNIQUE,
 rong INTEGER, cao INTEGER, thoi_luong REAL,
 them_luc TEXT NOT NULL DEFAULT (datetime('now')), xong_luc TEXT
);
CREATE TABLE IF NOT EXISTS thuat_ngu (
 id INTEGER PRIMARY KEY,
 nhom_id INTEGER NOT NULL REFERENCES nhom(id) ON DELETE CASCADE,
 goc TEXT NOT NULL, dich TEXT NOT NULL,
 loai TEXT NOT NULL DEFAULT 'thuat_ngu'
 CHECK (loai IN ('ten_nguoi','dia_danh','thuat_ngu')),
 so_lan INTEGER NOT NULL DEFAULT 1, khoa INTEGER NOT NULL DEFAULT 0,
 UNIQUE (nhom_id,goc)
);
CREATE TABLE IF NOT EXISTS nhat_ky (
 id INTEGER PRIMARY KEY,
 video_id INTEGER NOT NULL REFERENCES video(id) ON DELETE CASCADE,
 buoc TEXT NOT NULL, ket_qua TEXT NOT NULL, giay REAL,
 token_vao INTEGER, token_ra INTEGER, loi TEXT,
 luc TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS cong_viec (
 id TEXT PRIMARY KEY,
 video_id INTEGER REFERENCES video(id) ON DELETE CASCADE,
 trang_thai TEXT NOT NULL
 CHECK (trang_thai IN ('cho','dang_chay','cho_chon_khung','xong','suy_giam','loi')),
 buoc TEXT, tien_do REAL NOT NULL DEFAULT 0.0,
 duong_dan_ra TEXT, loi TEXT,
 tao_luc TEXT NOT NULL DEFAULT (datetime('now')),
 cap_nhat_luc TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def mo(path: str | Path) -> sqlite3.Connection:
    if str(path) != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path))
    con.row_factory = sqlite3.Row
    try:
        con.execute("PRAGMA foreign_keys=ON")
        con.executescript(SCHEMA)
    except BaseException:
        con.close()
        raise
    return con


def lay_nhom(con: sqlite3.Connection, ten: str) -> int:
    if not isinstance(ten, str) or not ten.strip():
        raise ValueError("Tên nhóm không được rỗng")
    con.execute("INSERT INTO nhom(ten) VALUES (?) ON CONFLICT(ten) DO NOTHING", (ten,))
    return con.execute("SELECT id FROM nhom WHERE ten=?", (ten,)).fetchone()[0]


def doc_thuat_ngu(con: sqlite3.Connection, nid: int | None) -> dict[str, str]:
    return dict(con.execute("SELECT goc,dich FROM thuat_ngu WHERE nhom_id=? ORDER BY goc", (nid,)))


def _kiem_thuat_ngu(moi: dict[str, str]) -> None:
    if not isinstance(moi, dict) or any(
        not isinstance(goc, str) or not goc.strip()
        or not isinstance(dich, str) or not dich.strip()
        for goc, dich in moi.items()
    ):
        raise ValueError("Thuật ngữ phải là object chuỗi không rỗng → chuỗi không rỗng")


def ghi_thuat_ngu(con: sqlite3.Connection, nid: int | None, moi: dict[str, str]) -> int:
    """Count observations without replacing any existing translation, locked or not."""
    _kiem_thuat_ngu(moi)
    if nid is None:
        return 0
    con.executemany(
        "INSERT INTO thuat_ngu(nhom_id,goc,dich) VALUES (?,?,?) "
        "ON CONFLICT(nhom_id,goc) DO UPDATE SET so_lan=thuat_ngu.so_lan+1",
        ((nid, goc, dich) for goc, dich in moi.items()),
    )
    return len(moi)


def dat_thuat_ngu(con: sqlite3.Connection, nid: int, goc: str, dich: str, khoa: bool = False) -> None:
    """Explicit user edit is allowed to replace a previously locked term."""
    _kiem_thuat_ngu({goc: dich})
    con.execute(
        "INSERT INTO thuat_ngu(nhom_id,goc,dich,khoa) VALUES (?,?,?,?) "
        "ON CONFLICT(nhom_id,goc) DO UPDATE SET dich=excluded.dich,khoa=excluded.khoa",
        (nid, goc, dich, int(khoa)),
    )


def da_ap_dung_dich(con: sqlite3.Connection, video_id: int, artifact_hash: str) -> bool:
    return con.execute(
        "SELECT 1 FROM nhat_ky WHERE video_id=? AND buoc='translate_apply' "
        "AND ket_qua='xong' AND loi=? LIMIT 1", (video_id, artifact_hash)
    ).fetchone() is not None


def ap_dung_dich(
    con: sqlite3.Connection, video_id: int, nhom_id: int | None,
    artifact_hash: str, moi: dict[str, str],
) -> int:
    """Atomically apply one artifact. Nested calls preserve caller transaction ownership."""
    _kiem_thuat_ngu(moi)
    if not isinstance(artifact_hash, str) or not artifact_hash:
        raise ValueError("Thiếu hash artifact dịch")
    nested = con.in_transaction
    if not nested:
        # Reserve the writer before checking the marker; no transport work inside.
        con.execute("BEGIN IMMEDIATE")
    con.execute("SAVEPOINT ap_dung_dich")
    try:
        if da_ap_dung_dich(con, video_id, artifact_hash):
            count = 0
        else:
            count = ghi_thuat_ngu(con, nhom_id, moi)
            con.execute(
                "INSERT INTO nhat_ky(video_id,buoc,ket_qua,loi) VALUES (?,'translate_apply','xong',?)",
                (video_id, artifact_hash),
            )
        con.execute("RELEASE SAVEPOINT ap_dung_dich")
        if not nested:
            con.commit()
        return count
    except BaseException:
        if nested:
            con.execute("ROLLBACK TO SAVEPOINT ap_dung_dich")
            con.execute("RELEASE SAVEPOINT ap_dung_dich")
        else:
            con.rollback()
        raise


def ghi_video(
    con: sqlite3.Connection, path: str | Path, work: str | Path,
    nid: int | None, W: int, H: int, duration: float,
) -> int:
    path = str(Path(path).resolve())
    con.execute(
        "INSERT INTO video(duong_dan,thu_muc_work,nhom_id,rong,cao,thoi_luong) VALUES (?,?,?,?,?,?) "
        "ON CONFLICT(duong_dan) DO UPDATE SET thu_muc_work=excluded.thu_muc_work,"
        "nhom_id=excluded.nhom_id,rong=excluded.rong,cao=excluded.cao,"
        "thoi_luong=excluded.thoi_luong,xong_luc=NULL",
        (path, str(Path(work).resolve()), nid, W, H, duration),
    )
    return con.execute("SELECT id FROM video WHERE duong_dan=?", (path,)).fetchone()[0]


def doc_hop(con: sqlite3.Connection, nid: int | None) -> dict[str, float] | None:
    row = con.execute("SELECT blur_x,blur_y,blur_w,blur_h FROM nhom WHERE id=?", (nid,)).fetchone()
    if row is None or all(value is None for value in row):
        return None
    # Main applies the shared geometry validator, including corrupt/partial DB data.
    return dict(zip(("x", "y", "w", "h"), row))


def ghi_hop(con: sqlite3.Connection, nid: int, hop: dict[str, float]) -> None:
    con.execute("UPDATE nhom SET blur_x=?,blur_y=?,blur_w=?,blur_h=? WHERE id=?",
                (hop["x"], hop["y"], hop["w"], hop["h"], nid))


def ghi_nhat_ky(
    con: sqlite3.Connection, video_id: int, buoc: str, ket_qua: str,
    giay: float | None = None, token_vao: int | None = None,
    token_ra: int | None = None, loi: str | None = None,
) -> None:
    if ket_qua not in {"xong", "bo_qua", "loi", "suy_giam"}:
        raise ValueError("Trạng thái nhật ký không hợp lệ")
    con.execute(
        "INSERT INTO nhat_ky(video_id,buoc,ket_qua,giay,token_vao,token_ra,loi) VALUES (?,?,?,?,?,?,?)",
        (video_id, buoc, ket_qua, giay, token_vao, token_ra, loi),
    )
    if buoc == "render" and ket_qua == "xong":
        con.execute("UPDATE video SET xong_luc=datetime('now') WHERE id=?", (video_id,))


def tao_cong_viec(con: sqlite3.Connection, cid: str, video_id: int | None = None) -> str:
    """Bang cong_viec chi bao tien do cho frontend; no khong quyet dinh resume."""
    if not isinstance(cid, str) or not cid.strip():
        raise ValueError("Thiếu id công việc")
    con.execute("INSERT INTO cong_viec(id,video_id,trang_thai) VALUES (?,?,'cho')", (cid, video_id))
    return cid


def cap_nhat_cong_viec(con: sqlite3.Connection, cid: str, **cot: object) -> None:
    hop_le = {"video_id", "trang_thai", "buoc", "tien_do", "duong_dan_ra", "loi"}
    la = cot.keys() - hop_le
    if la:
        raise ValueError(f"Cột công việc không hợp lệ: {sorted(la)}")
    if not cot:
        return
    dat = ",".join(f"{k}=?" for k in cot)
    con.execute(f"UPDATE cong_viec SET {dat},cap_nhat_luc=datetime('now') WHERE id=?",
                (*cot.values(), cid))


def doc_cong_viec(con: sqlite3.Connection, cid: str) -> sqlite3.Row | None:
    return con.execute("SELECT * FROM cong_viec WHERE id=?", (cid,)).fetchone()
