"""Kiem tra tool tai lieu: python tests_docx.py (can python-docx)."""
import subprocess
import sys
import tempfile
from pathlib import Path

from docx import Document


def test_docx_cli_preserves_sources():
    script = Path(__file__).with_name("tools_md2docx.py").resolve()
    original = script.read_bytes()
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "source.md"
        source.write_text("# Tieu de\nNoi dung", encoding="utf-8")
        before = source.read_bytes()
        alias = root / "alias.docx"
        alias.hardlink_to(source)
        for args in ([], [str(source)], [str(source), str(source)],
                     [str(source), str(alias)]):
            result = subprocess.run([sys.executable, str(script), *args],
                                    cwd=root, capture_output=True)
            assert result.returncode == 2, result.stderr
            assert source.read_bytes() == before
            assert script.read_bytes() == original
        output = root / "out.docx"
        subprocess.run([sys.executable, str(script), str(source), str(output)],
                       cwd=root, check=True, capture_output=True)
        assert [p.text for p in Document(output).paragraphs] == ["Tieu de", "Noi dung"]
        assert source.read_bytes() == before
    # Import must not process sys.argv or write any output.
    import tools_md2docx
    assert callable(tools_md2docx.main)


if __name__ == "__main__":
    test_docx_cli_preserves_sources()
    print("PASS docx CLI preserves sources")
