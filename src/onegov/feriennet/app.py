from functools import cached_property
from onegov.activity import Period, PeriodCollection, InvoiceCollection
from onegov.activity.models.invoice_reference import Schema
from onegov.core import utils
from onegov.core.orm import orm_cached
from onegov.feriennet.const import DEFAULT_DONATION_AMOUNTS
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
            <p class="banner-info">{info}</p>
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

    def mail_sponsor(self, request):
        sponsors = [
            sponsor.compiled(request) for sponsor in self.sponsors
            if getattr(sponsor, 'mail_url', None)
        ]

        if sponsors:
            sponsors[0].banners['src'] = sponsors[0].url_for(
                request, sponsors[0].banners['src'])

        return sponsors

    @property
    def default_period(self):
        return self.active_period or self.periods and self.periods[0]

    @property
    def public_organiser_data(self):
        return self.org.meta.get('public_organiser_data', ('name', 'website'))

    def get_sponsors(self, request):
        language = request.locale[:2]
        sponsors = [
            sponsor for sponsor in self.sponsors
            if (
                getattr(sponsor, 'banners', None)
                and sponsor.banners.get('src', {}).get(language, None)
            )
        ]

        if not sponsors:
            return None
        else:
            return sponsors

    def banners(self, request):
        sponsors = self.get_sponsors(request)
        banners = []

        for sponsor in sponsors:
            sponsor = sponsor.compiled(request)
            info = sponsor.banners.get('info', None)
            banners.append(
                BANNER_TEMPLATE.format(
                    id=id,
                    src=sponsor.url_for(request, sponsor.banners['src']),
                    url=sponsor.banners['url'],
                    tracker=sponsor.banners.get('tracker', ''),
                    info=info if info else ""
                )
            )

        return banners

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

    @property
    def show_donate(self):
        return self.meta.get('donate', True)

    @property
    def donation_amounts(self):
        return self.meta.get('donation_amounts', DEFAULT_DONATION_AMOUNTS)

    def show_volunteers(self, request):

        if not self.active_period:
            return False

        setting = self.org.meta.get('volunteers', 'disabled')

        if setting == 'enabled':
            return True

        if setting == 'admins' and request.is_admin:
            return True

        return False


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


@FeriennetApp.webasset('volunteer-cart')
def get_volunteer_cart():
    yield 'volunteer-cart.jsx'


@FeriennetApp.webasset('common')
def get_common_asset():
    yield from default_common_asset()
    yield 'reloadfrom.js'
    yield 'printthis.js'
    yield 'print.js'
    yield 'click-to-load.js'
    yield 'tracking.js'
