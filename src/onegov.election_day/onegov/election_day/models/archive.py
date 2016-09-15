from collections import OrderedDict
from datetime import date
from itertools import groupby
from onegov.ballot import ElectionCollection, VoteCollection
from time import mktime, strptime


def domain_sortfunc(item):
    if item.domain == 'federation':
        return 0
    if item.domain == 'canton':
        return 1
    return 2


def groupbydict(items, keyfunc, sortfunc=None):
    return OrderedDict(
        (key, list(group))
        for key, group in groupby(
            sorted(items, key=sortfunc or keyfunc),
            keyfunc
        )
    )


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

    def group_items(self, items, reverse=False):
        """ Groups a list of elections/votes. """

        if not items:
            return None

        dates = groupbydict(items, lambda i: i.date)
        for date_, items_by_date in dates.items():
            domains = groupbydict(
                items_by_date, lambda i: i.domain, domain_sortfunc
            )
            for domain, items_by_domain in domains.items():
                types = groupbydict(
                    items_by_domain, lambda i: i.__class__.__name__.lower()
                )
                domains[domain] = types
            dates[date_] = domains

        return dates

    def last_modified(self, ungrouped_items):
        """ Returns the last modification of the given elections/votes. """

        dates = (item.last_result_change for item in ungrouped_items)
        dates = list(filter(lambda x: x, dates))

        if not len(dates):
            return None

        return max(dates)

    def latest(self):
        """ Returns the lastest elections/votes. """

        items = ElectionCollection(self.session).get_latest() or []
        items.extend(VoteCollection(self.session).get_latest() or [])

        return items

    def by_date(self):
        """ Returns the elecetions/votes of a given date. """
        try:
            _date = date.fromtimestamp(mktime(strptime(self.date, '%Y-%m-%d')))
            items = ElectionCollection(self.session).by_date(_date) or []
            items.extend(VoteCollection(self.session).by_date(_date) or [])
        except (TypeError, ValueError):
            items = ElectionCollection(self.session).by_year(self.date) or []
            items.extend(VoteCollection(self.session).by_year(self.date) or [])

        return items
