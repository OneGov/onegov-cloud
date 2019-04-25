import random

from cached_property import cached_property
from onegov.activity import Period, PeriodCollection, InvoiceCollection
from onegov.activity.models.invoice_reference import Schema
from onegov.core import utils
from onegov.core.orm import orm_cached
from onegov.feriennet.initial_content import create_new_organisation
from onegov.feriennet.request import FeriennetRequest
from onegov.feriennet.sponsors import load_sponsors
from onegov.feriennet.theme import FeriennetTheme
from onegov.org import OrgApp
from onegov.org.app import get_common_asset as default_common_asset
from onegov.org.app import get_i18n_localedirs as default_i18n_localedirs
from onegov.org.app import get_public_ticket_messages \
    as default_public_ticket_messages
from onegov.user import User, UserCollection


BANNER_TEMPLATE = """
<div class="sponsor-banner">
    <div class="sponsor-banner-{id}">
        <a href="{url}">
            <img src="{src}">
        </a>
        <img src="{tracker}"
                 border="0"
                 height="1"
                 width="1"
                 onerror="
                    this.getAttribute('src').length != 0
                    && this.parentNode.parentNode.remove()
                 "
                 alt="Advertisement">
    </div>
</div>
"""


class FeriennetApp(OrgApp):

    #: the version of this application (do not change manually!)
    version = '1.6.5'

    request_class = FeriennetRequest

    def es_may_use_private_search(self, request):
        return request.is_admin

    @orm_cached(policy='on-table-change:periods')
    def active_period(self):
        return PeriodCollection(self.session()).active()

    @orm_cached(policy='on-table-change:periods')
    def periods(self):
        p = PeriodCollection(self.session()).query()
        p = p.order_by(Period.execution_start)

        return p

    @orm_cached(policy='on-table-change:periods')
    def periods_by_id(self):
        return {
            p.id.hex: p for p in PeriodCollection(self.session()).query()
        }

    @orm_cached(policy='on-table-change:users')
    def user_titles_by_name(self):
        return dict(UserCollection(self.session()).query().with_entities(
            User.username, User.title))

    @orm_cached(policy='on-table-change:users')
    def user_ids_by_name(self):
        return dict(UserCollection(self.session()).query().with_entities(
            User.username, User.id))

    @cached_property
    def sponsors(self):
        return load_sponsors(utils.module_path('onegov.feriennet', 'sponsors'))

    @property
    def default_period(self):
        return self.active_period or self.periods and self.periods[0]

    @property
    def public_organiser_data(self):
        return self.org.meta.get('public_organiser_data', ('name', 'website'))

    def banner(self, request, id):
        """ Randomly returns the html to one of the available booking banners.

        """
        candidates = [
            sponsor for sponsor in self.sponsors
            if getattr(sponsor, 'banners', None) and id in sponsor.banners
        ]

        if not candidates:
            return None

        winner = random.choice(candidates)
        winner = winner.compiled(request)

        return BANNER_TEMPLATE.format(
            id=id,
            src=winner.url_for(request, winner.banners[id]['src']),
            url=winner.banners[id]['url'],
            tracker=winner.banners[id].get('tracker', '')
        )

    def configure_organisation(self, **cfg):
        cfg.setdefault('enable_user_registration', True)
        cfg.setdefault('enable_yubikey', False)
        super().configure_organisation(**cfg)

    def invoice_schema_config(self):
        """ Returns the currently active schema_name and it's config. """
        schema_name = self.org.meta.get(
            'bank_reference_schema', 'feriennet-v1')

        if schema_name == 'raiffeisen-v1':
            schema_config = {
                'esr_identification_number': self.org.meta.get(
                    'bank_esr_identification_number'
                )
            }
        else:
            schema_config = None

        return schema_name, schema_config

    def invoice_collection(self, period_id=None, user_id=None):
        """ Returns the invoice collection guaranteed to be configured
        according to the organisation's settings.

        """
        schema_name, schema_config = self.invoice_schema_config()

        return InvoiceCollection(
            self.session(),
            period_id=period_id,
            user_id=user_id,
            schema=schema_name,
            schema_config=schema_config
        )

    def invoice_bucket(self):
        """ Returns the active invoice reference bucket. """

        return Schema.render_bucket(*self.invoice_schema_config())


@FeriennetApp.template_directory()
def get_template_directory():
    return 'templates'


@FeriennetApp.setting(section='org', name='create_new_organisation')
def get_create_new_organisation_factory():
    return create_new_organisation


@FeriennetApp.setting(section='org', name='status_mail_roles')
def get_status_mail_roles():
    return ('admin', )


@FeriennetApp.setting(section='org', name='ticket_manager_roles')
def get_ticket_manager_roles():
    return ('admin', )


@FeriennetApp.setting(section='org', name='public_ticket_messages')
def get_public_ticket_messages():
    return (*default_public_ticket_messages(), 'activity')


@FeriennetApp.setting(section='org', name='require_complete_userprofile')
def get_require_complete_userprofile():
    return True


@FeriennetApp.setting(section='org', name='is_complete_userprofile')
def get_is_complete_userprofile_handler():
    from onegov.feriennet.forms import UserProfileForm

    def is_complete_userprofile(request, username, user=None):
        user = user or UserCollection(
            request.session).by_username(username)

        form = UserProfileForm()
        form.request = request
        form.model = user
        form.on_request()

        form.process(obj=user)

        for field_id, field in form._fields.items():
            field.raw_data = field.data

        return form.validate()

    return is_complete_userprofile


@FeriennetApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs():
    return [utils.module_path('onegov.feriennet', 'locale')] \
        + default_i18n_localedirs()


@FeriennetApp.setting(section='core', name='theme')
def get_theme():
    return FeriennetTheme()


@FeriennetApp.static_directory()
def get_static_directory():
    return 'static'


@FeriennetApp.webasset_path()
def get_js_path():
    return 'assets/js'


@FeriennetApp.webasset('common')
def get_common_asset():
    yield from default_common_asset()
    yield 'reloadfrom.js'
    yield 'printthis.js'
    yield 'print.js'
    yield 'click-to-load.js'
    yield 'tracking.js'
