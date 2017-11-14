import click

from onegov.core.cli import command_group
from onegov.pdf import LexworkSigner


cli = command_group()


@cli.command('lexwork-signing-reasons')
@click.option('--host')
@click.option('--login')
@click.option('--password')
def lexwork_signing_reasons(host, login, password):
    """ Lists the reasons usable for Lexwork PDF signing. Example:

        onegov-pdf --select '/onegov_election_day/zg' lexwork-signing-reasons

    Uses the given host, login and password are tries to get the settings
    from the principal.

    """

    def list_reasons(request, app):
        try:
            pdf_signing = app.principal.pdf_signing
        except AttributeError:
            pdf_signing = None

        if pdf_signing:
            click.echo(
                click.style(
                    'Currently defined reason: {}'.format(
                        pdf_signing.get('reason', '')
                    ),
                    'yellow'
                )
            )
            ['reason']

        signer = LexworkSigner(
            host or app.principal.pdf_signing['host'],
            login or app.principal.pdf_signing['login'],
            password or app.principal.pdf_signing['password']
        )

        for reason in signer.signing_reasons:
            click.echo(click.style(reason, 'green'))

    return list_reasons
