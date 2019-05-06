import click
import os

from decimal import Decimal
from decimal import InvalidOperation
from onegov.core.cli import abort
from onegov.core.cli import command_group
from onegov.core.cli import pass_group_context
from onegov.core.crypto import random_token
from onegov.file.utils import as_fileintent
from onegov.swissvotes.collections import SwissVoteCollection
from onegov.swissvotes.models import SwissVote
from onegov.swissvotes.models import SwissVoteFile
from onegov.swissvotes.models.localized_file import LocalizedFile
from sqlalchemy import create_engine


cli = command_group()


@cli.command(context_settings={'creates_path': True})
@pass_group_context
def add(group_context):
    """ Adds an instance to the database. For example:

        onegov-swissvotes --select '/onegov_swissvotes/swissvotes' add

    """

    def add_instance(request, app):
        app.cache.invalidate()
        click.echo("Instance was created successfully")

    return add_instance


@cli.command()
@pass_group_context
def delete(group_context):
    """ Deletes an instance from the database. For example:

        onegov-swissvotes --select '/onegov_swissvotes/swissvotes' delete

    """

    def delete_instance(request, app):

        confirmation = "Do you really want to DELETE {}?".format(app.schema)

        if not click.confirm(confirmation):
            abort("Deletion process aborted")

        assert app.has_database_connection
        assert app.session_manager.is_valid_schema(app.schema)

        dsn = app.session_manager.dsn
        app.session_manager.session().close_all()
        app.session_manager.dispose()

        engine = create_engine(dsn)
        engine.execute('DROP SCHEMA "{}" CASCADE'.format(app.schema))
        engine.raw_connection().invalidate()
        engine.dispose()

        click.echo("Instance was deleted successfully")

    return delete_instance


@cli.command('import')
@click.argument('folder', type=click.Path(exists=True))
@pass_group_context
def import_attachments(group_context, folder):
    """ Import a attachments from the given folder. For example:

        onegov-swissvotes \
            --select '/onegov_swissvotes/swissvotes' \
            import data_folder

    Expects a data folder structure with the first level representing an
    attachment and the second level a locale. The PDFs have to be name by
    BFS number. For example:

        data/voting_text/de_CH/001.pdf
        data/voting_text/de_CH/038.1.pdf

    """

    def _import(request, app):
        votes = SwissVoteCollection(app)

        attachments = {}
        for name in os.listdir(folder):
            if (
                os.path.isdir(os.path.join(folder, name))
                and isinstance(SwissVote.__dict__.get(name), LocalizedFile)
            ):
                attachments[name] = os.path.join(folder, name)
            else:
                click.secho(f"Ignoring /{name}", fg='yellow')

        for attachment, attachment_folder in attachments.items():
            locales = {}
            for name in os.listdir(attachment_folder):
                if (
                    os.path.isdir(os.path.join(attachment_folder, name))
                    and name in app.locales
                ):
                    locales[name] = os.path.join(attachment_folder, name)
                else:
                    click.secho(f"Ignoring /{attachment}/{name}", fg='yellow')

            for locale, locale_folder in locales.items():
                for name in sorted(os.listdir(locale_folder)):
                    if not (name.endswith('.pdf') or name.endswith('.xlsx')):
                        click.secho(
                            f"Ignoring {attachment}/{locale}/{name}",
                            fg='yellow'
                        )
                        continue

                    try:
                        bfs_number = Decimal(
                            name.replace('.pdf', '').replace('.xlsx', '')
                        )
                    except InvalidOperation:
                        click.secho(
                            f"Invalid name {attachment}/{locale}/{name}",
                            fg='red'
                        )
                        continue

                    vote = votes.by_bfs_number(bfs_number)
                    if not vote:
                        click.secho(
                            f"No matching vote {bfs_number} for "
                            f"{attachment}/{locale}/{name}",
                            fg='red'
                        )
                        continue

                    file = SwissVoteFile(id=random_token())
                    with open(os.path.join(locale_folder, name), 'rb') as f:
                        file.reference = as_fileintent(
                            f, f'{attachment}-{locale}'
                        )
                    vote.__class__.__dict__[attachment].__set_by_locale__(
                        vote, file, locale
                    )

                    click.secho(
                        f"Added {attachment}/{locale}/{name}",
                        fg='green'
                    )

    return _import


@cli.command('reindex')
@pass_group_context
def reindex_attachments(group_context):
    """ Reindexes the attachments. """

    def _reindex(request, app):
        votes = SwissVoteCollection(app)
        for vote in votes.query():
            vote.vectorize_files()
            click.secho(f"Reindexed vote {vote.bfs_number}", fg='green')

    return _reindex
