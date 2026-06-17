"""HM1130105C rule."""
from __future__ import annotations
from collections import defaultdict
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate

# Sibling rules on the same SC: HM1130103C validates that any <fieldset> carries
# a non-empty <legend>; HM1130103C_1 covers <optgroup> labels. This rule covers
# the distinct obligation — related controls that form a group MUST be grouped
# with <fieldset>+<legend> in the first place (WCAG H71). A same-name radio or
# checkbox set of 2+ is the unambiguous "related group" signal.
_GROUPING_TYPES = ("radio", "checkbox")


@register
class GroupRelatedControlsInFieldset(Rule):
    """HM1130105C — same-name radio/checkbox groups need a <fieldset>+<legend>."""

    meta = RuleMeta(
        rule_id="HM1130105C",
        guideline="1.3.1",
        level=Level.A,
        desc="表單控制元件組件以欄位組<fieldset>組件來分群，並以說明<legend>組件來提供標題",
    )

    @staticmethod
    def _in_fieldset(el: Tag) -> bool:
        for p in el.parents:
            if isinstance(p, Tag) and p.name and p.name.lower() == "fieldset":
                return True
        return False

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        groups: dict[tuple[str, str], list[Tag]] = defaultdict(list)
        for inp in soup.find_all("input"):
            if not isinstance(inp, Tag) or should_skip(inp):
                continue
            t = (inp.get("type") or "").strip().lower()
            if t not in _GROUPING_TYPES:
                continue
            name = (inp.get("name") or "").strip()
            if not name:
                continue
            groups[(t, name)].append(inp)
        for (t, name), members in groups.items():
            if len(members) < 2:
                continue
            # Lenient on purpose: if any member already sits inside a <fieldset>
            # the author has grouped them — partial-wrapping ambiguity is left
            # to HM1130103C (legend presence), not failed here.
            if any(self._in_fieldset(m) for m in members):
                continue
            kind = "單選" if t == "radio" else "複選"
            report.add(self._issue(
                message=(
                    f"一組相關的{kind}控制元件（name=\"{name}\"，共{len(members)}個）未以"
                    "fieldset組件分群。請以<fieldset>包覆並以<legend>提供群組標題。"
                ),
                snippet=truncate(str(members[0])),
            ))
            ctx.state["HM1130105C_ok"] = False
            return
        ctx.state["HM1130105C_ok"] = True
