-- schema.sql - so do CSDL cua he thong dich phu de video Anh -> Viet
--
-- SINH TU MA NGUON, dung sua tay.
-- Nguon duy nhat la hang so SCHEMA trong pipeline/db.py.
-- Sinh lai:  .venv/Scripts/python.exe -c "from pipeline.db import SCHEMA; print(SCHEMA)"
--
-- Ung dung tu chay SCHEMA nay moi lan mo ket noi (db.mo), nen khong can
-- chay file nay de he thong hoat dong. File ton tai de doc va de in vao bao cao.

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

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
