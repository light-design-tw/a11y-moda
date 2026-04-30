"""Report rendering package — public API matches the old report.py module."""
from ._html import page_to_html_block, scan_to_html
from ._markdown import page_to_markdown, scan_to_markdown

__all__ = [
    "page_to_html_block",
    "page_to_markdown",
    "scan_to_html",
    "scan_to_markdown",
]
