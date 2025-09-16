""" The settings view, defining things like the logo or color of the org. """
from __future__ import annotations

from copy import copy
from dectate import Query
from markupsafe import Markup
from webob.exc import HTTPForbidden
from onegov.core.elements import Link, Confirm, Intercooler, BackLink
from onegov.core.security import Secret
from onegov.core.templates import render_macro
from onegov.form import Form
from onegov.org import _
from onegov.org.forms import AnalyticsSettingsForm
from onegov.org.forms import FooterSettingsForm
from onegov.org.forms import GeneralSettingsForm
from onegov.org.forms import HolidaySettingsForm
from onegov.org.forms import HomepageSettingsForm
from onegov.org.forms import MapSettingsForm
from onegov.org.forms import ModuleSettingsForm
from onegov.org.forms.settings import (
    OrgTicketSettingsForm, HeaderSettingsForm, FaviconSettingsForm,
    LinksSettingsForm, NewsletterSettingsForm, LinkMigrationForm,
    LinkHealthCheckForm, PeopleSettingsForm, SocialMediaSettingsForm,
    GeverSettingsForm, OneGovApiSettingsForm, DataRetentionPolicyForm,
    VATSettingsForm, EventSettingsForm, KabaSettingsForm,
    CitizenLoginSettingsForm, ResourceSettingsForm)
from onegov.org.management import LinkHealthCheck
from onegov.org.layout import DefaultLayout
from onegov.org.layout import SettingsLayout
from onegov.org.management import LinkMigration
from onegov.org.models import Organisation
from onegov.org.models import SwissHolidays
from onegov.api.models import ApiKey
from onegov.org.app import OrgApp
from uuid import uuid4
from webob.exc import HTTPNotFound


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.core.types import RenderData
    from onegov.org.request import OrgRequest
    from typing import type_check_only
    from webob import Response

    @type_check_only
    class ApiKeyWithDeleteLink(ApiKey):
        delete_link: Link


@OrgApp.html(
    model=Organisation,
    name='settings',
    template='settings.pt',
    permission=Secret
)
def view_settings(
    self: Organisation,
    request: OrgRequest,
    layout: SettingsLayout | None = None
) -> RenderData:

    layout = layout or SettingsLayout(self, request)

    def query_settings() -> Iterator[dict[str, Any]]:
        q = Query('view').filter(model=Organisation)

        for action, fn in q(request.app):
            if 'setting' in action.predicates:
                setting = copy(action.predicates)
                # exclude this setting view if it's disabled for the app
                if (
                    setting['name'] == 'citizen-login-settings'
                    and not request.app.settings.org.citizen_login_enabled
                ):
                    continue
                setting['title'] = setting['setting']
                setting['link'] = request.link(self, name=setting['name'])

                yield setting

    settings = list(query_settings())
    settings.sort(key=lambda s: s.get('order', 0))

    return {
        'layout': layout,
        'title': _('Settings'),
        'settings': settings
    }


def handle_generic_settings(
    self: Organisation,
    request: OrgRequest,
    form: Form,
    title: str,
    layout: SettingsLayout | None = None,
    subtitle: str | None = None
) -> RenderData | Response:

    layout = layout or SettingsLayout(self, request, title)
    layout.edit_mode = True
    layout.editmode_links[1] = BackLink(attrs={'class': 'cancel-link'})
    request.include('fontpreview')

    if form.submitted(request):
        form.populate_obj(self)

        request.success(_('Your changes were saved'))
        return request.redirect(request.link(self, name='settings'))
    elif request.method == 'GET':
        form.process(obj=self)

    return {
        'layout': layout,
        'title': title,
        'form': form,
        'subtitle': subtitle
    }


@OrgApp.form(
    model=Organisation, name='general-settings', template='form.pt',
    permission=Secret, form=GeneralSettingsForm, setting=_('General'),
    icon='fa-sliders', order=-1000)
def handle_general_settings(
    self: Organisation,
    request: OrgRequest,
    form: GeneralSettingsForm,
    layout: SettingsLayout | None = None
) -> RenderData | Response:
    return handle_generic_settings(self, request, form, _('General'), layout)


@OrgApp.form(
    model=Organisation, name='homepage-settings', template='form.pt',
    permission=Secret, form=HomepageSettingsForm, setting=_('Homepage'),
    icon='fa-home', order=-995)
def handle_homepage_settings(
    self: Organisation,
    request: OrgRequest,
    form: HomepageSettingsForm,
    layout: SettingsLayout | None = None
) -> RenderData | Response:
    return handle_generic_settings(self, request, form, _('Homepage'), layout)


@OrgApp.form(
    model=Organisation, name='favicon-settings', template='form.pt',
    permission=Secret, form=FaviconSettingsForm, setting=_('Favicon'),
    icon=' fa-external-link-square', order=-990)
def handle_favicon_settings(
    self: Organisation,
    request: OrgRequest,
    form: FaviconSettingsForm,
    layout: SettingsLayout | None = None
) -> RenderData | Response:
    return handle_generic_settings(self, request, form, _('Favicon'), layout)


@OrgApp.form(
    model=Organisation, name='social-media-settings', template='form.pt',
    permission=Secret, form=SocialMediaSettingsForm, setting=_('Social Media'),
    icon=' fa fa-share-alt', order=-985)
def handle_social_media_settings(
    self: Organisation,
    request: OrgRequest,
    form: SocialMediaSettingsForm,
    layout: SettingsLayout | None = None
) -> RenderData | Response:
    return handle_generic_settings(
        self, request, form, _('Social Media'), layout)


@OrgApp.form(
    model=Organisation, name='link-settings', template='form.pt',
    permission=Secret, form=LinksSettingsForm, setting=_('Links'),
    icon=' fa-link', order=-980)
def handle_links_settings(
    self: Organisation,
    request: OrgRequest,
    form: LinksSettingsForm,
    layout: SettingsLayout | None = None
) -> RenderData | Response:
    return handle_generic_settings(self, request, form, _('Links'), layout)


@OrgApp.form(
    model=Organisation, name='newsletter-settings', template='form.pt',
    permission=Secret, form=NewsletterSettingsForm,
    setting=_('Newsletter'), order=-951, icon='far fa-paper-plane'
)
def handle_newsletter_settings(
    self: Organisation,
    request: OrgRequest,
    form: NewsletterSettingsForm,
    layout: SettingsLayout | None = None
) -> RenderData | Response:
    return handle_generic_settings(
        self, request, form, _('Newsletter'), layout
    )


@OrgApp.form(
    model=Organisation, name='ticket-settings', template='form.pt',
    permission=Secret, form=OrgTicketSettingsForm,
    setting=_('Tickets'), order=-950, icon='fa-ticket'
)
def handle_ticket_settings(
    self: Organisation,
    request: OrgRequest,
    form: OrgTicketSettingsForm,
    layout: SettingsLayout | None = None
) -> RenderData | Response:
    resp = handle_generic_settings(
        self, request, form, _('Tickets'), layout)
    return resp


@OrgApp.form(
    model=Organisation, name='header-settings', template='form.pt',
    permission=Secret, form=HeaderSettingsForm, setting=_('Header'),
    icon='fa-window-maximize', order=-810)
def handle_header_settings(
    self: Organisation,
    request: OrgRequest,
    form: Form,
    layout: SettingsLayout | None = None
) -> RenderData | Response:
    layout = layout or SettingsLayout(self, request, _('Header'))
    return handle_generic_settings(self, request, form, _('Header'), layout)


@OrgApp.form(
    model=Organisation, name='footer-settings', template='form.pt',
    permission=Secret, form=FooterSettingsForm, setting=_('Footer'),
    icon='fa-window-minimize', order=-800)
def handle_footer_settings(
    self: Organisation,
    request: OrgRequest,
    form: FooterSettingsForm,
    layout: SettingsLayout | None = None
) -> RenderData | Response:
    return handle_generic_settings(self, request, form, _('Footer'), layout)


@OrgApp.form(
    model=Organisation, name='module-settings', template='form.pt',
    permission=Secret, form=ModuleSettingsForm, setting=_('Modules'),
    icon='fa-sitemap', order=-700)
def handle_module_settings(
    self: Organisation,
    request: OrgRequest,
    form: ModuleSettingsForm,
    layout: SettingsLayout | None = None
) -> RenderData | Response:
    return handle_generic_settings(
        self, request, form, _('Modules'), layout)


@OrgApp.form(
    model=Organisation, name='map-settings', template='form.pt',
    permission=Secret, form=MapSettingsForm, setting=_('Map'),
    icon='fa-map-marker', order=-700)
def handle_map_settings(
    self: Organisation,
    request: OrgRequest,
    form: MapSettingsForm,
    layout: SettingsLayout | None = None
) -> RenderData | Response:
    return handle_generic_settings(self, request, form, _('Map'), layout)


@OrgApp.form(
    model=Organisation, name='analytics-settings', template='form.pt',
    permission=Secret, form=AnalyticsSettingsForm, setting=_('Analytics'),
    icon='fa-line-chart ', order=-600)
def handle_analytics_settings(
    self: Organisation,
    request: OrgRequest,
    form: AnalyticsSettingsForm,
    layout: SettingsLayout | None = None
) -> RenderData | Response:
    return handle_generic_settings(self, request, form, _('Analytics'), layout)


@OrgApp.form(
    model=Organisation, name='gever-credentials', template='form.pt',
    permission=Secret, form=GeverSettingsForm, setting='Gever API',
    icon='fa-key', order=400)
def handle_gever_settings(
    self: Organisation,
    request: OrgRequest,
    form: GeverSettingsForm,
    layout: SettingsLayout | None = None
) -> RenderData | Response:
    return handle_generic_settings(self, request, form, 'Gever API', layout)


@OrgApp.form(
    model=Organisation, name='kaba-settings', template='form.pt',
    permission=Secret, form=KabaSettingsForm, setting='dormakaba API',
    icon='fa-key', order=400)
def handle_kaba_settings(
    self: Organisation,
    request: OrgRequest,
    form: KabaSettingsForm,
    layout: SettingsLayout | None = None
) -> RenderData | Response:
    return handle_generic_settings(
        self, request, form, 'dormakaba API', layout)


@OrgApp.form(
    model=Organisation, name='holiday-settings', template='form.pt',
    permission=Secret, form=HolidaySettingsForm, setting=_('Holidays'),
    icon='fa-calendar-o', order=-500)
def handle_holiday_settings(
    self: Organisation,
    request: OrgRequest,
    form: HolidaySettingsForm,
    layout: SettingsLayout | None = None
) -> RenderData | Response:
    return handle_generic_settings(self, request, form, _('Holidays'), layout)


@OrgApp.form(model=Organisation, name='holiday-settings-preview',
             permission=Secret, form=HolidaySettingsForm)
def preview_holiday_settings(
    self: Organisation,
    request: OrgRequest,
    form: HolidaySettingsForm,
    layout: DefaultLayout | None = None
) -> str:

    layout = layout or DefaultLayout(self, request)

    if form.submitted(request):
        holidays = SwissHolidays(
            cantons=form.holiday_settings.get('cantons', ()),
            other=form.holiday_settings.get('other', ())
        )
    else:
        holidays = SwissHolidays(
            cantons=form.holiday_settings.get('cantons', ())
        )

    if not holidays.all(layout.today().year):
        msg = request.translate(_('No holidays defined'))
        return f'<i class="holidays">{msg}</i>'

    return render_macro(
        layout.macros['holidays'],
        request,
        {
            'holidays': holidays,
            'layout': layout,
            'year': layout.today().year,
        }
    )


@OrgApp.form(
    model=Organisation, name='migrate-links', template='form.pt',
    permission=Secret, form=LinkMigrationForm, setting=_('Link Migration'),
    icon='fa fa-random', order=-400)
def handle_migrate_links(
    self: Organisation,
    request: OrgRequest,
    form: LinkMigrationForm,
    layout: DefaultLayout | None = None
) -> RenderData | Response:

    domain = request.domain
    button_text = _('Migrate')
    test_results = None

    if form.submitted(request):
        assert form.old_domain.data is not None
        test_only = form.test.data
        migration = LinkMigration(
            request,
            old_uri=form.old_domain.data,
            new_uri=request.domain
        )
        total, _grouped = migration.migrate_site_collection(test_only)

        if not test_only:
            request.success(
                _('Migrated ${number} links', mapping={'number': total}))
            return request.redirect(request.link(self, name='settings'))

        test_results = _('Total of ${number} links found.',
                         mapping={'number': total})

    return {
        'title': _('Link Migration'),
        'form': form,
        'layout': layout or DefaultLayout(self, request),
        'helptext': test_results,
        'button_text': button_text,
        'callout': _(
            'Migrates links from the given domain to the current domain '
            '"${domain}".',
            mapping={'domain': domain}
        ),
    }


@OrgApp.form(
    model=Organisation, name='link-check', template='linkcheck.pt',
    permission=Secret, form=LinkHealthCheckForm)
def handle_link_health_check(
    self: Organisation,
    request: OrgRequest,
    form: LinkHealthCheckForm,
    layout: DefaultLayout | None = None
) -> RenderData:

    healthcheck = LinkHealthCheck(request)
    check_responses = None
    stats = None

    if form.submitted(request):
        link_type = form.scope.data
        healthcheck.link_type = link_type
        stats, check_responses = healthcheck.unhealthy_urls()

    url_max_len = 80

    def truncate(text: str) -> str:
        if len(text) > url_max_len:
            return text[0:url_max_len - 1] + '...'
        return text

    return {
        'title': _('Link Check'),
        'form': form,
        'layout': layout or DefaultLayout(self, request),
        'check_responses': check_responses,
        'truncate': truncate,
        'stats': stats,
        'healthcheck': healthcheck
    }


@OrgApp.form(
    model=Organisation, name='event-settings', template='form.pt',
    permission=Secret, form=EventSettingsForm, setting=_('Events'),
    icon='fa-calendar', order=-700)
def handle_event_settings(
    self: Organisation,
    request: OrgRequest,
    form: EventSettingsForm,
    layout: SettingsLayout | None = None
) -> RenderData | Response:
    return handle_generic_settings(self, request, form, _('Events'), layout)


@OrgApp.form(
    model=Organisation, name='resource-settings', template='form.pt',
    permission=Secret, form=ResourceSettingsForm, setting=_('Resources'),
    icon='fa-home')
def handle_resource_settings(
    self: Organisation,
    request: OrgRequest,
    form: ResourceSettingsForm,
    layout: SettingsLayout | None = None
) -> RenderData | Response:
    return handle_generic_settings(self, request, form, _('Resources'), layout)


@OrgApp.form(
    model=Organisation, name='api-keys', template='api_keys.pt',
    permission=Secret, form=OneGovApiSettingsForm, setting=_('OneGov API'),
    icon='fa-key', order=1)
def handle_api_keys(
    self: Organisation,
    request: OrgRequest,
    form: OneGovApiSettingsForm,
    layout: SettingsLayout | None = None
) -> RenderData:
    """Handles the generation of API access keys."""

    request.include('fontpreview')
    title = _('OneGov API')
    user = request.current_user
    if not user:
        raise HTTPForbidden()

    if form.submitted(request):
        assert form.name.data is not None
        key = ApiKey(
            name=form.name.data,
            read_only=form.read_only.data,
            last_used=None,
            key=uuid4(),
            user=user,
        )
        request.session.add(key)
        request.session.flush()
        request.success(_('Your changes were saved'))

    layout = layout or SettingsLayout(self, request, title)

    def current_api_keys_by_user() -> Iterator[ApiKeyWithDeleteLink]:
        for api_key in user.api_keys:
            api_key_delete_link = Link(
                text=Markup('<i class="fa fa-trash" aria-hidden="True"></i>'),
                url=layout.csrf_protected_url(
                    request.link(api_key, name='+delete')),
                traits=(
                    Confirm(
                        _('Do you really want to delete this API key?'),
                        _('This action cannot be undone.'),
                        _('Delete'),
                        _('Cancel'),
                    ),
                    Intercooler(
                        request_method='DELETE',
                        redirect_after=request.link(self, name='api-keys'),
                    ),
                ),
            )
            # delete_link is temporarily stored on the object itself
            api_key.delete_link = api_key_delete_link
            yield api_key

    return {
        'api_keys_list': list(current_api_keys_by_user()),
        'title': title,
        'form': form,
        'layout': layout,
    }


@OrgApp.view(
    model=ApiKey,
    name='delete',
    permission=Secret,
    request_method='DELETE',
)
def delete_api_key(self: ApiKey, request: OrgRequest) -> None:
    request.assert_valid_csrf_token()

    request.session.delete(self)
    request.session.flush()
    request.message(_('ApiKey deleted.'), 'success')


@OrgApp.form(
    model=Organisation, name='data-retention-settings',
    template='form.pt', permission=Secret,
    form=DataRetentionPolicyForm, setting=_('Data Retention Policy'),
    icon='far fa-trash', order=-880,
)
def handle_ticket_data_deletion_settings(
    self: Organisation,
    request: OrgRequest,
    form: DataRetentionPolicyForm
) -> RenderData | Response:
    request.message(_('Proceed with caution. Tickets and the data they '
                      'contain may be irrevocable deleted.'), 'alert')
    return handle_generic_settings(
        self, request, form, _('Data Retention Policy'),
        SettingsLayout(self, request),
    )


@OrgApp.form(
    model=Organisation, name='vat-settings', template='form.pt',
    permission=Secret, form=VATSettingsForm, setting=_('Value Added Tax'),
    icon='fa-file-invoice-dollar', order=450)
def handle_vat_settings(
        self: Organisation,
        request: OrgRequest,
        form: VATSettingsForm,
        layout: SettingsLayout | None = None
) -> RenderData | Response:
    layout = layout or SettingsLayout(self, request, _('Value Added Tax'))
    return handle_generic_settings(self, request, form, _('Value Added Tax'),
                                   layout)


@OrgApp.form(
    model=Organisation, name='chat-settings', template='form.pt',
    permission=Secret, form=Form, setting=_('Chat'),
    icon='fa-window-maximize', order=-810)
def handle_chat_settings(
    self: Organisation,
    request: OrgRequest,
    form: Form,
    layout: SettingsLayout | None = None
) -> RenderData | Response:
    layout = layout or SettingsLayout(self, request, _('Chat'))
    return handle_generic_settings(self, request, form, _('Chat'), layout)


@OrgApp.form(
    model=Organisation, name='people-settings', template='form.pt',
    permission=Secret, form=PeopleSettingsForm, setting=_('People'),
    icon='fa-users', order=400,
)
def handle_people_settings(
    self: Organisation,
    request: OrgRequest,
    form: PeopleSettingsForm,
    layout: SettingsLayout | None = None
) -> RenderData | Response:
    layout = layout or SettingsLayout(self, request, _('People'))
    return handle_generic_settings(
        self, request, form, _('People'), layout
    )


@OrgApp.form(
    model=Organisation, name='citizen-login-settings', template='form.pt',
    permission=Secret, form=CitizenLoginSettingsForm,
    setting=_('Citizen Login'), icon='fa-id-card', order=480,
)
def handle_citizen_login_settings(
    self: Organisation,
    request: OrgRequest,
    form: CitizenLoginSettingsForm,
    layout: SettingsLayout | None = None
) -> RenderData | Response:

    if not request.app.settings.org.citizen_login_enabled:
        raise HTTPNotFound()

    layout = layout or SettingsLayout(self, request, _('Citizen Login'))
    return handle_generic_settings(
        self, request, form, _('Citizen Login'), layout
    )
