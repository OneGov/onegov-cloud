"""
.. _core-commands:

Core Commands
-------------

Provides a framework for cli commands run against one ore more onegov
cloud applications.

OneGov cli commands are usually ran against a onegov.yml config file, which
may contain definitions for multiple applications. It may define multiple
application with different applicaiton classes and it may contain wildcard
applications which run the same application class, but contain multiple
tennants for each application.

To have a command run against one or many applications we use a selector to
help select the applications we want to target in a command.

In addition to selectors, onegov core cli commands provide a simple way to
write a function that takes a request and an application. This function is
then called for each application matching the selector, with a proper
request and application context already setup (with the same characteristics
as if called through an url in the browser).

Selector
--------

A selector has the form <namespace>/<id>.

That is, it consists of the namespace of the application and it's id.

For example:

    * ``/foo/bar``
    * ``/onegov_election_day/gr``
    * ``/onegov_town/govikon``

To select non-wildcard applications we can just omit the id:

    * ``/foo``
    * ``/onegov_onboarding``

Finally, to select multiple applications we can use wildcards:

    * ``/foo/*``
    * ``/onegov_election_day/*``
    * ``/*/g??``

Execution
---------

To run a supported command we provide a selector as an option::

    bin/onegov-core --select '/foo/*' subcommand

To find out what kind of selectors are available, we can simply run::

    bin/onegov-core

Which will print out a list of selector suggestions.

Registering a Selector Based Command
------------------------------------

To write a selector based command we first create a command group::

    from onegov.core.cli import command_group
    cli = command_group()

Using that command group, we can register our own commands::

    @cli.command()
    def my_click_command():
        pass

This command works like any other click command::

    import click

    @cli.command()
    @click.option('--option')
    def my_click_command(option):
        pass

Each command has the ability to influence the way selectors work. For example,
a command which creates the path that matches the selector we can use::

    @cli.command(context_settings={'creates_path': True})

By default we expect that a selector is passed. For commands which usually run
against all applications we can provide a default selector::

    @cli.command(context_settings={'default_selector': '*'})

Using the app/request context
-----------------------------

For a lot of commands the easiest approach is to have a function which is
called for each application with a request. This allows us to write commands
which behave like they were written in a view.

To do that we register a command which returns a function with the following
signature::

    def handle_command(request, app):
        pass

For example::

    @cli.command()
    def my_click_command():

        def handle_command(request, app):
            pass

        return handle_command

Setup like this, ``handle_command`` will be called with a request for each
application (and tennant). This function acts exactly like a view. Most
importantly, it does *not* require transaction commits, because like with
ordinary requests, the transaction is automatically committed if no error
occurs.

Using the app configurations directly
-------------------------------------

Sometimes we don't want to use the request/app context, or maybe we want to
setup something before receiving a request.

To do this, we use the ``pass_group_context`` decorator.

For example::

    from onegov.core.cli import pass_group_context

    @cli.command()
    @pass_group_context
    def my_click_command(group_context):

        for appcfg in group_context.appcfgs:
            # do something

This is independent of the app/request context. If we return a function, the
function is going to be called with the request and the app. If we do not, the
command ends as expected.

Returning multiple functions
----------------------------

When a cli command returns multiple functions, they are run in succession.

The signature is taken into account. If there's a 'request' parameter in the
function, the usual request context is set up.

If there is no 'request' parameter in the function, it is called once per
appcfg, together with the group context::

    @cli.command()
    def my_special_command():

        def handle_command(request, app):
            pass

        def handle_raw(group_context, appcfg):
            pass

        return (handle_command, handle_raw)

Limiting Selectors to a Single Instance
---------------------------------------

Sometimes we want to write commands which only run against a single
application. A good example is a command which returns 1/0 depending on the
existence of something *in* an application.

To do that, we use::

    @cli.command(context_settings={'singular': True})
    def my_click_command():
        pass

If a selector is passed which matches more than one application, the command
is not executed.

"""

import click
import inspect
import sqlalchemy
import sys

from fnmatch import fnmatch
from onegov.core.orm import Base, SessionManager
from onegov.core.security import Public
from onegov.core.utils import scan_morepath_modules
from onegov.server.config import Config
from onegov.server.core import Server
from sqlalchemy.pool import NullPool
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

    :param selector:
        Selects the applications which should be captured by a
        :func:`command_group`.

        See :ref:`core-commands` for more documentation about
        selectors.

    :param config:
        The targeted onegov.yml file or an equivalent dictionary.

    :param default_selector:
        The selector used if none is provided. If not given, a selector
        *has* to be provided.

    :param creates_path:
        True if the given selector doesn't exist yet, but will be created.
        Commands which use this setting are expected to take a single path
        (no wildcards) and to create it during their runtime.

        Implies `singular` and `matches_required`.

    :param singular:
        True if the selector may not match multiple applications.

    :param matches_required:
        True if the selector *must* match at least one application.

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

        return SessionManager(dsn=dsn, base=Base, pool_config={
            'poolclass': NullPool
        })

    def available_schemas(self, appcfg):
        """ Returns all available schemas, if the application is database
        bound.

        """

        if 'dsn' not in appcfg.configuration:
            return []

        mgr = self.unbound_session_manager(appcfg.configuration['dsn'])
        return mgr.list_schemas(limit_to_namespace=appcfg.namespace)

    def split_match(self, match):
        match = match.lstrip('/')

        if '/' in match:
            return match.split('/', 1)
        else:
            return match, ''

    def match_to_path(self, match):
        """ Takes the given match and returns the application path used in
        http requests.

        """
        namespace, id = self.split_match(match)

        for appcfg in self.config.applications:
            if appcfg.namespace == namespace:
                return appcfg.path.replace('*', id).rstrip('/')

    def match_to_appcfg(self, match):
        """ Takes the given match and returns the maching appcfg object. """

        namespace, id = self.split_match(match)

        for appcfg in self.config.applications:
            if appcfg.namespace == namespace:
                return appcfg

    @property
    def appcfgs(self):
        """ Returns the matching appconfigs.

        Since there's only one appconfig per namespace, we ignore the path
        part of the selector and only focus on the namespace::

            /namespace/application_id

        """
        namespace_selector = self.selector.lstrip('/').split('/')[0]

        for appcfg in self.config.applications:
            if fnmatch(appcfg.namespace, namespace_selector):
                yield appcfg

    @property
    def available_selectors(self):
        """ Generates a list of available selectors.

        The list doesn't technically exhaust all options, but it returns
        all selectors targeting a single application as well as all selectors
        targeting a namespace by wildcard.

        """
        selectors = list(self.all_wildcard_selectors)
        selectors.extend(self.all_specific_selectors)

        return sorted(selectors)

    @property
    def all_wildcard_selectors(self):
        """ Returns all selectors targeting a namespace by wildcard. """

        for appcfg in self.config.applications:
            if appcfg.path.endswith('*'):
                yield '/' + appcfg.namespace + '/*'

    @property
    def all_specific_selectors(self):
        """ Returns all selectors targeting an application directly. """

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
    """ Takes the given *click* context and extracts all context specific
    settings from it.

    """

    if not context.invoked_subcommand:
        return {}

    # The context settings are stored on the command though they are actually
    # click's settings, not ours. Upon inspection we need to transfer them
    # here as a result. It's basically a piggy back ride.
    subcommand = context.command.commands[context.invoked_subcommand]
    if not hasattr(subcommand, 'onegov_settings'):
        subcommand.onegov_settings = {
            key: subcommand.context_settings.pop(key)
            for key in CONTEXT_SPECIFIC_SETTINGS
            if key in subcommand.context_settings
        }

    return subcommand.onegov_settings


#: Decorator to acquire the group context on a command::
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
        try:
            context = click.get_current_context()
            context_settings = get_context_specific_settings(context)
            context.obj = GroupContext(select, config, **context_settings)
            context.obj.validate_guard_conditions(context)
        except sqlalchemy.exc.OperationalError as e:
            if "Connection refused" in ' '.join(e.args):
                print(e)
                sys.exit(1)
            else:
                raise

    @command_group.resultcallback()
    def process_results(processor, select, config):
        """ Calls the function returned by the command once for each
        application matching the selector.

        Uses a proper request/application context for ease of use.

        """

        if not processor:
            return

        if callable(processor):
            processors = (processor, )
        else:
            processors = processor

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

                def configure_debug(self, **cfg):
                    # disable debug options in cli (like query output)
                    pass

            @CliApplication.path(path=view_path)
            class Model(object):
                pass

            @CliApplication.view(model=Model, permission=Public)
            def run_command(self, request):
                processor(request, request.app)

            @CliApplication.setting(section='cronjobs', name='enabled')
            def get_cronjobs_enabled():
                return False

            @CliApplication.setting_section(section='roles')
            def get_roles_setting():
                # override the security settings -> we need the public
                # role to work for anonymous users, even if the base
                # application disables that
                return {
                    'anonymous': {Public},
                }

            scan_morepath_modules(CliApplication)
            CliApplication.commit()

            applications.append({
                'path': appcfg.path,
                'application': CliApplication,
                'namespace': appcfg.namespace,
                'configuration': appcfg.configuration
            })

        server = Server(
            Config({
                'applications': applications,
                'logging': group_context.config.logging
            }),
            configure_morepath=False
        )

        def expects_request(processor):
            return 'request' in processor.__code__.co_varnames

        # call the matching applications
        client = Client(server)
        matches = list(group_context.matches)

        for match in matches:
            for processor in processors:
                if expects_request(processor):
                    path = group_context.match_to_path(match)
                    client.get(path + '/' + view_path)
                else:
                    appcfg = group_context.match_to_appcfg(match)
                    processor(group_context, appcfg)

    return command_group


def abort(msg):
    """ Prints the given error message and aborts the program with a return
    code of 1.

    """
    click.secho(msg, fg='red')

    sys.exit(1)
