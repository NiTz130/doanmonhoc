"""V-7 smoke media: `python test_pipeline.py --smoke`. Can ffmpeg that, khong can mang.

Day KHONG phai end-to-end: ASR va dich that la V-8, chi chay khi co uy quyen.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import subprocess


def _probe(path: Path) -> dict:
    ket = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format",
                          "-of", "json", str(path)], check=True, capture_output=True, text=True)
    return json.loads(ket.stdout)


def _video_gia(path: Path, W: int, H: int, giay: int = 5) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y",
                    "-f", "lavfi", "-i", f"testsrc=size={W}x{H}:rate=25:duration={giay}",
                    "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo:d={giay}",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
                    "-shortest", str(path)], check=True, capture_output=True, text=True)


def smoke_media() -> None:
    from pipeline import audio, render
    from pipeline.srt import Cue, ghi_srt
    # Hai cue cach nhau 2.0s: sau khi noi +-0.4 van con gap 1.2s > nguong gop, nen
    # khung t=2.5s roi ra ngoai moi khoang va chung minh duoc blur that su tat.
    cues = [Cue(1, 0.5, 1.5, "Xin chào thế giới"), Cue(2, 3.5, 4.5, "Dòng thứ hai\ncó dấu")]
    for W, H in ((1280, 720), (1920, 1080)):
        with TemporaryDirectory() as d:
            work = Path(d)
            video = work / "goc.mp4"
            _video_gia(video, W, H)

            wav = audio.tach(video, work / "audio.wav")
            audio.kiem_wav(wav)                 # mono 16 kHz PCM, khong rong
            print(f"  audio.tach {W}x{H}: {wav.name} OK")

            srt = work / "sub_vi.srt"
            ghi_srt(cues, srt)
            style = {"W": W, "H": H, "font_scale": 0.42,
                     "FontSize": 22, "MarginV": 30}
            for ten, hop in (("khong_blur", None), ("co_blur", {"x": .3, "y": .8, "w": .4, "h": .12})):
                ra = work / f"{ten}.mp4"
                render.ket_xuat(video, srt, hop,
                                render.khoang_mo(cues, 5.0) if hop else [], style, ra)
                d_goc, d_ra = _probe(video), _probe(ra)
                v = next(s for s in d_ra["streams"] if s["codec_type"] == "video")
                assert (v["width"], v["height"]) == (W, H), (ten, v["width"], v["height"])
                assert abs(float(d_ra["format"]["duration"])
                           - float(d_goc["format"]["duration"])) <= 0.1, ten
                assert any(s["codec_type"] == "audio" for s in d_ra["streams"]), \
                    f"{ten}: mat audio"
                print(f"  render {ten} {W}x{H}: {v['width']}x{v['height']}, "
                      f"{float(d_ra['format']['duration']):.2f}s, con audio OK")

            # Khung nhin de nguoi cham mat kiem chu Viet va vung mo (khong tu suy ra tu kich thuoc).
            for t, ten in ((1.0, "trong_cue"), (2.5, "ngoai_cue")):
                anh = Path.cwd() / f"smoke_{W}x{H}_{ten}.png"
                subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i",
                                str(work / "co_blur.mp4"), "-frames:v", "1", "-y", str(anh)],
                               check=True, capture_output=True, text=True)
                print(f"  khung {ten} t={t}s -> {anh.name} (xem bang mat)")


if __name__ == "__main__":
    smoke_media()
    print("smoke media: OK")
