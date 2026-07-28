from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
import platform
from typing import Optional

import typer

from . import __version__
from .fonts import font_cache_dir, resolve_font_stack
from .models import DocumentLanguage, RenderOptions, TypographyStyle
from .renderer import render_pdf


app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="把中英文 Markdown 简历渲染为自然分页的 PDF。",
)


@app.command()
def render(
    input_path: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        dir_okay=False,
        help="UTF-8 Markdown 简历。",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="输出 PDF。",
    ),
    language: DocumentLanguage = typer.Option(
        DocumentLanguage.AUTO,
        "--language",
        case_sensitive=True,
        help="auto、zh-CN 或 en。",
    ),
    style: TypographyStyle = typer.Option(
        TypographyStyle.AUTO,
        "--style",
        help="auto、sans、serif 或 hybrid。",
    ),
    font_size: float = typer.Option(10.5, "--font-size"),
    json_output: bool = typer.Option(False, "--json", help="输出机器可读结果。"),
) -> None:
    destination = output or input_path.with_suffix(".pdf")
    if destination.suffix.lower() != ".pdf":
        raise typer.BadParameter("输出文件必须使用 .pdf 扩展名。", param_hint="--output")
    try:
        markdown = input_path.read_text(encoding="utf-8")
        result = render_pdf(
            markdown,
            RenderOptions(
                language=language,
                style=style,
                body_font_pt=font_size,
            ),
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(result.pdf)
    except (OSError, UnicodeError, RuntimeError, ValueError) as exc:
        typer.echo(f"渲染失败：{exc}", err=True)
        raise typer.Exit(code=1)

    payload = {
        "output": str(destination.resolve()),
        "pages": result.metrics.pages,
        "language": result.language.value,
        "style": result.style.value,
        "font": result.font_label,
        "font_size": result.metrics.body_font_pt,
        "extracted_characters": result.quality.extracted_characters,
    }
    if json_output:
        typer.echo(json.dumps(payload, ensure_ascii=False))
    else:
        typer.echo(
            f"已生成 {destination}｜{payload['pages']} 页｜"
            f"{payload['language']}｜{payload['font']}｜自然分页"
        )


@app.command()
def doctor(
    download_fonts: bool = typer.Option(
        False,
        "--download-fonts",
        help="立即准备 Linux/WSL 使用的开源字体。",
    ),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    checks: dict[str, object] = {
        "version": __version__,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "font_cache": str(font_cache_dir()),
        "pango": False,
        "render": False,
    }
    errors: list[str] = []
    try:
        importlib.import_module("weasyprint")
        checks["pango"] = True
    except Exception as exc:
        errors.append(f"WeasyPrint/Pango 不可用：{exc}")

    if checks["pango"]:
        previous = os.environ.get("RESUMEMD_FORCE_NOTO")
        try:
            if download_fonts:
                os.environ["RESUMEMD_FORCE_NOTO"] = "1"
                resolve_font_stack(
                    TypographyStyle.HYBRID,
                    DocumentLanguage.CHINESE,
                )
            result = render_pdf(
                "# ResumeMD\n\n**自检**\n\n## 状态\n\n- PDF 渲染正常。"
            )
            checks["render"] = result.pdf.startswith(b"%PDF")
            checks["font"] = result.font_label
        except Exception as exc:
            errors.append(f"真实渲染失败：{exc}")
        finally:
            if previous is None:
                os.environ.pop("RESUMEMD_FORCE_NOTO", None)
            else:
                os.environ["RESUMEMD_FORCE_NOTO"] = previous

    checks["ok"] = not errors and bool(checks["render"])
    checks["errors"] = errors
    if json_output:
        typer.echo(json.dumps(checks, ensure_ascii=False))
    else:
        typer.echo(f"ResumeMD {checks['version']}｜Python {checks['python']}")
        typer.echo(f"平台：{checks['platform']}")
        typer.echo(f"字体缓存：{checks['font_cache']}")
        typer.echo("状态：正常" if checks["ok"] else "状态：需要修复")
        for error in errors:
            typer.echo(f"- {error}", err=True)
    if not checks["ok"]:
        if platform.system() == "Darwin":
            typer.echo("macOS 可尝试：brew install pango", err=True)
        elif platform.system() == "Linux":
            typer.echo(
                "Ubuntu/WSL 可尝试：sudo apt-get install -y libpango-1.0-0 "
                "libpangoft2-1.0-0",
                err=True,
            )
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
