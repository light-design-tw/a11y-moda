from __future__ import annotations
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Literal


class Level(IntEnum):
    A = 1
    AA = 2
    AAA = 3


Status = Literal["pass", "fail", "info", "caveat", "needs_human", "not_applicable"]


@dataclass
class Issue:
    rule_id: str
    guideline: str
    level: Level
    desc: str
    message: str = ""
    snippet: str = ""
    url: str = ""
    status: Status = "fail"


@dataclass
class PageReport:
    url: str
    status_code: int = 0
    issues: list[Issue] = field(default_factory=list)
    fetch_error: str = ""

    def add(self, issue: Issue) -> None:
        self.issues.append(issue)

    def by_status(self, status: Status) -> list[Issue]:
        return [i for i in self.issues if i.status == status]


@dataclass
class ScanReport:
    pages: list[PageReport] = field(default_factory=list)

    def add(self, p: PageReport) -> None:
        self.pages.append(p)

    @property
    def total_issues(self) -> int:
        return sum(len(p.issues) for p in self.pages)

    @property
    def total_failures(self) -> int:
        return sum(len(p.by_status("fail")) for p in self.pages)

    def aggregate_by_rule(self) -> dict[str, dict]:
        """Group same rule across pages — surfaces site-wide patterns."""
        agg: dict[str, dict] = {}
        for page in self.pages:
            for issue in page.issues:
                rec = agg.setdefault(issue.rule_id, {
                    "rule_id": issue.rule_id,
                    "guideline": issue.guideline,
                    "level": int(issue.level),
                    "desc": issue.desc,
                    "pages_affected": [],
                    "status": issue.status,
                })
                if page.url not in rec["pages_affected"]:
                    rec["pages_affected"].append(page.url)
        return agg
