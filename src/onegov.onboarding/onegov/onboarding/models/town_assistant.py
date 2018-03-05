import morepath
import re

from onegov.core import utils
from onegov.core.crypto import random_password
from onegov.core.templates import render_template
from onegov.onboarding import _
from onegov.onboarding.errors import AlreadyExistsError
from onegov.onboarding.forms import FinishForm, TownForm
from onegov.onboarding.layout import MailLayout
from onegov.onboarding.models.assistant import Assistant
from onegov.town.initial_content import create_new_organisation
from onegov.org.models import Organisation
from onegov.user import UserCollection

_valid_subdomain = re.compile(r'^[a-z0-9]+[a-z0-9-]+[a-z0-9]+$')


class TownAssistant(Assistant):
    """ An assistant guiding a user through onegov.town onboarding. """

    @Assistant.step(form=TownForm)
    def first_step(self, request, form):

        if form.submitted(request):
            request.browser_session['name'] = form.data['name']
            request.browser_session['user'] = form.data['user']
            request.browser_session['color'] = form.data['color'].get_hex()

            return morepath.redirect(request.link(self.for_next_step()))

        form.name.data = request.browser_session.get('name', form.name.data)
        form.user.data = request.browser_session.get('user', form.user.data)
        form.color.data = request.browser_session.get('color', form.color.data)

        return {
            'name': 'town-start',
            'title': _("Online Counter for Towns Demo"),
            'bullets': (
                _("Start using the online counter for your town immediately."),
                _("Setup takes less than one minute."),
                _("Free with no commitment.")
            ),
        }

    @Assistant.step(form=FinishForm)
    def last_step(self, request, form):

        for key in ('name', 'user', 'color'):
            if not request.browser_session.has(key):
                return morepath.redirect(request.link(self.for_prev_step()))

        name = request.browser_session['name']
        user = request.browser_session['user']
        color = request.browser_session['color']

        if form.submitted(request):
            try:
                product = self.add_town(name, user, color, request)
                error = None
            except AlreadyExistsError:
                product = None
                error = _(
                    "This town exists already and can't be created. Is it "
                    "your town but you did not create it? Please contact us."
                )
            else:
                self.app.send_hipchat(
                    'Onboarding',
                    (
                        'A new OneGov Cloud instance was started by {}: '
                        '<a href="{}">{}</a>'
                    ).format(user, product['url'], name)
                )
            finally:
                del request.browser_session['name']
                del request.browser_session['user']
                del request.browser_session['color']

            if error:
                return {
                    'name': 'town-error',
                    'title': _("Online Counter for Towns Demo"),
                    'error': error,
                    'form': None
                }
            else:
                return {
                    'name': 'town-success',
                    'title': _("Online Counter for Towns Demo"),
                    'product': product,
                    'message': _("Success! Have a look at your new website!"),
                    'warning': _(
                        "Please write down your username and password "
                        "before you continue. "
                    ),
                    'form': None
                }

        return {
            'name': 'town-ready',
            'title': _("Online Counter for Towns Demo"),
            'message': _(
                "We are ready to launch! Click continue once you're ready."
            ),
            'preview': {
                'name': name,
                'user': user,
                'domain': self.get_domain(name),
                'color': color
            },
            'cancel': request.link(self.for_prev_step())
        }

    @property
    def config(self):
        return self.app.onboarding['onegov.town']

    def get_subdomain(self, name):
        return utils.normalize_for_url(name)

    def get_domain(self, name):
        return '{}.{}'.format(self.get_subdomain(name), self.config['domain'])

    def get_schema(self, name):
        return '{}-{}'.format(
            self.config['namespace'],
            self.get_subdomain(name).replace('-', '_')
        )

    def add_town(self, name, user, color, request):
        current_schema = self.app.session_manager.current_schema
        password = random_password(16)

        try:
            schema = self.get_schema(name)
            custom_config = self.config['configuration']

            self.app.session_manager.set_current_schema(schema)
            session = self.app.session_manager.session()

            if session.query(Organisation).first():
                raise AlreadyExistsError

            with self.app.temporary_depot(schema, **custom_config):
                create_new_organisation(self.app, name=name, reply_to=user)

            org = session.query(Organisation).first()
            org.theme_options['primary-color'] = color

            users = UserCollection(self.app.session_manager.session())
            assert not users.query().first()

            users.add(user, password, 'admin')

            title = request.translate(_("Welcome to OneGov Cloud"))
            welcome_mail = render_template('mail_welcome.pt', request, {
                'url': 'https://{}'.format(self.get_domain(name)),
                'mail': user,
                'layout': MailLayout(self, request),
                'title': title,
                'org': name
            })

            self.app.es_perform_reindex()
            self.app.send_transactional_email(
                subject=title,
                receivers=(user, ),
                content=welcome_mail,
                reply_to='onegov@seantis.ch'
            )

        finally:
            self.app.session_manager.set_current_schema(current_schema)

        return {
            'info': [
                (_("Username"), user),
                (_("Password"), password),
            ],
            'url': 'https://{}'.format(self.get_domain(name))
        }
