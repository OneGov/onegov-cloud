from collections import OrderedDict
from onegov.core.collection import GenericCollection
from onegov.gazette.models import Issue
from sedate import utcnow
from sqlalchemy import extract


class IssueCollection(GenericCollection):

    @property
    def model_class(self):
        return Issue

    def query(self):
        query = super(IssueCollection, self).query()
        query = query.order_by(None).order_by(Issue.date)
        return query

    @property
    def current_issue(self):
        return self.query().filter(Issue.deadline > utcnow()).first()

    def by_name(self, name):
        return self.query().filter(Issue.name == name).first()

    @property
    def years(self):
        years = self.session.query(extract('year', Issue.date).distinct())
        years = sorted([int(year[0]) for year in years])
        return years

    def by_years(self, desc=False):
        issues = OrderedDict()
        for year in sorted(self.years, reverse=desc):
            query = self.query().filter(extract('year', Issue.date) == year)
            if desc:
                query = query.order_by(None).order_by(Issue.date.desc())
            issues[year] = query.all()
        return issues
