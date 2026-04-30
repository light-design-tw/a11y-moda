"""Shared helpers and constants."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ...models import Level, PageReport
from ..base import Rule, RuleMeta, register
from ..helpers import should_skip, truncate


