from collections import OrderedDict
from datetime import date
from itertools import groupby
from onegov.election_day.models import ArchivedResult
from sqlalchemy import cast, desc, distinct, extract, func, Integer
from time import mktime, strptime
from onegov.ballot import Election, ElectionCollection, Vote, VoteCollection


def groupbydict(items, keyfunc, sortfunc=None):
    return OrderedDict(
        (key, list(group))
        for key, group in groupby(
            sorted(items, key=sortfunc or keyfunc),
            keyfunc
        )
    )


class ArchivedResultCollection(object):

    def __init__(self, session, date=None):
        self.session = session
        self.date = date

    def for_date(self, date):
        return self.__class__(self.session, date)

    def query(self):
        return self.session.query(ArchivedResult)

    def get_years(self):
        """ Returns a list of available years. """

        year = cast(extract('year', ArchivedResult.date), Integer)
        query = self.session.query
        query = query(distinct(year))
        query = query.order_by(desc(year))

        return list(r[0] for r in query.all())

    def group_items(self, items, request):
        """ Groups a list of elections/votes. """

        if not items:
            return None

        dates = groupbydict(items, lambda i: i.date)
        order = ('federation', 'canton', 'municipality')
        if request.app.principal.domain == 'municipality':
            order = ('municipality', 'federation', 'canton')

        for date_, items_by_date in dates.items():
            domains = groupbydict(
                items_by_date,
                lambda i: i.domain,
                lambda i: order.index(i.domain) if i.domain in order else 99
            )
            for domain, items_by_domain in domains.items():
                types = groupbydict(
                    items_by_domain, lambda i: i.type
                )
                domains[domain] = types
            dates[date_] = domains

        return dates

    def latest(self):
        """ Returns the lastest results. """

        latest_date = self.query().with_entities(ArchivedResult.date)
        latest_date = latest_date.order_by(desc(ArchivedResult.date))
        latest_date = latest_date.limit(1).first()

        if not latest_date:
            return [], None
        else:
            return self.by_date(latest_date)

    def by_year(self, year):
        """ Returns the results for the given year. """

        query = self.query()
        query = query.filter(extract('year', ArchivedResult.date) == year)
        query = query.order_by(
            ArchivedResult.date,
            ArchivedResult.domain,
            ArchivedResult.name,
            ArchivedResult.shortcode,
            ArchivedResult.title
        )

        last_modified = self.session.query(
            func.max(query.subquery().c.last_result_change)
        )

        return query.all(), (last_modified.first() or [None])[0]

    def by_date(self, date_=None):
        """ Returns the results of a given/current date. """

        if date_ is None:
            try:
                date_ = date.fromtimestamp(
                    mktime(strptime(self.date, '%Y-%m-%d'))
                )
                return self.by_date(date_)
            except (TypeError, ValueError):
                try:
                    return self.by_year(int(self.date))
                except ValueError:
                    return self.latest()

        else:
            query = self.query()
            query = query.filter(ArchivedResult.date == date_)
            query = query.order_by(
                ArchivedResult.domain,
                ArchivedResult.name,
                ArchivedResult.shortcode,
                ArchivedResult.title
            )

            last_modified = self.session.query(
                func.max(query.subquery().c.last_result_change)
            )

            return query.all(), (last_modified.first() or [None])[0]

    def update(self, item, request):
        """ Updates a result. """

        url = request.link(item)

        result = self.query().filter_by(url=url).first()
        if result and result.last_result_change == item.last_result_change:
            return result

        add_result = False
        if not result:
            result = ArchivedResult()
            add_result = True

        result.url = url
        result.schema = self.session.info['schema']
        result.domain = item.domain
        result.name = request.app.principal.name
        result.date = item.date
        result.shortcode = item.shortcode
        result.title = item.title
        result.title_translations = item.title_translations
        result.last_result_change = item.last_result_change
        result.meta = {}
        result.meta['id'] = item.id
        result.meta['counted'] = item.counted
        result.meta['completed'] = item.completed

        if isinstance(item, Election):
            result.type = 'election'
            result.counted_entities = item.counted_entities
            result.total_entities = item.total_entities
            result.meta['elected_candidates'] = item.elected_candidates

        if isinstance(item, Vote):
            result.type = 'vote'
            result.counted_entities, result.total_entities = item.progress
            result.meta['answer'] = item.answer
            result.meta['nays_percentage'] = item.nays_percentage
            result.meta['yeas_percentage'] = item.yeas_percentage

        if add_result:
            self.session.add(result)

        return result

    def update_all(self, request):
        """ Updates all (local) results. """

        schema = self.session.info['schema']

        for item in self.query().filter_by(schema=schema):
            self.session.delete(item)

        for item in ElectionCollection(self.session).query():
            self.update(item, request)

        for item in VoteCollection(self.session).query():
            self.update(item, request)

    def add(self, item, request):
        """ Add a new election or vote and create a result entry.  """

        assert isinstance(item, Election) or isinstance(item, Vote)

        self.session.add(item)
        self.session.flush()

        self.update(item, request)
        self.session.flush()

    def delete(self, item, request):
        """ Deletes an election or vote and the associated result entry.  """

        assert isinstance(item, Election) or isinstance(item, Vote)

        for result in self.query().filter_by(url=request.link(item)):
            self.session.delete(result)

        self.session.delete(item)
        self.session.flush()
