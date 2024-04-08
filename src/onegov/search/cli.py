""" Provides commands related to the onegov.search. """

import click

from onegov.core.cli import command_group, pass_group_context
from sedate import utcnow


cli = command_group()


def psql_index_status(app):
    """ Prints the percentage of indexed documents per model. """

    success = True
    models = app.get_searchable_models()
    session = app.session()

    for model in models:
        try:
            q = session.query(model.fts_idx)
            total = q.count()
            if total == 0:
                continue  # empty table
        except Exception as e:
            click.secho(f'ERROR {e} model {model} has no fts_idx column ('
                        f'Hint: has upgrade step being executed?)', fg='red')
            success = False
            continue

        set_ftx = q.filter(model.fts_idx != None).count()
        percentage = set_ftx / total * 100
        if percentage < 60:
            click.secho(f'ERROR Percentage of indexed documents of model '
                        f'{model} is low: {percentage:.2f}% (Hint: has '
                        f'reindex step being executed?)', fg='red')
            success = False
        else:
            click.secho(f'Percentage of indexed documents of model '
                        f'{model} is {percentage:.2f}%')

    if not success:
        click.secho('Indexing status check NOT OK', fg='red')
    else:
        click.secho('Indexing status check OK', fg='green')


@cli.command(context_settings={'default_selector': '*'})
@click.option('--fail', is_flag=True, default=False, help='Fail on errors')
@pass_group_context
def reindex(group_context, fail):
    """ Reindexes all objects in the elasticsearch and psql database. """

    def run_reindex(request, app):
        if not hasattr(request.app, 'es_client'):
            return

        title = f"Reindexing {request.app.application_id}"
        click.secho(title, underline=True)

        start = utcnow()
        request.app.es_perform_reindex(fail)

        click.secho(f"took {utcnow() - start}")

    return run_reindex


@cli.command(context_settings={'default_selector': '*'})
@pass_group_context
def index_status(group_context):
    """ Prints the status of the psql index. """

    def run_index_status(request, app):
        if not hasattr(request.app, 'es_client'):
            return

        title = f"Index status of {request.app.application_id}"
        click.secho(title, underline=True)

        psql_index_status(app)

    return run_index_status
