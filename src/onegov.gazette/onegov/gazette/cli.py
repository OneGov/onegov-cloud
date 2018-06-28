""" Provides commands used to initialize gazette websites. """

import click
import transaction

from dateutil import parser
from onegov.core.cli import command_group
from onegov.core.cli import pass_group_context
from onegov.core.crypto import random_password
from onegov.core.csv import convert_xls_to_csv
from onegov.core.csv import CSVFile
from onegov.gazette import _
from onegov.gazette.collections import CategoryCollection
from onegov.gazette.collections import IssueCollection
from onegov.gazette.collections import OrganizationCollection
from onegov.gazette.models import GazetteNotice
from onegov.gazette.models import IssueName
from onegov.gazette.utils import SogcImporter
from onegov.user import User
from onegov.user import UserCollection
from onegov.user import UserGroupCollection
from raven import Client
from sedate import standardize_date


cli = command_group()


@cli.command(context_settings={'creates_path': True})
@pass_group_context
def add(group_context):
    """ Adds a gazette instance to the database. For example:

        onegov-gazette --select '/onegov_gazette/zug' add

    """

    def add_instance(request, app):
        if not app.principal:
            click.secho("principal.yml not found", fg='yellow')
        click.echo("Instance was created successfully")

    return add_instance


@cli.command(name='import-editors')
@click.argument('file', type=click.File('rb'))
@click.option('--clear/--no-clear', default=False)
@click.option('--dry-run/--no-dry-run', default=False)
@click.option('--locale', default='de_CH')
@pass_group_context
def import_editors(ctx, file, clear, dry_run, locale):
    """ Imports editors and groups. For example:

        onegov-gazette --select '/onegov_gazette/zug' import-editors data.xlsx

    """

    def import_editors_and_groups(request, app):
        request.locale = locale
        headers = {
            'group': request.translate(_("Group")),
            'name': request.translate(_("Name")),
            'email': request.translate(_("E-Mail"))
        }

        session = app.session()
        users = UserCollection(session)
        groups = UserGroupCollection(session)

        if clear:
            click.secho("Deleting all editors", fg='yellow')
            for user in users.query().filter(User.role == 'member'):
                session.delete(user)

            click.secho("Deleting all groups", fg='yellow')
            for group in groups.query():
                session.delete(group)

        csvfile = convert_xls_to_csv(
            file, sheet_name=request.translate(_("Editors"))
        )
        csv = CSVFile(csvfile, expected_headers=headers.values())
        lines = list(csv.lines)
        columns = {
            key: csv.as_valid_identifier(value)
            for key, value in headers.items()
        }

        added_groups = {}
        for group in set([line.gruppe for line in lines]):
            added_groups[group] = groups.add(name=group)
        count = len(added_groups)
        click.secho(f"{count} group(s) imported", fg='green')

        count = 0
        for line in lines:
            count += 1
            email = getattr(line, columns['email'])
            realname = getattr(line, columns['name'])
            group = getattr(line, columns['group'])
            group = added_groups[group] if group else None
            users.add(
                username=email,
                realname=realname,
                group=group,
                password=random_password(),
                role='member',
            )

        click.secho(f"{count} editor(s) imported", fg='green')

        if dry_run:
            transaction.abort()
            click.secho("Aborting transaction", fg='yellow')

    return import_editors_and_groups


@cli.command(name='import-organizations')
@click.argument('file', type=click.File('rb'))
@click.option('--clear/--no-clear', default=False)
@click.option('--dry-run/--no-dry-run', default=False)
@click.option('--locale', default='de_CH')
@pass_group_context
def import_organizations(ctx, file, clear, dry_run, locale):
    """ Imports Organizations. For example:

        onegov-gazette --select '/onegov_gazette/zug' \
            import-organizations data.xlsx

    """

    def _import_organizations(request, app):
        request.locale = locale
        headers = {
            'id': request.translate(_("ID")),
            'name': request.translate(_("Name")),
            'title': request.translate(_("Title")),
            'active': request.translate(_("Active")),
            'external_name': request.translate(_("External ID")),
            'parent': request.translate(_("Parent Organization"))
        }

        session = app.session()
        organizations = OrganizationCollection(session)

        if clear:
            click.secho("Deleting organizations", fg='yellow')
            for organization in organizations.query():
                session.delete(organization)

        csvfile = convert_xls_to_csv(
            file, sheet_name=request.translate(_("Organizations"))
        )
        csv = CSVFile(csvfile, expected_headers=headers.values())
        lines = list(csv.lines)
        columns = {
            key: csv.as_valid_identifier(value)
            for key, value in headers.items()
        }

        count = 0
        for line in lines:
            count += 1
            id_ = int(getattr(line, columns['id']))
            name = getattr(line, columns['name'])
            parent = getattr(line, columns['parent'])
            parent = int(parent) if parent else None
            title = getattr(line, columns['title'])
            active = bool(int(getattr(line, columns['active'])))
            external_name = getattr(line, columns['external_name'])

            organization = organizations.add_root(
                id=id_,
                name=name,
                title=title,
                active=active,
                external_name=external_name,
                order=count
            )
            organization.parent_id = parent

        click.secho(f"{count} organization(s) imported", fg='green')

        if dry_run:
            transaction.abort()
            click.secho("Aborting transaction", fg='yellow')

    return _import_organizations


@cli.command(name='import-categories')
@click.argument('file', type=click.File('rb'))
@click.option('--clear/--no-clear', default=False)
@click.option('--dry-run/--no-dry-run', default=False)
@click.option('--locale', default='de_CH')
@pass_group_context
def import_categories(ctx, file, clear, dry_run, locale):
    """ Imports categories. For example:

        onegov-gazette --select '/onegov_gazette/zug' \
            import-categories data.xlsx

    """

    def _import_categories(request, app):

        request.locale = locale
        headers = {
            'id': request.translate(_("ID")),
            'name': request.translate(_("Name")),
            'title': request.translate(_("Title")),
            'active': request.translate(_("Active"))
        }

        session = app.session()
        categories = CategoryCollection(session)

        if clear:
            click.secho("Deleting categories", fg='yellow')
            for category in categories.query():
                session.delete(category)

        csvfile = convert_xls_to_csv(
            file, sheet_name=request.translate(_("Categories"))
        )
        csv = CSVFile(csvfile, expected_headers=headers.values())
        lines = list(csv.lines)
        columns = {
            key: csv.as_valid_identifier(value)
            for key, value in headers.items()
        }

        count = 0
        for line in lines:
            count += 1
            id_ = int(getattr(line, columns['id']))
            name = getattr(line, columns['name'])
            title = getattr(line, columns['title'])
            active = bool(int(getattr(line, columns['active'])))
            categories.add_root(
                id=id_,
                name=name,
                title=title,
                active=active,
                order=count
            )

        click.secho(f"{count} categorie(s) imported", fg='green')

        if dry_run:
            transaction.abort()
            click.secho("Aborting transaction", fg='yellow')

    return _import_categories


@cli.command(name='import-issues')
@click.argument('file', type=click.File('rb'))
@click.option('--clear/--no-clear', default=False)
@click.option('--dry-run/--no-dry-run', default=False)
@click.option('--locale', default='de_CH')
@click.option('--timezone', default=None)
@pass_group_context
def import_issues(ctx, file, clear, dry_run, locale, timezone):
    """ Imports issues. For example:

        onegov-gazette --select '/onegov_gazette/zug' import-issues data.xlsx

    """

    def _import_issues(request, app):
        request.locale = locale
        headers = {
            'number': request.translate(_("Number")),
            'date': request.translate(_("Date")),
            'deadline': request.translate(_("Deadline"))
        }

        session = app.session()
        issues = IssueCollection(session)

        if clear:
            click.secho("Deleting issues", fg='yellow')
            for category in issues.query():
                session.delete(category)

        csvfile = convert_xls_to_csv(
            file, sheet_name=request.translate(_("Issues"))
        )
        csv = CSVFile(csvfile, expected_headers=headers.values())
        lines = list(csv.lines)
        columns = {
            key: csv.as_valid_identifier(value)
            for key, value in headers.items()
        }

        count = 0
        for line in lines:
            count += 1
            number = int(getattr(line, columns['number']))
            date_ = parser.parse(getattr(line, columns['date'])).date()
            deadline = standardize_date(
                parser.parse(getattr(line, columns['deadline'])),
                timezone or request.app.principal.time_zone
            )
            name = str(IssueName(date_.year, number))

            issues.add(
                name=name,
                number=number,
                date=date_,
                deadline=deadline
            )

        click.secho(f"{count} categorie(s) imported", fg='green')

        if dry_run:
            transaction.abort()
            click.secho("Aborting transaction", fg='yellow')

    return _import_issues


@cli.command(name='import-sogc')
@click.option('--clear/--no-clear', default=False)
@click.option('--dry-run/--no-dry-run', default=False)
@click.option('--sentry')
@pass_group_context
def import_sogc(ctx, clear, dry_run, sentry):
    """ Imports from the SOGC. For example:

        onegov-gazette --select '/onegov_gazette/zug' import-sogc

    """

    def _import_sogc(request, app):
        if not getattr(request.app.principal, 'sogc_import', None):
            return

        session = request.session
        if clear:
            click.secho("Deleting imported notices", fg='yellow')
            existing = session.query(GazetteNotice)
            existing = existing.filter(GazetteNotice.source.isnot(None))
            existing.delete()

        try:
            count = SogcImporter(session, request.app.principal.sogc_import)()
        except Exception as e:
            if sentry:
                Client(sentry).captureException()
            raise(e)

        click.secho(f"{count} notice(s) imported", fg='green')

        if dry_run:
            transaction.abort()
            click.secho("Aborting transaction", fg='yellow')

    return _import_sogc
