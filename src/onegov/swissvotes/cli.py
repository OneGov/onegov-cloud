from __future__ import annotations

import click
import os
import transaction

from decimal import Decimal
from decimal import InvalidOperation
from onegov.core.cli import abort
from onegov.core.cli import command_group
from onegov.core.cli import pass_group_context
from onegov.core.crypto import random_token
from onegov.file.utils import as_fileintent
from onegov.swissvotes.collections import SwissVoteCollection
from onegov.swissvotes.external_resources import MfgPosters
from onegov.swissvotes.external_resources import SaPosters
from onegov.swissvotes.external_resources import BsPosters
from onegov.swissvotes.models import SwissVote
from onegov.swissvotes.models import SwissVoteFile
from onegov.swissvotes.models.file import LocalizedFile


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable
    from onegov.core.cli.core import GroupContext
    from onegov.swissvotes.app import SwissvotesApp
    from onegov.swissvotes.request import SwissvotesRequest


cli = command_group()


@cli.command(context_settings={'creates_path': True})
@pass_group_context
def add(
    group_context: GroupContext
) -> Callable[[SwissvotesRequest, SwissvotesApp], None]:
    """ Adds an instance to the database. For example:

    .. code-block:: bash

        onegov-swissvotes --select '/onegov_swissvotes/swissvotes' add

    """

    def add_instance(
        request: SwissvotesRequest,
        app: SwissvotesApp
    ) -> None:

        app.cache.flush()
        click.echo('Instance was created successfully')

    return add_instance


@cli.command('import-attachments')
@click.argument('folder', type=click.Path(exists=True))
@pass_group_context
def import_attachments(
    group_context: GroupContext,
    folder: str
) -> Callable[[SwissvotesRequest, SwissvotesApp], None]:
    r""" Import a attachments from the given folder. For example:

    .. code-block:: bash

        onegov-swissvotes \
            --select '/onegov_swissvotes/swissvotes' \
            import-attachments data_folder

    Expects a data folder structure with the first level representing an
    attachment and the second level a locale. The PDFs have to be named by
    BFS number (single number or range). For example:

        data/voting_text/de_CH/001.pdf
        data/voting_text/de_CH/038.1.pdf
        data/voting_text/de_CH/622-625.pdf

    """

    def _import(request: SwissvotesRequest, app: SwissvotesApp) -> None:
        votes = SwissVoteCollection(app)

        attachments = {}
        for name in os.listdir(folder):
            if (
                os.path.isdir(os.path.join(folder, name))
                and isinstance(SwissVote.__dict__.get(name), LocalizedFile)
            ):
                attachments[name] = os.path.join(folder, name)
            else:
                click.secho(f'Ignoring /{name}', fg='yellow')

        for attachment, attachment_folder in attachments.items():
            locales = {}
            for name in os.listdir(attachment_folder):
                if (
                    os.path.isdir(os.path.join(attachment_folder, name))
                    and name in app.locales
                ):
                    locales[name] = os.path.join(attachment_folder, name)
                else:
                    click.secho(f'Ignoring /{attachment}/{name}', fg='yellow')

            for locale, locale_folder in locales.items():
                for name in sorted(os.listdir(locale_folder)):
                    numbers_str, _, ext = name.rpartition('.')
                    if ext not in ('pdf', 'xlsx'):
                        click.secho(
                            f'Ignoring {attachment}/{locale}/{name}',
                            fg='yellow'
                        )
                        continue

                    try:
                        numbers = [Decimal(x) for x in numbers_str.split('-')]
                        assert 1 <= len(numbers) <= 2
                        if len(numbers) == 2:
                            numbers = [
                                Decimal(x) for x in
                                range(int(numbers[0]), int(numbers[1]) + 1)
                            ]
                    except (AssertionError, InvalidOperation):
                        click.secho(
                            f'Invalid name {attachment}/{locale}/{name}',
                            fg='red'
                        )
                        continue

                    for bfs_number in numbers:
                        vote = votes.by_bfs_number(bfs_number)
                        if not vote:
                            click.secho(
                                f'No matching vote {bfs_number} for '
                                f'{attachment}/{locale}/{name}',
                                fg='red'
                            )
                            continue

                        file = SwissVoteFile(id=random_token())
                        with open(
                            os.path.join(locale_folder, name), 'rb'
                        ) as f:
                            file.reference = as_fileintent(
                                f, f'{attachment}-{locale}'
                            )
                        vote.__class__.__dict__[attachment].__set_by_locale__(
                            vote, file, locale
                        )

                        click.secho(
                            f'Added {attachment}/{locale}/{name}'
                            f' to {bfs_number}',
                            fg='green'
                        )

    return _import


@cli.command('import-campaign-material')
@click.argument('folder', type=click.Path(exists=True))
@pass_group_context
def import_campaign_material(
    group_context: GroupContext,
    folder: str
) -> Callable[[SwissvotesRequest, SwissvotesApp], None]:
    r""" Import a campaign material from the given folder. For example:

    .. code-block:: bash

        onegov-swissvotes \
            --select '/onegov_swissvotes/swissvotes' \
            import-campaign-material data_folder

    Expects all files within this folder and filenames starting with the BFS
    number. For example:

        229_Ja-PB_Argumentarium-Gründe-der-Trennung.pdf
        232-1_Nein_PB_Referentenführer.pdf

    """

    def _import(request: SwissvotesRequest, app: SwissvotesApp) -> None:
        attachments: dict[Decimal, list[str]] = {}

        votes = SwissVoteCollection(app)
        bfs_numbers = {
            bfs_number
            for bfs_number, in votes.query().with_entities(
                SwissVote.bfs_number
            )
        }
        for name in os.listdir(folder):
            if not name.endswith('.pdf'):
                click.secho(f'Ignoring {name}', fg='yellow')
                continue

            try:
                bfs_number = Decimal(
                    name.split('_', 1)[0].replace('-', '.')
                )
            except InvalidOperation:
                click.secho(f'Invalid name {name}', fg='red')
                continue

            if bfs_number in bfs_numbers:
                attachments.setdefault(bfs_number, []).append(name)
            else:
                click.secho(f'No matching vote for {name}', fg='red')

        for bfs_number in sorted(attachments):
            vote = app.session().query(SwissVote).filter_by(
                bfs_number=bfs_number
            ).one()
            existing = [file.filename for file in vote.campaign_material_other]
            names = sorted(attachments[bfs_number])
            for name in names:
                if name in existing:
                    click.secho(f'{name} already exists', fg='yellow')
                    continue

                file = SwissVoteFile(id=random_token())
                file.name = f'campaign_material_other-{name}'
                with open(os.path.join(folder, name), 'rb') as content:
                    file.reference = as_fileintent(content, name)
                vote.files.append(file)
                click.secho(f'Added {name}', fg='green')
            transaction.commit()

    return _import


@cli.command('reindex')
@pass_group_context
def reindex_attachments(
    group_context: GroupContext
) -> Callable[[SwissvotesRequest, SwissvotesApp], None]:
    """ Reindexes the attachments. """

    def _reindex(request: SwissvotesRequest, app: SwissvotesApp) -> None:
        bfs_numbers = sorted(app.session().query(SwissVote.bfs_number))
        for bfs_number, in bfs_numbers:
            click.secho(f'Reindexing vote {bfs_number}', fg='green')
            app.session().query(SwissVote).filter_by(
                bfs_number=bfs_number
            ).one().reindex_files()
            transaction.commit()

    return _reindex


@cli.command('update-resources')
@click.option('--details', is_flag=True, default=False)
@click.option('--mfg', is_flag=True, default=False)
@click.option('--sa', is_flag=True, default=False)
@click.option('--bs', is_flag=True, default=False)
@pass_group_context
def update_resources(
    group_context: GroupContext,
    details: bool,
    sa: bool,
    bs: bool,
    mfg: bool,
) -> Callable[[SwissvotesRequest, SwissvotesApp], None]:
    """ Updates external resources. """

    def _update_sources(
        request: SwissvotesRequest,
        app: SwissvotesApp
    ) -> None:

        posters: MfgPosters | BsPosters | SaPosters
        if mfg:
            click.echo('Updating MfG posters')
            if not app.mfg_api_token:
                abort('No token configured, aborting')
            posters = MfgPosters(app.mfg_api_token)
            added, updated, removed, failed = posters.fetch(app.session())
            click.secho(
                f'{added} added, {updated} updated, {removed} removed, '
                f'{len(failed)} failed',
                fg='green' if not failed else 'yellow'
            )
            if failed and details:
                failed_str = ', '.join(str(item) for item in sorted(failed))
                click.secho(f'Failed: {failed_str}', fg='yellow')

        if bs:
            click.echo('Updating BS posters')
            if not app.bs_api_token:
                abort('No token configured, aborting')
            posters = BsPosters(app.bs_api_token)
            added, updated, removed, failed = posters.fetch(app.session())
            click.secho(
                f'{added} added, {updated} updated, {removed} removed, '
                f'{len(failed)} failed',
                fg='green' if not failed else 'yellow'
            )
            if failed and details:
                failed_str = ', '.join(str(item) for item in sorted(failed))
                click.secho(f'Failed: {failed_str}', fg='yellow')

        if sa:
            click.echo('Updating SA posters')
            posters = SaPosters()
            added, updated, removed, failed = posters.fetch(app.session())
            click.secho(
                f'{added} added, {updated} updated, {removed} removed, '
                f'{len(failed)} failed',
                fg='green' if not failed else 'yellow'
            )
            if failed and details:
                failed_str = ', '.join(str(item) for item in sorted(failed))
                click.secho(f'Failed: {failed_str}', fg='yellow')

    return _update_sources
