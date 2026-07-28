from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

from resume_md import (
    DocumentLanguage,
    RenderOptions,
    TypographyStyle,
    detect_language,
    render_pdf,
)
from resume_md.parser import markdown_to_resume_html


ROOT = Path(__file__).parents[1]
CHINESE = ROOT / "examples" / "zh-product-designer.md"
ENGLISH = ROOT / "examples" / "en-product-manager.md"


def test_language_detection():
    assert detect_language(CHINESE.read_text(encoding="utf-8")) == DocumentLanguage.CHINESE
    assert detect_language(ENGLISH.read_text(encoding="utf-8")) == DocumentLanguage.ENGLISH


def test_render_chinese_pdf_ua_with_embedded_fonts():
    result = render_pdf(CHINESE.read_text(encoding="utf-8"))
    reader = PdfReader(BytesIO(result.pdf))
    embedded = []

    for page in reader.pages:
        fonts = page["/Resources"]["/Font"].get_object()
        for font_ref in fonts.values():
            font = font_ref.get_object()
            for descendant_ref in font.get("/DescendantFonts", ()):
                descriptor = descendant_ref.get_object()["/FontDescriptor"].get_object()
                embedded.append(
                    bool(descriptor.get("/FontFile2") or descriptor.get("/FontFile3"))
                )

    assert result.pdf.startswith(b"%PDF")
    assert result.language == DocumentLanguage.CHINESE
    assert result.metrics.pages >= 1
    assert result.quality.extracted_characters > 500
    assert result.quality.cjk_compatibility_characters == 0
    assert embedded and all(embedded)
    assert "/StructTreeRoot" in reader.trailer["/Root"]
    assert reader.trailer["/Root"]["/Lang"] == "zh-CN"


def test_apple_cff_fonts_are_normalized():
    result = render_pdf(
        CHINESE.read_text(encoding="utf-8"),
        RenderOptions(style=TypographyStyle.SERIF),
    )
    reader = PdfReader(BytesIO(result.pdf))
    stream_subtypes = []

    for page in reader.pages:
        fonts = page["/Resources"]["/Font"].get_object()
        for font_ref in fonts.values():
            for descendant_ref in font_ref.get_object().get("/DescendantFonts", ()):
                descendant = descendant_ref.get_object()
                descriptor = descendant["/FontDescriptor"].get_object()
                stream = descriptor.get("/FontFile3")
                if stream is not None:
                    stream_subtypes.append(stream.get_object().get("/Subtype"))

    assert "/OpenType" not in stream_subtypes
    assert reader.pdf_header == "%PDF-1.7"


def test_render_english_and_style_resolution():
    result = render_pdf(
        ENGLISH.read_text(encoding="utf-8"),
        RenderOptions(style=TypographyStyle.HYBRID),
    )
    reader = PdfReader(BytesIO(result.pdf))

    assert result.language == DocumentLanguage.ENGLISH
    assert result.style == TypographyStyle.HYBRID
    assert result.quality.extracted_characters > 900
    assert reader.trailer["/Root"]["/Lang"] == "en"


def test_common_section_names_receive_semantic_classes():
    html = markdown_to_resume_html(
        """# Example

**Designer**

example@example.com

## 个人简介

简介。

## Professional Experience

### Example Company | Designer

January 2022 - Present

- Built a product.
"""
    )

    assert "summary-section" in html
    assert "experience-section" in html
    assert "entry-meta" in html


def test_long_resume_flows_without_shrinking():
    entries = "\n\n".join(
        f"""### 示例公司 {index}｜产品设计师

上海｜2023.01 - 2025.01

- 负责复杂产品从用户研究到最终交付，持续验证信息结构与视觉表达。
- 与产品和工程团队协作，确保设计质量在不同终端保持一致。"""
        for index in range(18)
    )
    result = render_pdf(
        f"# 示例用户\n\n**产品设计师**\n\n## 工作经历\n\n{entries}"
    )

    assert result.metrics.pages >= 2
    assert result.metrics.body_font_pt == 10.5
    assert result.quality.pages == result.metrics.pages


def test_dangerous_links_and_images_are_removed():
    html = markdown_to_resume_html(
        """# Example

[safe](https://example.com)
[mail](mailto:hello@example.com)
[bad](javascript:alert(1))
[local](file:///etc/passwd)
![portrait](https://example.com/portrait.png)
"""
    )

    assert 'href="https://example.com"' in html
    assert 'href="mailto:hello@example.com"' in html
    assert 'href="javascript:' not in html
    assert 'href="file:' not in html
    assert "<img" not in html
    assert "portrait" in html


def test_render_options_reject_extreme_font_sizes():
    try:
        render_pdf("# Example", RenderOptions(body_font_pt=20))
    except ValueError as exc:
        assert "8.5pt" in str(exc)
    else:
        raise AssertionError("Expected a font size validation error")
