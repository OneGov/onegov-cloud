import click

from asyncio import run
from json import loads
from onegov.core.cli import command_group
from onegov.core.cli import pass_group_context
from onegov.websockets.client import authenticate
from onegov.websockets.client import broadcast as broadast_message
from onegov.websockets.client import register
from onegov.websockets.client import status as get_status
from onegov.websockets.server import main
from sentry_sdk import init as init_sentry
from urllib.parse import urlparse
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
@click.option('--port', type=int)
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

    Takes the configuration from the first found app if missing.

        onegov-websockets serve

    """

    if not all((host, port, token)) and group_context.config.applications:
        app = group_context.config.applications[0]
        config = app.configuration.get('websockets')
        url = config.get('manage_url')
        if url:
            url = urlparse(url)
            host = host or url.hostname
            port = port or url.port
        token = token or config.get('manage_token')

    assert all((host, port, token)), "invalid configuration"

    if sentry_dsn:
        init_sentry(
            dsn=sentry_dsn,
            release=sentry_release,
            environment=sentry_environment,
        )

    run(main(host, port, token))


@cli.command('listen')
@click.option('--url')
@click.option('--schema')
@click.option('--channel')
@click.option('--private', is_flag=True, default=False)
@pass_group_context
def listen(group_context, url, schema, channel, private):
    """ Listens for application-bound broadcasts from the websocket server.

    Requires either the selection of a websockets-enabled application or
    passing the optional parameters url and schema.

        onegov-websockets --select '/onegov_org/govikon' listen

    """

    def _listen(request, app):
        nonlocal url, schema, channel
        if private and channel:
            raise click.UsageError('Use either channel or private, not both')
        if private and not app.configuration.get('identity_secret'):
            raise click.UsageError('identity_secret not set')
        url = url or app.websockets_client_url(request)
        schema = schema or app.schema
        channel = app.websockets_private_channel if private else channel
        schema_channel = f'{schema}-{channel}' if channel else schema

        async def main():
            async with connect(url) as websocket:
                await register(websocket, schema, channel)
                click.echo(f'Listing on {url} @ {schema_channel}')
                async for message in websocket:
                    click.echo(message)

        run(main())

    return _listen


@cli.command('status')
@click.option('--url')
@click.option('--token')
@pass_group_context
def status(group_context, url, token):
    """ Shows the global status of the websocket server.

    Requires either the selection of a websockets-enabled application or
    passing the optional parameters.

        onegov-websockets --select '/onegov_org/govikon' status

    """

    def _status(request, app):
        nonlocal url, token
        url = url or app.websockets_manage_url
        token = token or app.websockets_manage_token

        async def main():
            async with connect(url) as websocket:
                await authenticate(websocket, token)
                response = await get_status(websocket)
                click.echo(response)

        run(main())

    return _status


@cli.command('broadcast')
@click.argument('message')
@click.option('--url')
@click.option('--schema')
@click.option('--token')
@click.option('--channel')
@click.option('--private', is_flag=True, default=False)
@pass_group_context
def broadcast(group_context, message, url, schema, token, channel, private):
    """ Broadcast to all application-bound connected clients.

    Requires either the selection of a websockets-enabled application or
    passing the optional parameters.

        onegov-websockets --select '/onegov_org/govikon' \
            broadcast '{"event":"refresh","path":"events/abcd"}'


    """

    def _broadcast(request, app):
        nonlocal url, schema, token, channel, private
        if private and channel:
            raise click.UsageError('Use either channel or private, not both')
        if private and not app.configuration.get('identity_secret'):
            raise click.UsageError('identity_secret not set')
        url = url or app.websockets_manage_url
        schema = schema or app.schema
        token = token or app.websockets_manage_token
        channel = app.websockets_private_channel if private else channel
        schema_channel = f'{schema}-{channel}' if channel else schema

        async def main():
            async with connect(url) as websocket:
                await authenticate(websocket, token)
                await broadast_message(
                    websocket,
                    schema,
                    channel,
                    loads(message),
                )
                click.echo(f'{message} sent to {schema_channel}')

        run(main())

    return _broadcast
