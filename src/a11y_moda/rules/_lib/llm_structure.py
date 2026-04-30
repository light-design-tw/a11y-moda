"""Shared helpers and constants."""
from __future__ import annotations
from bs4 import Tag
from ...models import Level
from ..base import Rule, RuleMeta, register
from ..helpers import should_skip, truncate
from .llm_common import OUTPUT_INSTRUCTIONS, have_llm, judge_or_caveat


