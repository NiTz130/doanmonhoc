"""SQLite memory and journal; ordinary writes commit in the caller's transaction."""
from __future__ import annotations

import os
import sqlite3
import unicodedata
from contextlib import closing
from pathlib import Path


LOI_MAT_HO_SO = ("Tiến trình xử lý đã khởi động lại nên công việc này không còn theo dõi được. "
                "Tải video lên lại để chạy tiếp; kết quả cũ đã tải xong vẫn giữ nguyên.")

TEN_NHOM_TOI_DA = 100
THUAT_NGU_TOI_DA = 200
TRANG_THAI_VIEC = ("cho", "dang_chay", "cho_chon_khung", "xong", "suy_giam", "loi")
VIEC_DANG_CHAY = ("cho", "dang_chay")           # cho_chon_khung dung yen, khong giu nhom
BANG_BAT_BUOC = {"nhom", "video", "thuat_ngu", "nhat_ky", "cong_viec"}
MAX_MOI_TRANG = 200


class KhongCo(LookupError):
    """Doi tuong khong ton tai (API: 404)."""


class DangBan(RuntimeError):
    """Co cong viec dang chay nen khong duoc doi du lieu dung chung (API: 409)."""


SCHEMA = """
CREATE TABLE IF NOT EXISTS nhom (
 id INTEGER PRIMARY KEY, ten TEXT NOT NULL UNIQUE,
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
CREATE TABLE IF NOT EXISTS lich_su (
 id INTEGER PRIMARY KEY,
 doi_tuong TEXT NOT NULL CHECK (doi_tuong IN ('nhom','thuat_ngu')),
 nhom_id INTEGER, khoa TEXT NOT NULL,
 hanh_dong TEXT NOT NULL CHECK (hanh_dong IN ('tao','sua','xoa')),
 cu TEXT, moi TEXT,
 luc TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS ix_nhat_ky_video ON nhat_ky(video_id, id);
CREATE INDEX IF NOT EXISTS ix_cong_viec_tt ON cong_viec(trang_thai, tao_luc);
CREATE INDEX IF NOT EXISTS ix_lich_su_nhom ON lich_su(nhom_id, id);
CREATE INDEX IF NOT EXISTS ix_video_nhom ON video(nhom_id);
-- Trigger, khong phai ma ung dung: moi duong ghi (CLI, API, thuat ngu hoc trong job,
-- xoa day chuyen cua nhom) deu de lai dau vet, khong duong nao bo qua duoc.
CREATE TRIGGER IF NOT EXISTS ls_thuat_ngu_tao AFTER INSERT ON thuat_ngu BEGIN
 INSERT INTO lich_su(doi_tuong,nhom_id,khoa,hanh_dong,moi)
 VALUES ('thuat_ngu',NEW.nhom_id,NEW.goc,'tao',NEW.dich);
END;
CREATE TRIGGER IF NOT EXISTS ls_thuat_ngu_sua AFTER UPDATE OF dich ON thuat_ngu
WHEN OLD.dich IS NOT NEW.dich BEGIN
 INSERT INTO lich_su(doi_tuong,nhom_id,khoa,hanh_dong,cu,moi)
 VALUES ('thuat_ngu',NEW.nhom_id,NEW.goc,'sua',OLD.dich,NEW.dich);
END;
CREATE TRIGGER IF NOT EXISTS ls_thuat_ngu_xoa AFTER DELETE ON thuat_ngu BEGIN
 INSERT INTO lich_su(doi_tuong,nhom_id,khoa,hanh_dong,cu)
 VALUES ('thuat_ngu',OLD.nhom_id,OLD.goc,'xoa',OLD.dich);
END;
CREATE TRIGGER IF NOT EXISTS ls_nhom_tao AFTER INSERT ON nhom BEGIN
 INSERT INTO lich_su(doi_tuong,nhom_id,khoa,hanh_dong) VALUES ('nhom',NEW.id,NEW.ten,'tao');
END;
CREATE TRIGGER IF NOT EXISTS ls_nhom_hop AFTER UPDATE OF blur_x,blur_y,blur_w,blur_h ON nhom
WHEN OLD.blur_x IS NOT NEW.blur_x OR OLD.blur_y IS NOT NEW.blur_y
  OR OLD.blur_w IS NOT NEW.blur_w OR OLD.blur_h IS NOT NEW.blur_h BEGIN
 INSERT INTO lich_su(doi_tuong,nhom_id,khoa,hanh_dong,cu,moi) VALUES ('nhom',NEW.id,NEW.ten,'sua',
  CASE WHEN OLD.blur_x IS NULL THEN NULL
       ELSE OLD.blur_x||','||OLD.blur_y||','||OLD.blur_w||','||OLD.blur_h END,
  NEW.blur_x||','||NEW.blur_y||','||NEW.blur_w||','||NEW.blur_h);
END;
CREATE TRIGGER IF NOT EXISTS ls_nhom_xoa AFTER DELETE ON nhom BEGIN
 INSERT INTO lich_su(doi_tuong,nhom_id,khoa,hanh_dong) VALUES ('nhom',OLD.id,OLD.ten,'xoa');
END;
"""


def mo(path: str | Path, *, cung_thread: bool = True) -> sqlite3.Connection:
    """`cung_thread=False` cho connection cua mot request FastAPI (LD-2).

    Starlette chay route sync trong threadpool va co the doi thread giua cac phan
    cua cung mot request; connection van chi thuoc mot request, khong dung chung.
    """
    if str(path) != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path), check_same_thread=cung_thread, timeout=10)
    con.row_factory = sqlite3.Row
    try:
        con.execute("PRAGMA foreign_keys=ON")
        if str(path) != ":memory:":
            # WAL: request doc tien do khong chan tac vu nen dang ghi (va nguoc lai).
            con.execute("PRAGMA journal_mode=WAL")
        con.create_function("chuan", 1, chuan, deterministic=True)
        con.executescript(SCHEMA)
    except BaseException:
        con.close()
        raise
    return con


def chuan(text: object) -> str:
    """Chuoi de tim kiem: bo dau, d->đ, chu thuong. 'Thành Sắt' khop 'thanh sat'."""
    ra = unicodedata.normalize("NFD", str(text or "").replace("đ", "d").replace("Đ", "D"))
    return "".join(c for c in ra if not unicodedata.combining(c)).casefold()


def kiem_ten_nhom(ten: object) -> str:
    if not isinstance(ten, str) or not ten.strip():
        raise ValueError("Tên nhóm không được rỗng")
    if len(ten) > TEN_NHOM_TOI_DA:
        raise ValueError(f"Tên nhóm dài tối đa {TEN_NHOM_TOI_DA} ký tự")
    return ten


def tim_nhom(con: sqlite3.Connection, ten: str) -> int:
    """Chi doc: nhom khong co thi bao KhongCo, khong tao (GET khong duoc ghi)."""
    kiem_ten_nhom(ten)
    row = con.execute("SELECT id FROM nhom WHERE ten=?", (ten,)).fetchone()
    if row is None:
        raise KhongCo("Không có nhóm này")
    return row[0]


def lay_nhom(con: sqlite3.Connection, ten: str) -> int:
    kiem_ten_nhom(ten)
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
    if any(len(goc) > THUAT_NGU_TOI_DA or len(dich) > THUAT_NGU_TOI_DA for goc, dich in moi.items()):
        raise ValueError(f"Thuật ngữ dài tối đa {THUAT_NGU_TOI_DA} ký tự mỗi vế")


def ghi_thuat_ngu(con: sqlite3.Connection, nid: int | None, moi: dict[str, str]) -> int:
    """Them tu moi hoc duoc; khong bao gio thay ban dich da co."""
    _kiem_thuat_ngu(moi)
    if nid is None:
        return 0
    con.executemany(
        "INSERT INTO thuat_ngu(nhom_id,goc,dich) VALUES (?,?,?) "
        "ON CONFLICT(nhom_id,goc) DO NOTHING",
        ((nid, goc, dich) for goc, dich in moi.items()),
    )
    return len(moi)


def dat_thuat_ngu(con: sqlite3.Connection, nid: int, goc: str, dich: str) -> None:
    """Lenh sua cua nguoi dung thay ban dich da co."""
    _kiem_thuat_ngu({goc: dich})
    con.execute(
        "INSERT INTO thuat_ngu(nhom_id,goc,dich) VALUES (?,?,?) "
        "ON CONFLICT(nhom_id,goc) DO UPDATE SET dich=excluded.dich",
        (nid, goc, dich),
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


def don_cong_viec_mat_ho_so(con: sqlite3.Connection, con_song: set[str]) -> int:
    """LD-5: job khong-terminal mat chu so huu sau restart thi bao loi, khong treo.

    Khong dong toi `xong`/`suy_giam`/`loi`, khong xoa `duong_dan_ra` cu.
    """
    cho = ("cho", "dang_chay", "cho_chon_khung")
    hang = [r[0] for r in con.execute(
        f"SELECT id FROM cong_viec WHERE trang_thai IN ({','.join('?' * len(cho))})", cho)]
    mat = [cid for cid in hang if cid not in con_song]
    con.executemany(
        "UPDATE cong_viec SET trang_thai='loi',loi=?,cap_nhat_luc=datetime('now') WHERE id=?",
        ((LOI_MAT_HO_SO, cid) for cid in mat))
    return len(mat)


# ---------------------------------------------------------------- tra cuu
# Moi ham liet ke tra (danh sach, tong): tong dem TRUOC khi cat trang de UI ve duoc
# bo phan trang. Cot sap xep di qua bang trang trang, khong bao gio noi chuoi tu input.

def _trang(trang: object, moi_trang: object) -> tuple[int, int]:
    if (isinstance(trang, bool) or not isinstance(trang, int) or trang < 1
            or isinstance(moi_trang, bool) or not isinstance(moi_trang, int)
            or not 1 <= moi_trang <= MAX_MOI_TRANG):
        raise ValueError(f"trang >= 1 và 1 <= moi_trang <= {MAX_MOI_TRANG}")
    return moi_trang, (trang - 1) * moi_trang


def _thu_tu(thu_tu: str) -> str:
    if thu_tu not in {"asc", "desc"}:
        raise ValueError("thu_tu phải là asc hoặc desc")
    return thu_tu.upper()


def _cot(sap_xep: str, cho_phep: dict[str, str]) -> str:
    if sap_xep not in cho_phep:
        raise ValueError("sap_xep phải là một trong: " + ", ".join(sorted(cho_phep)))
    return cho_phep[sap_xep]


def _mau(q: str) -> str:
    """Mau LIKE khong dau; % va _ trong q la ky tu thuong."""
    ra = chuan(q.strip()).replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{ra}%"


def liet_ke_nhom(con: sqlite3.Connection, q: str | None = None, sap_xep: str = "ten",
                 thu_tu: str = "asc", trang: int = 1, moi_trang: int = 50) -> tuple[list[dict], int]:
    cot, huong = _cot(sap_xep, {"ten": "chuan(n.ten)", "tao_luc": "n.tao_luc"}), _thu_tu(thu_tu)
    gioi, bo = _trang(trang, moi_trang)
    dk, tham = ("", []) if not q or not q.strip() else (
        " AND chuan(n.ten) LIKE ? ESCAPE '\\'", [_mau(q)])
    tong = con.execute(f"SELECT count(*) FROM nhom n WHERE 1=1{dk}", tham).fetchone()[0]
    hang = con.execute(
        "SELECT n.ten,n.blur_x,n.blur_y,n.blur_w,n.blur_h,n.tao_luc,"
        "(SELECT count(*) FROM thuat_ngu t WHERE t.nhom_id=n.id) AS so_thuat_ngu,"
        "(SELECT count(*) FROM video v WHERE v.nhom_id=n.id) AS so_video "
        f"FROM nhom n WHERE 1=1{dk} ORDER BY {cot} {huong}, n.id LIMIT ? OFFSET ?",
        [*tham, gioi, bo])
    return [dict(r) for r in hang], tong


def liet_ke_thuat_ngu(con: sqlite3.Connection, nid: int, q: str | None = None,
                      sap_xep: str = "goc", thu_tu: str = "asc", trang: int = 1,
                      moi_trang: int = 50) -> tuple[dict[str, str], int]:
    cot, huong = _cot(sap_xep, {"goc": "chuan(goc)", "dich": "chuan(dich)", "moi": "id"}), _thu_tu(thu_tu)
    gioi, bo = _trang(trang, moi_trang)
    # Tim ca ve goc lan ve dich: nguoi dung nho ban dich hon tu goc.
    if q and q.strip():
        dk, tham = (" AND (chuan(goc) LIKE ? ESCAPE '\\' OR chuan(dich) LIKE ? ESCAPE '\\')",
                    [nid, _mau(q), _mau(q)])
    else:
        dk, tham = "", [nid]
    tong = con.execute(f"SELECT count(*) FROM thuat_ngu WHERE nhom_id=?{dk}", tham).fetchone()[0]
    hang = con.execute(f"SELECT goc,dich FROM thuat_ngu WHERE nhom_id=?{dk} "
                       f"ORDER BY {cot} {huong}, id LIMIT ? OFFSET ?", [*tham, gioi, bo])
    return {r[0]: r[1] for r in hang}, tong


def liet_ke_cong_viec(con: sqlite3.Connection, trang_thai: str | None = None,
                      sap_xep: str = "tao_luc", thu_tu: str = "desc", trang: int = 1,
                      moi_trang: int = 50) -> tuple[list[dict], int]:
    if trang_thai is not None and trang_thai not in TRANG_THAI_VIEC:
        raise ValueError("trang_thai phải là một trong: " + ", ".join(TRANG_THAI_VIEC))
    cot = _cot(sap_xep, {"tao_luc": "tao_luc", "cap_nhat_luc": "cap_nhat_luc",
                         "tien_do": "tien_do"})
    huong = _thu_tu(thu_tu)
    gioi, bo = _trang(trang, moi_trang)
    dk, tham = (" WHERE trang_thai=?", [trang_thai]) if trang_thai else ("", [])
    tong = con.execute(f"SELECT count(*) FROM cong_viec{dk}", tham).fetchone()[0]
    hang = con.execute(
        "SELECT id,trang_thai,buoc,tien_do,loi,tao_luc,cap_nhat_luc,"
        "(duong_dan_ra IS NOT NULL) AS co_ket_qua "
        f"FROM cong_viec{dk} ORDER BY {cot} {huong}, rowid {huong} LIMIT ? OFFSET ?",
        [*tham, gioi, bo])
    return [{**dict(r), "co_ket_qua": bool(r["co_ket_qua"])} for r in hang], tong


def liet_ke_nhat_ky(con: sqlite3.Connection, video_id: int | None = None,
                    buoc: str | None = None, ket_qua: str | None = None,
                    trang: int = 1, moi_trang: int = 50) -> tuple[list[dict], int]:
    """Moi nhat truoc. Dau 'translate_apply' la khoa idempotency noi bo nen an di,
    tru khi nguoi goi hoi dung buoc do."""
    gioi, bo = _trang(trang, moi_trang)
    dk: list[str] = []
    tham: list[object] = []
    if video_id is not None:
        dk.append("n.video_id=?")
        tham.append(video_id)
    if buoc is not None:
        dk.append("n.buoc=?")
        tham.append(buoc)
    else:
        dk.append("n.buoc<>'translate_apply'")
    if ket_qua is not None:
        dk.append("n.ket_qua=?")
        tham.append(ket_qua)
    where = " AND ".join(dk)
    tong = con.execute(f"SELECT count(*) FROM nhat_ky n WHERE {where}", tham).fetchone()[0]
    hang = con.execute(
        "SELECT n.id,n.video_id,v.thu_muc_work,n.buoc,n.ket_qua,n.giay,n.token_vao,n.token_ra,"
        "n.loi,n.luc FROM nhat_ky n LEFT JOIN video v ON v.id=n.video_id "
        f"WHERE {where} ORDER BY n.id DESC LIMIT ? OFFSET ?", [*tham, gioi, bo])
    return [{**dict(r), "thu_muc_work": Path(r["thu_muc_work"]).name if r["thu_muc_work"] else None}
            for r in hang], tong


def liet_ke_lich_su(con: sqlite3.Connection, nhom_id: int | None = None,
                    doi_tuong: str | None = None, hanh_dong: str | None = None,
                    trang: int = 1, moi_trang: int = 50) -> tuple[list[dict], int]:
    if doi_tuong not in (None, "nhom", "thuat_ngu") or hanh_dong not in (None, "tao", "sua", "xoa"):
        raise ValueError("doi_tuong là nhom|thuat_ngu; hanh_dong là tao|sua|xoa")
    gioi, bo = _trang(trang, moi_trang)
    dk: list[str] = []
    tham: list[object] = []
    for cot, v in (("nhom_id", nhom_id), ("doi_tuong", doi_tuong), ("hanh_dong", hanh_dong)):
        if v is not None:
            dk.append(f"{cot}=?")
            tham.append(v)
    where = " AND ".join(dk) or "1=1"
    tong = con.execute(f"SELECT count(*) FROM lich_su WHERE {where}", tham).fetchone()[0]
    hang = con.execute(f"SELECT id,doi_tuong,nhom_id,khoa,hanh_dong,cu,moi,luc FROM lich_su "
                       f"WHERE {where} ORDER BY id DESC LIMIT ? OFFSET ?", [*tham, gioi, bo])
    return [dict(r) for r in hang], tong


# ---------------------------------------------------------------- xoa

def _kiem_khong_ban(con: sqlite3.Connection) -> None:
    dang = con.execute(f"SELECT count(*) FROM cong_viec WHERE trang_thai IN "
                       f"({','.join('?' * len(VIEC_DANG_CHAY))})", VIEC_DANG_CHAY).fetchone()[0]
    if dang:
        raise DangBan(f"Đang có {dang} công việc chạy; đợi chúng xong rồi thử lại")


def xoa_nhom(con: sqlite3.Connection, nid: int) -> None:
    """Xoa nhom keo theo thuat ngu (CASCADE); video giu lai, mat nhom (SET NULL)."""
    _kiem_khong_ban(con)
    con.execute("DELETE FROM nhom WHERE id=?", (nid,))


def xoa_thuat_ngu(con: sqlite3.Connection, nid: int, goc: str) -> None:
    _kiem_khong_ban(con)
    if con.execute("DELETE FROM thuat_ngu WHERE nhom_id=? AND goc=?", (nid, goc)).rowcount == 0:
        raise KhongCo("Không có thuật ngữ này")


# ---------------------------------------------------------------- sao luu

def _kiem_file_db(path: Path) -> None:
    """File phai la SQLite nguyen ven va co du bang cua he thong nay."""
    try:
        with closing(sqlite3.connect(f"{Path(path).resolve().as_uri()}?mode=ro", uri=True)) as raw:
            if raw.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("integrity_check không đạt")
            co = {r[0] for r in raw.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    except sqlite3.DatabaseError as exc:
        raise ValueError(f"Không phải file CSDL hợp lệ: {exc}") from None
    thieu = BANG_BAT_BUOC - co
    if thieu:
        raise ValueError(f"File thiếu bảng: {sorted(thieu)}")


def sao_luu(con: sqlite3.Connection, dich: Path) -> Path:
    """Chup nhat quan bang backup API (an toan khi dang co nguoi ghi, ke ca che do WAL).

    Ghi ra file tam roi kiem roi moi doi ten: ban sao luu hong khong bao gio che ban tot.
    """
    dich = Path(dich)
    dich.parent.mkdir(parents=True, exist_ok=True)
    tam = dich.with_name(dich.name + ".tmp")
    try:
        with closing(sqlite3.connect(tam)) as out:
            con.backup(out)
        _kiem_file_db(tam)
        os.replace(tam, dich)
    finally:
        tam.unlink(missing_ok=True)
    return dich


def khoi_phuc(con: sqlite3.Connection, nguon: Path) -> None:
    """Thay toan bo noi dung CSDL dang mo bang ban sao luu; chi tiep tuc khi nguon hop le."""
    nguon = Path(nguon)
    if not nguon.is_file():
        raise FileNotFoundError(f"Không tìm thấy file sao lưu: {nguon}")
    _kiem_file_db(nguon)
    _kiem_khong_ban(con)
    if con.in_transaction:
        raise RuntimeError("Không khôi phục được khi đang có giao dịch mở")
    with closing(sqlite3.connect(f"{nguon.resolve().as_uri()}?mode=ro", uri=True)) as src:
        src.backup(con)
    con.executescript(SCHEMA)           # ban sao luu cu thieu bang/trigger moi: bo sung
    con.execute("PRAGMA foreign_keys=ON")
