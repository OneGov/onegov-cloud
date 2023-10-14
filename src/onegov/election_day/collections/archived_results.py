from collections import OrderedDict
from datetime import date
from itertools import groupby
from onegov.ballot import Election
from onegov.ballot import ElectionCollection
from onegov.ballot import ElectionCompound
from onegov.ballot import ElectionCompoundCollection
from onegov.ballot import Vote
from onegov.ballot import VoteCollection
from onegov.core.collection import Pagination
from onegov.election_day.models import ArchivedResult
from onegov.election_day.utils import replace_url
from sedate import as_datetime
from sqlalchemy import cast
from sqlalchemy import desc
from sqlalchemy import distinct
from sqlalchemy import extract
from sqlalchemy import func
from sqlalchemy import Integer
from sqlalchemy import or_
from sqlalchemy.sql.expression import case
from time import mktime
from time import strptime


def groupbydict(items, keyfunc, sortfunc=None):
    return OrderedDict(
        (key, list(group))
        for key, group in groupby(
            sorted(items, key=sortfunc or keyfunc),
            keyfunc
        )
    )


class ArchivedResultCollection:

    def __init__(self, session, date_=None):
        self.session = session
        self.date = date_

    def for_date(self, date_):
        return self.__class__(self.session, date_)

    def query(self):
        return self.session.query(ArchivedResult)

    def get_years(self):
        """ Returns a list of available years. """

        year = cast(extract('year', ArchivedResult.date), Integer)
        query = self.session.query
        query = query(distinct(year))
        query = query.order_by(desc(year))

        return [year for year, in query]

    def group_items(self, items, request):
        """ Groups a list of archived results.

        Groups election compounds and elections to the same group. Removes
        elections already covered by an election compound. Merges region,
        district and none domains.
        """

        if not items:
            return None

        compounded = {
            url for item in items for url in getattr(item, 'elections', [])
        }

        dates = groupbydict(
            items,
            lambda i: i.date,
            lambda i: -(as_datetime(i.date).timestamp() or 0)
        )

        order = {
            'federation': 1,
            'canton': 2,
            'region': 3,
            'district': 3,
            'none': 3,
            'municipality': 4,
        }
        mapping = {
            'federation': 'federation',
            'canton': 'canton',
            'region': 'region',
            'district': 'region',
            'none': 'region',
            'municipality': 'municipality',
        }
        if request.app.principal.domain == 'municipality':
            order['municipality'] = 0

        for date_, items_by_date in dates.items():
            domains = groupbydict(
                items_by_date,
                lambda i: mapping.get(i.domain),
                lambda i: order.get(i.domain, 99)
            )
            for domain, items_by_domain in domains.items():
                types = groupbydict(
                    [
                        item for item in items_by_domain
                        if item.url not in compounded
                    ],
                    lambda i: 'vote' if i.type == 'vote' else 'election'
                )
                domains[domain] = types
            dates[date_] = domains

        return dates

    def current(self):
        """ Returns the current results.

        The current results are the results from either the next election day
        relative to today or the last results relative to today, if no next.

        """

        next_date = self.query().with_entities(ArchivedResult.date)
        next_date = next_date.filter(ArchivedResult.date >= date.today())
        next_date = next_date.order_by(ArchivedResult.date)
        next_date = next_date.limit(1).scalar()

        last_date = self.query().with_entities(ArchivedResult.date)
        last_date = last_date.filter(ArchivedResult.date <= date.today())
        last_date = last_date.order_by(desc(ArchivedResult.date))
        last_date = last_date.limit(1).scalar()

        current_date = next_date or last_date
        return self.by_date(current_date) if current_date else ([], None)

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
            func.max(query.subquery().c.last_modified)
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
                    return self.current()

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
                func.max(query.subquery().c.last_modified)
            )

            return query.all(), (last_modified.first() or [None])[0]

    def update(self, item, request, old=None):
        """ Updates a result. """

        url = request.link(item)
        url = replace_url(url, request.app.principal.official_host)
        if old:
            old = replace_url(old, request.app.principal.official_host)
        else:
            old = url
        result = self.query().filter_by(url=old).first()

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
        result.title_translations = item.title_translations
        result.last_modified = item.last_modified
        result.last_result_change = item.last_result_change
        result.external_id = item.id
        result.counted = item.counted
        result.completed = item.completed
        result.counted_entities, result.total_entities = item.progress
        result.has_results = item.has_results
        result.meta = result.meta or {}

        if isinstance(item, Election):
            result.type = 'election'
            result.turnout = item.turnout
            result.elected_candidates = item.elected_candidates
            for association in item.associations:
                self.update(association.election_compound, request)

        if isinstance(item, ElectionCompound):
            result.type = 'election_compound'
            result.elections = [
                request.link(election) for election in item.elections
            ]

        if isinstance(item, Vote):
            result.type = 'vote'
            result.turnout = item.turnout
            result.answer = item.answer
            result.nays_percentage = item.nays_percentage
            result.yeas_percentage = item.yeas_percentage

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

        for item in ElectionCompoundCollection(self.session).query():
            self.update(item, request)

        for item in VoteCollection(self.session).query():
            self.update(item, request)

    def add(self, item, request):
        """ Add a new election or vote and create a result entry.  """

        assert (
            isinstance(item, Election)
            or isinstance(item, ElectionCompound)
            or isinstance(item, Vote)
        )

        self.session.add(item)
        self.session.flush()

        self.update(item, request)
        self.session.flush()

    def clear(self, item, request):
        """ Clears an election or vote and the associated result entry.  """

        assert (
            isinstance(item, Election)
            or isinstance(item, ElectionCompound)
            or isinstance(item, Vote)
        )

        item.clear_results()
        self.update(item, request)
        for election in getattr(item, 'elections', []):
            self.update(election, request)

        self.session.flush()

    def delete(self, item, request):
        """ Deletes an election or vote and the associated result entry.  """

        assert (
            isinstance(item, Election)
            or isinstance(item, ElectionCompound)
            or isinstance(item, Vote)
        )

        url = request.link(item)
        url = replace_url(url, request.app.principal.official_host)
        for result in self.query().filter_by(url=url):
            self.session.delete(result)

        self.session.delete(item)
        self.session.flush()


class SearchableArchivedResultCollection(ArchivedResultCollection, Pagination):

    def __init__(
            self,
            app,
            date_=None,
            from_date=None,
            to_date=None,
            item_type=None,
            domains=None,
            term=None,
            answers=None,
            locale='de_CH',
            page=0
    ):
        super().__init__(app.session(), date_=date_)
        self.app = app
        self.from_date = from_date
        self.to_date = to_date or date.today()
        self.item_type = item_type
        self.domains = domains
        self.term = term
        self.answers = answers
        self.locale = locale
        self.page = page

    def __eq__(self, other):
        return self.page == other.page

    def subset(self):
        return self.query()

    @property
    def page_index(self):
        return self.page

    def page_by_index(self, index):
        return self.__class__(
            app=self.app,
            date_=self.date,
            from_date=self.from_date,
            to_date=self.to_date,
            item_type=self.item_type,
            domains=self.domains,
            term=self.term,
            answers=self.answers,
            locale=self.locale,
            page=index
        )

    @staticmethod
    def term_to_tsquery_string(term):
        """ Returns the current search term transformed to use within
        Postgres ``to_tsquery`` function.
        Removes all unwanted characters, replaces prefix matching, joins
        word together using FOLLOWED BY.
        """

        def cleanup(word, whitelist_chars=',.-_'):
            result = ''.join(
                (c for c in word if c.isalnum() or c in whitelist_chars)
            )
            return f'{result}:*' if word.endswith('*') else result

        parts = (cleanup(part) for part in (term or '').split())
        return ' <-> '.join(tuple(part for part in parts if part))

    @staticmethod
    def match_term(column, language, term):
        """ Usage:
         model.filter(match_term(model.col, 'german', 'my search term')) """
        document_tsvector = func.to_tsvector(language, column)
        ts_query_object = func.to_tsquery(language, term)
        return document_tsvector.op('@@')(ts_query_object)

    @staticmethod
    def filter_text_by_locale(column, term, locale=None):
        """ Returns an SQLAlchemy filter statement based on the search term.
        If no locale is provided, it will use english as language.

        ``to_tsquery`` creates a tsquery value from term, which must consist of
         single tokens separated by these Boolean operators:

            * ``&`` (AND)
            * ``|`` (OR)
            * ``!`` (NOT)

        ``to_tsvector`` parses a textual document into tokens, reduces the
        tokens to lexemes, and returns a tsvector which lists the lexemes
        together with their positions in the document.

        The document is processed according to the specified or default text
        search configuration.

        """

        mapping = {'de_CH': 'german', 'fr_CH': 'french', 'it_CH': 'italian',
                   'rm_CH': 'english'}
        return SearchableArchivedResultCollection.match_term(
            column, mapping.get(locale, 'english'), term
        )

    @property
    def term_filter(self):
        term = SearchableArchivedResultCollection.term_to_tsquery_string(
            self.term
        )
        return (
            SearchableArchivedResultCollection.filter_text_by_locale(
                ArchivedResult.shortcode, term, self.locale
            ),
            SearchableArchivedResultCollection.filter_text_by_locale(
                ArchivedResult.title, term, self.locale
            )
        )

    def query(self):
        query = self.session.query(ArchivedResult)

        if self.item_type:
            if self.item_type == 'election':
                query = query.filter(ArchivedResult.type.in_(
                    ('election', 'election_compound')
                ))

                # exclude elections already covered by election compounds
                exclude = self.session.query(ArchivedResult.meta['elections'])
                exclude = [result[0] for result in exclude if result[0]]
                exclude = [item for items in exclude for item in items]
                exclude = [item.split('/')[-1] for item in exclude]
                if exclude:
                    query = query.filter(
                        ArchivedResult.meta['id'].notin_(exclude)
                    )
            else:
                query = query.filter(ArchivedResult.type == self.item_type)

        if self.domains:
            domains = set(self.domains)
            if 'region' in domains:
                domains.add('district')
                domains.add('none')
            query = query.filter(ArchivedResult.domain.in_(domains))

        if self.to_date:
            if self.to_date > date.today():
                self.to_date = date.today()
            if self.to_date != date.today():
                query = query.filter(ArchivedResult.date <= self.to_date)

        if self.from_date:
            if self.to_date and self.from_date > self.to_date:
                self.from_date = self.to_date
            query = query.filter(ArchivedResult.date >= self.from_date)

        if self.answers and self.item_type == 'vote':
            query = query.filter(
                ArchivedResult.type == 'vote',
                ArchivedResult.meta['answer'].astext.in_(self.answers)
            )

        if self.term and self.term != '*':
            query = query.filter(or_(*self.term_filter))

        # order by date and type
        order = (
            'federation', 'canton', 'region', 'district', 'none',
            'municipality'
        )
        if self.app.principal.domain == 'municipality':
            order = (
                'municipality', 'federation', 'canton', 'region', 'district',
                'none'
            )
        query = query.order_by(
            ArchivedResult.date.desc(),
            case(
                tuple(
                    (ArchivedResult.domain == domain, index) for
                    index, domain in enumerate(order, 1)
                )
            )
        )
        return query

    def reset_query_params(self):
        self.from_date = None
        self.to_date = date.today()
        self.item_type = None
        self.domains = None
        self.term = None
        self.answers = None
        self.locale = 'de_CH'

    @classmethod
    def for_item_type(cls, session, item_type, **kwargs):
        if item_type in ['vote', 'election']:
            kwargs['item_type'] = item_type
            return cls(session, **kwargs)
