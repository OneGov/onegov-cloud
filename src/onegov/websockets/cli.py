import click

from asyncio import run
from onegov.core.cli import command_group
from onegov.core.cli import pass_group_context
from onegov.websockets import log
from onegov.websockets.client import authenticate
from onegov.websockets.client import register
from onegov.websockets.client import status as get_status
from onegov.websockets.client import broadcast as broadast_message
from onegov.websockets.server import main
from websockets import connect


cli = command_group()


@cli.command('serve')
@click.option('--host')
@click.option('--port')
@click.option('--token')
@pass_group_context
def serve(group_context, host, port, token):
    """ Starts the global websocket server.

    Requires either the selection of a websockets-enabled application or
    passing the optional parameters.

        onegov-websockets --select '/onegov_org/govikon' serve

    """

    def _serve(request, app):
        run(
            main(
                host or app.websockets_host,
                port or app.websockets_port,
                token or app.websockets_token
            )
        )

    return _serve


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
