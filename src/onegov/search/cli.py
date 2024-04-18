""" Provides commands related to the onegov.search. """

import click

from onegov.core.cli import command_group, pass_group_context
from sedate import utcnow


cli = command_group()


def psql_index_status(app):
    """ Prints the percentage of indexed documents per model. """

    success = 1  # 1 = OK, 2 = WARNING, 3 = ERROR
    count = 0
    models = app.get_searchable_models()
    session = app.session()

    for model in models:
        try:
            q = session.query(model.fts_idx)
            count = q.count()
            if count == 0:
                continue  # empty table
        except Exception as e:
            click.secho(f'ERROR {e} model {model} has no fts_idx column ('
                        f'Hint: has upgrade step being executed?)', fg='red')
            success = 3
            continue

        ftx_set = q.filter(model.fts_idx != None).count()
        percentage = ftx_set / count * 100
        if 10 <= percentage < 90:
            click.secho(f'WARNING Percentage of {count} indexed '
                        f'documents of model {model} is low: '
                        f'{percentage:.2f}% (Hint: has reindex step being '
                        f'executed?)')
            success = 2 if success < 2 else success
        elif percentage < 10:
            click.secho(f'ERROR Percentage of {count} indexed '
                        f'documents of model {model} is super low: '
                        f'{percentage:.2f}% (Hint: has reindex step being '
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
