# Repository Guidelines

## Project Structure & Module Organization

This app translates English video subtitles into Vietnamese and renders subtitled video.
- `pipeline/`: audio extraction, ASR, translation, blur regions, rendering, SQLite, and shared orchestration in `dieu_phoi.py`.
- `api/`: FastAPI routes; `main.py`: internal CLI using the same orchestrator. Keep media/model processing out of routes.
- `web/`: plain HTML/CSS/JavaScript, local fonts, and vendored Three.js; no frontend build step.
- `test_pipeline.py`, `tests_*.py`: Python checks; `test/frontend.cjs`: browser checks.
- `docs/`: design, team responsibilities, Git workflow, and recorded evidence. `work/` holds ignored runtime artifacts and the database.

## Build, Test, and Development Commands

Use Python 3.12, `uv`, and ffmpeg 6+ with subtitle/filter support. Run from the repository root:

- `uv sync`: install Python dependencies.
- `.venv/Scripts/python.exe -m uvicorn api.app:app --reload`: serve the app at `http://127.0.0.1:8000`.
- `.\start_system.bat`: Windows shortcut to start the backend and open the browser.
- `.venv/Scripts/python.exe test_pipeline.py`: run the 78 offline regression checks.
- `.venv/Scripts/python.exe tools_coverage.py --min 90`: measure line coverage of the offline suite (no extra dependency; currently 91.2%).
- `.venv/Scripts/python.exe test_pipeline.py --smoke`: run media smoke checks requiring ffmpeg; inspect generated images.
- `.venv/Scripts/python.exe test_pipeline.py --real`: run real GPU, Whisper, NLLB and ffmpeg checks (`tests_real.py`, about 1 minute). A missing GPU or cached model reports `NOT RUN`; it never downloads models.
- `npm ci` then `npx playwright install chromium`: prepare browser tests.
- `.venv/Scripts/python.exe -m http.server 8765 --bind 127.0.0.1 --directory web`: serve frontend fixtures; run `npm run test:frontend` in another terminal.

## Coding Style & Naming Conventions

Follow surrounding code: four-space Python indentation, type hints, and `snake_case`; JavaScript uses two-space indentation and semicolons. Preserve established Vietnamese identifiers and interface text. Match existing compact CSS formatting. No formatter or linter is configured. Reuse existing modules and avoid adding frameworks or dependencies unnecessarily.

## Testing Guidelines

Python uses plain assertions, fake callables, FastAPI `TestClient`, and in-memory SQLite. Name checks `test_*` and register/import them through `test_pipeline.py`. Browser tests use Playwright with mocked API responses. `tools_coverage.py` measures line coverage only for the offline suite; no CI enforces its threshold. Cover changed behavior and relevant failures; distinguish offline/browser evidence from real ASR and translation acceptance. `tests_real.py` is run only by `--real`, not imported into the default runner. `test/runtime_logic.py` (real uvicorn + ffmpeg + SQLite) is not part of the `test_pipeline.py` runner; run it separately with `PYTHONUTF8=1`.

## Commit & Pull Request Guidelines

History uses short, descriptive Vietnamese or English subjects without mandatory Conventional Commit prefixes. Follow `docs/GIT.md`; parallel contributors use `feat/*` branches. PRs target `main`: describe behavior, include validation results, link relevant tasks, and attach screenshots for UI changes. Enable hooks with `git config core.hooksPath .githooks`; do not bypass branch guards.

## Security & Configuration

Never commit secrets, media, models, or `work/`. Translation runs locally (NLLB); the app reads no API key or `.env`. The first translation downloads about 600 MB of model files, so ask before running it on a metered connection. Preserve cached artifacts and manually edited subtitles.
