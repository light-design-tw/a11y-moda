"""Auto-discover all rule modules under codes/<theme>/<rule_id>.py."""
from __future__ import annotations
import importlib
import pkgutil

from . import codes  # noqa: F401
from .base import Rule, RuleMeta, register, RuleContext, all_rules  # noqa: F401


def _discover():
    pkg = codes
    for _, name, ispkg in pkgutil.iter_modules(pkg.__path__):
        sub_full = f"{pkg.__name__}.{name}"
        sub_mod = importlib.import_module(sub_full)
        if ispkg:
            for _, leaf, _ in pkgutil.iter_modules(sub_mod.__path__):
                importlib.import_module(f"{sub_full}.{leaf}")


_discover()
