import click

from onegov.core.cli import command_group
from onegov.pdf import LexworkSigner


cli = command_group()


@cli.command('list-pdf-signing-reasons')
@click.argument('host')
@click.argument('login')
@click.argument('password')
def list_pdf_signing_reasons(host, login, password):
    """ Lists the reasons usable for PDF signing. Example:

        onegov-pdf --select '/onegov_election_day/zg'
            list-pdf-signing-reasons

    """

    def list_reasons(request, app):
        click.echo(LexworkSigner(host, login, password).signing_reasons)

    return list_reasons
