"""Translate cue text with bounded content recovery; transport errors propagate."""
from __future__ import annotations

import json
import re
import warnings
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class PhanHoi:
    content: object
    finish_reason: str = "stop"
    token_vao: int = 0
    token_ra: int = 0


@dataclass(frozen=True)
class KetQua:
    ban: list[str]
    thuat_ngu_moi: dict[str, str]
    giu_nguon: list[int]
    token_vao: int
    token_ra: int


def _text(value: object) -> bool:
    return (isinstance(value, str) and bool(value.strip())
            and all(part.strip() for part in value.strip().splitlines())
            and "\x00" not in value)


def dich(lines: list[str], glossary: dict[str, str],
         goi: Callable[[dict[str, object]], PhanHoi], lo: int = 25) -> KetQua:
    """Return translated cues and zero-based source-retained indexes.

    Lo 25 cue; doi model thi do lai.
    """
    if type(lo) is not int or lo <= 0:
        raise ValueError("Kich thuoc lo phai la so nguyen duong")
    if not lines or not all(_text(s) for s in lines):
        raise ValueError("Phu de nguon rong hoac sai cau truc")
    if not isinstance(glossary, dict) or not all(_text(k) and _text(v) for k, v in glossary.items()):
        raise ValueError("Glossary phai chua chuoi khong rong")
    effective = dict(glossary)
    new: dict[str, str] = {}
    output = list(lines)
    retained: list[int] = []
    token_in = token_out = 0

    def request(indexes: list[int]) -> dict[int, str]:
        nonlocal token_in, token_out
        response = goi({"lines": {str(j + 1): lines[i] for j, i in enumerate(indexes)},
                        "context": lines[max(0, indexes[0] - 5):indexes[0]],
                        "glossary": dict(effective)})
        token_in += response.token_vao
        token_out += response.token_ra
        if response.finish_reason != "stop":
            warnings.warn("Phan hoi dich chua hoan tat: " + response.finish_reason, stacklevel=2)
            return {}
        data = response.content
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                return {}
        if not isinstance(data, dict) or not isinstance(data.get("lines"), dict):
            return {}
        expected = {str(j + 1): i for j, i in enumerate(indexes)}
        if data["lines"].keys() - expected.keys():
            warnings.warn("Bo qua khoa du trong ban dich", stacklevel=2)
        valid = {i: data["lines"][key].strip() for key, i in expected.items()
                 if _text(data["lines"].get(key))}
        terms = data.get("thuat_ngu_moi", {})
        if not isinstance(terms, dict) or not all(_text(k) and _text(v) for k, v in terms.items()):
            warnings.warn("Bo qua thuat_ngu_moi sai cau truc", stacklevel=2)
        elif valid:
            for key, value in terms.items():
                if key not in effective:
                    effective[key] = new[key] = value.strip()
        return valid

    def translate(indexes: list[int], depth: int = 0) -> None:
        valid = request(indexes)
        if not valid and len(indexes) > 1 and depth < 2:
            middle = len(indexes) // 2
            translate(indexes[:middle], depth + 1)
            translate(indexes[middle:], depth + 1)
            return
        for i in indexes:
            if i not in valid:
                valid.update(request([i]))
            if i in valid:
                output[i] = valid[i]
            else:
                retained.append(i)
                warnings.warn(f"Giu nguon cue {i + 1}: dich van khong hop le", stacklevel=2)

    for start in range(0, len(lines), lo):
        translate(list(range(start, min(start + lo, len(lines)))))
    return KetQua(output, new, retained, token_in, token_out)


MODEL_CUC_BO = "JustFrederik/nllb-200-distilled-600M-ct2-int8"     # ~600MB, tu tai lan dau


def _che(text: str, gloss: list[tuple[str, str]]) -> tuple[str, list[str]]:
    """Thay thuat ngu nguon (gloss da xep cum dai truoc) bang the Zq<i>x; tra cau va ban dich tung the."""
    dung: list[str] = []
    for k, v in gloss:
        text, n = re.subn(rf"(?<!\w){re.escape(k)}(?!\w)", f"Zq{len(dung)}x", text, flags=re.I)
        if n:
            dung.append(v)
    return " ".join(text.split()), dung      # CS-1: mot cue vao, mot cue ra, khong dong trong


def _tra(vi: str, dung: list[str]) -> str | None:
    """Tra the ve thuat ngu; None khi model lam mat hay bien dang the, de rac khong chay vao video."""
    for i, v in enumerate(dung):
        vi, n = re.subn(rf"zq{i}x", lambda _: v, vi, flags=re.I)
        if not n:
            return None
    return None if dung and re.search("zq", vi, re.I) else vi


def tao_goi_cuc_bo(repo: str = MODEL_CUC_BO) -> Callable[[dict[str, object]], PhanHoi]:
    """Dich bang NLLB chay tai may (CTranslate2): khong key, khong mang sau lan tai dau.

    Model dich may khong tu rut thuat ngu moi nen `thuat_ngu_moi` luon rong; glossary ep bang cach thay tu nguon bang the giu cho.
    Model nap muon o lan dich dau: job dung o man ve hop hay trung cache dich khong
    phai tai ~600MB, va NLLB khong chiem VRAM trong luc Whisper chay.
    """
    from pipeline.asr import loi_cuda

    tk = tr = thu_muc = None

    def dung(device: str):
        import ctranslate2
        return ctranslate2.Translator(thu_muc, device=device)

    def nap() -> None:
        nonlocal tk, tr, thu_muc
        from huggingface_hub import snapshot_download
        from tokenizers import Tokenizer
        try:
            thu_muc = snapshot_download(repo)
        except Exception as exc:
            raise RuntimeError(f"Khong tai duoc model dich {repo} (~600MB, chi tai lan dau); "
                               "kiem tra ket noi mang roi chay lai") from exc
        tk = Tokenizer.from_file(thu_muc + "/tokenizer.json")
        # GPU neu co (auto), loi CUDA luc nap hay luc dich thi lui ve CPU mot lan.
        try:
            tr = dung("auto")
        except (RuntimeError, OSError) as exc:
            if not loi_cuda(exc):
                raise
            tr = dung("cpu")

    def dich_lo(vao):
        nonlocal tr
        try:
            return tr.translate_batch(vao, target_prefix=[["vie_Latn"]] * len(vao), beam_size=4)
        except (RuntimeError, OSError) as exc:
            if not loi_cuda(exc):
                raise
            tr = dung("cpu")
            return tr.translate_batch(vao, target_prefix=[["vie_Latn"]] * len(vao), beam_size=4)

    def ma(cau: list[str]) -> list[list[str]]:
        return [["eng_Latn"] + tk.encode(s, add_special_tokens=False).tokens + ["</s>"] for s in cau]

    def giai(r) -> str:
        return tk.decode([tk.token_to_id(t) for t in r.hypotheses[0][1:]])

    def goi(payload: dict[str, object]) -> PhanHoi:
        if tr is None:
            nap()
        gloss = sorted(payload["glossary"].items(), key=lambda kv: -len(kv[0]))
        khoa, goc = list(payload["lines"]), list(payload["lines"].values())
        che = [_che(t, gloss) for t in goc]
        vao = ma([s for s, _ in che])
        ra = [_tra(giai(r), the) for r, (_, the) in zip(dich_lo(vao), che)]
        hong = [i for i, v in enumerate(ra) if v is None]
        so_token = sum(map(len, vao))
        if hong:
            # Model lam hong the: dich lai cau goc khong ep thuat ngu, thua mat thuat ngu con hon rac trong video.
            warnings.warn(f"Model lam hong the thuat ngu o {len(hong)} cau; dich lai khong ep thuat ngu", stacklevel=2)
            lai = ma([" ".join(goc[i].split()) for i in hong])
            for i, r in zip(hong, dich_lo(lai)):
                ra[i] = giai(r)
            so_token += sum(map(len, lai))
        return PhanHoi({"lines": dict(zip(khoa, ra)), "thuat_ngu_moi": {}}, "stop", so_token, 0)

    return goi

