"""Shared helpers and constants."""
from __future__ import annotations
from bs4 import BeautifulSoup
from ...models import Level, PageReport
from ..base import Rule, RuleMeta, register


_AA_NORMAL = 4.5

_AA_LARGE = 3.0

_AAA_NORMAL = 7.0

_AAA_LARGE = 4.5

def _contrast_issues(samples, normal_threshold: float, large_threshold: float):
    bad = []
    for s in samples:
        if getattr(s, "unmeasurable", False):
            continue
        threshold = large_threshold if s.is_large_text else normal_threshold
        if s.ratio < threshold:
            bad.append((s, threshold))
    return bad

def _unmeasurable_samples(samples):
    return [s for s in samples if getattr(s, "unmeasurable", False)]

