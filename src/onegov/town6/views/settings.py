""" The settings view, defining things like the logo or color of the org. """
from __future__ import annotations

from wtforms.fields import StringField, BooleanField, IntegerField

from onegov.core.security import Secret
from onegov.form import Form, merge_forms, move_fields
from onegov.org import _
from onegov.org.elements import Link
from onegov.org.forms.settings import (
    FaviconSettingsForm, LinksSettingsForm, HeaderSettingsForm,
    FooterSettingsForm, ModuleSettingsForm, MapSettingsForm,
    AnalyticsSettingsForm, HolidaySettingsForm, OrgTicketSettingsForm,
    HomepageSettingsForm, NewsletterSettingsForm, LinkMigrationForm,
    LinkHealthCheckForm, PeopleSettingsForm, SocialMediaSettingsForm,
    EventSettingsForm, GeverSettingsForm, OneGovApiSettingsForm,
    DataRetentionPolicyForm, FirebaseSettingsForm, VATSettingsForm,
    KabaSettingsForm, CitizenLoginSettingsForm, ResourceSettingsForm)
from onegov.org.models import Organisation
from onegov.town6.forms.settings import RISSettingsForm
from onegov.org.views.settings import (
    handle_homepage_settings, handle_people_settings, view_settings,
    handle_ticket_settings, preview_holiday_settings, handle_general_settings,
    handle_favicon_settings, handle_links_settings, handle_header_settings,
    handle_footer_settings, handle_module_settings, handle_map_settings,
    handle_analytics_settings, handle_holiday_settings,
    handle_newsletter_settings, handle_generic_settings, handle_migrate_links,
    handle_link_health_check, handle_social_media_settings,
    handle_event_settings, handle_api_keys, handle_chat_settings,
    handle_kaba_settings, handle_citizen_login_settings,
    handle_resource_settings)

from onegov.town6.app import TownApp
from onegov.town6.forms.settings import (
    GeneralSettingsForm, ChatSettingsForm)
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
        online_counter_label = StringField(
            fieldset=_('Online Counter'),
            label=_('Online Counter Label'),
            description=_('Forms and applications'))

        hide_online_counter = BooleanField(
            fieldset=_('Online Counter'),
            label=_('Hide Online Counter on Homepage'))

        reservations_label = StringField(
            fieldset=_('Reservations'),
            label=_('Reservations Label'),
            description=_('Daypasses and rooms'))

        hide_reservations = BooleanField(
            fieldset=_('Reservations'),
            label=_('Hide Reservations on Homepage'))

        daypass_label = StringField(
            fieldset=_('SBB Daypass'),
            label=_('SBB Daypass Label'),
            description=_('Generalabonnement for Towns'))

        publications_label = StringField(
            fieldset=_('Publication'),
            label=_('Publications Label'),
            description=_('Official Documents'))

        hide_publications = BooleanField(
            fieldset=_('Publication'),
            label=_('Hide Publications on Homepage'))

        e_move_label = StringField(
            fieldset=_('E-Move'),
            label=_('E-Move Label'),
            description=_('E-Move')
        )

        e_move_url = StringField(
            fieldset=_('E-Move'),
            label=_('E-Move Url'),
            description=_('E-Move')
        )

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
            'online_counter_label',
            'hide_online_counter',
            'reservations_label',
            'hide_reservations',
            'daypass_label',
            'e_move_label',
            'e_move_url',
            'publications_label',
            'hide_publications',
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
    model=Organisation, name='general-settings', template='form.pt',
    permission=Secret, form=GeneralSettingsForm, setting=_('General'),
    icon='fa-cogs', order=-1000)
def town_handle_general_settings(
    self: Organisation,
    request: TownRequest,
    form: GeneralSettingsForm
) -> RenderData | Response:
    return handle_general_settings(
        self, request, form, SettingsLayout(self, request))


@TownApp.form(model=Organisation, name='homepage-settings', template='form.pt',
              permission=Secret, form=get_custom_settings_form,
              setting=_('Homepage'), icon='fa-home', order=-995)
def custom_handle_settings(
    self: Organisation,
    request: TownRequest,
    form: HomepageSettingsForm
) -> RenderData | Response:
    form.delete_field('homepage_cover')

    return handle_homepage_settings(
        self, request, form, SettingsLayout(self, request))


@TownApp.form(
    model=Organisation, name='favicon-settings', template='form.pt',
    permission=Secret, form=FaviconSettingsForm, setting=_('Favicon'),
    icon='fas fa-external-link-square-alt', order=-990)
def town_handle_favicon_settings(
    self: Organisation,
    request: TownRequest,
    form: FaviconSettingsForm
) -> RenderData | Response:
    return handle_favicon_settings(
        self, request, form, SettingsLayout(self, request))


@TownApp.form(
    model=Organisation, name='social-media-settings', template='form.pt',
    permission=Secret, form=SocialMediaSettingsForm, setting=_('Social Media'),
    icon=' fa fa-share-alt', order=-985)
def town_handle_social_media_settings(
    self: Organisation,
    request: TownRequest,
    form: SocialMediaSettingsForm
) -> RenderData | Response:
    return handle_social_media_settings(
        self, request, form, SettingsLayout(self, request))


@TownApp.form(
    model=Organisation, name='link-settings', template='form.pt',
    permission=Secret, form=LinksSettingsForm, setting=_('Links'),
    icon='fa-link', order=-980)
def town_handle_links_settings(
    self: Organisation,
    request: TownRequest,
    form: LinksSettingsForm
) -> RenderData | Response:
    return handle_links_settings(
        self, request, form, SettingsLayout(self, request))


@TownApp.form(model=Organisation, name='chat-settings', template='form.pt',
              permission=Secret, form=ChatSettingsForm,
              setting=_('Chat'), icon='far fa-comments', order=-980)
def town_handle_chat_settings(
    self: Organisation,
    request: TownRequest,
    form: ChatSettingsForm
) -> RenderData | Response:
    return handle_chat_settings(
        self, request, form, SettingsLayout(self, request))


@TownApp.form(model=Organisation, name='gever-credentials', template='form.pt',
              permission=Secret, form=GeverSettingsForm,
              setting='Gever API', icon='fa-key', order=400)
def town_handle_gever_settings(
    self: Organisation,
    request: TownRequest,
    form: GeverSettingsForm
) -> RenderData | Response:
    return handle_generic_settings(self, request, form, 'Gever API',
                                   SettingsLayout(self, request))


@TownApp.form(model=Organisation, name='kaba-settings', template='form.pt',
              permission=Secret, form=KabaSettingsForm,
              setting='dormakaba API', icon='fa-key', order=400)
def town_handle_kaba_settings(
    self: Organisation,
    request: TownRequest,
    form: KabaSettingsForm
) -> RenderData | Response:
    return handle_kaba_settings(
        self, request, form, SettingsLayout(self, request))


@TownApp.form(
    model=Organisation, name='header-settings', template='form.pt',
    permission=Secret, form=HeaderSettingsForm, setting=_('Header'),
    icon='fa-window-maximize', order=-810)
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
    icon='fa-window-minimize', order=-800)
def town_handle_footer_settings(
    self: Organisation,
    request: TownRequest,
    form: FooterSettingsForm
) -> RenderData | Response:
    return handle_footer_settings(
        self, request, form, SettingsLayout(self, request))


@TownApp.form(
    model=Organisation, name='module-settings', template='form.pt',
    permission=Secret, form=ModuleSettingsForm, setting=_('Modules'),
    icon='fa-sitemap', order=-700)
def town_handle_module_settings(
    self: Organisation,
    request: TownRequest,
    form: ModuleSettingsForm
) -> RenderData | Response:
    return handle_module_settings(
        self, request, form, SettingsLayout(self, request))


@TownApp.form(
    model=Organisation, name='map-settings', template='form.pt',
    permission=Secret, form=MapSettingsForm, setting=_('Map'),
    icon='fa-map-marker-alt', order=-700)
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
    icon='fa-chart-bar ', order=-600)
def town_handle_analytics_settings(
    self: Organisation,
    request: TownRequest,
    form: AnalyticsSettingsForm
) -> RenderData | Response:
    return handle_analytics_settings(
        self, request, form, SettingsLayout(self, request))


@TownApp.form(
    model=Organisation, name='holiday-settings', template='form.pt',
    permission=Secret, form=HolidaySettingsForm, setting=_('Holidays'),
    icon='fa-calendar', order=-500)
def town_handle_holiday_settings(
    self: Organisation,
    request: TownRequest,
    form: HolidaySettingsForm
) -> RenderData | Response:
    return handle_holiday_settings(
        self, request, form, SettingsLayout(self, request))


@TownApp.form(
    model=Organisation, name='ticket-settings', template='form.pt',
    permission=Secret, form=OrgTicketSettingsForm,
    setting=_('Tickets'), order=-950, icon='fa-ticket-alt'
)
def town_handle_ticket_settings(
    self: Organisation,
    request: TownRequest,
    form: OrgTicketSettingsForm
) -> RenderData | Response:
    return handle_ticket_settings(
        self, request, form, SettingsLayout(self, request))


@TownApp.form(
    model=Organisation, name='newsletter-settings', template='form.pt',
    permission=Secret, form=NewsletterSettingsForm,
    setting=_('Newsletter'), order=-951, icon='far fa-paper-plane'
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
    model=Organisation, name='migrate-links', template='form.pt',
    permission=Secret, form=LinkMigrationForm, setting=_('Link Migration'),
    icon='fas fa-random', order=-400)
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


@TownApp.form(
    model=Organisation, name='event-settings', template='form.pt',
    permission=Secret, form=EventSettingsForm, setting=_('Events'),
    icon='fa-calendar-alt', order=-200)
def town_handle_event(
    self: Organisation,
    request: TownRequest,
    form: EventSettingsForm
) -> RenderData | Response:
    return handle_event_settings(
        self, request, form, SettingsLayout(self, request)
    )


@TownApp.form(
    model=Organisation, name='resource-settings', template='form.pt',
    permission=Secret, form=ResourceSettingsForm, setting=_('Resources'),
    icon='fa-building')
def town_handle_resource(
    self: Organisation,
    request: TownRequest,
    form: ResourceSettingsForm,
    layout: SettingsLayout | None = None
) -> RenderData | Response:
    return handle_resource_settings(
        self, request, form, SettingsLayout(self, request))


@TownApp.form(
    model=Organisation, name='api-keys', template='api_keys.pt',
    permission=Secret, form=OneGovApiSettingsForm, icon='fa-key',
    setting=_('OneGov API'), order=1)
def town_handle_api_keys(
    self: Organisation,
    request: TownRequest,
    form: OneGovApiSettingsForm
) -> RenderData | Response:
    return handle_api_keys(self, request, form, SettingsLayout(self, request))


@TownApp.form(
    model=Organisation, name='data-retention-settings',
    template='form.pt',
    permission=Secret, form=DataRetentionPolicyForm,
    setting=_('Data Retention Policy'), icon='far fa-trash', order=-880,
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
    model=Organisation, name='firebase', template='form.pt',
    permission=Secret, form=FirebaseSettingsForm, setting='Firebase',
    icon='fa-bell', order=400,
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


@TownApp.form(
    model=Organisation, name='vat-settings', template='form.pt',
    permission=Secret, form=VATSettingsForm, setting=_('Value Added Tax'),
    icon='fa-file-invoice-dollar', order=450
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
    model=Organisation, name='people-settings', template='form.pt',
    permission=Secret, form=PeopleSettingsForm, setting=_('People'),
    icon='fa-users', order=400,
)
def town_handle_people_settings(
    self: Organisation, request: TownRequest, form: PeopleSettingsForm
) -> RenderData | Response:
    return handle_people_settings(
        self, request, form, SettingsLayout(self, request)
    )


@TownApp.form(
    model=Organisation, name='ris-enable', template='form.pt',
    permission=Secret, form=RISSettingsForm,
    setting=_('Ratsinformationssystem'), icon='fa-landmark', order=500
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


@TownApp.form(
    model=Organisation, name='citizen-login-settings', template='form.pt',
    permission=Secret, form=CitizenLoginSettingsForm,
    setting=_('Citizen Login'), icon='fa-id-card', order=480,
)
def town_handle_citizen_login_settings(
    self: Organisation, request: TownRequest, form: CitizenLoginSettingsForm
) -> RenderData | Response:
    return handle_citizen_login_settings(
        self, request, form, SettingsLayout(self, request)
    )
