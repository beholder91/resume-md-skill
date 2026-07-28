#!/usr/bin/env python3
"""Install ResumeMD into an isolated user environment."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile


REPOSITORY_SOURCE = (
    "git+https://github.com/beholder91/resume-md.git@main"
    "#subdirectory=plugins/resume-md"
)


def run(command: list[str], *, env: dict[str, str] | None = None) -> None:
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        env=env,
    )
    if completed.returncode:
        details = (completed.stderr or completed.stdout).strip()
        raise RuntimeError(
            f"命令执行失败（{completed.returncode}）：{' '.join(command)}\n{details}"
        )


def default_source() -> str:
    plugin_root = Path(__file__).resolve().parents[3]
    if (plugin_root / "pyproject.toml").is_file():
        return str(plugin_root)
    return REPOSITORY_SOURCE


def dependency_hint() -> str:
    if platform.system() == "Darwin":
        return "brew install pango"
    if platform.system() == "Linux":
        return (
            "sudo apt-get update && sudo apt-get install -y "
            "libpango-1.0-0 libpangoft2-1.0-0"
        )
    return "ResumeMD 0.1.0 暂不支持原生 Windows；请在 WSL 中安装。"


def install(source: str, skip_smoke: bool = False) -> dict[str, object]:
    if sys.version_info < (3, 9):
        raise RuntimeError("ResumeMD 需要 Python 3.9 或更高版本。")
    if os.name == "nt":
        raise RuntimeError(
            "ResumeMD 0.1.0 暂不支持原生 Windows，请在 WSL 中运行。"
        )

    data_root = Path.home() / ".local" / "share" / "resume-md"
    venv = data_root / "venv"
    executable = venv / "bin" / "python"
    cli = venv / "bin" / "resume-md"
    bin_dir = Path.home() / ".local" / "bin"
    entrypoint = bin_dir / "resume-md"

    data_root.mkdir(parents=True, exist_ok=True)
    if not executable.exists():
        run([sys.executable, "-m", "venv", str(venv)])
    run([str(executable), "-m", "pip", "install", "--upgrade", "pip"])
    run([str(executable), "-m", "pip", "install", "--upgrade", source])

    bin_dir.mkdir(parents=True, exist_ok=True)
    if entrypoint.is_symlink():
        entrypoint.unlink()
    elif entrypoint.exists():
        raise RuntimeError(
            f"{entrypoint} 已存在且不是 ResumeMD 链接，请先确认后手动移除。"
        )
    entrypoint.symlink_to(cli)

    smoke: dict[str, object] = {"ok": False}
    if not skip_smoke:
        with tempfile.TemporaryDirectory(prefix="resume-md-smoke-") as directory:
            root = Path(directory)
            markdown = root / "smoke.md"
            output = root / "smoke.pdf"
            markdown.write_text(
                "# ResumeMD\n\n**Local renderer**\n\n"
                "## Status\n\n- Installation smoke test.\n",
                encoding="utf-8",
            )
            environment = os.environ.copy()
            if platform.system() == "Darwin":
                environment.setdefault(
                    "DYLD_FALLBACK_LIBRARY_PATH",
                    "/opt/homebrew/lib:/usr/local/lib",
                )
            try:
                completed = subprocess.run(
                    [
                        str(cli),
                        "render",
                        str(markdown),
                        "--output",
                        str(output),
                        "--json",
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                    env=environment,
                )
            except subprocess.CalledProcessError as exc:
                raise RuntimeError(
                    "安装完成，但真实 PDF 自检失败。\n"
                    f"请先运行：{dependency_hint()}\n"
                    f"{exc.stderr.strip()}"
                ) from exc
            if not output.read_bytes().startswith(b"%PDF"):
                raise RuntimeError("安装自检没有生成有效 PDF。")
            smoke = json.loads(completed.stdout)
            smoke["ok"] = True

    return {
        "ok": True,
        "command": str(entrypoint),
        "venv": str(venv),
        "source": source,
        "smoke": smoke,
        "path_hint": (
            None
            if shutil.which("resume-md")
            else '把 "$HOME/.local/bin" 加入 PATH，或直接使用上面的完整命令。'
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="在用户目录中安装 ResumeMD，并执行真实 PDF 自检。"
    )
    parser.add_argument("--source", default=default_source())
    parser.add_argument("--skip-smoke", action="store_true")
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    try:
        result = install(arguments.source, arguments.skip_smoke)
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"ResumeMD 安装失败：{exc}", file=sys.stderr)
        print(f"系统依赖修复建议：{dependency_hint()}", file=sys.stderr)
        return 1
    if arguments.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"ResumeMD 已安装：{result['command']}")
        if result["path_hint"]:
            print(result["path_hint"])
        print("真实 PDF 自检通过。" if result["smoke"]["ok"] else "已跳过 PDF 自检。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
