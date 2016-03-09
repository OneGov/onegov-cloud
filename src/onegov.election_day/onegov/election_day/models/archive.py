from time import mktime, strptime
from datetime import date
from onegov.ballot import ElectionCollection, VoteCollection
from onegov.core.utils import groupbylist


class Archive(object):
    """ Provides methods for votes/elections. """

    def __init__(self, session, date=None):
        self.session = session
        self.date = date

    def for_date(self, date):
        return self.__class__(self.session, date)

    def get_years(self):
        years = ElectionCollection(self.session).get_years() or []
        years.extend(VoteCollection(self.session).get_years() or [])
        return sorted(set(years), reverse=True)

    def group_items(self, items, reverse=False):
        if not items:
            return None

        return groupbylist(
            sorted(items, key=lambda i: i.date, reverse=reverse),
            lambda i: (i.__class__.__name__.lower(), i.domain, i.date)
        )

    def latest(self):
        items = ElectionCollection(self.session).get_latest() or []
        items.extend(VoteCollection(self.session).get_latest() or [])

        return self.group_items(items, reverse=True)

    def by_date(self):
        try:
            _date = date.fromtimestamp(mktime(strptime(self.date, '%Y-%m-%d')))
            items = ElectionCollection(self.session).by_date(_date) or []
            items.extend(VoteCollection(self.session).by_date(_date) or [])
        except (TypeError, ValueError):
            items = ElectionCollection(self.session).by_year(self.date) or []
            items.extend(VoteCollection(self.session).by_year(self.date) or [])

        return self.group_items(items)
