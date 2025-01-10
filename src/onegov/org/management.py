import re
import time
from sqlalchemy import Integer
import transaction
from sqlalchemy import text, bindparam, String
from collections import defaultdict
from aiohttp import ClientTimeout
from sqlalchemy.orm import object_session
from urlextract import URLExtract
from onegov.async_http.fetch import async_aiohttp_get_all
from onegov.core.utils import normalize_for_url
from dataclasses import dataclass, field
from onegov.org.models import SiteCollection
from onegov.people import AgencyCollection


from typing import Literal, NamedTuple, TYPE_CHECKING, Tuple, Dict

if TYPE_CHECKING:
    from collections.abc import Iterator
    from collections.abc import Iterable, Sequence
    from onegov.form import Form
    from onegov.org.request import OrgRequest
    from onegov.page import Page
    from typing import Self


sample_size = 5


class ModelsWithLinksMixin:
    fields_with_urls = ('lead', 'text', 'url')

    if TYPE_CHECKING:
        request: OrgRequest

    @property
    def site_collection(self) -> SiteCollection:
        return SiteCollection(self.request.session)


class LinkMigration(ModelsWithLinksMixin):

    def __init__(
        self,
        request: 'OrgRequest',
        old_uri: str,
        new_uri: str = '',
        use_domain: bool = True
    ) -> None:

        self.request = request
        self.old_uri = old_uri
        self.new_uri = new_uri
        self.use_domain = use_domain

        if use_domain:
            old_is_domain = not self.old_uri.startswith('http')
            new_is_domain = not self.new_uri.startswith('http')

            if old_is_domain != new_is_domain:
                raise ValueError('Domains must be consistent')

    def migrate_url(
        self,
        item: object,
        fields_with_urls: 'Iterable[str]',
        test: bool = False,
        group_by: str | None = None,
        count_obj: dict[str, dict[str, int]] | None = None
    ) -> tuple[int, dict[str, dict[str, int]]]:
        """Supports replacing url's and domain names.

        """
        count = 0
        count_by_id = count_obj or {}

        old_uri = self.old_uri
        new_uri = self.new_uri
        group_by = group_by or item.__class__.__name__

        def repl(matchobj: re.Match[str]) -> str:
            if self.use_domain:
                return f'{matchobj.group(1)}{new_uri}'
            return new_uri

        if self.use_domain:
            # Prevent replacing things that might not be an url
            pattern = re.compile(r'(https?://)' + f'({re.escape(old_uri)})')
        else:
            pattern = re.compile(re.escape(old_uri))

        for _field in fields_with_urls:
            value = getattr(item, _field, None)
            if not value:
                continue
            new_val = pattern.sub(repl, value)
            if value != new_val:
                count += 1
                id_count = count_by_id.setdefault(
                    group_by,
                    defaultdict(int)
                )

                id_count[_field] += 1
                if not test:
                    setattr(
                        item,
                        _field,
                        new_val
                    )
        return count, count_by_id

    def migrate(
        self,
        test: bool = False
    ) -> tuple[int, dict[str, dict[str, int]], 'MigrationReportData']:
        total, grouped = self.migrate_site_collection(test=test)

        report = self.migrate_content_mixin()
        return total, grouped, report

    def migrate_site_collection(
        self,
        test: bool = False
    ) -> tuple[int, dict[str, dict[str, int]]]:

        grouped: dict[str, dict[str, int]] = {}
        total = 0

        for entries in self.site_collection.get().values():
            for item in entries:
                count, grouped_count = self.migrate_url(
                    item, self.fields_with_urls,
                    test=test,
                    count_obj=grouped
                )
                grouped = grouped_count
                total += count
        return total, grouped

    def analyze_table_changes(
        self,
        table: str,
        columns: list[str],
    ) -> 'TableMigrationData':
        """Analyze changes that would be made to a table without executing
        updates."""
        column_data = []
        errors = 0
        warnings = []

        for col in columns:
            is_json = col in {'meta', 'content', 'snapshot'}
            count_sql = generate_count_sql(table, col, is_json)

            try:
                pattern = f'%{self.old_uri}%'
                result = self.request.session.execute(
                    text(count_sql).bindparams(
                        bindparam('pattern', type_=String),
                        bindparam('sample_size', type_=Integer)
                    ),
                    {
                        'pattern': pattern,
                        'sample_size': sample_size
                    },
                ).fetchone()

                count, samples = result if result else (0, [])
                samples = samples or []
                column_data.append(
                    ColumnMigrationData(
                        name=col,
                        affected_rows=count,
                        sample_values=samples,
                        is_json=is_json,
                    )
                )

            except Exception as e:
                errors += 1
                warnings.append(f'Error analyzing {col}: {e!s}')

        return TableMigrationData(
            name=table,
            columns=column_data,
            total_rows=sum(col.affected_rows for col in column_data),
            error_count=errors,
            warnings=warnings,
        )

    def execute_table_update(self, table: str, columns: list[str]) -> None:
        """Execute the actual update for a table."""
        update_sql = generate_update_sql(table, columns)
        self.request.session.execute(
            text(update_sql).bindparams(
                bindparam('old_uri', type_=String),
                bindparam('new_uri', type_=String),
            ),
            {'old_uri': self.old_uri, 'new_uri': self.new_uri},
        )

    def migrate_content_mixin(
        self, test_only: bool = True
    ) -> 'MigrationReportData':
        """Analyze or execute content migration based on test_only flag.

        Automates the process of emitting sql statements to update content like
        we used to do manually:

        update pages set content = replace(content::text, 'old', 'new')::jsonb;
        update forms set meta = replace(meta::text, 'old', 'new')::jsonb;
        """
        updates = [
            ('pages', ['meta', 'content']),
            ('forms', ['meta', 'content']),
            ('events', ['meta', 'content']),
            ('resources', ['meta', 'content']),
            ('people', ['meta', 'content', 'picture_url']),
            ('organisations', ['meta', 'logo_url']),
            ('directories', ['content']),
            ('tickets', ['snapshot']),
            ('external_links', ['url']),
        ]

        tables_data = []

        for table, columns in updates:
            # Always analyze changes first
            table_data = self.analyze_table_changes(table, columns)
            tables_data.append(table_data)

            # Execute update if not in test mode and there are changes
            if not test_only and table_data.total_affected > 0:
                try:
                    self.execute_table_update(table, columns)
                except Exception as e:
                    table_data.error_count += 1
                    table_data.warnings.append(
                        f'Error updating table: {e!s}'
                    )

        if not test_only:
            transaction.commit()

        return MigrationReportData(
            old_uri=self.old_uri,
            new_uri=self.new_uri,
            tables=tables_data,
            is_dry_run=test_only,
        )


@dataclass
class ColumnMigrationData:
    name: str
    affected_rows: int
    sample_values: list[
        str
    ]  # Store some example values that would be changed
    is_json: bool


@dataclass
class TableMigrationData:
    name: str
    columns: list[ColumnMigrationData]
    total_rows: int
    error_count: int = 0
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.warnings = self.warnings or []

    @property
    def total_affected(self) -> int:
        return sum(col.affected_rows for col in self.columns)


@dataclass
class MigrationReportData:
    old_uri: str
    new_uri: str
    tables: list[TableMigrationData]
    is_dry_run: bool

    @property
    def total_affected_rows(self) -> int:
        return sum(table.total_affected for table in self.tables)


def generate_count_sql(
    table: str,
    column: str,
    is_json: bool = False,
) -> str:
    """Generate SQL to count and sample rows that would be affected.
    """
    # Base content selection varies based on JSON status
    content_select = (
        f'{column}::text as content' if is_json else f'{column} as content'
    )

    return f"""  # nosec[B608]
        WITH affected AS (
            SELECT {content_select}
            FROM {table}
            WHERE {column}{'::text' if is_json else ''} LIKE :pattern
        )
        SELECT COUNT(*) as count,
               array_agg(content) FILTER (
                   WHERE content IN (
                       SELECT content
                       FROM affected
                       ORDER BY random()
                       LIMIT :sample_size
                   )
               ) as samples
        FROM affected
    """


def generate_update_sql(table: str, columns: list[str]) -> str:
    """Generate the update SQL statement for a table."""

    def json_replace_expression(col: str) -> str:
        return f'{col} = replace({col}::text, :old_uri, :new_uri)::jsonb'

    def text_replace_expression(col: str) -> str:
        return f'{col} = replace({col}, :old_uri, :new_uri)'

    sql_parts = []
    for col in columns:
        if col in {'meta', 'content', 'snapshot'}:
            sql_parts.append(json_replace_expression(col))
        else:
            sql_parts.append(text_replace_expression(col))

    return f"UPDATE {table} SET {', '.join(sql_parts)}"  # nosec[B608]


class PageNameChange(ModelsWithLinksMixin):

    def __init__(
        self,
        request: 'OrgRequest',
        page: 'Page',
        new_name: str
    ) -> None:

        assert new_name == normalize_for_url(new_name)
        assert page.name != new_name

        self.request = request
        self.page = page
        self.new_name = new_name

    @property
    def subpages(self) -> list['Page']:
        pages: list[Page] = []

        def add(page: 'Page') -> None:
            nonlocal pages
            pages.append(page)
            for child in page.children:
                add(child)

        for p in self.page.children:
            add(p)

        return pages

    def execute(self, test: bool = False) -> int:
        """ Executes a page name change. All subpages' urls are changed by
        this action. For all subpages, the old and new url must be swapped in
        all possible fields of all sites of the SiteCollection.
        """

        page = self.page
        subpages = self.subpages
        old_name = page.name

        def run() -> int:
            # Make sure the order before and after is the same
            urls_before = tuple(
                self.request.link(p) for p in (*subpages, page))
            page.name = self.new_name
            urls_after = tuple(self.request.link(p) for p in (*subpages, page))
            assert urls_before != urls_after

            count = 0
            for before, after in zip(urls_before, urls_after):
                migration = LinkMigration(self.request, before, after)
                total, _ = migration.migrate(test=test)
                count += total
            return count

        if test:
            with object_session(page).no_autoflush:
                counter = run()
                page.name = old_name
                transaction.abort()
                return counter
        return run()

    @classmethod
    def from_form(cls, model: 'Page', form: 'Form') -> 'Self':
        return cls(form.request, model, form['name'].data)  # type:ignore


class LinkCheck:
    def __init__(self, name: str, link: str, url: str) -> None:
        self.name = name
        self.link = link
        self.url = self.ensure_protocol(url)
        self.status: int | None = None
        self.message: str | None = None

    def ensure_protocol(self, url: str) -> str:
        if not url.startswith('http'):
            return 'https://' + url
        return url


class LinkHealthCheck(ModelsWithLinksMixin):
    """
    Check either internal or external urls for status 200.
    """

    class Statistic(NamedTuple):
        total: int
        ok: int
        nok: int
        error: int
        duration: float

    def __init__(
        self,
        request: 'OrgRequest',
        link_type: Literal['internal', 'external', ''] | None = None,
        total_timout: float = 30
    ) -> None:
        """
        :param request: morepath request object
        :param external_only: check external links not matching current domain
        :param total_timout: timout for all requests in seconds
        """
        self.request = request
        if link_type:
            assert link_type in ('internal', 'external')

        self.link_type = link_type or None
        self.domain = self.request.domain
        self.extractor = URLExtract()

        self.timeout = ClientTimeout(
            total=total_timout
        )

    @property
    def internal_only(self) -> bool:
        return self.link_type == 'internal'

    @property
    def external_only(self) -> bool:
        return self.link_type == 'external'

    def internal_link(self, url: str) -> bool:
        return self.domain in url

    def filter_urls(self, urls: 'Sequence[str]') -> 'Sequence[str]':
        if self.external_only:
            return tuple(url for url in urls if not self.internal_link(url))
        if self.internal_only:
            return tuple(url for url in urls if self.internal_link(url))
        return urls

    def find_urls(self) -> 'Iterator[tuple[str, str, Sequence[str]]]':
        for entries in self.site_collection.get().values():
            for entry in entries:
                urls = []
                for field in self.fields_with_urls:
                    text = getattr(entry, field, None)
                    if not text:
                        continue
                    found = self.extractor.find_urls(text, only_unique=True)
                    if not found:
                        continue
                    urls += found
                if urls:
                    yield (
                        entry.__class__.__name__,
                        self.request.link(entry),
                        self.filter_urls(urls)
                    )
        for agency in AgencyCollection(self.request.session).query():
            urls = self.extractor.find_urls(agency.portrait, only_unique=True)
            if urls:
                yield (
                    'Agency',
                    self.request.link(agency),
                    self.filter_urls(urls)
                )

    def url_list_generator(self) -> 'Iterator[LinkCheck]':
        for name, model_link, urls in self.find_urls():
            for url in urls:
                yield LinkCheck(name, model_link, url)

    def unhealthy_urls(self) -> tuple[Statistic, 'Sequence[LinkCheck]']:
        """ We check the urls in the backend, unless they are internal.
        In that case, we can not do that since we do not have async support.
        Otherwise returns the LinkChecks with empty statistics for use in
        the frontend.
        """
        assert self.link_type, 'link_type must be set'
        started = time.time()

        total_count = 0
        error_count = 0
        not_okay_status = 0

        def handle_errors(check: LinkCheck, exception: Exception) -> LinkCheck:
            nonlocal total_count
            nonlocal error_count
            check.message = str(exception)
            total_count += 1
            error_count += 1
            return check

        def on_success(check: LinkCheck, status: int) -> LinkCheck:
            nonlocal total_count
            nonlocal not_okay_status
            check.status = status
            check.message = f'Status {status}'
            total_count += 1
            if status != 200:
                not_okay_status += 1
            return check

        urls: Sequence[LinkCheck]
        if self.link_type == 'external':
            urls = async_aiohttp_get_all(
                urls=tuple(self.url_list_generator()),
                response_attr='status',
                callback=on_success,
                handle_exceptions=handle_errors,
                timeout=self.timeout
            )
            stats = self.Statistic(
                total=total_count,
                error=error_count,
                nok=not_okay_status,
                ok=total_count - error_count - not_okay_status,
                duration=time.time() - started
            )
        else:
            urls = tuple(self.url_list_generator())
            stats = self.Statistic(
                total=0,
                error=0,
                nok=0,
                ok=0,
                duration=time.time() - started
            )

        return stats, tuple(check for check in urls if check.status != 200)
