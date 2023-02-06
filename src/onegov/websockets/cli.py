import click

from asyncio import run
from onegov.core.cli import command_group
from onegov.core.cli import pass_group_context
from onegov.websockets import log
from onegov.websockets.client import authenticate
from onegov.websockets.client import broadcast as broadast_message
from onegov.websockets.client import register
from onegov.websockets.client import status as get_status
from onegov.websockets.server import main
from sentry_sdk import init as init_sentry
from websockets import connect


cli = command_group()


@cli.group(
    invoke_without_command=True,
    context_settings={
        'matches_required': False,
        'default_selector': '*'
    }
)
@click.option('--host')
@click.option('--port')
@click.option('--token')
@click.option('--sentry-dsn')
@click.option('--sentry-environment', default='testing')
@click.option('--sentry-release')
@pass_group_context
def serve(
    group_context,
    host, port, token,
    sentry_dsn, sentry_environment, sentry_release
):
    """ Starts the global websocket server.

    Takes configuration from the first found app if missing.

        onegov-websockets serve

    """

    if not all((host, port, token)) and group_context.config.applications:
        app = group_context.config.applications[0]
        host = host or app.configuration.get('websockets_host')
        port = port or app.configuration.get('websockets_port')
        token = token or app.configuration.get('websockets_token')

    assert all((host, port, token)), "invalid configuration"

    if sentry_dsn:
        init_sentry(
            dsn=sentry_dsn,
            release=sentry_release,
            environment=sentry_environment,
        )

    run(main(host, port, token))


@cli.command('listen')
@click.option('--host')
@click.option('--port')
@click.option('--schema')
@pass_group_context
def listen(group_context, host, port, schema):
    """ Listens for application-bound broadcasts from the websocket server.

    Requires either the selection of a websockets-enabled application or
    passing the optional parameters.

        onegov-websockets --select '/onegov_org/govikon' listen

    """

    def _listen(request, app):
        url = (
            f'ws://{host or app.websockets_host}:{port or app.websockets_port}'
        )

        async def main():
            async with connect(url) as websocket:
                await register(websocket, app.schema or schema)
                log.info(f'Listing on {url} @ {app.schema or schema}')
                async for message in websocket:
                    log.info(message)

        run(main())

    return _listen


@cli.command('status')
@click.option('--host')
@click.option('--port')
@click.option('--token')
@pass_group_context
def status(group_context, host, port, token):
    """ Shows the global status of the websocket server.

    Requires either the selection of a websockets-enabled application or
    passing the optional parameters.

        onegov-websockets --select '/onegov_org/govikon' status

    """

    def _status(request, app):
        url = (
            f'ws://{host or app.websockets_host}:{port or app.websockets_port}'
        )

        async def main():
            async with connect(url) as websocket:
                await authenticate(
                    websocket,
                    token or app.websockets_token
                )
                response = await get_status(websocket)
                click.echo(response)

        run(main())

    return _status


@cli.command('broadcast')
@click.argument('message')
@click.option('--host')
@click.option('--port')
@click.option('--schema')
@click.option('--token')
@pass_group_context
def broadcast(group_context, message, host, port, schema, token):
    """ Broadcast to all application-bound connected clients.

    Requires either the selection of a websockets-enabled application or
    passing the optional parameters.

        onegov-websockets --select '/onegov_org/govikon' broadcast

    """

    def _broadcast(request, app):
        url = (
            f'ws://{host or app.websockets_host}:{port or app.websockets_port}'
        )

        async def main():
            async with connect(url) as websocket:
                await authenticate(
                    websocket,
                    token or app.websockets_token
                )
                await broadast_message(
                    websocket,
                    app.schema or schema,
                    message
                )
                click.echo(f'{message} sent to {app.schema or schema}')

        run(main())

    return _broadcast
