"""Shared helpers and constants."""
from __future__ import annotations
import re
from bs4 import Tag
from ...models import Level
from ..base import Rule, RuleMeta, register
from ..helpers import should_skip, truncate


