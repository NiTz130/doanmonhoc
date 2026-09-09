"""Prefer validated sidecars, then text subtitle streams."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from pipeline.srt import doc_srt, ghi_srt, file_tam

CODEC_CHU = {'subrip', 'ass', 'ssa', 'mov_text', 'webvtt', 'text'}
ALIASES = [('en','eng'), ('vi','vie'), ('fr','fra','fre'), ('de','deu','ger'),
           ('es','spa'), ('zh','zho','chi'), ('ja','jpn'), ('ko','kor'), ('ru','rus')]


def alias_lang(lang: str) -> tuple[str, ...]:
    lang = lang.lower()
    return next((a for a in ALIASES if lang in a), (lang,))


def tim_sidecar(video: Path, lang: str = 'en') -> Path | None:
    video = Path(video)
    for suffix in (*('.'+a+'.srt' for a in alias_lang(lang)), '.srt'):
        path = video.with_suffix(suffix)
        if path.is_file():
            return path
    return None


def probe_subs(video: Path) -> list[dict]:
    result = subprocess.run(['ffprobe','-v','error','-select_streams','s',
        '-show_entries','stream=index,codec_name:stream_tags=language','-of','json',
        str(Path(video).resolve())], check=True, capture_output=True, text=True)
    return json.loads(result.stdout)['streams']


def tim_phu_de(video: Path, ra: Path, lang: str = 'en') -> bool:
    sidecar = tim_sidecar(video, lang)
    if sidecar:
        ghi_srt(doc_srt(sidecar), ra)
        return True
    tracks = [(i,t) for i,t in enumerate(probe_subs(video)) if t.get('codec_name') in CODEC_CHU]
    if not tracks:
        return False
    index, _ = next(((i,t) for i,t in tracks
        if t.get('tags',{}).get('language','').lower() in alias_lang(lang)), tracks[0])
    with file_tam(Path(ra)) as tmp:
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(Path(video).resolve()),
            '-map',f'0:s:{index}','-c:s','srt',str(tmp)], check=True, capture_output=True, text=True)
        ghi_srt(doc_srt(tmp),tmp)
    return True
