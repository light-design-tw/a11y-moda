"""Shared helpers and constants."""
from __future__ import annotations
import re
from bs4 import BeautifulSoup, Tag
from ...llm import parse_verdict
from ...models import Level, PageReport
from ..base import Rule, RuleMeta, register
from ..helpers import should_skip, truncate
from .llm_common import OUTPUT_INSTRUCTIONS, _SAMPLE_LIMIT, have_llm, judge_or_caveat


