"""V-11: HTTP/runtime boundary with real uvicorn, ffmpeg, SQLite and filesystem.

Only ASR and translation are deterministic seams.  Audio/render wrappers delegate
to the real modules and merely count calls.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
EVIDENCE = Path(os.environ.get(
    "LOGIC_RUNTIME_EVIDENCE",
    r"C:\Users\BINH\AppData\Local\Temp\logic-van-hanh-2026-09-16-luna-ultra\runtime",
))


def _port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _multipart(video: Path, fields: dict[str, str]) -> tuple[bytes, str]:
    boundary = "----luna-runtime-logic"
    body = bytearray()
    for key, value in fields.items():
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode())
        body.extend(str(value).encode())
        body.extend(b"\r\n")
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(f'Content-Disposition: form-data; name="file"; filename="{video.name}"\r\n'.encode())
    body.extend(b"Content-Type: video/mp4\r\n\r\n")
    body.extend(video.read_bytes())
    body.extend(f"\r\n--{boundary}--\r\n".encode())
    return bytes(body), f"multipart/form-data; boundary={boundary}"


def _request(url: str, method: str = "GET", body: bytes | None = None,
             content_type: str | None = None, timeout: float = 15) -> tuple[int, object, bytes]:
    headers = {}
    if content_type:
        headers["Content-Type"] = content_type
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            value = json.loads(raw) if raw and response.headers.get_content_type() == "application/json" else raw
            return response.status, value, raw
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        try:
            value = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            value = raw.decode(errors="replace")
        return exc.code, value, raw


def _get(base: str, path: str) -> tuple[int, object, bytes]:
    return _request(base + path)


def _post_json(base: str, path: str, value: dict) -> tuple[int, object, bytes]:
    return _request(base + path, "POST", json.dumps(value).encode(), "application/json")


def _upload(base: str, video: Path, **fields: str) -> tuple[int, object, bytes]:
    body, content_type = _multipart(video, {key: str(value) for key, value in fields.items()})
    return _request(base + "/api/video", "POST", body, content_type, timeout=30)


def _poll(base: str, cid: str, evidence: list[dict], deadline: float = 40,
          stop: set[str] | None = None) -> dict:
    stop = stop or {"xong", "suy_giam", "loi"}
    end = time.monotonic() + deadline
    while time.monotonic() < end:
        status, value, raw = _get(base, f"/api/cong-viec/{cid}")
        assert status == 200, (status, value, raw[:500])
        assert isinstance(value, dict)
        entry = {"cid": cid, "trang_thai": value.get("trang_thai"),
                 "buoc": value.get("buoc"), "tien_do": value.get("tien_do")}
        if not evidence or evidence[-1] != entry:
            evidence.append(entry)
        if value.get("trang_thai") in stop:
            return value
        time.sleep(0.1)
    raise AssertionError(f"timeout polling {cid}: {evidence[-5:]}")


def _wait_file(path: Path, deadline: float = 20) -> None:
    end = time.monotonic() + deadline
    while time.monotonic() < end:
        if path.is_file():
            return
        time.sleep(0.05)
    raise AssertionError(f"timeout waiting for {path}")


def _sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _fixture(root: Path) -> Path:
    sys.path.insert(0, str(ROOT))
    from tests_smoke import _video_gia

    video = root / "fixture.mp4"
    _video_gia(video, 640, 360, 4)
    return video


def _sitecustomize(shim: Path, counters: Path, hold: Path,
                   started: Path, release: Path) -> None:
    # This module is generated outside the repository and loaded only by the
    # uvicorn child through PYTHONPATH; production code has no test switch.
    code = f'''\
import importlib
import json
from pathlib import Path
import time
from types import SimpleNamespace

from pipeline.srt import Cue, ghi_srt
from pipeline.translate import KetQua, PhanHoi
from pipeline import dieu_phoi

COUNTERS = Path({str(counters)!r})
HOLD = Path({str(hold)!r})
STARTED = Path({str(started)!r})
RELEASE = Path({str(release)!r})

def tick(name):
    data = json.loads(COUNTERS.read_text(encoding="utf-8"))
    data[name] = int(data.get(name, 0)) + 1
    COUNTERS.write_text(json.dumps(data, sort_keys=True), encoding="utf-8")

def audio_tach(video, ra, separate=False):
    tick("audio")
    return REAL_AUDIO.tach(video, ra, separate)

def fake_asr(wav, ra, lang="en", model="large-v3", tao_model=None, vad=True):
    tick("asr")
    ghi_srt([Cue(1, 0.5, 1.2, "first cue"), Cue(2, 2.0, 2.7, "second cue")], Path(ra))

def fake_translate(lines, glossary, goi, lo=400):
    tick("dich")
    if HOLD.is_file():
        STARTED.write_text("1", encoding="utf-8")
        end = time.monotonic() + 30
        while not RELEASE.is_file() and time.monotonic() < end:
            time.sleep(0.02)
        if not RELEASE.is_file():
            raise RuntimeError("runtime test release timeout")
    return KetQua(["VI " + text for text in lines], {{}}, [], 0, 0)

def fake_provider(payload):
    lines = payload.get("lines", {{}})
    return PhanHoi({{"lines": {{key: "VI " + value for key, value in lines.items()}},
                   "thuat_ngu_moi": {{}}}})

REAL_AUDIO = importlib.import_module("pipeline.audio")
REAL_RENDER = importlib.import_module("pipeline.render")
REAL_ASR = SimpleNamespace(nhan_dang=fake_asr)
REAL_TRANSLATE = SimpleNamespace(dich=fake_translate)

def render_ket_xuat(*args, **kwargs):
    tick("render")
    return REAL_RENDER.ket_xuat(*args, **kwargs)

def render_module():
    return SimpleNamespace(ket_xuat=render_ket_xuat,
                           khoang_mo=REAL_RENDER.khoang_mo,
                           gop_khoang=REAL_RENDER.gop_khoang)

def nap(name):
    if name == "audio":
        return SimpleNamespace(tach=audio_tach)
    if name == "asr":
        return REAL_ASR
    if name == "translate":
        return REAL_TRANSLATE
    if name == "render":
        return render_module()
    return importlib.import_module("pipeline." + name)

dieu_phoi._nap = nap
import api.viec as viec
viec.tao_goi = lambda tc: fake_provider
'''
    shim.mkdir(parents=True, exist_ok=True)
    (shim / "sitecustomize.py").write_text(code, encoding="utf-8")


def _start(root: Path, shim: Path, port: int) -> subprocess.Popen:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join((str(shim), str(ROOT)))
    environment["PYTHONUNBUFFERED"] = "1"
    return subprocess.Popen(
        [str(PYTHON), "-m", "uvicorn", "api.app:app", "--host", "127.0.0.1",
         "--port", str(port), "--workers", "1", "--no-access-log"],
        cwd=root, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True,
    )


def _stop(process: subprocess.Popen | None, log: Path, force: bool = False) -> None:
    if process is None:
        return
    if process.poll() is None:
        (process.kill if force else process.terminate)()
    try:
        stdout, stderr = process.communicate(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate(timeout=10)
    log.write_text(f"PID={process.pid} exit={process.returncode}\n"
                   f"--- stdout ---\n{stdout}\n--- stderr ---\n{stderr}", encoding="utf-8")


def _ready(base: str, process: subprocess.Popen) -> None:
    end = time.monotonic() + 25
    while time.monotonic() < end:
        if process.poll() is not None:
            raise AssertionError(f"uvicorn exited {process.returncode}")
        try:
            status, value, _ = _get(base, "/api/nhom")
            if status == 200:
                return
        except (OSError, urllib.error.URLError):
            pass
        time.sleep(0.1)
    raise AssertionError("uvicorn health-check timeout")


def _cid(response: tuple[int, object, bytes]) -> str:
    status, value, raw = response
    assert status == 202 and isinstance(value, dict), (status, value, raw[:500])
    return str(value["id"])


def _canonical(root: Path, video: Path, group: str) -> tuple[Path, Path]:
    from pipeline.srt import chu_ky

    digest = _sha(video)
    source = (root / "work" / "tai_len" / "nguon" /
              chu_ky(["nhom", group])[:16] / digest / "nguon.media")
    work = root / "work" / f"{source.stem}-{chu_ky(str(source.resolve()))[:8]}"
    return source, work


def runtime() -> None:
    if not PYTHON.is_file():
        raise AssertionError(f"NOT RUN: missing interpreter {PYTHON}")
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    results: dict[str, object] = {"status": "RUNNING", "python": str(PYTHON),
                                  "repo": str(ROOT), "poll": []}
    process: subprocess.Popen | None = None
    port = _port()
    with tempfile.TemporaryDirectory(prefix="logic-runtime-") as temporary:
        root = Path(temporary)
        shim = root / "shim"
        counters = root / "counters.json"
        hold = root / "hold"
        started = root / "started"
        release = root / "release"
        counters.write_text(json.dumps({"audio": 0, "asr": 0, "dich": 0, "render": 0}),
                            encoding="utf-8")
        video = _fixture(root)
        _sitecustomize(shim, counters, hold, started, release)
        base = f"http://127.0.0.1:{port}"
        log_number = 0

        def stop_current(force=False):
            nonlocal process, log_number
            if process is not None:
                _stop(process, EVIDENCE / f"uvicorn-{log_number}-{process.pid}.log", force)
                process = None
                log_number += 1

        try:
            process = _start(root, shim, port)
            _ready(base, process)

            # Initial ASR -> frames -> replacement continuation -> real output.
            first = _cid(_upload(base, video, blur="on", force_asr="true", nhom="main"))
            initial = _poll(base, first, results["poll"], stop={"cho_chon_khung"})
            assert initial["trang_thai"] == "cho_chon_khung", initial
            status, frames, raw = _get(base, f"/api/cong-viec/{first}/khung")
            assert status == 200 and isinstance(frames, list) and len(frames) == 2, (status, frames, raw[:500])
            status, image, raw = _get(base, f"/api/cong-viec/{first}/khung/1")
            assert status == 200 and raw.startswith(b"\x89PNG"), (status, raw[:20])
            snapshot = root / "work" / "tai_len" / first / "khung" / "sub_goc.srt"
            assert snapshot.is_file()
            before = json.loads(counters.read_text(encoding="utf-8"))
            assert (before["audio"], before["asr"], before["dich"]) == (1, 1, 0), before
            box = {"x": 0.3, "y": 0.75, "w": 0.4, "h": 0.15}
            posted = _post_json(base, f"/api/cong-viec/{first}/hop", {
                "co_blur": True, "che_do_vung": "thay_the",
                "vung": [{**box, "cue": None},
                         {"x": 0.3, "y": 0.05, "w": 0.4, "h": 0.15, "cue": [1]}],
            })
            assert posted[0] == 200 and posted[1]["che_do_vung"] == "thay_the", posted
            finished = _poll(base, first, results["poll"])
            assert finished["trang_thai"] in {"xong", "suy_giam"}, finished
            status, output, raw = _get(base, f"/api/cong-viec/{first}/ket-qua")
            assert status == 200 and len(raw) > 1000, (status, len(raw))
            output_hash = hashlib.sha256(raw).hexdigest()
            downloaded = root / "first-download.mp4"
            downloaded.write_bytes(raw)
            probe = json.loads(subprocess.run(
                ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json",
                 str(downloaded)], capture_output=True, check=True, text=True).stdout)
            streams = probe["streams"]
            video_stream = next(s for s in streams if s["codec_type"] == "video")
            assert (video_stream["width"], video_stream["height"]) == (640, 360)
            assert any(s["codec_type"] == "audio" for s in streams)
            after_first = json.loads(counters.read_text(encoding="utf-8"))
            assert (after_first["audio"], after_first["asr"], after_first["dich"]) == (1, 1, 1), after_first

            # Same byte/group, different filename: shared cache, independent CID/output.
            renamed = root / "renamed.mkv"
            shutil.copyfile(video, renamed)
            second = _cid(_upload(base, renamed, blur="off", nhom="main"))
            second_done = _poll(base, second, results["poll"])
            assert second_done["trang_thai"] in {"xong", "suy_giam"}, second_done
            after_same = json.loads(counters.read_text(encoding="utf-8"))
            assert (after_same["audio"], after_same["asr"], after_same["dich"]) == \
                   (after_first["audio"], after_first["asr"], after_first["dich"]), after_same
            status, second_raw, _ = _get(base, f"/api/cong-viec/{second}/ket-qua")
            assert status == 200 and len(second_raw) > 1000
            status, first_again, _ = _get(base, f"/api/cong-viec/{first}/ket-qua")
            assert status == 200 and hashlib.sha256(first_again).hexdigest() == output_hash

            # Different group cannot reuse the main work/cache.
            other = _cid(_upload(base, video, blur="off", nhom="other"))
            other_done = _poll(base, other, results["poll"])
            assert other_done["trang_thai"] in {"xong", "suy_giam"}, other_done
            after_other = json.loads(counters.read_text(encoding="utf-8"))
            assert (after_other["audio"], after_other["asr"], after_other["dich"]) == \
                   (after_first["audio"] + 1, after_first["asr"] + 1, after_first["dich"] + 1), after_other

            # Real upload admission race: first writer is held in fake translation.
            hold.write_text("1", encoding="utf-8")
            import sqlite3
            with closing(sqlite3.connect(root / "work" / "subtitles.db")) as con:
                jobs_before_race = con.execute("SELECT COUNT(*) FROM cong_viec").fetchone()[0]
            with ThreadPoolExecutor(max_workers=1) as pool:
                first_race = pool.submit(_upload, base, video, blur="off", nhom="race")
                _wait_file(started)
                second_race = _upload(base, video, blur="off", nhom="race")
                assert second_race[0] == 409, second_race
                release.write_text("1", encoding="utf-8")
            race_response = first_race.result(timeout=30)
            race_cid = _cid(race_response)
            assert _poll(base, race_cid, results["poll"])["trang_thai"] in {"xong", "suy_giam"}
            with closing(sqlite3.connect(root / "work" / "subtitles.db")) as con:
                jobs_after_race = con.execute("SELECT COUNT(*) FROM cong_viec").fetchone()[0]
            assert jobs_after_race == jobs_before_race + 1, (jobs_before_race, jobs_after_race)
            hold.unlink(missing_ok=True)
            started.unlink(missing_ok=True)
            release.unlink(missing_ok=True)

            # POST race: status becomes dang_chay under the first continuation claim.
            post_race = _cid(_upload(base, video, blur="on", nhom="post-race"))
            assert _poll(base, post_race, results["poll"], stop={"cho_chon_khung"})["trang_thai"] == "cho_chon_khung"
            hold.write_text("1", encoding="utf-8")
            with ThreadPoolExecutor(max_workers=1) as pool:
                first_post = pool.submit(_post_json, base, f"/api/cong-viec/{post_race}/hop", {
                    "x": 0.3, "y": 0.75, "w": 0.4, "h": 0.15, "che_do_vung": "thay_the"})
                _wait_file(started)
                second_post = _post_json(base, f"/api/cong-viec/{post_race}/hop", {
                    "x": 0.3, "y": 0.75, "w": 0.4, "h": 0.15, "che_do_vung": "thay_the"})
                assert second_post[0] == 409, second_post
                release.write_text("1", encoding="utf-8")
                assert first_post.result(timeout=30)[0] == 200
            assert _poll(base, post_race, results["poll"])["trang_thai"] in {"xong", "suy_giam"}
            hold.unlink(missing_ok=True)
            started.unlink(missing_ok=True)
            release.unlink(missing_ok=True)

            # Snapshot stale is rejected before continuation; old snapshot remains readable.
            stale = _cid(_upload(base, video, blur="on", nhom="stale"))
            assert _poll(base, stale, results["poll"], stop={"cho_chon_khung"})["trang_thai"] == "cho_chon_khung"
            stale_source, stale_work = _canonical(root, video, "stale")
            stale_sub = stale_work / "sub_goc.srt"
            stale_snapshot = root / "work" / "tai_len" / stale / "khung" / "sub_goc.srt"
            snapshot_hash = _sha(stale_snapshot)
            from pipeline.srt import Cue, ghi_srt
            ghi_srt([Cue(1, 0.5, 1.2, "changed"), Cue(2, 2.0, 2.7, "second"),
                     Cue(3, 3.0, 3.4, "third")], stale_sub)
            stale_post = _post_json(base, f"/api/cong-viec/{stale}/hop", {
                "x": 0.3, "y": 0.75, "w": 0.4, "h": 0.15,
                "che_do_vung": "thay_the"})
            assert stale_post[0] == 409, stale_post
            assert _sha(stale_snapshot) == snapshot_hash

            # Normal restart while waiting: no active lock, orphan becomes loi.
            restart_cid = _cid(_upload(base, video, blur="on", nhom="restart"))
            assert _poll(base, restart_cid, results["poll"], stop={"cho_chon_khung"})["trang_thai"] == "cho_chon_khung"
            restart_source, restart_work = _canonical(root, video, "restart")
            assert not (restart_work / ".lock").exists()
            stop_current()
            process = _start(root, shim, port)
            _ready(base, process)
            status, restart_state, _ = _get(base, f"/api/cong-viec/{restart_cid}")
            assert status == 200 and restart_state["trang_thai"] == "loi", restart_state
            assert _post_json(base, f"/api/cong-viec/{restart_cid}/hop", {"co_blur": False})[0] == 409
            assert _get(base, f"/api/cong-viec/not-an-id")[0] == 404
            status, retained, retained_raw = _get(base, f"/api/cong-viec/{first}/ket-qua")
            assert status == 200 and hashlib.sha256(retained_raw).hexdigest() == output_hash

            # Separate crash case: kill the exact child while it owns a lock.
            crash_source, crash_work = _canonical(root, video, "crash")
            hold.write_text("1", encoding="utf-8")
            started.unlink(missing_ok=True)
            release.unlink(missing_ok=True)
            crash = _cid(_upload(base, video, blur="off", nhom="crash"))
            # The upload has already scheduled work; wait until the real claim reaches provider hold.
            _wait_file(started)
            stop_current(force=True)
            assert (crash_work / ".lock").is_file(), crash_work
            hold.unlink(missing_ok=True)
            process = _start(root, shim, port)
            _ready(base, process)
            status, crash_state, _ = _get(base, f"/api/cong-viec/{crash}")
            assert status == 200 and crash_state["trang_thai"] == "loi", crash_state
            assert _upload(base, video, blur="off", nhom="crash")[0] == 409

            # Cache remains reusable after restart; lock from crash remains untouched.
            before_final = json.loads(counters.read_text(encoding="utf-8"))
            after_restart = _cid(_upload(base, video, blur="off", nhom="main"))
            assert _poll(base, after_restart, results["poll"])["trang_thai"] in {"xong", "suy_giam"}
            counters_final = json.loads(counters.read_text(encoding="utf-8"))
            assert (counters_final["audio"], counters_final["asr"], counters_final["dich"]) == \
                   (before_final["audio"], before_final["asr"], before_final["dich"]), counters_final
            results.update({"status": "PASS", "first": first, "second": second,
                            "other": other, "race": race_cid, "post_race": post_race,
                            "stale": stale, "restart": restart_cid, "crash": crash,
                            "output_sha256": output_hash, "counters": counters_final,
                            "temp_root_cleaned": True})
        except BaseException as exc:
            results.update({"status": "FAIL", "error": f"{type(exc).__name__}: {exc}",
                            "counters": json.loads(counters.read_text(encoding="utf-8"))})
            raise
        finally:
            hold.unlink(missing_ok=True)
            release.unlink(missing_ok=True)
            stop_current(force=False)
            results["temp_root_cleaned"] = not root.exists()
            (EVIDENCE / "runtime-results.json").write_text(
                json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    assert results["status"] == "PASS", results
    results["temp_root_cleaned"] = not root.exists()
    (EVIDENCE / "runtime-results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    runtime()
