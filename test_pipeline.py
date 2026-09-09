"""Chay assert offline: python test_pipeline.py; media: them --smoke."""
from pathlib import Path
import tempfile


def test_srt_roundtrip_validation():
    from pipeline.srt import Cue, doc_srt, ghi_srt
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "sub.srt"
        cues = [Cue(1, 1.12, 3.45, "Xin chào\nthế giới")]
        ghi_srt(cues, p)
        assert doc_srt(p) == cues
        assert not p.read_bytes().startswith(b"\xef\xbb\xbf")
        for text in ("", "broken", "1\n00:00:03,000 --> 00:00:01,000\nx"):
            p.write_text(text, encoding="utf-8")
            try:
                doc_srt(p)
            except ValueError:
                pass
            else:
                raise AssertionError(text)


def test_atomic_write_and_lock():
    from pipeline.srt import file_tam, khoa_work
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "good.txt"
        p.write_text("good", encoding="utf-8")
        try:
            with file_tam(p) as tmp:
                tmp.write_text("bad", encoding="utf-8")
                raise ValueError("interrupted")
        except ValueError:
            pass
        assert p.read_text(encoding="utf-8") == "good"
        with khoa_work(Path(d)):
            try:
                with khoa_work(Path(d)):
                    raise AssertionError("lock accepted twice")
            except FileExistsError:
                pass
        assert not (Path(d) / ".lock").exists()


if __name__ == "__main__":
    for ten, ham in sorted(list(globals().items())):
        if ten.startswith("test_"):
            ham()
            print("OK", ten)
