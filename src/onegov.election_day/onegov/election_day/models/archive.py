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

    def to_json(self, items, request):
        results = []
        for item in items:
            values = {
                'data_url': request.link(item, 'json'),
                'date': item.date.isoformat(),
                'domain': item.domain,
                'progress': {},
                'title': item.title_translations,
                'type': item.__class__.__name__.lower(),
                'url': request.link(item),
            }

            try:
                values['progress']['counted'] = (
                    item.counted_municipalities or 0
                )
                values['progress']['total'] = item.total_municipalities or 0
            except AttributeError:
                divider = len(item.ballots) or 1
                values['progress']['counted'] = item.progress[0] or 0 / divider
                values['progress']['total'] = item.progress[1] or 0 / divider
                values['answer'] = item.answer or ""
                values['yeas_percentage'] = item.yeas_percentage
                values['nays_percentage'] = item.nays_percentage

            results.append(values)

        return results

    def latest(self, group=True):
        items = ElectionCollection(self.session).get_latest() or []
        items.extend(VoteCollection(self.session).get_latest() or [])

        return self.group_items(items, reverse=True) if group else items

    def latest_json(self, request):
        return self.to_json(self.latest(group=False), request)

    def by_date(self, group=True):
        try:
            _date = date.fromtimestamp(mktime(strptime(self.date, '%Y-%m-%d')))
            items = ElectionCollection(self.session).by_date(_date) or []
            items.extend(VoteCollection(self.session).by_date(_date) or [])
        except (TypeError, ValueError):
            items = ElectionCollection(self.session).by_year(self.date) or []
            items.extend(VoteCollection(self.session).by_year(self.date) or [])

        return self.group_items(items) if group else items

    def by_date_json(self, request):
        return self.to_json(self.by_date(group=False), request)
