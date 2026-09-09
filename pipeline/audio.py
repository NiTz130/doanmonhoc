"""Extract mono PCM audio, optionally isolate vocals using Demucs."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

from pipeline.srt import file_tam


def kiem_wav(path: Path) -> None:
    with wave.open(str(path),'rb') as wav:
        if wav.getnchannels() != 1 or wav.getframerate() != 16000 or wav.getsampwidth() != 2 or wav.getnframes() == 0:
            raise ValueError('Audio phải là WAV PCM 16-bit, mono, 16 kHz và không rỗng')


def tach(video: Path, ra: Path, separate: bool = False) -> Path:
    ra = Path(ra)
    if separate and importlib.util.find_spec('demucs') is None:
        raise RuntimeError('Thiếu Demucs; cài extra demucs trước khi dùng --separate')
    with file_tam(ra) as tmp:
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(Path(video).resolve()),
            '-map','0:a:0','-vn','-ac','1','-ar','16000','-c:a','pcm_s16le',str(tmp)],
            check=True,capture_output=True,text=True)
        kiem_wav(tmp)
    if not separate:
        return ra
    vocals = ra.with_name('vocals.wav')
    with tempfile.TemporaryDirectory(dir=ra.parent) as directory:
        subprocess.run([sys.executable,'-m','demucs','--two-stems=vocals','-n','htdemucs',
            '-o',directory,str(ra.resolve())],check=True,capture_output=True,text=True)
        source = Path(directory)/'htdemucs'/ra.stem/'vocals.wav'
        if not source.is_file():
            raise RuntimeError('Demucs kết thúc nhưng không tạo vocals.wav')
        with file_tam(vocals) as tmp:
            subprocess.run(['ffmpeg','-v','error','-y','-i',str(source),'-ac','1','-ar',
                '16000','-c:a','pcm_s16le',str(tmp)],check=True,capture_output=True,text=True)
            kiem_wav(tmp)
    return vocals
