from __future__ import annotations

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
from onegov.town6.initial_content import create_new_organisation
from onegov.org.models import Organisation
from onegov.user import UserCollection


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.request import CoreRequest
    from onegov.core.types import RenderData
    from webob import Response


_valid_subdomain = re.compile(r'^[a-z0-9]+[a-z0-9-]+[a-z0-9]+$')


class TownAssistant(Assistant):
    """ An assistant guiding a user through onegov.town6 onboarding. """

    @Assistant.step(form=TownForm)
    def first_step(
        self,
        request: CoreRequest,
        form: TownForm
    ) -> RenderData | Response:

        if form.submitted(request):
            request.browser_session['name'] = form.name.data
            request.browser_session['user'] = form.user.data
            request.browser_session['user_name'] = form.user_name.data
            request.browser_session['phone_number'] = form.phone_number.data
            request.browser_session['color'] = form.color.data

            return morepath.redirect(request.link(self.for_next_step()))

        form.name.data = request.browser_session.get('name', form.name.data)
        form.user.data = request.browser_session.get('user', form.user.data)
        form.color.data = request.browser_session.get('color', form.color.data)
        form.user_name.data = request.browser_session.get(
            'user_name', form.user_name.data
        )
        form.phone_number.data = request.browser_session.get(
            'phone_number', form.phone_number.data
        )

        return {
            'name': 'town-start',
            'title': _('Online Counter for Towns Demo'),
            'bullets': (
                _('Start using the online counter for your town immediately.'),
                _('Setup takes less than one minute.'),
                _('Free with no commitment.')
            ),
        }

    @Assistant.step(form=FinishForm)
    def last_step(
        self,
        request: CoreRequest,
        form: FinishForm
    ) -> RenderData | Response:

        for key in ('name', 'user', 'color'):
            if not request.browser_session.has(key):
                return morepath.redirect(request.link(self.for_prev_step()))

        name = request.browser_session['name']
        user_name = request.browser_session['user_name']
        phone_number = request.browser_session['phone_number']
        user = request.browser_session['user']
        color = request.browser_session['color']

        if form.submitted(request):
            try:
                product = self.add_town(name, user, color, request)
                error = None

                self.app.send_zulip(
                    subject='OneGov Onboarding',
                    content='\n'.join((
                        f'A new OneGov Cloud instance was started by '
                        f'{user_name}:',
                        f"[{name}]({product['url']})",
                        f'Email: {user}',
                        f'Phone: {phone_number}'
                    ))
                )
            except AlreadyExistsError:
                product = None
                error = _(
                    "This town exists already and can't be created. Is it "
                    "your town but you did not create it? Please contact us."
                )
            finally:
                del request.browser_session['name']
                del request.browser_session['user']
                del request.browser_session['color']
                del request.browser_session['phone_number']
                del request.browser_session['user_name']

            if error:
                return {
                    'name': 'town-error',
                    'title': _('Online Counter for Towns Demo'),
                    'error': error,
                    'form': None
                }
            else:
                return {
                    'name': 'town-success',
                    'title': _('Online Counter for Towns Demo'),
                    'product': product,
                    'message': _('Success! Have a look at your new website!'),
                    'warning': _(
                        'Please write down your username and password '
                        'before you continue. '
                    ),
                    'form': None
                }

        return {
            'name': 'town-ready',
            'title': _('Online Counter for Towns Demo'),
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
    def config(self) -> dict[str, Any]:
        return self.app.onboarding['onegov.town6']

    def get_subdomain(self, name: str) -> str:
        return utils.normalize_for_url(name)

    def get_domain(self, name: str) -> str:
        return '{}.{}'.format(self.get_subdomain(name), self.config['domain'])

    def get_schema(self, name: str) -> str:
        return '{}-{}'.format(
            self.config['namespace'],
            self.get_subdomain(name).replace('-', '_')
        )

    def add_town(
        self,
        name: str,
        user: str,
        color: str,
        request: CoreRequest
    ) -> RenderData:

        current_schema = self.app.session_manager.current_schema
        assert current_schema is not None
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
            assert org is not None and org.theme_options is not None
            org.theme_options['primary-color-ui'] = color

            users = UserCollection(self.app.session_manager.session())
            assert not users.query().first()

            users.add(user, password, 'admin')

            title = request.translate(_('Welcome to OneGov Cloud'))
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
                (_('Username'), user),
                (_('Password'), password),
            ],
            'url': 'https://{}'.format(self.get_domain(name))
        }
