""" The settings view, defining things like the logo or color of the org. """
from __future__ import annotations

from wtforms.fields import BooleanField, IntegerField

from onegov.core.security import Secret
from onegov.form import Form, merge_forms, move_fields
from onegov.org import _
from onegov.org.elements import Link
from onegov.org.forms.settings import (
    LinksSettingsForm, HeaderSettingsForm,
    FooterSettingsForm, AccessSettingsForm, MapSettingsForm,
    AnalyticsSettingsForm, HolidaySettingsForm, OrgTicketSettingsForm,
    HomepageSettingsForm, NewsletterSettingsForm, LinkMigrationForm,
    LinkHealthCheckForm, OrganisationProfileSettingsForm, PeopleSettingsForm,
    EventSettingsForm, GeverSettingsForm, OneGovApiSettingsForm,
    DataRetentionPolicyForm, FirebaseSettingsForm, VATSettingsForm,
    KabaSettingsForm, ResourceSettingsForm)
from onegov.org.models import Organisation
from onegov.town6.forms.settings import (
    RISSettingsForm, ModuleActivationSettingsForm)
from onegov.org.views.settings import (
    handle_homepage_settings, handle_module_activation_settings,
    handle_organisation_settings, handle_people_settings, view_settings,
    handle_ticket_settings, preview_holiday_settings,
    handle_appearance_settings, handle_links_settings, handle_header_settings,
    handle_footer_settings, handle_access_settings, handle_map_settings,
    handle_analytics_settings, handle_holiday_settings,
    handle_newsletter_settings, handle_generic_settings, handle_migrate_links,
    handle_link_health_check,
    handle_event_settings, handle_api_keys, handle_chat_settings,
    handle_kaba_settings, handle_resource_settings)

from onegov.town6.app import TownApp
from onegov.town6.forms.settings import (
    AppearanceSettingsForm, ChatSettingsForm)
from onegov.town6.layout import SettingsLayout, DefaultLayout


from typing import overload, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


FormT = TypeVar('FormT', bound=Form)


@overload
def get_custom_settings_form(
    model: Organisation,
    request: TownRequest,
    homepage_settings_form: type[FormT]
) -> type[FormT]: ...


@overload
def get_custom_settings_form(
    model: Organisation,
    request: TownRequest,
    homepage_settings_form: None = None
) -> type[HomepageSettingsForm]: ...


def get_custom_settings_form(
    model: Organisation,
    request: TownRequest,
    homepage_settings_form: type[Form] | None = None
) -> type[Form]:

    class CustomFieldsForm(Form):

        news_limit_homepage = IntegerField(
            fieldset=_('News and Events'),
            label=_('Number of news entries on homepage')
        )

        event_limit_homepage = IntegerField(
            fieldset=_('News and Events'),
            label=_('Number of events displayed on homepage')
        )

    return move_fields(
        form_class=merge_forms(
            homepage_settings_form or HomepageSettingsForm, CustomFieldsForm),
        fields=(
            'event_limit_homepage',
            'news_limit_homepage',
        ),
        after='homepage_cover'
    )


def custom_footer_settings_form(
    model: Organisation,
    request: TownRequest
) -> type[FooterSettingsForm]:

    class ExtendedFooterSettings(Form):
        always_show_partners = BooleanField(
            label=_('Show partners on all pages'),
            description=_('Shows the footer on all pages but for admins'),
            fieldset=_('Partner display')
        )

    return merge_forms(FooterSettingsForm, ExtendedFooterSettings)


# General Settings
@TownApp.html(
    model=Organisation,
    name='settings',
    template='settings.pt',
    permission=Secret
)
def view_town_settings(
    self: Organisation,
    request: TownRequest
) -> RenderData:
    return view_settings(self, request, SettingsLayout(self, request))


@TownApp.form(
    model=Organisation, name='organisation-settings', template='form.pt',
    permission=Secret, form=OrganisationProfileSettingsForm,
    setting=_('Organisation Profile'),
    icon='fa-building', order=0, category=_('General'))
def town_handle_organisation_settings(
    self: Organisation,
    request: TownRequest,
    form: OrganisationProfileSettingsForm
) -> RenderData | Response:
    return handle_organisation_settings(
        self, request, form, SettingsLayout(self, request))


@TownApp.form(
    model=Organisation, name='ticket-settings', template='form.pt',
    permission=Secret, form=OrgTicketSettingsForm,
    setting=_('Tickets'), order=10, icon='fa-ticket-alt'
)
def town_handle_ticket_settings(
    self: Organisation,
    request: TownRequest,
    form: OrgTicketSettingsForm
) -> RenderData | Response:
    return handle_ticket_settings(
        self, request, form, SettingsLayout(self, request))


@TownApp.form(model=Organisation, name='homepage-settings', template='form.pt',
              permission=Secret, form=get_custom_settings_form,
              setting=_('Homepage'), icon='fa-home', order=20)
def custom_handle_settings(
    self: Organisation,
    request: TownRequest,
    form: HomepageSettingsForm
) -> RenderData | Response:
    form.delete_field('homepage_cover')

    return handle_homepage_settings(
        self, request, form, SettingsLayout(self, request))


@TownApp.form(
    model=Organisation, name='appearance-settings', template='form.pt',
    permission=Secret, form=AppearanceSettingsForm, setting=_('Appearance'),
    icon='fa-eye', order=30)
def town_handle_appearance_settings(
    self: Organisation,
    request: TownRequest,
    form: AppearanceSettingsForm
) -> RenderData | Response:
    return handle_appearance_settings(
        self, request, form, SettingsLayout(self, request))


@TownApp.form(
    model=Organisation, name='header-settings', template='form.pt',
    permission=Secret, form=HeaderSettingsForm, setting=_('Header'),
    icon='fa-window-maximize', order=40)
def town_handle_header_settings(
    self: Organisation,
    request: TownRequest,
    form: HeaderSettingsForm
) -> RenderData | Response:
    return handle_header_settings(
        self, request, form, SettingsLayout(self, request))


@TownApp.form(
    model=Organisation, name='footer-settings', template='form.pt',
    permission=Secret, form=custom_footer_settings_form, setting=_('Footer'),
    icon='fa-window-minimize', order=50)
def town_handle_footer_settings(
    self: Organisation,
    request: TownRequest,
    form: FooterSettingsForm
) -> RenderData | Response:
    return handle_footer_settings(
        self, request, form, SettingsLayout(self, request))


@TownApp.form(
    model=Organisation, name='data-retention-settings',
    template='form.pt',
    permission=Secret, form=DataRetentionPolicyForm,
    setting=_('Data Retention Policy'), icon='far fa-trash', order=60,
)
def town_handle_ticket_data_deletion_settings(
    self: Organisation,
    request: TownRequest,
    form: DataRetentionPolicyForm
) -> RenderData | Response:
    request.message(_('Proceed with caution. Tickets and the data they '
                      'contain may be irrevocable deleted.'), 'alert')
    return handle_generic_settings(
        self, request, form, _('Data Retention Policy'),
        SettingsLayout(self, request),
    )


@TownApp.form(
    model=Organisation, name='vat-settings', template='form.pt',
    permission=Secret, form=VATSettingsForm, setting=_('Value Added Tax'),
    icon='fa-file-invoice-dollar', order=70
)
def handle_vat_settings(
        self: Organisation,
        request: TownRequest,
        form: VATSettingsForm,
        layout: SettingsLayout | None = None
) -> RenderData | Response:
    layout = layout or SettingsLayout(self, request, _('Value Added Tax'))
    return handle_generic_settings(
        self, request, form, _('Value Added Tax'), layout
    )


@TownApp.form(
    model=Organisation, name='access-settings', template='form.pt',
    permission=Secret, form=AccessSettingsForm, setting=_('Access (mTAN)'),
    icon='fa-lock', order=80)
def town_handle_access_settings(
    self: Organisation,
    request: TownRequest,
    form: AccessSettingsForm
) -> RenderData | Response:
    return handle_access_settings(
        self, request, form, SettingsLayout(self, request))


@TownApp.form(
    model=Organisation, name='link-settings', template='form.pt',
    permission=Secret, form=LinksSettingsForm, setting=_('Links'),
    icon='fa-link', order=90)
def town_handle_links_settings(
    self: Organisation,
    request: TownRequest,
    form: LinksSettingsForm
) -> RenderData | Response:
    return handle_links_settings(
        self, request, form, SettingsLayout(self, request))


@TownApp.form(
    model=Organisation, name='holiday-settings', template='form.pt',
    permission=Secret, form=HolidaySettingsForm, setting=_('Holidays'),
    icon='fa-calendar', order=500)
def town_handle_holiday_settings(
    self: Organisation,
    request: TownRequest,
    form: HolidaySettingsForm
) -> RenderData | Response:
    return handle_holiday_settings(
        self, request, form, SettingsLayout(self, request))


@TownApp.form(
    model=Organisation, name='map-settings', template='form.pt',
    permission=Secret, form=MapSettingsForm, setting=_('Map'),
    icon='fa-map-marker-alt', order=100)
def town_handle_map_settings(
    self: Organisation,
    request: TownRequest,
    form: MapSettingsForm
) -> RenderData | Response:
    return handle_map_settings(
        self, request, form, SettingsLayout(self, request))


@TownApp.form(
    model=Organisation, name='analytics-settings', template='form.pt',
    permission=Secret, form=AnalyticsSettingsForm, setting=_('Analytics'),
    icon='fa-chart-bar ', order=110)
def town_handle_analytics_settings(
    self: Organisation,
    request: TownRequest,
    form: AnalyticsSettingsForm
) -> RenderData | Response:
    return handle_analytics_settings(
        self, request, form, SettingsLayout(self, request))


# Module Settings
@TownApp.form(
    model=Organisation, name='module-activation-settings', template='form.pt',
    permission=Secret, form=ModuleActivationSettingsForm,
    setting=_('Activate/deactivate modules'), order=0, icon='far fa-th-large',
    category=_('Modules')
)
def town_handle_module_activation_settings(
    self: Organisation,
    request: TownRequest,
    form: ModuleActivationSettingsForm
) -> RenderData | Response:
    return handle_module_activation_settings(
        self, request, form, SettingsLayout(self, request)
    )


@TownApp.form(
    model=Organisation, name='newsletter-settings', template='form.pt',
    permission=Secret, form=NewsletterSettingsForm,
    setting=_('Newsletter'), order=10, icon='far fa-paper-plane',
    category=_('Modules')
)
def town_handle_newsletter_settings(
    self: Organisation,
    request: TownRequest,
    form: NewsletterSettingsForm
) -> RenderData | Response:
    return handle_newsletter_settings(
        self, request, form, SettingsLayout(self, request)
    )


@TownApp.form(
    model=Organisation, name='resource-settings', template='form.pt',
    permission=Secret, form=ResourceSettingsForm, setting=_('Resources'),
    icon='fa-building', order=20, category=_('Modules'))
def town_handle_resource(
    self: Organisation,
    request: TownRequest,
    form: ResourceSettingsForm,
    layout: SettingsLayout | None = None
) -> RenderData | Response:
    return handle_resource_settings(
        self, request, form, SettingsLayout(self, request))


@TownApp.form(
    model=Organisation, name='people-settings', template='form.pt',
    permission=Secret, form=PeopleSettingsForm, setting=_('People directory'),
    icon='fa-users', order=30, category=_('Modules')
)
def town_handle_people_settings(
    self: Organisation, request: TownRequest, form: PeopleSettingsForm
) -> RenderData | Response:
    return handle_people_settings(
        self, request, form, SettingsLayout(self, request)
    )


@TownApp.form(
    model=Organisation, name='event-settings', template='form.pt',
    permission=Secret, form=EventSettingsForm, setting=_('Events'),
    icon='fa-calendar-alt', order=40, category=_('Modules'))
def town_handle_event(
    self: Organisation,
    request: TownRequest,
    form: EventSettingsForm
) -> RenderData | Response:
    return handle_event_settings(
        self, request, form, SettingsLayout(self, request)
    )


@TownApp.form(model=Organisation, name='chat-settings', template='form.pt',
              permission=Secret, form=ChatSettingsForm,
              setting=_('Chat'), icon='far fa-comments', order=50,
              category=_('Modules'))
def town_handle_chat_settings(
    self: Organisation,
    request: TownRequest,
    form: ChatSettingsForm
) -> RenderData | Response:
    return handle_chat_settings(
        self, request, form, SettingsLayout(self, request))


@TownApp.form(
    model=Organisation, name='ris-enable', template='form.pt',
    permission=Secret, form=RISSettingsForm,
    setting=_('Ratsinformationssystem'), icon='fa-landmark', order=500,
    category=_('Modules')
)
def town_handle_ris_enable(
    self: Organisation,
    request: TownRequest,
    form: RISSettingsForm
) -> RenderData | Response:
    return handle_generic_settings(
        self, request, form, _('Ratsinformationssystem (RIS)'),
        SettingsLayout(self, request)
    )


# Advanced Settings
@TownApp.form(model=Organisation, name='gever-credentials', template='form.pt',
              permission=Secret, form=GeverSettingsForm,
              setting='Gever API', icon='fa-key', order=30,
              category=_('Advanced Settings'))
def town_handle_gever_settings(
    self: Organisation,
    request: TownRequest,
    form: GeverSettingsForm
) -> RenderData | Response:
    return handle_generic_settings(self, request, form, 'Gever API',
                                   SettingsLayout(self, request))


@TownApp.form(model=Organisation, name='kaba-settings', template='form.pt',
              permission=Secret, form=KabaSettingsForm,
              setting='dormakaba API', icon='fa-key', order=20,
              category=_('Advanced Settings'))
def town_handle_kaba_settings(
    self: Organisation,
    request: TownRequest,
    form: KabaSettingsForm
) -> RenderData | Response:
    return handle_kaba_settings(
        self, request, form, SettingsLayout(self, request))


@TownApp.form(
    model=Organisation,
    name='holiday-settings-preview',
    permission=Secret,
    form=HolidaySettingsForm
)
def town_preview_holiday_settings(
    self: Organisation,
    request: TownRequest,
    form: HolidaySettingsForm
) -> str:
    return preview_holiday_settings(
        self, request, form, DefaultLayout(self, request))


@TownApp.form(
    model=Organisation, name='api-keys', template='api_keys.pt',
    permission=Secret, form=OneGovApiSettingsForm, icon='fa-key',
    setting=_('OneGov API'), order=10, category=_('Advanced Settings'))
def town_handle_api_keys(
    self: Organisation,
    request: TownRequest,
    form: OneGovApiSettingsForm
) -> RenderData | Response:
    return handle_api_keys(self, request, form, SettingsLayout(self, request))


@TownApp.form(
    model=Organisation, name='firebase', template='form.pt',
    permission=Secret, form=FirebaseSettingsForm, setting=_('Firebase (App)'),
    icon='fa-bell', order=40, category=_('Advanced Settings')
)
def town_handle_firebase_settings(
    self: Organisation, request: TownRequest, form: FirebaseSettingsForm
) -> RenderData | Response:
    link_to_push_notfications = request.link(self, '/push-notifications')
    return handle_generic_settings(
        self, request, form, 'Firebase', SettingsLayout(self, request),
        Link(_('Push Notification Overview'),
             url=link_to_push_notfications)(request)
    )


# Settings in Management, not Settings View
@TownApp.form(
    model=Organisation, name='migrate-links', template='form.pt',
    permission=Secret, form=LinkMigrationForm)
def town_handle_migrate_links(
    self: Organisation,
    request: TownRequest,
    form: LinkMigrationForm
) -> RenderData | Response:
    return handle_migrate_links(
        self, request, form, DefaultLayout(self, request)
    )


@TownApp.form(
    model=Organisation, name='link-check', template='linkcheck.pt',
    permission=Secret, form=LinkHealthCheckForm)
def town_handle_link_health_check(
    self: Organisation,
    request: TownRequest,
    form: LinkHealthCheckForm
) -> RenderData | Response:
    return handle_link_health_check(
        self, request, form, DefaultLayout(self, request)
    )
