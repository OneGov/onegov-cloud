""" Provides commands related to the onegov.search. """

import click

from onegov.core.cli import command_group, pass_group_context
from sedate import utcnow
from sqlalchemy import func, text

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from onegov.core.cli.core import GroupContext
    from onegov.core.framework import Framework
    from onegov.core.request import CoreRequest
    from onegov.search.mixins import Searchable

cli = command_group()


def psql_index_status(app: 'Framework') -> None:
    """ Prints the percentage of indexed documents per model. """

    success = 1  # 1 = OK, 2 = WARNING, 3 = ERROR
    models = app.get_searchable_models()  # type:ignore[attr-defined]
    session = app.session()

    model: type[Searchable]
    for model in models:
        try:
            q = session.query(model.fts_idx)
            if not session.query(q.exists()).scalar():
                continue  # empty table
        except Exception as e:
            click.secho(f'ERROR {e} model {model} has no fts_idx column ('
                        f'Hint: has upgrade step been executed?)', fg='red')
            success = 3
            continue

        q = session.query(model).with_entities(func.count(text('*')))
        count = q.scalar()
        q = session.query(func.count(model.fts_idx))
        ftx_set = q.filter(model.fts_idx.isnot(None)).scalar()
        percentage = ftx_set / count * 100
        if 10 <= percentage < 90:
            click.secho(f'WARNING Percentage of {count} indexed '
                        f'documents of model {model} is low: '
                        f'{percentage:.2f}% (Hint: has reindex step been '
                        f'executed?)')
            success = 2 if success < 2 else success
        elif percentage < 10:
            click.secho(f'ERROR Percentage of {count} indexed '
                        f'documents of model {model} is very low: '
                        f'{percentage:.2f}% (Hint: has reindex step been '
                        f'executed?)')
            success = 3 if success < 3 else success
        else:
            click.secho(f'Percentage of {count} indexed documents of model '
                        f'{model} is {percentage:.2f}%')

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
    group_context: 'GroupContext',
    fail: bool
) -> 'Callable[[CoreRequest, Framework], None]':
    """ Reindexes all objects in the elasticsearch and psql database. """

    def run_reindex(request: 'CoreRequest', app: 'Framework') -> None:
        if not hasattr(request.app, 'es_client'):
            return

        title = f"Reindexing {request.app.application_id}"
        click.secho(title, underline=True)

        start = utcnow()
        request.app.perform_reindex(fail)  # type:ignore[attr-defined]

        click.secho(f"took {utcnow() - start}")

    return run_reindex


@cli.command(context_settings={'default_selector': '*'})
@pass_group_context
def index_status(
    group_context: 'GroupContext'
) -> 'Callable[[CoreRequest, Framework], None]':
    """ Prints the status of the psql index. """

    def run_index_status(request: 'CoreRequest', app: 'Framework') -> None:
        if not hasattr(request.app, 'es_client'):
            return

        title = f"Index status of {request.app.application_id}"
        click.secho(title, underline=True)

        psql_index_status(app)

    return run_index_status
