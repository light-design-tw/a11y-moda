"""Shared helpers and constants."""
from __future__ import annotations
from urllib.parse import urlparse
from bs4 import Tag
from ...models import Level
from ..base import Rule, RuleMeta, register
from ..helpers import truncate


_PROPRIETARY_EXT = {".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"}

