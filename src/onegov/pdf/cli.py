import click

from onegov.core.cli import command_group
from onegov.pdf import LexworkSigner


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable
    from onegov.core.framework import Framework
    from onegov.core.request import CoreRequest


cli = command_group()


@cli.command('lexwork-signing-reasons')
@click.option('--host')
@click.option('--login')
@click.option('--password')
def lexwork_signing_reasons(
    host: str | None,
    login: str | None,
    password: str | None
) -> 'Callable[[CoreRequest, Framework], None]':
    """ Lists the reasons usable for Lexwork PDF signing. Example:

        onegov-pdf --select '/onegov_election_day/zg' lexwork-signing-reasons

    Uses the given host, login and password and tries to get the settings
    from the principal.

    """

    def list_reasons(request: 'CoreRequest', app: 'Framework') -> None:
        try:
            pdf_signing = app.principal.pdf_signing  # type:ignore
        except AttributeError:
            pdf_signing = {}

        if pdf_signing:
            click.echo(
                click.style(
                    'Currently defined reason: {}'.format(
                        pdf_signing.get('reason', '')
                    ),
                    'yellow'
                )
            )

        signer = LexworkSigner(
            host or pdf_signing.get('host'),
            login or pdf_signing.get('login'),
            password or pdf_signing.get('password')
        )

        for reason in signer.signing_reasons:
            click.echo(click.style(reason, 'green'))

    return list_reasons
