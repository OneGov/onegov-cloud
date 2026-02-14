from __future__ import annotations

import math

from functools import cached_property
from onegov.core.collection import Pagination
from onegov.core.orm.types import MarkupText
from onegov.event.models import Event
from onegov.search import SearchIndex
from onegov.search.utils import language_from_locale
from markupsafe import Markup
from operator import itemgetter
from sedate import align_date_to_day, as_datetime, replace_timezone, utcnow
from sqlalchemy import case, func, inspect, type_coerce
from sqlalchemy_utils import escape_like


from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from collections.abc import Iterable
    from datetime import date
    from onegov.org.request import OrgRequest
    from onegov.search import Searchable
    from sqlalchemy.orm import Query
    from uuid import UUID
    from wtforms.fields.choices import _Choice


class Search(Pagination[Any]):
    results_per_page = 10
    TYPE_LABEL_TEMPLATE = Markup(
        '<span class="with-count" data-count="{count}">{label}</span>'
    )

    def __init__(
        self,
        request: OrgRequest,
        query: str,
        types: Iterable[str] | str | None = None,
        start: date | None = None,
        end: date | None = None,
        page: int = 0,
    ) -> None:
        self.request = request
        self.query = query
        self.types = (
            {types}
            if types and isinstance(types, str)
            else set(types or ())
        )
        self.start = start
        self.end = end
        self.page = page  # page index

        self.number_of_results: int | None = None

    # for morepath link generation
    @cached_property
    def type(self) -> list[str] | None:
        return list(self.types) if self.types else None

    @cached_property
    def available_documents(self) -> int:
        return sum(self.available_documents_per_type.values())

    @cached_property
    def available_documents_per_type(self) -> dict[str, int]:
        return dict(self.apply_common_filters(
            self.request.session.query(
                SearchIndex.owner_type,
                func.count(SearchIndex.id)
            ),
            with_type_filter=False
        ).group_by(SearchIndex.owner_type))

    @cached_property
    def document_type_filter_labels(self) -> dict[str, set[str]]:
        type_map = {
            model.__name__: model
            for model in self.request.app.searchable_models()
        }
        types_with_results = {
            type_name: count
            for type_name, count in self.available_documents_per_type.items()
            if count > 0
            if type_name in type_map
        }
        if not types_with_results:
            return {}

        labels: dict[str, set[str]] = {}
        for type_name in types_with_results:
            title = type_map[type_name].fts_type_title
            if callable(title):
                title = title(self.request)
            label = self.request.translate(title)
            labels.setdefault(label, set()).add(type_name)
        return labels

    @cached_property
    def document_type_filter_choices(self) -> list[_Choice]:
        return [
            (
                label,
                self.TYPE_LABEL_TEMPLATE.format(
                    label=label,
                    count=sum(
                        self.available_documents_per_type[type_name]
                        for type_name in type_names
                    )
                ),
            )
            for label, type_names in sorted(
                self.document_type_filter_labels.items(),
                key=itemgetter(0)
            )
        ]

    @cached_property
    def available_results(self) -> int:
        if self.number_of_results is None:
            _ = self.batch
            assert self.number_of_results is not None
        return self.number_of_results

    @property
    def q(self) -> str:
        """
        Returns the user's query term from the search field of the UI

        """
        return self.query

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Search):
            return NotImplemented
        return self.page == other.page and self.query == other.query

    def subset(self) -> Query[Any]:
        if self.query.startswith('#'):
            return self.hashtag_search()
        else:
            return self.generic_search()

    @property
    def page_index(self) -> int:
        return self.page

    def page_by_index(self, index: int) -> Search:
        return Search(
            self.request,
            self.query,
            self.types,
            self.start,
            self.end,
            index
        )

    @cached_property
    def batch(self) -> tuple[Any, ...]:
        if not self.query.lstrip('#'):
            self.number_of_results = 0
            return ()

        query = self.cached_subset

        # compute the number of results for this query
        self.number_of_results = (
            query
            # remove order for speed
            .order_by(None)
            .with_entities(func.count(SearchIndex.id))
            .scalar()
        )
        return self.load_batch(query)

    @cached_property
    def load_batch_results(self) -> tuple[Any, ...]:
        """
        Load search results and sort upcoming events by occurrence start date.
        """
        batch = self.batch

        # FIXME: This is highly questionable, we probably should add a time
        #        decayed portion to the result ranking instead (we already
        #        had one, but it's too agressive compared to ElasticSearch,
        #        we should apply the same Gaussian decay we did before but
        #        make sure we only do that for records where the time portion
        #        actually is an indicator for relevancy, some documents will
        #        never or rarely change and remain eternally relevant)
        future_events: list[Event] = []
        other: list[Searchable] = []
        for search_result in batch:
            if (isinstance(search_result, Event)
                    and search_result.latest_occurrence
                    and search_result.latest_occurrence.start > utcnow()):
                future_events.append(search_result)
            else:
                other.append(search_result)

        if not future_events:
            return batch

        future_events.sort(
            key=lambda e: e.latest_occurrence.start,  # type:ignore[union-attr]
            reverse=True
        )
        return (*future_events, *other)

    def apply_common_filters(
        self,
        query: Any,
        with_type_filter: bool = True
    ) -> Any:
        """ Applies common search filters like e.g. access filters. """
        private_search = self.request.app.fts_may_use_private_search(
            self.request
        )
        # FIXME: This doesn't handle elevated/downgaraded permissions properly
        #        yet like access to tickets by user group. We could add a new
        #        column `groupids` to the search index if a particular result
        #        should bypass regular access checks for non-admins and check
        #        if at least one of the groups match instead.
        role = getattr(self.request.identity, 'role', 'anonymous')
        available_accesses = {
            'admin': (),  # can see everything
            'editor': (),  # can see everything
            # FIXME: For mtan access to work properly we probably need to
            #        split public and private content, so you can still find
            #        an object by it's public name, but not via data that
            #        should only be visible once authenticated.
            'supporter': ('member', 'public'),  # TODO: 'mtan'
            'member': ('member', 'public')  # TODO: 'mtan'
        }.get(role, ('public',))  # TODO: 'mtan'
        if not available_accesses and not private_search:
            # downgrade access level if private search is not possible
            available_accesses = ('member', 'public')
        if available_accesses:
            query = query.filter(SearchIndex.access.in_(available_accesses))
            query = query.filter(SearchIndex.published)

        # FIXME: We may need to redesign this a little, for starters we
        #        probably want to flip this boolean from public to private
        #        in order to make it less confusing and make sure that
        #        the boolean is only set for models we want to be affected
        #        by the outcome of this method.
        if not private_search:
            query = query.filter(SearchIndex.public)

        if with_type_filter:
            labels = self.document_type_filter_labels
            types = {
                type_name
                for label in self.types
                for type_name in labels.get(label, ())
            }
            if types:
                query = query.filter(SearchIndex.owner_type.in_(types))

        if self.start is not None:
            # NOTE: This will need to change if we allow different timezones
            #       but when we do, we should probably store it on the request
            #       rather than our layouts.
            start = replace_timezone(as_datetime(self.start), 'Europe/Zurich')
            query = query.filter(SearchIndex.last_change >= start)

        if self.end is not None:
            # NOTE: This will need to change if we allow different timezones
            #       but when we do, we should probably store it on the request
            #       rather than our layouts.
            end = replace_timezone(as_datetime(self.end), 'Europe/Zurich')
            end = align_date_to_day(end, 'Europe/Zurich', 'up')
            query = query.filter(SearchIndex.last_change <= end)

        return query

    @cached_property
    def language(self) -> str:
        language = self.request.locale
        if language_from_locale(language) == 'simple':
            return 'simple'
        return language or 'simple'

    def generic_search(self) -> Query[SearchIndex]:
        ts_query = func.websearch_to_tsquery(self.language, self.query)

        decay = 0.99
        scale = (90 * 24 * 3600)  # 90 days to reach target decay
        offset = (7 * 24 * 3600)  # 7 days without decay
        two_times_variance_squared = -(scale**2 / math.log(decay))
        query = self.request.session.query(SearchIndex).filter(
            SearchIndex.data_vector.op('@@')(ts_query)
        ).order_by(
            (
                (
                    100.0 * func.ts_rank(
                        SearchIndex.title_vector,
                        ts_query,
                    ) + func.ts_rank_cd(
                        SearchIndex.data_vector,
                        ts_query,
                        2 | 4 | 16
                    )
                )
                # FIXME: We could probably improve performance a lot if
                #        we stored the time decay in the search table and
                #        recomputed it once a day in a crobjob
                * func.greatest(
                    func.exp(
                        -func.greatest(
                            func.abs(
                                func.extract(
                                    'epoch',
                                    utcnow() - func.coalesce(
                                        SearchIndex.last_change,
                                        utcnow()
                                    )
                                )
                            ) - offset,
                            0
                        ).op('^')(2) / two_times_variance_squared
                    ),
                    1e-6
                )
                # HACK: We may want to add some fts_rank_modifier property
                #       to searchable models instead and add a column to
                #       the index for that, that would allow us to weigh
                #       results per type more effectively. Currently files
                #       are he most egregious offender though, so we just
                #       hardcode this into the query.
                * case(
                    (SearchIndex.owner_tablename == 'files', 0.1),
                    # NOTE: Tickets may be excluded entirely in the
                    #       future but for now we'll de-prioritize them
                    (SearchIndex.owner_tablename == 'tickets', 0.2),
                    else_=1.0
                )
            ).desc().label('rank')
        )
        return self.apply_common_filters(query)

    def hashtag_search(self) -> Query[SearchIndex]:
        tag = self.query.lstrip('#')
        query = self.request.session.query(SearchIndex)
        query = query.filter(SearchIndex._tags.any_() == tag)
        # TODO: Do we want to order results in some way?
        return self.apply_common_filters(query)

    def load_batch(self, query: Query[SearchIndex]) -> tuple[Searchable, ...]:
        batch: list[tuple[str, UUID | int | str]]
        batch = [
            (
                tablename,
                id_uuid if id_uuid is not None else (
                id_int if id_int is not None else
                id_str)
            )
            for tablename, id_uuid, id_int, id_str in query.with_entities(
                SearchIndex.owner_tablename,
                SearchIndex.owner_id_uuid,
                SearchIndex.owner_id_int,
                SearchIndex.owner_id_str
            ).offset(self.offset).limit(self.results_per_page)
        ]
        if not batch:
            return ()

        table_batches: dict[str, set[UUID | int | str]] = {}
        for tablename, owner_id in batch:
            table_batches.setdefault(tablename, set()).add(owner_id)

        indexable_base_models = {
            model.__tablename__: model
            for model in self.request.app.indexable_base_models()
        }

        results_by_id: dict[UUID | int | str, Searchable] = {}
        for tablename, table_batch in table_batches.items():
            base_model = indexable_base_models.get(tablename)
            if base_model is None:
                # NOTE: We might want to log this, although this should
                #       only ever happen if the search index is out of
                #       date and contains entries for tables that have
                #       since been removed.
                continue

            primary_key, = inspect(base_model).primary_key  # type: ignore[union-attr]

            results_by_id.update(
                self.request.session.query(primary_key, base_model)
                .filter(primary_key.in_(table_batch))
            )

        return tuple(
            result
            for __, owner_id in batch
            if (result := results_by_id.get(owner_id)) is not None
        )

    def feeling_lucky(self) -> str | None:
        # FIXME: make this actually return a random result
        if self.batch:
            first_entry = self.batch[0]

            # XXX the default view to the event should be doing the redirect
            if isinstance(first_entry, Event):
                return self.request.link(first_entry, 'latest')
            else:
                return self.request.link(first_entry)
        return None

    @cached_property
    def subset_count(self) -> int:
        return self.available_results

    def suggestions(self) -> tuple[str, ...]:
        if not self.query:
            return ()

        number_of_suggestions = 15

        if self.query.startswith('#'):  # hashtag search
            q = self.query.lstrip('#').lower()
            subquery = self.apply_common_filters(
                self.request.session.query(
                    func.unnest(
                        SearchIndex._tags
                    ).label('tag')
                ).distinct()
            ).subquery()
            query = self.request.session.query(subquery.c.tag)
            if len(q) >= 0:
                query = query.filter(func.unaccent(subquery.c.tag).ilike(
                    func.unaccent(f'{escape_like(q)}%'),
                    '*'
                ))
            return tuple(
                f'#{tag}'
                for tag, in query
                .order_by(subquery.c.tag.asc())
                .limit(number_of_suggestions)
            )
        else:
            subquery = self.apply_common_filters(
                self.request.session.query(
                    func.unnest(
                        SearchIndex.suggestion
                    ).label('suggestion')
                ).distinct()
            ).subquery()
            # FIXME: This could be a lot faster if suggestions were
            #        their own table, we also don't handle language
            #        specific normalization of accents/umlauts yet
            #        for auto-complete
            return tuple(
                suggestion
                for suggestion, in self.request.session
                .query(subquery.c.suggestion)
                .filter(func.unaccent(subquery.c.suggestion).ilike(
                    func.unaccent(f'{escape_like(self.query)}%'),
                    '*'
                ))
                .order_by(subquery.c.suggestion.asc())
                .limit(number_of_suggestions)
            )

    def highlight_results(self, markup: Markup) -> Markup:
        return self.request.session.query(
            type_coerce(
                func.ts_headline(
                    self.language,
                    markup,
                    func.websearch_to_tsquery(self.language, self.query),
                    'HighlightAll=true, StartSel=<em>, StopSel=</em>'
                ),
                MarkupText
            )
        ).one()[0]
