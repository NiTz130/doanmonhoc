-- schema.sql - so do CSDL cua he thong dich phu de video Anh -> Viet
--
-- SINH TU MA NGUON, dung sua tay.
-- Nguon duy nhat la hang so SCHEMA trong pipeline/db.py.
-- Sinh lai:  .venv/Scripts/python.exe -c "from pipeline.db import SCHEMA; print(SCHEMA)"
--
-- Ung dung tu chay SCHEMA nay moi lan mo ket noi (db.mo), nen khong can
-- chay file nay de he thong hoat dong. File ton tai de doc va de in vao bao cao.

PRAGMA foreign_keys = ON;

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
