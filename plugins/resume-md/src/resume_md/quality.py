from io import BytesIO
from typing import Optional

from pypdf import PdfReader

from .models import QualityReport


def verify_pdf(pdf: bytes, expected_pages: Optional[int] = None) -> QualityReport:
    reader = PdfReader(BytesIO(pdf))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    compatibility = [
        character
        for character in text
        if "\u2e80" <= character <= "\u2fdf"
        or "\uf900" <= character <= "\ufaff"
    ]
    links = sum(len(page.get("/Annots") or []) for page in reader.pages)

    report = QualityReport(
        pages=len(reader.pages),
        extracted_characters=len(text),
        cjk_compatibility_characters=len(compatibility),
        links=links,
    )
    if expected_pages is not None and report.pages != expected_pages:
        raise ValueError(f"PDF 页数异常：预期 {expected_pages}，实际 {report.pages}。")
    if report.cjk_compatibility_characters:
        raise ValueError("PDF 中文文本包含 CJK 部首或兼容字符，可能影响 ATS。")
    if report.extracted_characters == 0:
        raise ValueError("PDF 无法提取文本。")
    return report
