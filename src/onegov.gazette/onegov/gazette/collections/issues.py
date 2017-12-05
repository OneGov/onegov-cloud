from onegov.gazette.models import Issue
from onegov.core.collection import GenericCollection
from sedate import utcnow


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
