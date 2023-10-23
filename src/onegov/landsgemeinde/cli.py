""" Provides commands used to initialize org websites. """
import click

from onegov.core.cli import command_group, pass_group_context, abort
from onegov.core import html
from onegov.org.models import Organisation
from onegov.landsgemeinde.collections import VotumCollection
from onegov.landsgemeinde.collections import AgendaItemCollection
from onegov.landsgemeinde.models import AgendaItem

cli = command_group()


@cli.command(context_settings={'creates_path': True})
@click.argument('name')
@click.option(
    '--locale',
    default='de_CH',
    type=click.Choice(['de_CH', 'fr_CH', 'it_CH'])
)
@pass_group_context
def add(group_context, name, locale):
    """ Adds an org with the given name to the database. For example:

        onegov-org --select '/onegov_org/evilcorp' add "Evilcorp"

    """

    def add_org(request, app):

        if app.session().query(Organisation).first():
            abort("{} already contains an organisation".format(
                group_context.selector))

        app.settings.org.create_new_organisation(app, name, locale=locale)

        click.echo("{} was created successfully".format(name))

    return add_org


@cli.command('fill-person-info')
@pass_group_context
@click.option('--dry-run', is_flag=True, default=False)
def fill_person_info(group_context, dry_run=False):
    """ Takes the first two rows of the votum text and fills them into the
        name and function field of the person.

    Example:
    onegov-landsgemeinde --select '/onegov_landsgemeinde/gl' fill-person-info
    """

    def copy_text_to_first_field(request, app):
        votums = VotumCollection(app.session()).query()
        counter = 0
        for votum in votums:
            if votum.motion and not votum.text:
                counter += 1
                votum.text = votum.motion
                votum.motion = ''
        click.secho(f'{counter} votum texts moved', fg='green')

    def fill_fields(request, app):
        copy_text_to_first_field(request, app)
        c_names = 0
        c_functions = 0
        votums = VotumCollection(app.session()).query()
        agenda_items = AgendaItemCollection(app.session()).query()
        for votum in votums:
            agenda_item = agenda_items.filter(
                AgendaItem.id == votum.agenda_item_id).all()[0]
            for i, line in enumerate(html.html_to_text(votum.text).splitlines(
            )[0:3]):
                click.echo(f' ----- {agenda_item.title}')
                if ', ' not in line and line:
                    if i == 0 and len(line) < 30 and not votum.person_name:
                        c_names += 1
                        click.secho(votum.person_name, fg='red')
                        if not dry_run:
                            votum.person_name = line
                    elif len(line) < 30 and not votum.person_function:
                        c_functions += 1
                        click.secho(votum.person_name, fg='blue')
                        if not dry_run:
                            votum.person_function = line

                if ', ' in line:
                    name, function = line.split(', ')[0:2]
                    if len(name) < 30 and not votum.person_name:
                        c_names += 1
                        click.secho(name, fg='yellow')
                        if not dry_run:
                            votum.person_name = name
                    if len(function) < 30 and not votum.person_function:
                        c_functions += 1
                        click.secho(function, fg='green')
                        if not dry_run:
                            votum.person_function = function

        if not dry_run:
            click.echo(
                f'Filled in {c_names} names and {c_functions} functions.')
        if dry_run:
            click.echo(
                f'Would fill in{c_names} names and {c_functions} functions.')

    return fill_fields
