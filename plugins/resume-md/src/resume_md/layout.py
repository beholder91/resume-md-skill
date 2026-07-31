from dataclasses import dataclass
from importlib import resources
import os
import sys
from typing import Any

if sys.platform == "darwin":
    os.environ.setdefault("DYLD_FALLBACK_LIBRARY_PATH", "/opt/homebrew/lib")

from weasyprint import HTML

from .fonts import FontStack
from .models import DocumentLanguage, RenderMetrics, RenderOptions
from .parser import escaped_title


@dataclass(frozen=True)
class _LayoutValues:
    font: float
    leading: float
    section: float
    entry: float
    bullet: float
    header: float
    name: float
    h2: float
    h3: float


BASE_FONT = 10.5
NATURAL = {
    DocumentLanguage.CHINESE: _LayoutValues(
        10.5, 1.62, 16.5, 9.0, 3.2, 15.5, 29.0, 13.4, 11.4
    ),
    DocumentLanguage.ENGLISH: _LayoutValues(
        10.5, 1.48, 14.5, 8.0, 2.8, 14.5, 28.0, 13.2, 11.7
    ),
}


def _values(
    body_font_pt: float,
    language: DocumentLanguage,
) -> _LayoutValues:
    natural = NATURAL[language]
    scale = body_font_pt / BASE_FONT
    return _LayoutValues(
        font=body_font_pt,
        leading=natural.leading,
        section=natural.section * scale,
        entry=natural.entry * scale,
        bullet=natural.bullet * scale,
        header=natural.header * scale,
        name=natural.name * scale,
        h2=natural.h2 * scale,
        h3=natural.h3 * scale,
    )


def _style(values: _LayoutValues) -> str:
    variables = {
        "body-size": f"{values.font:.4f}pt",
        "body-leading": f"{values.leading:.4f}",
        "entry-gap": f"{values.entry:.4f}pt",
        "bullet-gap": f"{values.bullet:.4f}pt",
        "header-gap": f"{values.header:.4f}pt",
        "name-size": f"{values.name:.4f}pt",
        "section-title-size": f"{values.h2:.4f}pt",
        "entry-title-size": f"{values.h3:.4f}pt",
        "headline-size": f"{values.font - 0.35:.4f}pt",
        "small-size": f"{values.font - 1.05:.4f}pt",
        "meta-size": f"{values.font - 0.85:.4f}pt",
        "label-size": f"{values.font - 0.35:.4f}pt",
        "section-top": f"{values.section:.4f}pt",
        "section-heading-bottom": f"{values.entry * 0.78:.4f}pt",
        "entry-head-bottom": f"{values.entry * 0.48:.4f}pt",
        "label-top": f"{values.entry * 0.72:.4f}pt",
        "label-bottom": f"{values.bullet * 0.65:.4f}pt",
        "skill-gap": f"{values.bullet * 0.9:.4f}pt",
    }
    return "; ".join(f"--{key}: {value}" for key, value in variables.items())


def _build_html(
    markdown: str,
    content: str,
    fonts: FontStack,
    values: _LayoutValues,
    language: DocumentLanguage,
) -> str:
    theme_root = resources.files("resume_md").joinpath("themes", "natural")
    template = theme_root.joinpath("template.html").read_text(encoding="utf-8")
    css = theme_root.joinpath("print.css").read_text(encoding="utf-8")
    replacements = {
        "{{ROOT_STYLE}}": _style(values),
        "{{LANGUAGE}}": language.value,
        "{{TITLE}}": escaped_title(markdown),
        "{{FONT_BODY}}": fonts.body,
        "{{FONT_HEADING}}": fonts.heading,
        "{{FONT_FACE_CSS}}": fonts.css,
        "{{THEME_CSS}}": css,
        "{{CONTENT}}": content,
    }
    html = template
    for placeholder, replacement in replacements.items():
        html = html.replace(placeholder, replacement)
    return html


def _has_class(box: Any, class_name: str) -> bool:
    element = getattr(box, "element", None)
    return element is not None and class_name in (element.get("class") or "").split()


def _find_box(box: Any, class_name: str):
    if _has_class(box, class_name):
        return box
    for child in getattr(box, "children", ()):
        found = _find_box(child, class_name)
        if found is not None:
            return found
    return None


def _measure(document) -> tuple[int, float]:
    pages = len(document.pages)
    used_height = 0.0
    printable_height = 0.0

    for page in document.pages:
        root = page._page_box
        printable_height += root.height
        sheet = _find_box(root, "sheet")
        if sheet is not None:
            used_height += min(sheet.height, root.height)

    if printable_height <= 0:
        raise ValueError("PDF 页面结构异常。")
    return pages, used_height / printable_height


def render_document(
    markdown: str,
    content: str,
    fonts: FontStack,
    options: RenderOptions,
    language: DocumentLanguage,
):
    values = _values(options.body_font_pt, language)
    html = _build_html(markdown, content, fonts, values, language)
    document = HTML(string=html).render()
    pages, fill_ratio = _measure(document)
    metrics = RenderMetrics(
        pages=pages,
        body_font_pt=values.font,
        density=0.0,
        fill_ratio=fill_ratio,
        section_top_pt=values.section,
    )
    return document, metrics
