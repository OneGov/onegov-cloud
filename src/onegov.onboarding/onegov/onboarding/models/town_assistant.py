import morepath
import re

from libres.context.registry import create_default_registry
from onegov.core import utils
from onegov.core.crypto import random_password
from onegov.onboarding import _
from onegov.onboarding.errors import AlreadyExistsError
from onegov.onboarding.forms import TownForm, TownSettingsForm
from onegov.onboarding.models.assistant import Assistant
from onegov.town.initial_content import add_initial_content
from onegov.town.models import Town
from onegov.user import UserCollection

_valid_subdomain = re.compile(r'^[a-z0-9]+[a-z0-9-]+[a-z0-9]+$')


class TownAssistant(Assistant):
    """ An assistant guiding a user through onegov.town onboarding. """

    @Assistant.step(form=TownForm)
    def first_step(self, request, form):

        if form.submitted(request):
            request.browser_session['name'] = form.data['name']
            request.browser_session['user'] = form.data['user']

            return morepath.redirect(request.link(self.for_next_step()))

        return {
            'title': _("Online Counter for Towns Demo"),
            'bullets': (
                _("Start using the online counter for your town immediately."),
                _("Setup takes less than one minute."),
                _("Free with no commitment."),
                _("Try before you buy.")
            )
        }

    @Assistant.step(form=TownSettingsForm)
    def second_step(self, request, form):

        for key in ('name', 'user'):
            if not request.browser_session.has(key):
                return morepath.redirect(request.link(self.for_prev_step()))

        if form.submitted(request):
            request.browser_session['color'] = form.data['color'].get_hex()

            return morepath.redirect(request.link(self.for_next_step()))

        return {
            'title': _("Online Counter for Towns Demo"),
            'bullets': (
                _("Start using the online counter for your town immediately."),
                _("Setup takes less than one minute."),
                _("Free with no commitment."),
                _("Try before you buy.")
            )
        }

    @Assistant.step(form=None)
    def last_step(self, request):

        for key in ('name', 'user', 'color'):
            if not request.browser_session.has(key):
                return morepath.redirect(request.link(self.for_first_step()))

        name = request.browser_session['name']
        user = request.browser_session['user']
        color = request.browser_session['color']

        try:
            product = self.add_town(request.app, name, user, color)
            error = None
        except AlreadyExistsError:
            product = None
            error = _(
                "This town exists already and can't be created. Is it your "
                "town but you did not create it? Please contact us."
            )

        return {
            'title': _("Online Counter for Towns Demo"),
            'bullets': (
                _("Start using the online counter for your town immediately."),
                _("Setup takes less than one minute."),
                _("Free with no commitment."),
                _("Try before you buy.")
            ),
            'product': product,
            'error': error
        }

    def add_town(self, app, name, user, color):
        config = app.onboarding['onegov.town']

        subdomain = utils.normalize_for_url(name)
        domain = '{}.{}'.format(subdomain, config['domain'])

        new_schema = '{}-{}'.format(
            config['namespace'], subdomain.replace('-', '_'))

        current_schema = app.session_manager.current_schema
        password = random_password(16)

        try:
            app.session_manager.set_current_schema(new_schema)

            if app.session_manager.session().query(Town).first():
                raise AlreadyExistsError

            add_initial_content(
                libres_registry=create_default_registry(),
                session_manager=app.session_manager,
                town_name=name
            )

            town = app.session_manager.session().query(Town).first()
            town.theme_options['primary-color'] = color

            users = UserCollection(app.session_manager.session())
            assert not users.query().first()

            users.add(user, password, 'admin')

        finally:
            app.session_manager.set_current_schema(current_schema)

        return {
            'info': [
                (_("Name"), name),
                (_("Domain"), domain),
                (_("Username"), user),
                (_("Password"), password),
            ],
            'url': 'https://{}'.format(domain)
        }
