import re
from typing import Optional

from .fonts import resolve_font_stack
from .layout import render_document
from .models import DocumentLanguage, RenderOptions, RenderResult
from .parser import markdown_to_resume_html
from .pdf_compat import make_pdfkit_compatible
from .quality import verify_pdf


def detect_language(markdown: str) -> DocumentLanguage:
    cjk = len(re.findall(r"[\u3400-\u9fff]", markdown))
    letters = len(re.findall(r"[A-Za-z]", markdown))
    return (
        DocumentLanguage.CHINESE
        if cjk >= 8 and cjk >= letters * 0.08
        else DocumentLanguage.ENGLISH
    )


def render_pdf(markdown: str, options: Optional[RenderOptions] = None) -> RenderResult:
    options = options or RenderOptions()
    options.validate()
    if not markdown.strip():
        raise ValueError("Markdown 内容不能为空。")

    language = (
        detect_language(markdown)
        if options.language == DocumentLanguage.AUTO
        else options.language
    )
    style, fonts = resolve_font_stack(options.style, language)
    content = markdown_to_resume_html(markdown)
    document, metrics = render_document(
        markdown,
        content,
        fonts,
        options,
        language,
    )
    pdf = document.write_pdf(pdf_variant="pdf/ua-1")
    pdf = make_pdfkit_compatible(pdf)
    quality = verify_pdf(pdf, metrics.pages)
    return RenderResult(
        pdf=pdf,
        metrics=metrics,
        quality=quality,
        language=language,
        style=style,
        font_label=fonts.label,
    )
