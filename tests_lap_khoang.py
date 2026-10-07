"""V-12b: lap khoang trong do phu — render, subs, audio, main (CLI).

Offline: ffmpeg, ffprobe, demucs va pipeline deu bi thay bang ham gia;
`--smoke` va `--real` moi chay ffmpeg/model that.
"""
from __future__ import annotations

import io
import json
import os
import subprocess
import tempfile
import wave
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch


def _loi(ham, loai=ValueError, *a, **kw):
    try:
        ham(*a, **kw)
    except loai as exc:
        return exc
    raise AssertionError(f"{ham} khong nem {loai.__name__}")


def _wav(path, kenh=1, tan_so=16000, khung=160):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(kenh)
        w.setsampwidth(2)
        w.setframerate(tan_so)
        w.writeframes(b"\x00\x00" * kenh * khung)


# --------------------------------------------------------------- render

def test_render_khoang_tham_so_sai_va_cue_ngoai_phim():
    from pipeline.render import cue_thanh_khoang, gop_khoang
    from pipeline.srt import Cue
    for kw in ({"nghi": -1}, {"gap": 0}, {"toi_da": 0}):
        _loi(cue_thanh_khoang, ValueError, [Cue(1, 0, 1, "a")], **kw)
    assert cue_thanh_khoang([]) == []
    # Cue nam sau het phim: gap nhan doi toi khi >= het ma van khong noi duoc -> lam mo ca phim.
    cues = [Cue(1, 0, 1, "a"), Cue(2, 100, 101, "b"), Cue(3, 200, 201, "c")]
    assert cue_thanh_khoang(cues, thoi_luong=5, toi_da=1) == [(0.0, 5)]
    assert len(cue_thanh_khoang(cues, thoi_luong=300, toi_da=1)) == 1
    assert gop_khoang([]) == [] and gop_khoang([(5, 6), (1, 2), (2, 3)]) == [(1, 3), (5, 6)]


def test_render_kieu_chu_khong_hop_va_font_scale_sai():
    from pipeline.render import kieu_chu
    ngang, doc = kieu_chu(1920, 1080), kieu_chu(1080, 1920)
    assert (ngang["FontSize"], ngang["MarginV"]) == (22, 30)
    assert (doc["FontSize"], doc["MarginV"]) == (16, 90)
    assert kieu_chu(1280, 720, (0, 600, 400, 60))["MarginV"] == 60
    assert kieu_chu(1280, 720, (0, 600, 400, 4))["FontSize"] == 8
    for xau in (0, -1, True, "0.4", None, float("nan")):
        _loi(kieu_chu, ValueError, 1280, 720, None, xau)


def test_bo_ma_hoa_nvenc_chay_duoc_hoac_lui_ve_libx264():
    from pipeline import render
    tot = subprocess.CompletedProcess([], 0, "", "")
    hong = subprocess.CompletedProcess([], 1, "", "no nvenc")
    try:
        for kq, mong in ((tot, "h264_nvenc"), (hong, "libx264")):
            render.bo_ma_hoa.cache_clear()
            with patch.object(render.subprocess, "run", return_value=kq) as run:
                assert render.bo_ma_hoa()[1] == mong
                render.bo_ma_hoa()
                assert run.call_count == 1                          # lru_cache: chi thu mot lan
    finally:
        render.bo_ma_hoa.cache_clear()


def _ffmpeg_gia(loi_ffmpeg=None, probe=None):
    lenh = []

    def run(args, **kw):
        lenh.append((args, kw))
        if args[0] == "ffprobe":
            return subprocess.CompletedProcess(args, 0 if probe is not None else 1,
                                               json.dumps(probe) if probe is not None else "", "bad")
        if loi_ffmpeg:
            return subprocess.CompletedProcess(args, 1, "", loi_ffmpeg)
        Path(args[-1]).write_bytes(b"mp4")
        return subprocess.CompletedProcess(args, 0, "", "")
    return run, lenh


def _loc(lenh_ffmpeg):
    return lenh_ffmpeg[lenh_ffmpeg.index("-filter_complex") + 1]


def test_ket_xuat_filtergraph_loai_tru_chung_va_loi_ffmpeg():
    from pipeline import render
    HOP = {"x": 0.1, "y": 0.8, "w": 0.5, "h": 0.1}
    RIENG = {**HOP, "cue": [3]}
    probe_tot = {"streams": [{"width": 1280, "height": 720}], "format": {"duration": "3.5"}}
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        srt = d / "v.vi.srt"
        srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nXin chào\n", encoding="utf-8")
        style = {"W": 1280, "H": 720}
        vung = [(HOP, [(0, 1)]), (RIENG, [(2, 3)]), (HOP, [])]
        run, lenh = _ffmpeg_gia(probe=probe_tot)
        with patch.object(render.subprocess, "run", run), \
                patch.object(render, "bo_ma_hoa", return_value=("-c:v", "libx264")):
            ra = render.ket_xuat(d / "v.mp4", srt, vung, style, d / "ra.mp4", loai_tru_chung=[(2, 3)])
            assert ra.read_bytes() == b"mp4"
            loc = _loc(lenh[0][0])
            assert loc.count("overlay=") == 2                       # hop khong co khoang bi bo
            assert "*not(between(t\\,2.000\\,3.000))" in loc         # chi vung chung bi tru
            assert loc.count("not(") == 1                           # vung rieng thang o ca hai bien
            assert "subtitles=v.vi.ass" in loc and (d / "v.vi.ass").is_file()
            assert lenh[0][1]["cwd"] == str(d.resolve())
            # Khong co vung nao: chi ve phu de, khong overlay.
            trong = render.ket_xuat(d / "v.mp4", srt, [], style, d / "trong.mp4")
            assert trong.is_file() and "overlay" not in _loc(lenh[-2][0])
        # ffmpeg loi -> RuntimeError kem stderr; file dich cu va thu muc khong bi dong vao.
        (d / "cu.mp4").write_bytes(b"ban-cu")
        run, _ = _ffmpeg_gia(loi_ffmpeg="Invalid argument")
        with patch.object(render.subprocess, "run", run), \
                patch.object(render, "bo_ma_hoa", return_value=("-c:v", "libx264")):
            assert "Invalid argument" in str(_loi(render.ket_xuat, RuntimeError, d / "v.mp4", srt,
                                                  vung, style, d / "cu.mp4"))
        assert (d / "cu.mp4").read_bytes() == b"ban-cu"
        assert not [p for p in d.iterdir() if p.name.startswith(".cu-")]
        # Thieu ffmpeg/ffprobe: bao ten tool, khong chay gi.
        with patch.object(render.shutil, "which", side_effect=lambda t: None if t == "ffprobe" else "x"):
            assert "ffprobe" in str(_loi(render.ket_xuat, RuntimeError, d / "v.mp4", srt, vung, style,
                                         d / "z.mp4"))


def test_kiem_ra_tu_choi_output_khong_co_luong_video():
    from pipeline import render
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "o.mp4"
        f.write_bytes(b"x")
        for probe in (None, {}, {"streams": []}, {"streams": [{}], "format": {"duration": "0"}}):
            run, _ = _ffmpeg_gia(probe=probe)
            with patch.object(render.subprocess, "run", run):
                _loi(render._kiem_ra, RuntimeError, f)
        run, _ = _ffmpeg_gia(probe={"streams": [{"width": 2, "height": 2}], "format": {"duration": "1"}})
        with patch.object(render.subprocess, "run", run):
            render._kiem_ra(f)                                     # hop le thi khong nem


# --------------------------------------------------------------- subs, audio

def test_probe_subs_doc_json_ffprobe_va_nem_khi_ffprobe_loi():
    from pipeline import subs
    ra = subprocess.CompletedProcess([], 0, json.dumps({"streams": [{"index": 2, "codec_name": "subrip"}]}), "")
    with patch.object(subs.subprocess, "run", return_value=ra) as run:
        assert subs.probe_subs(Path("v.mp4")) == [{"index": 2, "codec_name": "subrip"}]
        assert run.call_args.kwargs["check"] is True               # loi ffprobe khong bi nuot
    with patch.object(subs.subprocess, "run", side_effect=subprocess.CalledProcessError(1, "ffprobe")):
        _loi(subs.probe_subs, subprocess.CalledProcessError, Path("v.mp4"))
    assert subs.alias_lang("EN") == ("en", "eng") and subs.alias_lang("xx") == ("xx",)


def test_audio_kiem_wav_va_tach_khong_tach_giong():
    from pipeline import audio
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        for ten, kw in (("ok", {}), ("sai_kenh", {"kenh": 2}), ("sai_tan_so", {"tan_so": 44100}),
                        ("rong", {"khung": 0})):
            _wav(d / f"{ten}.wav", **kw)
            if ten == "ok":
                audio.kiem_wav(d / "ok.wav")
            else:
                _loi(audio.kiem_wav, ValueError, d / f"{ten}.wav")

        def run(args, **kw):
            _wav(args[-1])
            return subprocess.CompletedProcess(args, 0, "", "")
        with patch.object(audio.subprocess, "run", run):
            assert audio.tach(d / "v.mp4", d / "sub" / "a.wav") == d / "sub" / "a.wav"
        audio.kiem_wav(d / "sub" / "a.wav")

        # ffmpeg hong -> loi lan ra, khong de WAV do dang.
        with patch.object(audio.subprocess, "run", side_effect=subprocess.CalledProcessError(1, "ffmpeg")):
            _loi(audio.tach, subprocess.CalledProcessError, d / "v.mp4", d / "hong.wav")

        # ffmpeg "thanh cong" nhung ra WAV sai kenh -> kiem_wav chan, khong thay file dich.
        def run_sai(args, **kw):
            _wav(args[-1], kenh=2)
            return subprocess.CompletedProcess(args, 0, "", "")
        with patch.object(audio.subprocess, "run", run_sai):
            _loi(audio.tach, ValueError, d / "v.mp4", d / "sai.wav")
        assert not (d / "hong.wav").exists() and not (d / "sai.wav").exists()
        assert not [p for p in d.rglob(".*") if p.is_file()]      # khong de file tam


def test_audio_tach_giong_demucs_gia():
    from pipeline import audio
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        with patch.object(audio.importlib.util, "find_spec", return_value=None):
            assert "Demucs" in str(_loi(audio.tach, RuntimeError, d / "v.mp4", d / "a.wav", separate=True))

        def run_demucs(tao_vocals):
            def run(args, **kw):
                if "demucs" in args:
                    ra = Path(args[args.index("-o") + 1]) / "htdemucs" / Path(args[-1]).stem
                    if tao_vocals:
                        ra.mkdir(parents=True)
                        _wav(ra / "vocals.wav")
                else:
                    _wav(args[-1])
                return subprocess.CompletedProcess(args, 0, "", "")
            return run
        with patch.object(audio.importlib.util, "find_spec", return_value=object()):
            with patch.object(audio.subprocess, "run", run_demucs(True)):
                assert audio.tach(d / "v.mp4", d / "a.wav", separate=True) == d / "vocals.wav"
            audio.kiem_wav(d / "vocals.wav")
            with patch.object(audio.subprocess, "run", run_demucs(False)):
                assert "vocals.wav" in str(_loi(audio.tach, RuntimeError, d / "v.mp4", d / "b.wav",
                                                separate=True))
        assert not [p for p in d.iterdir() if p.is_dir()]         # thu muc tam cua demucs da don


# --------------------------------------------------------------- cli

def _cli_chay(args, chay=None, which="ffmpeg"):
    """Chay main.main voi pipeline gia; tra (ma thoat, stdout, stderr)."""
    import main as cli
    out, err = io.StringIO(), io.StringIO()
    with patch.object(cli.shutil, "which", return_value=which), \
            patch.object(cli.dieu_phoi, "tao_goi", lambda m: object()), \
            patch.object(cli.dieu_phoi, "chay", chay or (lambda *a, **kw: None)), \
            redirect_stdout(out), redirect_stderr(err):
        try:
            ma = cli.main(args)
        except SystemExit as exc:                                  # argparse thoat bang SystemExit
            ma = exc.code
    return ma, out.getvalue(), err.getvalue()


def _ngat(*a, **k):
    raise KeyboardInterrupt


def test_cli_chay_mot_video_theo_trang_thai_ket_qua():
    from pipeline.dieu_phoi import KetQua
    cu = Path.cwd()
    with tempfile.TemporaryDirectory() as d:
        os.chdir(d)
        try:
            Path("work").mkdir()
            Path("v.mp4").write_bytes(b"x")
            ra_nhan = []

            def chay(tt, **extra):
                def f(video, tc, bao, con=None, goi=None):
                    bao("Buoc thu", 0.5)
                    ra_nhan.append(tc.ra)
                    return KetQua(tt, Path("work/w"), Path("ra.mp4"), canh_bao=["cue 2 giu nguyen"], **extra)
                return f
            ma, out, _ = _cli_chay(["v.mp4", "-o", "x.mp4"], chay("xong"))
            assert ma == 0 and "XONG: ra.mp4" in out and "[  50%] Buoc thu" in out
            assert ra_nhan == [Path("x.mp4")]
            ma, _, err = _cli_chay(["video", "v.mp4"], chay("suy_giam"))
            assert ma == 1 and "SUY GIAM: cue 2 giu nguyen" in err
            ma, _, err = _cli_chay(["v.mp4"], chay("cho_chon_khung", khung=[Path("k0.png")]))
            assert ma == 1 and "DUNG LAI" in err and "--blur-box" in err
            # Loi nhap/cau hinh: ma 1 va khong goi pipeline.
            goi = []
            assert _cli_chay(["khong-co.mp4"], lambda *a, **k: goi.append(1))[0] == 1
            ma, _, err = _cli_chay(["v.mp4"], lambda *a, **k: goi.append(1), which=None)
            assert ma == 1 and "ffmpeg" in err and not goi
            assert _cli_chay(["v.mp4", "--blur-box", "1,2,3"])[0] == 2     # argparse: sai dang hop
            assert _cli_chay(["v.mp4", "--blur-box", "a,b,c,d"])[0] == 2
            assert _cli_chay(["v.mp4"], _ngat)[0] == 130                   # Ctrl+C

            def hong(*a, **k):
                raise RuntimeError("model hong")
            ma, _, err = _cli_chay(["v.mp4"], hong)
            assert ma == 1 and "LOI: model hong" in err
            ma, out, _ = _cli_chay([])                                     # khong lenh -> tro giup
            assert ma == 2 and "usage" in out.lower()
        finally:
            os.chdir(cu)


def test_cli_batch_dem_ket_qua_tung_video_va_loi_khong_dung_lo():
    from pipeline.dieu_phoi import KetQua
    cu = Path.cwd()
    with tempfile.TemporaryDirectory() as d:
        os.chdir(d)
        try:
            Path("work").mkdir()
            thu = Path("lo")
            thu.mkdir()
            for ten in ("a.mp4", "b.mp4", "c.mp4", "d.mp4"):
                (thu / ten).write_bytes(b"x")
            (thu / "ghi_chu.txt").write_text("bo qua", encoding="utf-8")
            kq = {"a.mp4": "xong", "b.mp4": "suy_giam", "c.mp4": "cho_chon_khung"}

            def chay(video, tc, bao, con=None, goi=None):
                if video.name == "d.mp4":
                    raise RuntimeError("hong giua chung")
                return KetQua(kq[video.name], Path("w"), Path("ra.mp4"), canh_bao=["x"])
            ma, out, err = _cli_chay(["batch", str(thu)], chay)
            assert ma == 1 and "xong=1, suy_giam=1, cho_chon_khung=1, loi=1" in out
            assert "LOI d.mp4: hong giua chung" in err
            kq.update({"b.mp4": "xong", "c.mp4": "xong"})
            (thu / "d.mp4").unlink()
            ma, out, _ = _cli_chay(["batch", str(thu)], chay)
            assert ma == 0 and "xong=3" in out
            assert _cli_chay(["batch", str(thu)], _ngat)[0] == 130         # Ctrl+C khong bi nuot thanh "loi"
            Path("rong").mkdir()
            ma, _, err = _cli_chay(["batch", "rong"], chay)
            assert ma == 1 and "Khong co video" in err
            assert _cli_chay(["batch", str(thu)], chay, which=None)[0] == 1    # preflight chan truoc vong lap
            assert _cli_chay(["batch", str(thu), "--blur-box", "x"])[0] == 2
        finally:
            os.chdir(cu)


def test_cli_nhom_list_set_box_glossary():
    cu = Path.cwd()
    with tempfile.TemporaryDirectory() as d:
        os.chdir(d)
        try:
            Path("work").mkdir()
            assert _cli_chay(["nhom", "list"])[1] == ""
            assert _cli_chay(["nhom", "set-term", "Phim", "Ironhold", "Thành Sắt"])[0] == 0
            assert _cli_chay(["nhom", "list"])[1] == "Phim\tchua co hop\n"
            assert _cli_chay(["nhom", "set-box", "Phim", "0.3,0.855,0.4,0.09"])[0] == 0
            assert _cli_chay(["nhom", "list"])[1] == "Phim\thop 0.3,0.855,0.4,0.09\n"
            assert _cli_chay(["nhom", "glossary", "Phim"])[1] == "Ironhold\tThành Sắt\n"
            assert _cli_chay(["nhom", "set-box", "Phim", "2,2,2,2"])[0] == 1   # hop ngoai 0-1: validator chan
            assert _cli_chay(["nhom", "set-box", "Phim", "abc"])[0] == 2
            assert _cli_chay(["nhom"])[0] == 2                                  # thieu viec con
            ma, out, _ = _cli_chay(["lich-su"])
            assert ma == 0 and "Ironhold" in out
        finally:
            os.chdir(cu)


# --------------------------------------------------------------- hoi quy tu review doc lap (commit 8da22f2)

def test_lich_su_cua_nhom_da_xoa_van_xem_duoc():
    """Hoi quy: lich_su_tim doi ten -> id bang tim_nhom, nen nhom da xoa bi 404 dung luc can xem ai xoa."""
    from contextlib import closing
    from pipeline import db, dieu_phoi
    with closing(db.mo(":memory:")) as con:
        with con:
            dieu_phoi.nhom_tao(con, "Ironhold")
        assert [r["hanh_dong"] for r in dieu_phoi.lich_su_tim(con, nhom="Ironhold")[0]] == ["tao"]
        with con:
            dieu_phoi.nhom_xoa(con, "Ironhold")
        dong, tong = dieu_phoi.lich_su_tim(con, nhom="Ironhold")
        assert {r["hanh_dong"] for r in dong} == {"tao", "xoa"} and tong == 2
        _loi(dieu_phoi.lich_su_tim, dieu_phoi.KhongCo, con, nhom="chua-tung-co")   # ten la van la 404
        assert dieu_phoi.lich_su_tim(con)[1] == 2                                  # khong loc: nhu cu


def test_khoi_phuc_dang_ban_khong_de_lai_ban_an_toan_vo_ich():
    """Hoi quy: ban 'truoc-khoi-phuc' duoc chup truoc khi kiem DangBan, moi lan thu lai de them mot ban."""
    from contextlib import closing
    from pipeline import db, dieu_phoi
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        with closing(db.mo(d / "a.db")) as con:
            with con:
                db.lay_nhom(con, "A")
            ban = db.sao_luu(con, d / "bk.db")
            with con:
                db.tao_cong_viec(con, "dang-chay")
            for _ in range(3):
                _loi(dieu_phoi.khoi_phuc, db.DangBan, con, ban, d / "sao_luu")
            assert not (d / "sao_luu").exists() or not list((d / "sao_luu").glob("truoc-khoi-phuc-*"))


def test_loi_sao_luu_luc_khoi_dong_khong_chan_server():
    """Hoi quy: lifespan khong bat loi sao luu, nen o day day hoac CLI giu khoa DB la server khong len."""
    from api import viec
    from tests_api import _san
    with patch("pipeline.dieu_phoi.sao_luu_tu_dong", side_effect=OSError("day dia")), \
            patch("logging.warning") as canh_bao, \
            _san() as (client, video):
        assert client.get("/api/nhom").status_code == 200
        assert any("sao luu" in str(c.args[0]).lower() for c in canh_bao.call_args_list)
        r = client.post("/api/sao-luu")                         # sao luu bang tay van chay, cung thu muc voi ban tu dong
        assert r.status_code == 201 and (viec.DB.parent / "sao_luu" / r.json()["tep"]).is_file()


def test_tach_cau_manh_co_moc_khong_do_dai_thi_giu_nguyen_segment():
    """Hoi quy (do tren phim 16 phut, Whisper large-v3): cau cuoi segment co start==end lam
    kiem_cue nem 'Moc thoi gian khong hop le' va hong ca buoc nhan dang."""
    from types import SimpleNamespace as S
    from pipeline import asr
    from pipeline.srt import kiem_cue

    def w(t, a, b):
        return S(word=t, start=a, end=b)
    seg = S(start=84.26, end=84.52, text=" Even. Minecraft is a game.",
            words=[w(" Even.", 84.26, 84.40), w(" Minecraft", 84.52, 84.52), w(" is", 84.52, 84.52),
                   w(" a", 84.52, 84.52), w(" game.", 84.52, 84.52)])
    cues = asr.tach_cau(seg)
    assert len(cues) == 1 and cues[0].text == "Even. Minecraft is a game."      # khong mat chu
    assert (cues[0].bat_dau, cues[0].ket_thuc) == (84.26, 84.52)
    kiem_cue(cues)                                                              # hop le, ghi SRT duoc
    tot = S(start=1.0, end=3.0, text=" Hi. There.",
            words=[w(" Hi.", 1.0, 1.5), w(" There.", 2.0, 3.0)])
    assert [(c.bat_dau, c.ket_thuc) for c in asr.tach_cau(tot)] == [(1.0, 1.5), (2.0, 3.0)]   # van tach binh thuong
