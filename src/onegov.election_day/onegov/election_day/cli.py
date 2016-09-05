""" Provides commands used to initialize election day websites. """

import click

from onegov.core.cli import command_group, pass_group_context, abort


cli = command_group()


@cli.command(context_settings={'creates_path': True})
@pass_group_context
def add(group_context):
    """ Adds an election day instance with to the database. This requires that
    the principal.yml is present in the file storage. For example:

        onegov-election-day --select '/onegov_election_day/zg' add

    """

    def add_instance(request, app):
        app.cache.invalidate()
        if not app.principal:
            abort("principal.yml not found")

        click.echo("Instance was created successfully")

    return add_instance
