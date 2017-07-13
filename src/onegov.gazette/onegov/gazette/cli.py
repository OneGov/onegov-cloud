""" Provides commands used to initialize gazette websites. """

from click import echo
from click import secho
from onegov.core.cli import command_group
from onegov.core.cli import pass_group_context


cli = command_group()


@cli.command(context_settings={'creates_path': True})
@pass_group_context
def add(group_context):
    """ Adds a gazette instance to the database. For example:

        onegov-gazette --select '/onegov_gazette/zug' add

    """

    def add_instance(request, app):
        if not app.principal:
            secho("principal.yml not found", fg='yellow')
        echo("Instance was created successfully")

    return add_instance
