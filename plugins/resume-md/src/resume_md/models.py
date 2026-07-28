from dataclasses import dataclass
from enum import Enum


class DocumentLanguage(str, Enum):
    AUTO = "auto"
    CHINESE = "zh-CN"
    ENGLISH = "en"


class TypographyStyle(str, Enum):
    AUTO = "auto"
    SANS = "sans"
    SERIF = "serif"
    HYBRID = "hybrid"


@dataclass(frozen=True)
class RenderOptions:
    language: DocumentLanguage = DocumentLanguage.AUTO
    style: TypographyStyle = TypographyStyle.AUTO
    body_font_pt: float = 10.5

    def validate(self) -> None:
        if not 8.5 <= self.body_font_pt <= 14:
            raise ValueError("正文字号必须在 8.5pt 到 14pt 之间。")


@dataclass(frozen=True)
class RenderMetrics:
    pages: int
    body_font_pt: float
    density: float
    fill_ratio: float
    section_top_pt: float


@dataclass(frozen=True)
class QualityReport:
    pages: int
    extracted_characters: int
    cjk_compatibility_characters: int
    links: int


@dataclass(frozen=True)
class RenderResult:
    pdf: bytes
    metrics: RenderMetrics
    quality: QualityReport
    language: DocumentLanguage
    style: TypographyStyle
    font_label: str
