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
        """ Returns a list of available years. """

        years = ElectionCollection(self.session).get_years() or []
        years.extend(VoteCollection(self.session).get_years() or [])
        return sorted(set(years), reverse=True)

    def group_items(self, ungrouped_items, reverse=False):
        """ Groups a list of elections/votes. """

        if not ungrouped_items:
            return None

        return groupbylist(
            sorted(ungrouped_items, key=lambda i: i.date, reverse=reverse),
            lambda i: (i.__class__.__name__.lower(), i.domain, i.date)
        )

    def last_modified(self, ungrouped_items):
        """ Returns the last modification of the given elections/votes. """

        dates = (item.last_result_change for item in ungrouped_items)
        dates = list(filter(lambda x: x, dates))

        if not len(dates):
            return None

        return max(dates)

    def latest(self, group=True):
        """ Returns the lastest elections/votes (grouped or ungrouped). """

        items = ElectionCollection(self.session).get_latest() or []
        items.extend(VoteCollection(self.session).get_latest() or [])

        return self.group_items(items, reverse=True) if group else items

    def by_date(self, group=True):
        try:
            _date = date.fromtimestamp(mktime(strptime(self.date, '%Y-%m-%d')))
            items = ElectionCollection(self.session).by_date(_date) or []
            items.extend(VoteCollection(self.session).by_date(_date) or [])
        except (TypeError, ValueError):
            items = ElectionCollection(self.session).by_year(self.date) or []
            items.extend(VoteCollection(self.session).by_year(self.date) or [])

        return self.group_items(items) if group else items
