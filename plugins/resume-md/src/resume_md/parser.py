from html import escape
import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup, NavigableString, Tag
from markdown_it import MarkdownIt


_SECTION_KINDS = (
    (
        "summary-section",
        (
            "个人概述",
            "个人简介",
            "职业概述",
            "自我介绍",
            "summary",
            "professional summary",
            "career summary",
            "profile",
            "objective",
            "about",
        ),
    ),
    (
        "skills-section",
        (
            "专业技能",
            "技能清单",
            "核心技能",
            "技术能力",
            "skills",
            "technical skills",
            "core competencies",
            "expertise",
        ),
    ),
    (
        "experience-section",
        (
            "工作经历",
            "工作经验",
            "职业经历",
            "实习经历",
            "experience",
            "professional experience",
            "work experience",
            "employment",
        ),
    ),
    (
        "projects-section",
        (
            "项目经历",
            "独立项目",
            "个人项目",
            "开源项目",
            "projects",
            "selected projects",
            "personal projects",
            "portfolio",
        ),
    ),
    (
        "research-section",
        (
            "研究经历",
            "科研经历",
            "论文发表",
            "research",
            "research experience",
            "publications",
        ),
    ),
    (
        "education-section",
        ("教育经历", "教育背景", "学历", "education", "academic background"),
    ),
    (
        "awards-section",
        (
            "奖项荣誉",
            "荣誉奖项",
            "证书",
            "certifications",
            "awards",
            "awards and certifications",
            "honors",
        ),
    ),
)

_DATE_TOKEN = (
    r"(?:(?:19|20)\d{2}(?:[./-]\d{1,2})?"
    r"|(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|"
    r"Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|"
    r"Nov(?:ember)?|Dec(?:ember)?)\.?\s+(?:19|20)\d{2})"
)


def extract_title(markdown: str) -> str:
    for line in markdown.splitlines():
        if line.startswith("# "):
            return line[2:].strip() or "简历"
    return "简历"


def _safe_link(href: str) -> bool:
    parsed = urlparse(href)
    return parsed.scheme in {"http", "https", "mailto"}


def _meaningful_children(parent: Tag) -> list[Tag]:
    return [child for child in parent.children if isinstance(child, Tag)]


def _is_strong_only(paragraph: Tag) -> bool:
    tags = _meaningful_children(paragraph)
    non_whitespace = [
        child
        for child in paragraph.children
        if isinstance(child, NavigableString) and child.strip()
    ]
    return (
        len(tags) == 1
        and tags[0].name == "strong"
        and not non_whitespace
    )


def _looks_like_entry_meta(paragraph: Tag) -> bool:
    text = paragraph.get_text(" ", strip=True)
    if len(text) > 90:
        return False
    has_date = bool(
        re.search(
            rf"{_DATE_TOKEN}"
            rf"(?:\s*(?:-|–|—|至|to|until|~)\s*"
            rf"(?:{_DATE_TOKEN}|至今|present|current|now))?",
            text,
            flags=re.IGNORECASE,
        )
    )
    has_link = paragraph.find("a") is not None
    has_compact_separator = "｜" in text or " | " in text
    return has_date or has_link or has_compact_separator


def _section_classes(title: str) -> list[str]:
    normalized = "".join(title.casefold().split()).strip("：:")
    classes = ["resume-section"]
    for class_name, aliases in _SECTION_KINDS:
        if any("".join(alias.casefold().split()) in normalized for alias in aliases):
            classes.append(class_name)
            break
    return classes


def markdown_to_resume_html(markdown: str) -> str:
    renderer = MarkdownIt("commonmark", {"html": False, "linkify": False})
    renderer.enable(("table", "strikethrough"))
    fragment = renderer.render(markdown)
    soup = BeautifulSoup(
        f'<div class="markdown-source">{fragment}</div>',
        "html.parser",
    )
    source = soup.select_one(".markdown-source")
    if source is None:
        raise ValueError("Markdown 解析失败。")

    for link in source.find_all("a"):
        href = link.get("href", "")
        if not _safe_link(href):
            link.unwrap()
    for image in source.find_all("img"):
        image.replace_with(image.get("alt", ""))

    resume = soup.new_tag("article", attrs={"class": "resume"})
    nodes = _meaningful_children(source)

    has_sections = any(node.name == "h2" for node in nodes)
    if has_sections and nodes and nodes[0].name == "h1":
        header = soup.new_tag("header", attrs={"class": "resume-header"})
        while nodes and nodes[0].name != "h2":
            header.append(nodes.pop(0).extract())

        paragraphs = header.find_all("p", recursive=False)
        for paragraph, class_name in zip(
            paragraphs,
            ("headline", "contact", "links"),
        ):
            paragraph["class"] = [class_name]
        resume.append(header)
    else:
        preamble = soup.new_tag("div", attrs={"class": "resume-preamble"})
        while nodes and nodes[0].name != "h2":
            preamble.append(nodes.pop(0).extract())
        if _meaningful_children(preamble):
            resume.append(preamble)

    while nodes:
        heading = nodes.pop(0)
        if heading.name != "h2":
            continue

        title = heading.get_text(" ", strip=True)
        classes = _section_classes(title)

        section = soup.new_tag(
            "section",
            attrs={"class": classes, "data-title": title},
        )
        section.append(heading.extract())
        body = soup.new_tag("div", attrs={"class": "section-body"})
        section.append(body)

        section_nodes: list[Tag] = []
        while nodes and nodes[0].name != "h2":
            section_nodes.append(nodes.pop(0))

        while section_nodes:
            if section_nodes[0].name != "h3":
                body.append(section_nodes.pop(0).extract())
                continue

            entry = soup.new_tag("article", attrs={"class": "entry"})
            entry_head = soup.new_tag("header", attrs={"class": "entry-head"})
            entry_head.append(section_nodes.pop(0).extract())
            if (
                section_nodes
                and section_nodes[0].name == "p"
                and _looks_like_entry_meta(section_nodes[0])
            ):
                meta = section_nodes.pop(0).extract()
                meta["class"] = [*meta.get("class", []), "entry-meta"]
                entry_head.append(meta)
            entry.append(entry_head)

            while section_nodes and section_nodes[0].name != "h3":
                node = section_nodes.pop(0).extract()
                if node.name == "p" and _is_strong_only(node):
                    node["class"] = [*node.get("class", []), "entry-label"]
                entry.append(node)
            body.append(entry)

        resume.append(section)

    if not _meaningful_children(resume):
        raise ValueError("Markdown 中没有可渲染的内容。")
    return str(resume)


def escaped_title(markdown: str) -> str:
    return escape(extract_title(markdown), quote=True)
