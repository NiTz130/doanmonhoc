"""Offline contracts for media; no model download or GUI."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch


def test_asr_fallback_all_phases():
    from pipeline import asr
    from pipeline.srt import doc_srt
    for phase in ('constructor', 'transcribe', 'generator'):
        devices = []
        def factory(name, device, compute_type):
            devices.append(device)
            if device == 'cuda' and phase == 'constructor':
                raise RuntimeError('CUDA driver version is insufficient')
            class Model:
                def transcribe(self, *args, **kwargs):
                    if device == 'cuda' and phase == 'transcribe':
                        raise RuntimeError('CUDA out of memory')
                    def segments():
                        yield SimpleNamespace(start=0, end=1, text=' hello ')
                        if device == 'cuda' and phase == 'generator':
                            raise RuntimeError('cuDNN library not found')
                    return segments(), None
            return Model()
        with TemporaryDirectory() as d:
            dest = Path(d) / 'out.srt'
            asr.nhan_dang(Path(d)/'audio.wav', dest, tao_model=factory)
            assert devices == ['cuda', 'cpu']
            assert len(doc_srt(dest)) == 1
    for message in ('Invalid audio file', 'Model not found'):
        calls = []
        def broken(*args, **kwargs):
            calls.append(kwargs['device'])
            raise RuntimeError(message)
        with TemporaryDirectory() as d:
            dest = Path(d)/'out.srt'
            dest.write_text('old')
            try:
                asr.nhan_dang(Path(d)/'a.wav', dest, tao_model=broken)
                assert False
            except RuntimeError as e:
                assert str(e) == message
            assert calls == ['cuda'] and dest.read_text() == 'old'


def test_box_intervals_and_style():
    from pipeline.markbox import kiem_hop
    from pipeline.render import hop_sang_pixel, cue_thanh_khoang, kieu_chu
    from pipeline.srt import Cue
    box = dict(co_blur=True, x=.3, y=.8, w=.4, h=.1)
    for W, H in ((1920,1080), (1280,720)):
        px = hop_sang_pixel(box,W,H)
        assert all(n % 2 == 0 for n in px)
        style = kieu_chu(W,H,px)
        assert style['MarginV'] == H-px[1]-px[3]
        assert style['FontSize'] == round(px[3]*.42)
        assert style['PlayResY'] == H
    for key,val in [('x',-.1),('y',float('nan')),('h',float('inf')),('w',0),('w',.9),('x',True)]:
        try:
            kiem_hop(dict(box, **{key:val}))
            assert False, (key,val)
        except ValueError:
            pass
    try:
        hop_sang_pixel(dict(box,w=.00001),1920,1080)
        assert False
    except ValueError:
        pass
    assert cue_thanh_khoang([Cue(1,1,2,'a'),Cue(2,2.5,4,'b')]) == [(0.6,4.4)]
    assert len(cue_thanh_khoang([Cue(i+1,i*10+1,i*10+2,'a') for i in range(300)])) <= 50


def test_subtitle_priority_and_codecs():
    from pipeline import subs
    from pipeline.srt import Cue, ghi_srt, doc_srt
    with TemporaryDirectory() as d:
        video = Path(d)/'movie.mkv'
        generic = video.with_suffix('.srt')
        english = video.with_suffix('.eng.srt')
        ghi_srt([Cue(1,0,1,'generic')], generic)
        ghi_srt([Cue(1,0,1,'english')], english)
        assert subs.tim_sidecar(video,'en') == english
        assert subs.tim_sidecar(video,'vi') == generic
        generic.unlink(); english.unlink()
        dest = Path(d)/'out.srt'
        with patch.object(subs, 'probe_subs', return_value=[{'codec_name':'hdmv_pgs_subtitle'}]):
            assert not subs.tim_phu_de(video,dest)
        tracks = [{'codec_name':'hdmv_pgs_subtitle'}, {'codec_name':'subrip','tags':{'language':'eng'}}]
        def run(cmd, **kwargs):
            assert cmd[cmd.index('-map')+1] == '0:s:1'
            ghi_srt([Cue(1,0,1,'embedded')],Path(cmd[-1]))
        with patch.object(subs, 'probe_subs', return_value=tracks), patch.object(subs.subprocess, 'run', side_effect=run):
            assert subs.tim_phu_de(video,dest)
        assert doc_srt(dest)[0].text == 'embedded'


if __name__ == '__main__':
    for name, fn in list(globals().items()):
        if name.startswith('test_'):
            fn()
            print('PASS', name)


def test_moc_khung_mot_khung_moi_cue():
    """43 phu de thi phai co 43 khung: lay mau 8 khung lam cau nhay cho lot luoi."""
    from pipeline.markbox import moc_khung
    from pipeline.srt import Cue
    cues = [Cue(i + 1, i * 2.0, i * 2.0 + 1.5, f"line {i + 1}") for i in range(43)]
    moc = moc_khung(cues)
    assert len(moc) == 43
    assert [m["i"] for m in moc] == list(range(43))
    assert moc[0]["giay"] == 0.3 and moc[42]["giay"] == 84.3
    assert moc[42]["text"] == "line 43"
    assert moc_khung([]) == []


def test_kieu_chu_bam_hop_ap_cho_moi_cau():
    """Nhieu vung mo nhung phu de Viet chi ve mot cho: chon hop nao lam chuan."""
    from pipeline.render import ket_xuat
    duoi = {"x": .3, "y": .80, "w": .4, "h": .12, "cue": None}
    tren = {"x": .3, "y": .05, "w": .4, "h": .12, "cue": [1]}
    chon = []

    def bat(W, H, px, font_scale=0.42, du_phong=None):
        chon.append(px)
        return {"PlayResX": W, "PlayResY": H, "FontName": "Arial",
                "FontSize": 20, "MarginV": 10}

    import pipeline.render as render
    from pipeline.srt import Cue, ghi_srt
    import tempfile
    from pathlib import Path
    from unittest.mock import patch

    with tempfile.TemporaryDirectory() as d:
        srt = Path(d) / "s.srt"
        ghi_srt([Cue(1, 0, 1, "a"), Cue(2, 2, 3, "b")], srt)
        style = {"W": 1280, "H": 720, "font_scale": .42}
        # Chan truoc khi cham ffmpeg: chi can biet kieu_chu duoc goi voi hop nao.
        with patch.object(render, "kieu_chu", bat), \
                patch.object(render.subprocess, "run", side_effect=AssertionError("stop")):
            for vung in ([(duoi, [(0.0, 3.0)]), (tren, [(1.6, 3.0)])],
                         [(tren, [(1.6, 3.0)]), (duoi, [(0.0, 3.0)])]):
                try:
                    ket_xuat(Path(d) / "v.mp4", srt, vung, style, Path(d) / "r.mp4")
                except AssertionError:
                    pass
    # Ca hai thu tu deu phai ra hop `duoi` (cue=None), khong phu thuoc thu tu danh sach.
    assert len(chon) == 2 and chon[0] == chon[1], chon
    assert chon[0] == render.hop_sang_pixel(duoi, 1280, 720), chon[0]


def test_viet_ass_bo_the_dinh_dang_goc():
    # Bao ve loi: the <i>/<font>/{\an8} cua phu de goc chay nguyen chu len hinh.
    from pipeline.render import viet_ass
    from pipeline.srt import Cue
    cues = [Cue(1, 0, 1, "<i>Xin chao</i>"), Cue(2, 1, 2, '<font color="#fff">A</font>'),
            Cue(3, 2, 3, "{\\an8}Tren"), Cue(4, 3, 4, "a < b > c"), Cue(5, 4, 5, "{la}"),
            Cue(6, 5, 6, "<B>x</B>\n<u>y</u>")]
    with TemporaryDirectory() as d:
        ra = Path(d) / "x.ass"
        viet_ass(cues, {"PlayResX": 1280, "PlayResY": 720, "FontName": "Arial",
                        "FontSize": 20, "MarginV": 10}, ra)
        ass = ra.read_text(encoding="utf-8")
    for xau in ("<i>", "</i>", "<font", "\\an8", "<B>", "<u>"):
        assert xau not in ass, xau
    assert ",,Xin chao\n" in ass and ",,Tren\n" in ass and ",,x\\Ny\n" in ass
    assert "a < b > c" in ass
    assert ",,(la)\n" in ass


def test_asr_bo_segment_rong_hoac_nguoc_thoi_gian():
    # Bao ve loi: mot segment rong/end<=start cua Whisper lam hong ca cong viec.
    from pipeline import asr
    from pipeline.srt import doc_srt
    seg = [SimpleNamespace(start=0, end=1, text=" a "), SimpleNamespace(start=1, end=2, text="  "),
           SimpleNamespace(start=3, end=3, text="b"), SimpleNamespace(start=4, end=5, text="c")]

    class Model:
        def transcribe(self, *args, **kwargs):
            return iter(seg), None
    with TemporaryDirectory() as d:
        ra = Path(d) / "out.srt"
        asr.nhan_dang(Path(d) / "a.wav", ra, tao_model=lambda *a, **k: Model())
        cues = doc_srt(ra)
    assert [(c.idx, c.bat_dau, c.ket_thuc, c.text) for c in cues] == [(1, 0, 1, "a"), (2, 4, 5, "c")]


def test_doc_srt_bo_cue_hong():
    # Bao ve loi: SRT ngoai doi co khoi chi co moc gio lam tu choi ca file.
    from pipeline.srt import doc_srt
    hong = "1\n00:00:00,000 --> 00:00:01,000\na\n\n2\n00:00:02,000 --> 00:00:03,000\n\n"
    hong += "3\n00:00:05,000 --> 00:00:04,000\nnguoc\n\n4\n00:00:06,000 --> 00:00:07,000\nb\n"
    with TemporaryDirectory() as d:
        p = Path(d) / "x.srt"
        p.write_text(hong, encoding="utf-8")
        try:
            doc_srt(p)
            assert False
        except ValueError:
            pass
        cues = doc_srt(p, bo_cue_hong=True)
        assert [(c.idx, c.bat_dau, c.text) for c in cues] == [(1, 0, "a"), (2, 6, "b")]
        for xau in ("1\n00:00:00,000 --> xx\na\n", "1\nkhong co mui ten\nchu\n"):
            p.write_text(xau, encoding="utf-8")
            try:
                doc_srt(p, bo_cue_hong=True)
                assert False, xau
            except ValueError:
                pass


def test_tim_phu_de_sidecar_co_cue_rong():
    # Bao ve loi: sidecar co mot cue rong lam hong ca cong viec.
    from pipeline import subs
    from pipeline.srt import doc_srt
    with TemporaryDirectory() as d:
        video = Path(d) / "m.mkv"
        video.with_suffix(".srt").write_text(
            "1\n00:00:00,000 --> 00:00:01,000\na\n\n2\n00:00:02,000 --> 00:00:03,000\n\n"
            "3\n00:00:04,000 --> 00:00:05,000\nb\n", encoding="utf-8")
        ra = Path(d) / "out.srt"
        assert subs.tim_phu_de(video, ra)
        assert [c.text for c in doc_srt(ra)] == ["a", "b"]


def test_nhan_dien_hoan_doi_khi_xoay():
    # Video quay doc: ffprobe bao kich thuoc truoc khi xoay, ffmpeg tu xoay hinh.
    import json
    from pipeline import dieu_phoi

    def chay(side):
        def gia(lenh, **_kw):
            assert any("stream_side_data=rotation" in a for a in lenh), lenh
            s = {"width": 640, "height": 360}
            if side is not None:
                s["side_data_list"] = side
            return SimpleNamespace(stdout=json.dumps({"streams": [s], "format": {"duration": "2.0"}}))
        with patch.object(dieu_phoi.subprocess, "run", gia):
            return dieu_phoi.nhan_dien(Path("x.mp4"))

    for side in ([{"rotation": 90}], [{"rotation": -90}], [{"rotation": 270}]):
        assert chay(side) == (360, 640, 2.0), side
    for side in ([{"rotation": 180}], None, [{}]):
        assert chay(side) == (640, 360, 2.0), side


def test_asr_tach_segment_nhieu_cau_theo_tu():
    # Hoi quy: Whisper gop "No, ...? The adult is talking." vao mot segment -> mat 1 dong phu de.
    from pipeline import asr
    from pipeline.srt import doc_srt
    def w(t, a, b): return SimpleNamespace(word=t, start=a, end=b)
    nhieu = SimpleNamespace(start=0, end=3, text=" Yes, sir. I'm sorry. Dr. Who? ", words=[
        w(" Yes,", 0, .3), w(" sir.", .3, .6), w(" I'm", 1, 1.2), w(" sorry.", 1.2, 1.8),
        w(" Dr.", 2, 2.2), w(" Who?", 2.2, 3)])
    mot = SimpleNamespace(start=5, end=7, text=" Okay then. ", words=[w(" Okay", 5.2, 6), w(" then.", 6, 7)])
    khong_tu = SimpleNamespace(start=8, end=9, text=" no words.")     # model gia/khong co words
    rong = SimpleNamespace(start=10, end=11, text=" x.", words=[])

    class Model:
        def transcribe(self, *args, **kwargs):
            assert kwargs.get("word_timestamps") is True
            return iter([nhieu, mot, khong_tu, rong]), None
    with TemporaryDirectory() as d:
        ra = Path(d) / "out.srt"
        asr.nhan_dang(Path(d) / "a.wav", ra, tao_model=lambda *a, **k: Model())
        cues = [(c.bat_dau, c.ket_thuc, c.text) for c in doc_srt(ra)]
    assert cues == [(0, .6, "Yes, sir."), (1, 1.8, "I'm sorry."), (2, 3, "Dr. Who?"),   # "Dr." khong ket cau
                    (5, 7, "Okay then."), (8, 9, "no words."), (10, 11, "x.")]            # 1 cau / khong co tu: giu moc segment


def test_gop_cau_asr():
    # Whisper ngat giua cau: gop toi dau cham; khong gop qua khoang lang hoac qua dai.
    from pipeline.asr import gop_cau
    from pipeline.srt import Cue
    c = [Cue(1, 0, 2, "It was released"), Cue(2, 2.2, 4, "in 2009."), Cue(3, 4.1, 5, "Next."),
         Cue(4, 8, 9, "no end"), Cue(5, 9.1, 12, "tail")]
    r = gop_cau(c)
    assert [(x.idx, x.bat_dau, x.ket_thuc, x.text) for x in r] == [
        (1, 0, 4, "It was released in 2009."), (2, 4.1, 5, "Next."), (3, 8, 12, "no end tail")]
    assert gop_cau([Cue(1, 0, 1, "a"), Cue(2, 1.1, 20, "b")])[1].text == "b"      # dai > 10s
