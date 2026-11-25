# Load libraries
import logging
import os
import re

logger = logging.getLogger(__name__)

_EPUB_STYLE_PATTERN = re.compile(
    r'<link[^>]+rel=["\']stylesheet["\'][^>]*/?>', re.IGNORECASE
)
_EPUB_HEAD_PATTERN = re.compile(
    r"<head>.*?</head>", re.IGNORECASE | re.DOTALL
)
_XML_DECL_PATTERN = re.compile(r"<\?xml[^>]*\?>", re.IGNORECASE)
_DOCTYPE_PATTERN = re.compile(r"<!DOCTYPE[^>]*>", re.IGNORECASE)
_HTML_WRAPPER_PATTERN = re.compile(
    r"<html[^>]*>(.*)</html>", re.IGNORECASE | re.DOTALL
)
_BODY_PATTERN = re.compile(
    r"<body[^>]*>(.*)</body>", re.IGNORECASE | re.DOTALL
)


# Cleans EPUB chapter HTML for standalone web reading
def clean_chapter_html(raw_html: str) -> str:
    html = _XML_DECL_PATTERN.sub("", raw_html)
    html = _DOCTYPE_PATTERN.sub("", html)

    body_match = _BODY_PATTERN.search(html)

    if body_match:
        html = body_match.group(1)
        
    else:
        html_match = _HTML_WRAPPER_PATTERN.search(html)

        if html_match:
            html = html_match.group(1)

        html = _EPUB_HEAD_PATTERN.sub("", html)

    html = _EPUB_STYLE_PATTERN.sub("", html)
    html = html.strip()

    return html


# Saves cleaned chapter HTML files to the specified directory
def save_chapters_as_html(
    chapters: list[dict],
    output_dir: str,
) -> list[str]:
    os.makedirs(output_dir, exist_ok=True)
    paths = []

    for chapter in chapters:
        num = chapter.get("chapter_number", 0)
        content = chapter.get("html_content", "")
        cleaned = clean_chapter_html(content)
        filename = f"chapter_{num:03d}.html"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(cleaned)

        paths.append(filepath)

    return paths
