from __future__ import annotations

from collections import OrderedDict
from datetime import date
from itertools import groupby
from onegov.core.collection import Pagination
from onegov.election_day.collections.elections import ElectionCollection
from onegov.election_day.collections.election_compounds import \
    ElectionCompoundCollection
from onegov.election_day.collections.votes import VoteCollection
from onegov.election_day.models import ArchivedResult, ComplexVote
from onegov.election_day.models import Election
from onegov.election_day.models import ElectionCompound
from onegov.election_day.models import Vote
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


from typing import overload
from typing import Any
from typing import Literal
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import SupportsRichComparison
    from collections.abc import Callable
    from collections.abc import Collection
    from collections.abc import Iterable
    from datetime import datetime
    from onegov.election_day.app import ElectionDayApp
    from onegov.election_day.request import ElectionDayRequest
    from sqlalchemy.dialects.postgresql import TSVECTOR
    from sqlalchemy.orm import Query
    from sqlalchemy.orm import Session
    from sqlalchemy.sql import ColumnElement
    from typing import TypeVar
    from typing import Self

    _T1 = TypeVar('_T1')
    _T2 = TypeVar('_T2')
    _T3 = TypeVar('_T3')
    _TSupportsRichComparison = TypeVar(
        '_TSupportsRichComparison',
        bound='SupportsRichComparison'
    )


@overload
def groupbydict(
    items: Iterable[_T1],
    keyfunc: Callable[[_T1], _TSupportsRichComparison],
    sortfunc: None = None,
    groupfunc: Callable[[Iterable[_T1]], list[_T1]] = list,
) -> dict[_TSupportsRichComparison, list[_T1]]: ...


@overload
def groupbydict(
    items: Iterable[_T1],
    keyfunc: Callable[[_T1], _T2],
    sortfunc: Callable[[_T1], SupportsRichComparison],
    groupfunc: Callable[[Iterable[_T1]], list[_T1]] = list,
) -> dict[_T2, list[_T1]]: ...


@overload
def groupbydict(
    items: Iterable[_T1],
    keyfunc: Callable[[_T1], _TSupportsRichComparison],
    sortfunc: None = None,
    *,
    groupfunc: Callable[[Iterable[_T1]], _T2],
) -> dict[_TSupportsRichComparison, _T2]: ...


@overload
def groupbydict(
    items: Iterable[_T1],
    keyfunc: Callable[[_T1], _TSupportsRichComparison],
    sortfunc: None,
    groupfunc: Callable[[Iterable[_T1]], _T2],
) -> dict[_TSupportsRichComparison, _T2]: ...


@overload
def groupbydict(
    items: Iterable[_T1],
    keyfunc: Callable[[_T1], _T2],
    sortfunc: Callable[[_T1], SupportsRichComparison],
    groupfunc: Callable[[Iterable[_T1]], _T3],
) -> dict[_T2, _T3]: ...


def groupbydict(
    items: Iterable[_T1],
    keyfunc: Callable[[_T1], Any],
    sortfunc: Callable[[_T1], Any] | None = None,
    groupfunc: Callable[[Iterable[_T1]], Any] = list
) -> dict[Any, Any]:

    return OrderedDict(
        (key, groupfunc(group))
        for key, group in groupby(
            sorted(items, key=sortfunc or keyfunc),
            keyfunc
        )
    )


class ArchivedResultCollection:

    def __init__(self, session: Session, date_: str | None = None):
        self.session = session
        self.date = date_

    def for_date(self, date_: str) -> Self:
        return self.__class__(self.session, date_)

    def query(self) -> Query[ArchivedResult]:
        return self.session.query(ArchivedResult)

    def get_years(self) -> list[int]:
        """ Returns a list of available years. """

        year = cast(extract('year', ArchivedResult.date), Integer)
        query = self.session.query(distinct(year))
        query = query.order_by(desc(year))

        return [year for year, in query]

    def group_items(
        self,
        items: Collection[ArchivedResult],
        request: ElectionDayRequest
    ) -> dict[date, dict[str | None, dict[str, list[ArchivedResult]]]] | None:
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

        return groupbydict(
            items,
            lambda i: i.date,
            lambda i: -(as_datetime(i.date).timestamp() or 0),
            lambda i: groupbydict(
                i,
                lambda j: mapping.get(j.domain),
                lambda j: order.get(j.domain, 99),
                lambda j: groupbydict(
                    (item for item in j if item.url not in compounded),
                    lambda k: 'vote' if k.type == 'vote' else 'election'
                )
            )
        )

    def current(self) -> tuple[list[ArchivedResult], datetime | None]:
        """ Returns the current results.

        The current results are the results from either the next election day
        relative to today or the last results relative to today, if no next.

        """

        next_date = self.query().with_entities(func.min(ArchivedResult.date))
        next_date = next_date.filter(ArchivedResult.date >= date.today())
        current_date = next_date.scalar()

        if current_date is None:
            last_date = self.query().with_entities(
                func.max(ArchivedResult.date)
            )
            last_date = last_date.filter(ArchivedResult.date <= date.today())
            current_date = last_date.scalar()

        return self.by_date(current_date) if current_date else ([], None)

    def by_year(
        self,
        year: int
    ) -> tuple[list[ArchivedResult], datetime | None]:
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
        result = query.all()

        last_modifieds = [r.last_modified for r in result if r.last_modified]
        last_modified = max(last_modifieds) if last_modifieds else None

        return result, last_modified

    def by_date(
        self,
        date_: date | None = None
    ) -> tuple[list[ArchivedResult], datetime | None]:
        """ Returns the results of a given/current date. """

        if date_ is None:
            if self.date is None:
                return self.current()

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

        query = self.query()
        query = query.filter(ArchivedResult.date == date_)
        query = query.order_by(
            ArchivedResult.domain,
            ArchivedResult.name,
            ArchivedResult.shortcode,
            ArchivedResult.title
        )

        result = query.all()

        last_modifieds = [r.last_modified for r in result if r.last_modified]
        last_modified = max(last_modifieds) if last_modifieds else None

        return result, last_modified

    def update(
        self,
        item: Election | ElectionCompound | Vote,
        request: ElectionDayRequest,
        old: str | None = None
    ) -> ArchivedResult:
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
        result.title_translations = (
            item.short_title_translations
            or item.title_translations
        )
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
            if item.election_compound:
                self.update(item.election_compound, request)

        if isinstance(item, ElectionCompound):
            result.type = 'election_compound'
            result.elections = [
                request.link(election) for election in item.elections
            ]

        if isinstance(item, Vote):
            result.type = 'vote'
            result.turnout = item.turnout
            result.answer = item.answer or ''
            result.nays_percentage = item.nays_percentage
            result.yeas_percentage = item.yeas_percentage
            result.direct = item.direct

            if isinstance(item, ComplexVote):
                result.title_proposal_translations = (
                    item.title_translations or {}
                )
                ballot = item.proposal
                result.nays_percentage_proposal = ballot.nays_percentage
                result.yeas_percentage_proposal = ballot.yeas_percentage

                ballot = item.counter_proposal
                result.title_counter_proposal_translations = (
                    ballot.title_translations or {}
                )
                result.nays_percentage_counter_proposal = (
                    ballot.nays_percentage
                )
                result.yeas_percentage_counter_proposal = (
                    ballot.yeas_percentage
                )

                ballot = item.tie_breaker
                result.title_tie_breaker_translations = (
                    ballot.title_translations or {}
                )
                result.nays_percentage_tie_breaker = (
                    ballot.nays_percentage
                )
                result.yeas_percentage_tie_breaker = (
                    ballot.yeas_percentage
                    )

        if add_result:
            self.session.add(result)

        return result

    def update_all(self, request: ElectionDayRequest) -> None:
        """ Updates all (local) results. """

        schema = self.session.info['schema']

        for item in self.query().filter_by(schema=schema):
            self.session.delete(item)

        for election in ElectionCollection(self.session).query():
            self.update(election, request)

        for compound in ElectionCompoundCollection(self.session).query():
            self.update(compound, request)

        for vote in VoteCollection(self.session).query():
            self.update(vote, request)

    def add(
        self,
        item: Election | ElectionCompound | Vote,
        request: ElectionDayRequest
    ) -> None:
        """ Add a new election or vote and create a result entry.  """

        assert isinstance(item, (Election, ElectionCompound, Vote))

        self.session.add(item)
        self.session.flush()

        self.update(item, request)
        self.session.flush()

    def clear_results(
        self,
        item: Election | ElectionCompound | Vote,
        request: ElectionDayRequest,
        clear_all: bool = False
    ) -> None:
        """ Clears the result of an election or vote.  """

        assert isinstance(item, (Election, ElectionCompound, Vote))

        item.clear_results(clear_all)
        self.update(item, request)
        for election in getattr(item, 'elections', []):
            self.update(election, request)

        self.session.flush()

    def delete(
        self,
        item: Election | ElectionCompound | Vote,
        request: ElectionDayRequest
    ) -> None:
        """ Deletes an election or vote and the associated result entry.  """

        assert isinstance(item, (Election, ElectionCompound, Vote))

        url = request.link(item)
        url = replace_url(url, request.app.principal.official_host)
        for result in self.query().filter_by(url=url):
            self.session.delete(result)

        self.session.delete(item)
        self.session.flush()


class SearchableArchivedResultCollection(
    ArchivedResultCollection,
    Pagination[ArchivedResult]
):

    page: int

    def __init__(
            self,
            app: ElectionDayApp,
            date_: str | None = None,
            from_date: date | None = None,
            to_date: date | None = None,
            item_type: str | None = None,
            domains: list[str] | None = None,
            term: str | None = None,
            answers: list[str] | None = None,
            locale: str = 'de_CH',
            page: int = 0
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

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and self.page == other.page

    def subset(self) -> Query[ArchivedResult]:
        return self.query()

    @property
    def page_index(self) -> int:
        return self.page

    def page_by_index(self, index: int) -> Self:
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
    def term_to_tsquery_string(term: str | None) -> str:
        """ Returns the current search term transformed to use within
        Postgres ``to_tsquery`` function.
        Removes all unwanted characters, replaces prefix matching, joins
        word together using FOLLOWED BY.
        """

        def cleanup(word: str, whitelist_chars: str = ',.-_') -> str:
            result = ''.join(
                c for c in word if c.isalnum() or c in whitelist_chars
            )
            return f'{result}:*' if word.endswith('*') else result

        parts = (cleanup(part) for part in (term or '').split())
        return ' <-> '.join(part for part in parts if part)

    @staticmethod
    def match_term(
        column: ColumnElement[Any],
        language: str,
        term: str
    ) -> ColumnElement[TSVECTOR | None]:
        """ Generate a clause element for a given search term.

        Usage::

            model.filter(match_term(model.col, 'german', 'my search term'))
        """
        document_tsvector = func.to_tsvector(language, column)
        ts_query_object = func.to_tsquery(language, term)
        return document_tsvector.op('@@')(ts_query_object)

    @staticmethod
    def filter_text_by_locale(
        column: ColumnElement[Any],
        term: str,
        locale: str = 'en'
    ) -> ColumnElement[TSVECTOR | None]:
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
                   'rm_CH': 'english', 'en': 'english'}
        return SearchableArchivedResultCollection.match_term(
            column, mapping.get(locale, 'english'), term
        )

    @property
    def term_filter(self) -> tuple[
        ColumnElement[TSVECTOR | None],
        ColumnElement[TSVECTOR | None]
    ]:
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

    def query(self) -> Query[ArchivedResult]:
        query = self.session.query(ArchivedResult)

        if self.item_type:
            if self.item_type == 'election':
                query = query.filter(ArchivedResult.type.in_(
                    ('election', 'election_compound')
                ))

                # exclude elections already covered by election compounds
                exclude = [
                    item.split('/')[-1]
                    for items, in self.session.query(
                        ArchivedResult.meta['elections']
                    )
                    for item in items or ()
                ]
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
            case(  # type: ignore[call-overload]
                *(
                    (ArchivedResult.domain == domain, index)
                    for index, domain in enumerate(order, 1)
                )
            )
        )
        return query

    def reset_query_params(self) -> None:
        self.from_date = None
        self.to_date = date.today()
        self.item_type = None
        self.domains = None
        self.term = None
        self.answers = None
        self.locale = 'de_CH'

    @overload
    @classmethod
    def for_item_type(
        cls,
        app: ElectionDayApp,
        item_type: Literal['vote', 'election'],
        *,
        date_: str | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        domains: list[str] | None = None,
        term: str | None = None,
        answers: list[str] | None = None,
        locale: str = 'de_CH',
        page: int = 0
    ) -> Self: ...

    @overload
    @classmethod
    def for_item_type(
        cls,
        app: ElectionDayApp,
        item_type: str | None,
        *,
        date_: str | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        domains: list[str] | None = None,
        term: str | None = None,
        answers: list[str] | None = None,
        locale: str = 'de_CH',
        page: int = 0
    ) -> Self | None: ...

    @classmethod
    def for_item_type(
        cls,
        app: ElectionDayApp,
        item_type: str | None,
        *,
        date_: str | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        domains: list[str] | None = None,
        term: str | None = None,
        answers: list[str] | None = None,
        locale: str = 'de_CH',
        page: int = 0
    ) -> Self | None:
        if item_type in ('vote', 'election'):
            return cls(
                app,
                item_type=item_type,
                date_=date_,
                from_date=from_date,
                to_date=to_date,
                domains=domains,
                term=term,
                answers=answers,
                locale=locale,
                page=page,

            )
        return None
