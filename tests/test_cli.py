import json
from pathlib import Path

from typer.testing import CliRunner

from resume_md.cli import app


ROOT = Path(__file__).parents[1]
RUNNER = CliRunner()


def test_render_command_outputs_json(tmp_path):
    output = tmp_path / "resume.pdf"
    result = RUNNER.invoke(
        app,
        [
            "render",
            str(ROOT / "examples" / "en-software-engineer.md"),
            "--output",
            str(output),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["language"] == "en"
    assert payload["pages"] >= 1
    assert output.read_bytes().startswith(b"%PDF")


def test_render_command_rejects_non_pdf_output(tmp_path):
    result = RUNNER.invoke(
        app,
        [
            "render",
            str(ROOT / "examples" / "en-software-engineer.md"),
            "--output",
            str(tmp_path / "resume.txt"),
        ],
    )

    assert result.exit_code != 0
    assert ".pdf" in result.output


def test_render_command_reports_invalid_utf8(tmp_path):
    source = tmp_path / "resume.md"
    source.write_bytes(b"\xff\xfe")
    result = RUNNER.invoke(app, ["render", str(source)])

    assert result.exit_code == 1
    assert "渲染失败" in result.output

