"""Whisper recognition with one narrowly scoped CPU fallback."""
from __future__ import annotations

import gc
import logging
from pathlib import Path
from collections.abc import Callable

from pipeline.srt import Cue, ghi_srt


def loi_cuda(exc: RuntimeError | OSError) -> bool:
    text = str(exc).lower()
    return any(x in text for x in ('cuda out of memory', 'cuda driver version is insufficient',
        'no cuda-capable device', 'cuda failed with error out of memory',
        'cudnn', 'cublas', 'cudart', 'nvcuda.dll', 'cuda driver library cannot be found'))


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
                vad_parameters={'min_silence_duration_ms':500})
            return [Cue(i+1,s.start,s.end,s.text.strip()) for i,s in enumerate(segments)]
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
    ghi_srt(cues, ra)
