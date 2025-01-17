from __future__ import annotations

from collections import OrderedDict
from onegov.core.collection import GenericCollection
from onegov.gazette.models import Issue
from sedate import utcnow
from sqlalchemy import extract


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query


class IssueCollection(GenericCollection[Issue]):

    @property
    def model_class(self) -> type[Issue]:
        return Issue

    def query(self) -> Query[Issue]:
        query = super().query()
        query = query.order_by(None).order_by(Issue.date)
        return query

    @property
    def current_issue(self) -> Issue | None:
        return self.query().filter(Issue.deadline > utcnow()).first()

    def by_name(self, name: str) -> Issue | None:
        return self.query().filter(Issue.name == name).first()

    @property
    def years(self) -> list[int]:
        years = self.session.query(extract('year', Issue.date).distinct())
        return sorted(int(year) for year, in years)

    def by_years(self, desc: bool = False) -> dict[int, list[Issue]]:
        issues = OrderedDict()
        # FIXME: This is pretty inefficient, we should fetch all the rows
        #        in a single query and append to the individual lists
        for year in sorted(self.years, reverse=desc):
            query = self.query().filter(extract('year', Issue.date) == year)
            if desc:
                query = query.order_by(None).order_by(Issue.date.desc())
            issues[year] = query.all()
        return issues
