""" Provides commands related to the onegov.search. """
from __future__ import annotations

import click

from onegov.core.cli import command_group, pass_group_context
from onegov.search.search_index import SearchIndex
from onegov.search.utils import apply_searchable_polymorphic_filter
from operator import attrgetter
from sedate import utcnow
from sqlalchemy import func


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable
    from onegov.core.cli.core import GroupContext
    from onegov.core.framework import Framework
    from onegov.core.request import CoreRequest
    from onegov.search.integration import SearchApp


cli = command_group()


def psql_index_status(app: SearchApp) -> None:
    """ Prints the percentage of indexed documents per model. """

    success = 1  # 1 = OK, 2 = WARNING, 3 = ERROR
    session = app.session()

    index_counts = dict(session.query(
        SearchIndex.owner_tablename,
        func.count(SearchIndex.id)
    ).group_by(SearchIndex.owner_tablename))

    click.echo(f'| Status | {"Tablename": <40} | Indexed | No. docs |')
    click.echo(f'|--------|-{"---------":-<40}-|---------|----------|')

    for model in sorted(
        app.indexable_base_models(),
        key=attrgetter('__tablename__')
    ):
        tablename = model.__tablename__
        # FIXME: Replace this with a func.count query too by replacing
        #        fts_skip with a hybrid_property
        count = sum(
            1
            for obj in apply_searchable_polymorphic_filter(
                session.query(model),
                model
            )
            if not getattr(obj, 'fts_skip', False)
        )
        if not count:
            # nothing to index, so we indexed it all
            percentage = 100.0
        else:
            percentage = index_counts.get(tablename, 0) / count * 100.0

        if 10.0 <= percentage < 90.0:
            status = click.style(' WARN ', fg='yellow')
            success = max(success, 2)
        elif percentage < 10.0:
            status = click.style('  ERR ', fg='red')
            success = max(success, 3)
        else:
            status = click.style('  OK  ', fg='green')
        click.echo(
            f'| {status} | {tablename:<40} | {percentage: >6.2f}% | '
            f' {count:>7} |',
        )

    if success == 1:
        click.secho('Indexing status check OK', fg='green')
    elif success == 2:
        click.secho('Indexing status check WARNING', fg='yellow')
    elif success == 3:
        click.secho('Indexing status check NOT OK', fg='red')


@cli.command(context_settings={'default_selector': '*'})
@click.option('--fail', is_flag=True, default=False, help='Fail on errors')
@pass_group_context
def reindex(
    group_context: GroupContext,
    fail: bool
) -> Callable[[CoreRequest, Framework], None]:
    """ Reindexes all objects in the search index. """

    def run_reindex(request: CoreRequest, app: Framework) -> None:
        if not getattr(request.app, 'fts_search_enabled', False):
            return

        title = f'Reindexing {request.app.application_id}'
        click.secho(title, underline=True)

        start = utcnow()
        request.app.perform_reindex(fail)  # type:ignore[attr-defined]

        click.secho(f'took {utcnow() - start}')

    return run_reindex


@cli.command(context_settings={'default_selector': '*'})
@pass_group_context
def index_status(
    group_context: GroupContext
) -> Callable[[CoreRequest, Framework], None]:
    """ Prints the status of the search index. """

    def run_index_status(request: CoreRequest, app: Framework) -> None:
        if not getattr(request.app, 'fts_search_enabled', False):
            return

        title = f'Index status of {app.application_id}'
        click.secho(title, underline=True)

        psql_index_status(app)  # type: ignore[arg-type]

    return run_index_status
