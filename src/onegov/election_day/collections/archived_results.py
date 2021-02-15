from collections import OrderedDict
from datetime import date
from itertools import groupby
from onegov.ballot import Election
from onegov.ballot import ElectionCollection
from onegov.ballot import ElectionCompound
from onegov.ballot import ElectionCompoundCollection
from onegov.ballot import Vote
from onegov.ballot import VoteCollection
from onegov.election_day.models import ArchivedResult
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
from onegov.core.collection import Pagination


def groupbydict(items, keyfunc, sortfunc=None):
    return OrderedDict(
        (key, list(group))
        for key, group in groupby(
            sorted(items, key=sortfunc or keyfunc),
            keyfunc
        )
    )


class ArchivedResultCollection(object):

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

        return list(r[0] for r in query.all())

    def group_items(self, items, request):
        """ Groups a list of archived results.

        Groups election compounds and elections to the same group. Removes
        elections already covered by an election compound.
        """

        if not items:
            return None

        compounded = {
            id_ for item in items for id_ in getattr(item, 'elections', [])
        }

        dates = groupbydict(items, lambda i: i.date)
        order = ('federation', 'canton', 'region', 'municipality')
        if request.app.principal.domain == 'municipality':
            order = ('municipality', 'federation', 'canton', 'region')

        for date_, items_by_date in dates.items():
            domains = groupbydict(
                items_by_date,
                lambda i: i.domain,
                lambda i: order.index(i.domain) if i.domain in order else 99
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
                func.max(query.subquery().c.last_modified)
            )

            return query.all(), (last_modified.first() or [None])[0]

    def update(self, item, request):
        """ Updates a result. """
        url = request.link(item)

        result = self.query().filter_by(url=url).first()

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

        self.session.flush()

    def delete(self, item, request):
        """ Deletes an election or vote and the associated result entry.  """

        assert (
            isinstance(item, Election)
            or isinstance(item, ElectionCompound)
            or isinstance(item, Vote)
        )

        for result in self.query().filter_by(url=request.link(item)):
            self.session.delete(result)

        self.session.delete(item)
        self.session.flush()


class SearchableArchivedResultCollection(
        ArchivedResultCollection, Pagination):

    def __init__(
            self,
            session,
            date_=None,
            from_date=None,
            to_date=None,
            types=None,
            item_type=None,
            domains=None,
            term=None,
            answers=None,
            locale='de_CH',
            page=0
    ):
        super().__init__(session, date_=date_)
        self.from_date = from_date
        self.to_date = to_date or date.today()
        self.types = types
        self.item_type = item_type
        self.domains = domains
        self.term = term
        self.answers = answers
        self.locale = locale
        self.app_principal_domain = None
        self.page = page

    def __eq__(self, other):
        return self.page == other.page

    def subset(self):
        return self.query()

    @staticmethod
    def allowed_item_types():
        return tuple(a[0] for a in ArchivedResult.types_of_results)

    @property
    def page_index(self):
        return self.page

    def page_by_index(self, index):
        return self.__class__(
            session=self.session,
            date_=self.date,
            from_date=self.from_date,
            to_date=self.to_date,
            types=self.types,
            item_type=self.item_type,
            domains=self.domains,
            term=self.term,
            answers=self.answers,
            locale=self.locale,
            page=index
        )

    def group_items(self, items, request):
        compounded = {
            id_ for item in items for id_ in getattr(item, 'elections', [])
        }

        items = dict(
            votes=tuple(v for v in items if v.type == 'vote'),
            elections=tuple(
                e for e in items if e.type in ['election', 'election_compound']
                if e.url not in compounded
            )
        )

        return items

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
        assert self.term
        assert self.locale
        term = SearchableArchivedResultCollection.term_to_tsquery_string(
            self.term)
        # The title is a translations hybrid, .title is a shorthand
        return (
            SearchableArchivedResultCollection.filter_text_by_locale(
                ArchivedResult.shortcode, term, self.locale),
            SearchableArchivedResultCollection.filter_text_by_locale(
                ArchivedResult.title, term, self.locale)
        )

    def check_from_date_to_date(self):
        if not self.to_date or not self.from_date:
            return

        if self.to_date > date.today():
            self.to_date = date.today()
        if self.from_date > self.to_date:
            self.from_date = self.to_date

    def query(self, no_filter=False, sort=True):

        if no_filter:
            return self.session.query(ArchivedResult)
        assert self.to_date, 'to_date must have a datetime.date value'

        self.check_from_date_to_date()
        order = ('federation', 'canton', 'region', 'municipality')
        if self.app_principal_domain == 'municipality':
            order = ('municipality', 'federation', 'canton', 'region')

        def generate_cases():
            return tuple(
                (ArchivedResult.domain == opt, ind) for
                ind, opt in enumerate(order, 1)
            )

        query = self.session.query(ArchivedResult)

        if self.item_type:
            # Treat compound election as elections
            if self.item_type == 'vote':
                query = query.filter(ArchivedResult.type == self.item_type)
            else:
                query = query.filter(ArchivedResult.type.in_(
                    ('election', 'election_compound')
                ))

        elif self.types and len(self.types) != len(
                ArchivedResult.types_of_results):
            query = query.filter(ArchivedResult.type.in_(self.types))
        if self.domains and (len(self.domains) != len(
                ArchivedResult.types_of_domains)):
            query = query.filter(ArchivedResult.domain.in_(self.domains))
        if self.from_date:
            query = query.filter(ArchivedResult.date >= self.from_date)
        if self.to_date != date.today():
            query = query.filter(ArchivedResult.date <= self.to_date)

        is_vote = (self.item_type == 'vote'
                   or (self.types and 'vote' in self.types))

        answer_matters = (
            self.answers and len(self.answers) != len(
                ArchivedResult.types_of_answers))

        if answer_matters and is_vote:
            vote_answer = ArchivedResult.meta['answer'].astext
            query = query.filter(
                ArchivedResult.type == 'vote',
                vote_answer.in_(self.answers))
        if self.term:
            query = query.filter(or_(*self.term_filter))

        if sort:
            query = query.order_by(
                ArchivedResult.date.desc(),
                case(generate_cases())
            )
        return query

    def reset_query_params(self):
        self.from_date = None
        self.to_date = date.today()
        self.types = None
        self.item_type = None
        self.domains = None
        self.term = None
        self.answers = None
        self.locale = 'de_CH'

    @classmethod
    def for_item_type(cls, session, item_type, **kwargs):
        if item_type not in cls.allowed_item_types():
            return None
        kwargs['item_type'] = item_type
        return cls(session, **kwargs)
