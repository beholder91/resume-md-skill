from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import platform
import tempfile
from typing import Callable, Optional
from urllib.request import urlopen

from .models import DocumentLanguage, TypographyStyle


@dataclass(frozen=True)
class FontStack:
    label: str
    body: str
    heading: str
    css: str = ""


_NOTO_COMMIT = "f8d157532fbfaeda587e826d4cd5b21a49186f7c"
_FONT_FILES = {
    "sans": {
        "filename": "NotoSansSC-VF.ttf",
        "url": (
            "https://raw.githubusercontent.com/notofonts/noto-cjk/"
            f"{_NOTO_COMMIT}/Sans/Variable/TTF/Subset/NotoSansSC-VF.ttf"
        ),
        "sha256": "d68bafcb48a2707749396aa12bbbd833cb70401f3a9a689fd2902c7e0d295964",
        "family": "ResumeMD Noto Sans SC",
    },
    "serif": {
        "filename": "NotoSerifSC-VF.ttf",
        "url": (
            "https://raw.githubusercontent.com/notofonts/noto-cjk/"
            f"{_NOTO_COMMIT}/Serif/Variable/TTF/Subset/NotoSerifSC-VF.ttf"
        ),
        "sha256": "5326cfb097e3ab26fcb39329752b5c0a439bf8d5c4649520e4b492939c352a09",
        "family": "ResumeMD Noto Serif SC",
    },
}


def font_cache_dir() -> Path:
    configured = os.environ.get("RESUMEMD_FONT_CACHE")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".cache" / "resume-md" / "fonts"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download(url: str, destination: Path) -> None:
    with urlopen(url, timeout=90) as response, destination.open("wb") as handle:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            handle.write(chunk)


def ensure_font(
    kind: str,
    downloader: Optional[Callable[[str, Path], None]] = None,
) -> Path:
    metadata = _FONT_FILES[kind]
    cache = font_cache_dir()
    cache.mkdir(parents=True, exist_ok=True)
    target = cache / metadata["filename"]
    if target.exists() and _sha256(target) == metadata["sha256"]:
        return target
    if target.exists():
        target.unlink()

    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.",
        dir=str(cache),
    )
    os.close(file_descriptor)
    temporary = Path(temporary_name)
    try:
        (downloader or _download)(metadata["url"], temporary)
        actual = _sha256(temporary)
        if actual != metadata["sha256"]:
            raise RuntimeError(
                f"字体校验失败：{target.name}（期望 {metadata['sha256']}，实际 {actual}）。"
            )
        temporary.replace(target)
    except Exception as exc:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(
            "无法准备 ResumeMD 字体。请检查网络后重试；"
            f"下载地址：{metadata['url']}。原始错误：{exc}"
        ) from exc
    return target


def _font_face(kind: str, path: Path) -> str:
    family = _FONT_FILES[kind]["family"]
    uri = path.resolve().as_uri()
    return (
        f'@font-face {{ font-family: "{family}"; src: url("{uri}") '
        'format("truetype"); font-style: normal; font-weight: 100 900; }}'
    )


def _resolved_style(
    style: TypographyStyle,
    language: DocumentLanguage,
) -> TypographyStyle:
    if style != TypographyStyle.AUTO:
        return style
    return TypographyStyle.SANS


def resolve_font_stack(
    style: TypographyStyle,
    language: DocumentLanguage,
) -> tuple[TypographyStyle, FontStack]:
    resolved = _resolved_style(style, language)
    use_system = (
        platform.system() == "Darwin"
        and os.environ.get("RESUMEMD_FORCE_NOTO") != "1"
    )
    if use_system:
        if language == DocumentLanguage.CHINESE:
            sans = '"PingFang SC", "Hiragino Sans GB", sans-serif'
            serif = '"Songti SC", "STSong", serif'
            labels = {"sans": "PingFang SC", "serif": "Songti SC"}
        else:
            sans = '"Helvetica Neue", Helvetica, Arial, sans-serif'
            serif = 'Georgia, "Times New Roman", serif'
            labels = {"sans": "Helvetica Neue", "serif": "Georgia"}
        if resolved == TypographyStyle.SANS:
            return resolved, FontStack(labels["sans"], sans, sans)
        if resolved == TypographyStyle.SERIF:
            return resolved, FontStack(labels["serif"], serif, serif)
        return resolved, FontStack(
            f"{labels['serif']} + {labels['sans']}",
            sans,
            serif,
        )

    needed = ("sans", "serif") if resolved == TypographyStyle.HYBRID else (resolved.value,)
    paths = {kind: ensure_font(kind) for kind in needed}
    css = "\n".join(_font_face(kind, path) for kind, path in paths.items())
    sans = f'"{_FONT_FILES["sans"]["family"]}", sans-serif'
    serif = f'"{_FONT_FILES["serif"]["family"]}", serif'
    if resolved == TypographyStyle.SANS:
        return resolved, FontStack("Noto Sans SC", sans, sans, css)
    if resolved == TypographyStyle.SERIF:
        return resolved, FontStack("Noto Serif SC", serif, serif, css)
    return resolved, FontStack("Noto Serif SC + Noto Sans SC", sans, serif, css)


def font_manifest() -> dict:
    return {
        key: {
            "filename": value["filename"],
            "url": value["url"],
            "sha256": value["sha256"],
        }
        for key, value in _FONT_FILES.items()
    }
