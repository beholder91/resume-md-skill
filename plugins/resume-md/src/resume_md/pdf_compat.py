from io import BytesIO

from fontTools.ttLib import TTFont
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject


def make_pdfkit_compatible(pdf: bytes) -> bytes:
    """Normalize embedded CFF fonts for Apple's PDFKit renderer.

    WeasyPrint embeds subsetted CFF fonts in an OpenType wrapper. PDFKit can
    resolve the text mapping incorrectly for fonts such as PingFang SC, even
    though other PDF renderers display the same file correctly. A CIDFontType0
    may embed the raw CFF program directly, which PDFKit handles reliably.
    """

    reader = PdfReader(BytesIO(pdf))
    converted_fonts = 0
    seen_fonts: set[int] = set()

    for page in reader.pages:
        resources = page.get("/Resources")
        if resources is None:
            continue
        fonts_ref = resources.get_object().get("/Font")
        if fonts_ref is None:
            continue

        for font_ref in fonts_ref.get_object().values():
            font_id = getattr(font_ref, "idnum", id(font_ref))
            if font_id in seen_fonts:
                continue
            seen_fonts.add(font_id)

            font = font_ref.get_object()
            if font.get("/Subtype") != "/Type0":
                continue

            for descendant_ref in font.get("/DescendantFonts", ()):
                descendant = descendant_ref.get_object()
                if descendant.get("/Subtype") != "/CIDFontType0":
                    continue

                descriptor_ref = descendant.get("/FontDescriptor")
                if descriptor_ref is None:
                    continue
                font_stream_ref = descriptor_ref.get_object().get("/FontFile3")
                if font_stream_ref is None:
                    continue

                font_stream = font_stream_ref.get_object()
                if font_stream.get("/Subtype") != "/OpenType":
                    continue

                font_data = font_stream.get_data()
                if not font_data.startswith(b"OTTO"):
                    continue

                open_type_font = TTFont(BytesIO(font_data), lazy=False)
                try:
                    if "CFF " not in open_type_font:
                        continue
                    cff_data = open_type_font.getTableData("CFF ")
                finally:
                    open_type_font.close()

                font_stream.set_data(cff_data)
                font_stream[NameObject("/Subtype")] = NameObject("/CIDFontType0C")
                converted_fonts += 1

    if converted_fonts == 0:
        return pdf

    writer = PdfWriter(clone_from=reader)
    writer.pdf_header = reader.pdf_header
    output = BytesIO()
    writer.write(output)
    return output.getvalue()
