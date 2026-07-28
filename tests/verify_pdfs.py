#!/usr/bin/env python3
"""Verify rendered example PDFs as release artifacts."""

from io import BytesIO
from pathlib import Path
import sys

from pypdf import PdfReader


def verify(path: Path) -> None:
    data = path.read_bytes()
    reader = PdfReader(BytesIO(data))
    if not reader.pages:
        raise ValueError(f"{path}: no pages")
    if "/StructTreeRoot" not in reader.trailer["/Root"]:
        raise ValueError(f"{path}: not tagged as PDF/UA")

    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    if len(text.strip()) < 100:
        raise ValueError(f"{path}: extracted text is unexpectedly short")
    if any(
        "\u2e80" <= character <= "\u2fdf"
        or "\uf900" <= character <= "\ufaff"
        for character in text
    ):
        raise ValueError(f"{path}: contains CJK compatibility characters")

    embedded = 0
    for page in reader.pages:
        fonts = page["/Resources"]["/Font"].get_object()
        for font_ref in fonts.values():
            for descendant_ref in font_ref.get_object().get("/DescendantFonts", ()):
                descriptor = descendant_ref.get_object()["/FontDescriptor"].get_object()
                if descriptor.get("/FontFile2") or descriptor.get("/FontFile3"):
                    embedded += 1
    if embedded == 0:
        raise ValueError(f"{path}: no embedded fonts")

    print(f"{path.name}: {len(reader.pages)} page(s), {len(text)} chars, fonts embedded")


def main() -> int:
    directory = Path(sys.argv[1] if len(sys.argv) > 1 else "test/output")
    paths = sorted(directory.glob("*.pdf"))
    if len(paths) != 6:
        raise ValueError(f"expected 6 PDFs in {directory}, found {len(paths)}")
    for path in paths:
        verify(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

