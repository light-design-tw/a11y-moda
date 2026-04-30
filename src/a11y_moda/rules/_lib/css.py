"""Shared helpers and constants."""
from __future__ import annotations
import re
from bs4 import BeautifulSoup
from ...css_utils import collect_declarations
from ...models import Level, PageReport
from ..base import Rule, RuleMeta, register


_RELATIVE_UNIT_SUFFIXES = ("em", "ex", "cap", "ch", "ic", "lh", "rem", "rex", "rcap", "rch",
                           "ric", "rlh", "%", "vh", "vw", "vi", "vb", "vmax", "vmin", "vmin", "vmax")

_NAMED_SIZES = {"xx-small", "x-small", "small", "medium", "large", "x-large", "xx-large",
                "smaller", "larger", "inherit", "initial", "revert", "unset", "0"}

_FUNCTIONAL_PREFIXES = ("calc(", "var(", "min(", "max(", "clamp(", "round(", "mod(",
                        "sin(", "cos(", "tan(", "asin(", "acos(", "atan(", "atan2(",
                        "pow(", "sqrt(", "hypot(", "log(", "exp(")

_ABSOLUTE_UNIT_RE = re.compile(r"\b\d*\.?\d+(?:px|pt|pc|in|cm|mm|q)\b", re.IGNORECASE)

def _is_relative_or_named(value: str) -> bool:
    v = value.strip().lower().rstrip(";")
    if not v or v == "0" or v in _NAMED_SIZES:
        return True
    if any(v.startswith(fn) for fn in _FUNCTIONAL_PREFIXES):
        return True
    if any(v.endswith(suf) for suf in _RELATIVE_UNIT_SUFFIXES):
        return True
    return False

