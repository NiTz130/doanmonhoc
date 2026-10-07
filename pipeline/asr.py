"""Whisper recognition with one narrowly scoped CPU fallback."""
from __future__ import annotations

import gc
import logging
import re
from pathlib import Path
from collections.abc import Callable

from pipeline.srt import Cue, ghi_srt


def loi_cuda(exc: RuntimeError | OSError) -> bool:
    text = str(exc).lower()
    return any(x in text for x in ('cuda out of memory', 'cuda driver version is insufficient',
        'no cuda-capable device', 'cuda failed with error out of memory',
        'cudnn', 'cublas', 'cudart', 'nvcuda.dll', 'cuda driver library cannot be found'))


def gop_cau(cues: list[Cue], gap: float = 1.0, toi_da: float = 10.0) -> list[Cue]:
    """Whisper hay ngat giua cau; dich tung manh roi se mat mach. Gop cac cue lien tiep cho
    toi khi gap dau ket cau, khoang lang > gap giay hoac cue dai qua toi_da giay."""
    ra: list[Cue] = []
    for c in cues:
        if ra and not re.search(r'[.?!…]["\')]*$', ra[-1].text) \
                and c.bat_dau - ra[-1].ket_thuc <= gap and c.ket_thuc - ra[-1].bat_dau <= toi_da:
            t = ra[-1]
            ra[-1] = Cue(t.idx, t.bat_dau, c.ket_thuc, t.text + ' ' + c.text)
        else:
            ra.append(Cue(len(ra) + 1, c.bat_dau, c.ket_thuc, c.text))
    return ra


_VIET_TAT = {'mr.', 'mrs.', 'ms.', 'dr.', 'st.', 'jr.', 'sr.', 'vs.'}


def tach_cau(s) -> list[Cue]:
    """Whisper hay nhet nhieu cau vao mot segment (mat dong phu de, mat moc thoi gian).
    Co moc tung tu thi tach tai dau ket cau; segment mot cau hoac khong co words giu nguyen."""
    cue = Cue(0, s.start, s.end, s.text.strip())
    words = getattr(s, 'words', None)
    if not words:
        return [cue]
    cum: list[list] = [[]]
    for w in words:
        cum[-1].append(w)
        t = w.word.strip().lower()
        if re.search(r'[.?!…]["\')]*$', t) and t not in _VIET_TAT:
            cum.append([])
    cum = [c for c in cum if c]
    if len(cum) < 2:
        return [cue]
    cues = [Cue(0, c[0].start, c[-1].end, ''.join(w.word for w in c).strip()) for c in cum]
    # Whisper hay cho tu cuoi segment start==end; manh nhu vay lam kiem_cue chan ca buoc ASR.
    return cues if all(c.bat_dau < c.ket_thuc for c in cues) else [cue]


def nhan_dang(wav: Path, ra: Path, lang: str = 'en', model: str = 'large-v3',
             tao_model: Callable | None = None, vad: bool = True) -> None:
    """vad=True cắt khoảng lặng để Whisper khỏi bịa chữ, nhưng Silero VAD coi nhạc nền
    là không phải tiếng nói: với video ca nhạc nó vứt gần hết audio. Tắt bằng --vad off.
    """
    if tao_model is None:
        from faster_whisper import WhisperModel
        tao_model = WhisperModel

    def nhan(device: str) -> list[Cue]:
        recognizer = tao_model(model, device=device,
                              compute_type='int8_float16' if device == 'cuda' else 'int8')
        try:
            segments, _ = recognizer.transcribe(str(wav), language=lang, vad_filter=vad,
                vad_parameters={'min_silence_duration_ms':500}, word_timestamps=True)
            tat_ca = list(segments)
            tot = [s for s in tat_ca if s.text.strip() and s.end > s.start]
            if len(tot) < len(tat_ca):
                logging.warning('Bo %d segment rong hoac end<=start cua Whisper', len(tat_ca) - len(tot))
            return [c for s in tot for c in tach_cau(s)]
        finally:
            del recognizer

    try:
        cues = nhan('cuda')
    except (RuntimeError, OSError) as exc:
        if not loi_cuda(exc):
            raise
        # Release traceback references to the failed GPU generator before CPU loading.
        exc.__traceback__ = None
        gc.collect()
        logging.warning('CUDA không sẵn sàng; thử CPU/int8 một lần: %s', exc)
        try:
            cues = nhan('cpu')
        except (RuntimeError, OSError) as cpu_exc:
            raise cpu_exc from exc
    ghi_srt(gop_cau(cues), ra)
