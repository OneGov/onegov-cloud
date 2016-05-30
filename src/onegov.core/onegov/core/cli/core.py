""" Provides a framework for cli commands run against one ore more onegov
cloud applications.

"""

import click
import inspect
import sys

from fnmatch import fnmatch
from onegov.core.orm import Base, SessionManager
from onegov.core.utils import scan_morepath_modules
from onegov.server.config import Config
from onegov.server.core import Server
from uuid import uuid4
from webtest import TestApp as Client


#: :class:`GroupContext` settings which may be overriden by commands
CONTEXT_SPECIFIC_SETTINGS = (
    'default_selector',
    'creates_path',
    'singular',
    'matches_required'
)


class GroupContextGuard(object):
    """ Contains methods which abort the commandline program if any condition
    is not met.

    Used as a mixin in :class:`GroupContext`.

    """
    def validate_guard_conditions(self, click_context):
        matches = tuple(self.matches)

        for name, method in inspect.getmembers(self, inspect.ismethod):
            if name.startswith('abort'):
                method(click_context, matches)

    def abort_if_no_selector(self, click_context, matches):
        if not self.selector:
            click.secho("Available selectors:")

            for selector in self.available_selectors:
                click.secho(" - {}".format(selector))

            abort("No selector provided, aborting.")

    def abort_if_no_subcommand(self, click_context, matches):
        if click_context.invoked_subcommand is None:
            click.secho("Paths matching the selector:")

            for match in matches:
                click.secho(" - {}".format(match))

            abort("No subcommand provided, aborting.")

    def abort_if_no_match(self, click_context, matches):
        if self.matches_required and not matches:
            click.secho("Available selectors:")

            for selector in self.available_selectors:
                click.secho(" - {}".format(selector))

            abort("Selector doesn't match any paths, aborting.")

    def abort_if_not_singular(self, click_context, matches):
        if self.singular and len(matches) > 1:
            click.secho("Paths matching the selector:")

            for match in matches:
                click.secho(" - {}".format(match))

            abort("The selector must match a single path, aborting.")

    def abort_if_no_create_path(self, click_context, matches):
        if self.creates_path:
            if len(matches) > 1:
                abort("This selector may not reference an existing path")

            if len(self.selector.lstrip('/').split('/')) != 2:
                abort("This selector must reference a full path")

            if '*' in self.selector:
                abort("This selector may not contain a wildcard")


class GroupContext(GroupContextGuard):
    """ Provides access to application configs for group commands.

    """

    def __init__(self, selector, config, default_selector=None,
                 creates_path=False, singular=False, matches_required=True):

        if isinstance(config, dict):
            self.config = Config(config)
        else:
            self.config = Config.from_yaml_file(config)

        self.selector = selector or default_selector
        self.creates_path = creates_path

        if self.creates_path:
            self.singular = True
            self.matches_required = False
        else:
            self.singular = singular
            self.matches_required = matches_required

    def unbound_session_manager(self, dsn):
        """ Returns a session manager *not yet bound to a schema!*. """

        return SessionManager(dsn=dsn, base=Base)

    def available_schemas(self, appcfg):
        if 'dsn' not in appcfg.configuration:
            return []

        mgr = self.unbound_session_manager(appcfg.configuration['dsn'])
        return mgr.list_schemas(limit_to_namespace=appcfg.namespace)

    def match_to_path(self, match):
        match = match.lstrip('/')

        if '/' in match:
            namespace, id = match.split('/')[:2]
        else:
            namespace, id = match, ''

        for appcfg in self.config.applications:
            if appcfg.namespace == namespace:
                return appcfg.path.replace('*', id).rstrip('/')

    @property
    def appcfgs(self):
        """ Returns the matching appconfigs.

        Since there's only one appconfig per namespace, we ignore the path
        part of the selector and only focus on the namespace:

            /namespace/application_id

        """
        namespace_selector = self.selector.lstrip('/').split('/')[0]

        for appcfg in self.config.applications:
            if fnmatch(appcfg.namespace, namespace_selector):
                yield appcfg

    @property
    def available_selectors(self):
        selectors = list(self.all_wildcard_selectors)
        selectors.extend(self.all_specific_selectors)

        return sorted(selectors)

    @property
    def all_wildcard_selectors(self):
        for appcfg in self.config.applications:
            if appcfg.path.endswith('*'):
                yield '/' + appcfg.namespace + '/*'

    @property
    def all_specific_selectors(self):
        for appcfg in self.config.applications:
            if not appcfg.path.endswith('*'):
                yield '/' + appcfg.namespace
            else:
                for schema in self.available_schemas(appcfg):
                    yield '/' + schema.replace('-', '/')

    @property
    def matches(self):
        """ Returns the specific selectors matching the context selector.

        That is, a combination of namespace / application id is returned.
        Since we only know an exhaustive list of application id's *if* we have
        a database connection this is currently limited to applications with
        one. Since we do not have any others yet that's fine.

        However if we implement a database-less application in the future which
        takes wildcard ids, we need some way to enumerate those ids.

        See https://github.com/OneGov/onegov.core/issues/13
        """
        if self.selector:
            for selector in self.all_specific_selectors:
                if fnmatch(selector, self.selector):
                    yield selector

        if self.creates_path:
            yield self.selector.rstrip('/')


def get_context_specific_settings(context):

    if not context.invoked_subcommand:
        return {}

    # The context settings are stored on the command though they are actually
    # click's settings, not ours. Upon inspection we need to transfer them
    # here as a result.
    subcommand = context.command.commands[context.invoked_subcommand]
    if not hasattr(subcommand, 'onegov_settings'):
        subcommand.onegov_settings = {
            key: subcommand.context_settings.pop(key)
            for key in CONTEXT_SPECIFIC_SETTINGS
            if key in subcommand.context_settings
        }

    return subcommand.onegov_settings


#: Decorator to acquire the group context on a command:
#:
#:     @cli.command()
#:     @pass_group_context()
#:     def my_command(group_context):
#:         pass
#:
pass_group_context = click.make_pass_decorator(GroupContext, ensure=True)


def command_group():
    """ Generates a click command group for individual modules.

    Each individual module may have its own command group from which to run
    commands to. Read `<http://click.pocoo.org/6/commands/>`_ to learn more
    about command groups.

    The returned command group will provide the individual commands with
    an optional list of applications to operate on and it allows commands
    to return a callback function which will be invoked with the app config
    (if available), an application instance and a request.

    That is to say, the command group automates setting up a proper request
    context.

    """

    @click.group(invoke_without_command=True)
    @click.option(
        '--select', default=None,
        help="Selects the applications this command should be applied to")
    @click.option(
        '--config', default='onegov.yml',
        help="The onegov config file")
    def command_group(select, config):
        context = click.get_current_context()
        context.obj = group_context = GroupContext(
            select, config, **get_context_specific_settings(context))

        click.secho("Given selector: {}".format(
            group_context.selector or 'None'
        ), fg='green')

        group_context.validate_guard_conditions(context)

    @command_group.resultcallback()
    def process_results(processor, select, config):

        if not processor:
            return

        group_context = click.get_current_context().obj

        # load all applications into the server
        view_path = uuid4().hex
        applications = []

        for appcfg in group_context.appcfgs:

            class CliApplication(appcfg.application_class):

                def is_allowed_application_id(self, application_id):

                    if group_context.creates_path:
                        return True

                    return super().is_allowed_application_id(application_id)

            @CliApplication.path(path=view_path)
            class Model(object):
                pass

            @CliApplication.view(model=Model)
            def run_command(self, request):
                processor(request, request.app)

            scan_morepath_modules(CliApplication)
            CliApplication.commit()

            applications.append({
                'path': appcfg.path,
                'application': CliApplication,
                'namespace': appcfg.namespace,
                'configuration': appcfg.configuration
            })

        server = Server(
            Config({'applications': applications}),
            configure_morepath=False
        )

        # call the matching applications
        client = Client(server)

        matches = list(group_context.matches)

        for match in matches:
            path = group_context.match_to_path(match)
            client.get(path + '/' + view_path)

    return command_group


def abort(msg):
    """ Prints the given error message and aborts the program with a return
    code of 1.

    """
    click.secho(msg, fg='red')

    sys.exit(1)
