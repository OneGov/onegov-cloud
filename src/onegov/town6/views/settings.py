""" The settings view, defining things like the logo or color of the org. """
from wtforms import StringField, BooleanField, IntegerField

from onegov.core.security import Secret
from onegov.form import Form, merge_forms, move_fields
from onegov.org import _
from onegov.town6.forms.settings import GeneralSettingsForm, \
    ChatSettingsForm

from onegov.org.forms.settings import FaviconSettingsForm, LinksSettingsForm, \
    HeaderSettingsForm, FooterSettingsForm, ModuleSettingsForm, \
    MapSettingsForm, AnalyticsSettingsForm, HolidaySettingsForm, \
    OrgTicketSettingsForm, HomepageSettingsForm, NewsletterSettingsForm
from onegov.org.models import Organisation
from onegov.org.views.settings import (
    handle_homepage_settings, view_settings,
    handle_ticket_settings, preview_holiday_settings, handle_general_settings,
    handle_favicon_settings, handle_links_settings, handle_header_settings,
    handle_footer_settings, handle_module_settings, handle_map_settings,
    handle_analytics_settings, handle_holiday_settings,
    handle_newsletter_settings, handle_generic_settings)

from onegov.town6.app import TownApp

from onegov.town6.layout import SettingsLayout, DefaultLayout


def get_custom_settings_form(model, request, homepage_settings_form=None):

    class CustomFieldsForm(Form):
        online_counter_label = StringField(
            label=_("Online Counter Label"),
            description=_("Forms and applications"))

        reservations_label = StringField(
            label=_("Reservations Label"),
            description=_("Daypasses and rooms"))

        daypass_label = StringField(
            label=_("SBB Daypass Label"),
            description=_("Generalabonnement for Towns"))

        publications_label = StringField(
            label=_("Publications Label"),
            description=_("Official Documents"))

        e_move_label = StringField(
            label=_('E-Move Label'),
            description=_('E-Move')
        )

        e_move_url = StringField(
            label=_('E-Move Url'),
            description=_('E-Move')
        )

        hide_publications = BooleanField(
            label=_("Hide Publications on Homepage"))

        event_limit_homepage = IntegerField(
            label=_("Number of events displayed on homepage")
        )

        news_limit_homepage = IntegerField(
            label=_("Number of news entries on homepage")
        )

    return move_fields(
        form_class=merge_forms(
            homepage_settings_form or HomepageSettingsForm, CustomFieldsForm),
        fields=(
            'online_counter_label',
            'reservations_label',
            'daypass_label',
            'publications_label',
            'e_move_label',
            'e_move_url',
            'hide_publications',
            'event_limit_homepage',
            'news_limit_homepage',
        ),
        after='homepage_image_6'
    )


def custom_footer_settings_form(model, request):

    class ExtendedFooterSettings(Form):
        always_show_partners = BooleanField(
            label=_('Show partners on all pages'),
            description=_('Shows the footer on all pages but for admins'),
            fieldset=_('Partner display')
        )

    return merge_forms(FooterSettingsForm, ExtendedFooterSettings)


@TownApp.html(
    model=Organisation, name='settings', template='settings.pt',
    permission=Secret)
def view_town_settings(self, request):
    return view_settings(self, request, SettingsLayout(self, request))


@TownApp.form(
    model=Organisation, name='general-settings', template='form.pt',
    permission=Secret, form=GeneralSettingsForm, setting=_("General"),
    icon='fa-cogs', order=-1000)
def town_handle_general_settings(self, request, form):
    return handle_general_settings(
        self, request, form, SettingsLayout(self, request))


@TownApp.form(model=Organisation, name='homepage-settings', template='form.pt',
              permission=Secret, form=get_custom_settings_form,
              setting=_("Homepage"), icon='fa-home', order=-995)
def custom_handle_settings(self, request, form):

    form.delete_field('homepage_cover')
    form.delete_field('redirect_homepage_to')
    form.delete_field('redirect_path')

    return handle_homepage_settings(
        self, request, form, SettingsLayout(self, request))


@TownApp.form(
    model=Organisation, name='favicon-settings', template='form.pt',
    permission=Secret, form=FaviconSettingsForm, setting=_("Favicon"),
    icon='fas fa-external-link-square-alt', order=-990)
def town_handle_favicon_settings(self, request, form):
    return handle_favicon_settings(
        self, request, form, SettingsLayout(self, request))


@TownApp.form(
    model=Organisation, name='link-settings', template='form.pt',
    permission=Secret, form=LinksSettingsForm, setting=_("Links"),
    icon='fa-link', order=-980)
def town_handle_links_settings(self, request, form):
    return handle_links_settings(
        self, request, form, SettingsLayout(self, request))


@TownApp.form(model=Organisation, name='chat-settings', template='form.pt',
              permission=Secret, form=ChatSettingsForm,
              setting=_("Chat"), icon='far fa-comments', order=-980)
def handle_chat_settings(self, request, form):
    return handle_generic_settings(
        self, request, form, _("Chat"), SettingsLayout(self, request))


@TownApp.form(
    model=Organisation, name='header-settings', template='form.pt',
    permission=Secret, form=HeaderSettingsForm, setting=_("Header"),
    icon='fa-window-maximize', order=-810)
def town_handle_header_settings(self, request, form):
    return handle_header_settings(
        self, request, form, SettingsLayout(self, request))


@TownApp.form(
    model=Organisation, name='footer-settings', template='form.pt',
    permission=Secret, form=custom_footer_settings_form, setting=_("Footer"),
    icon='fa-window-minimize', order=-800)
def town_handle_footer_settings(self, request, form):
    return handle_footer_settings(
        self, request, form, SettingsLayout(self, request))


@TownApp.form(
    model=Organisation, name='module-settings', template='form.pt',
    permission=Secret, form=ModuleSettingsForm, setting=_("Modules"),
    icon='fa-sitemap', order=-700)
def town_handle_module_settings(self, request, form):
    return handle_module_settings(
        self, request, form, SettingsLayout(self, request))


@TownApp.form(
    model=Organisation, name='map-settings', template='form.pt',
    permission=Secret, form=MapSettingsForm, setting=_("Map"),
    icon='fa-map-marker-alt', order=-700)
def town_handle_map_settings(self, request, form):
    return handle_map_settings(
        self, request, form, SettingsLayout(self, request))


@TownApp.form(
    model=Organisation, name='analytics-settings', template='form.pt',
    permission=Secret, form=AnalyticsSettingsForm, setting=_("Analytics"),
    icon='fa-chart-bar ', order=-600)
def town_handle_analytics_settings(self, request, form):
    return handle_analytics_settings(
        self, request, form, SettingsLayout(self, request))


@TownApp.form(
    model=Organisation, name='holiday-settings', template='form.pt',
    permission=Secret, form=HolidaySettingsForm, setting=_("Holidays"),
    icon='fa-calendar', order=-500)
def town_handle_holiday_settings(self, request, form):
    return handle_holiday_settings(
        self, request, form, SettingsLayout(self, request))


@TownApp.form(
    model=Organisation, name='ticket-settings', template='form.pt',
    permission=Secret, form=OrgTicketSettingsForm,
    setting=_("Ticket Settings"), order=-950, icon='fa-ticket-alt'
)
def town_handle_ticket_settings(self, request, form):
    return handle_ticket_settings(
        self, request, form, SettingsLayout(self, request))


@TownApp.form(
    model=Organisation, name='newsletter-settings', template='form.pt',
    permission=Secret, form=NewsletterSettingsForm,
    setting=_("Newsletter Settings"), order=-951, icon='far fa-paper-plane'
)
def town_handle_newsletter_settings(self, request, form, layout=None):
    return handle_newsletter_settings(
        self, request, form, SettingsLayout(self, request)
    )


@TownApp.form(model=Organisation, name='holiday-settings-preview',
              permission=Secret, form=HolidaySettingsForm)
def town_preview_holiday_settings(self, request, form):
    return preview_holiday_settings(
        self, request, form, DefaultLayout(self, request))
