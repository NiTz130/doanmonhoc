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
