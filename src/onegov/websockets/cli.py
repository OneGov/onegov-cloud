import click

from asyncio import run
from onegov.core.cli import command_group
from onegov.core.cli import pass_group_context
from onegov.websockets import log
from onegov.websockets.client import authenticate
from onegov.websockets.client import register
from onegov.websockets.client import status as get_status
from onegov.websockets.client import broadcast as broadast_message
from websockets import connect


cli = command_group()

# todo: Server command?


@cli.command('listen')
@click.option('--host', default='localhost:8765')
@pass_group_context
def listen(group_context, host):
    """ Listens for broadcasts from the websocket server.

        onegov-websockets --select '/onegov_org/govikon' listen

    """

    def _listen(request, app):
        async def coro():
            async with connect(f'ws://{host}') as websocket:
                await register(websocket, app.schema)
                log.info(f'Listing on {host} @ {app.schema}')
                async for message in websocket:
                    log.info(message)

        run(coro())

    return _listen


@cli.command('status')
@click.option('--host', default='localhost:8765')
@click.option('--token')
@pass_group_context
def status(group_context, host, token):
    """ Shows the status of the websocket server.

        onegov-websockets --select '/onegov_org/govikon' status

    """

    def _status(request, app):
        async def coro():
            async with connect(f'ws://{host}') as websocket:
                await authenticate(websocket, token or 'token')  # todo: token
                response = await get_status(websocket)
                click.echo(response)

        run(coro())

    return _status


@cli.command('broadcast')
@click.argument('message')
@click.option('--host', default='localhost:8765')
@click.option('--token')
@pass_group_context
def broadcast(group_context, message, host, token):
    """ Broadcast to all connected clients.

        onegov-websockets --select '/onegov_org/govikon' broadcast

    """

    def _broadcast(request, app):
        async def coro():
            async with connect(f'ws://{host}') as websocket:
                await authenticate(websocket, token or 'token')  # todo: token
                await broadast_message(websocket, app.schema, message)
                click.echo(f'{message} sent to {app.schema}')

        run(coro())

    return _broadcast
