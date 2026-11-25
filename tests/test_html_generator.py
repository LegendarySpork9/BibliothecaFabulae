# Load libraries
import os
import tempfile

from backend.downloader.html_generator import clean_chapter_html, save_chapters_as_html


def test_clean_chapter_html_strips_body():
    raw = """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Ch1</title><link rel="stylesheet" href="style.css"/></head>
<body>
<h2>Chapter Title</h2>
<p>Content here.</p>
</body>
</html>"""

    result = clean_chapter_html(raw)

    assert "<html" not in result
    assert "<head>" not in result
    assert "stylesheet" not in result
    assert "<h2>Chapter Title</h2>" in result
    assert "<p>Content here.</p>" in result


def test_clean_chapter_html_no_body():
    raw = "<div><p>Simple content</p></div>"
    result = clean_chapter_html(raw)

    assert "<p>Simple content</p>" in result


def test_save_chapters_as_html():
    chapters = [
        {"chapter_number": 1, "html_content": "<body><p>Chapter 1</p></body>"},
        {"chapter_number": 2, "html_content": "<body><p>Chapter 2</p></body>"},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        paths = save_chapters_as_html(chapters, tmpdir)

        assert len(paths) == 2
        assert os.path.exists(paths[0])
        assert os.path.exists(paths[1])
        assert paths[0].endswith("chapter_001.html")
        assert paths[1].endswith("chapter_002.html")

        with open(paths[0], encoding="utf-8") as f:
            content = f.read()
            assert "<p>Chapter 1</p>" in content
