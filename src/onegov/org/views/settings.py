""" The settings view, defining things like the logo or color of the org. """

from copy import copy

from dectate import Query
from markupsafe import Markup
from webob.exc import HTTPForbidden

from onegov.core.elements import Link, Confirm, Intercooler
from onegov.core.request import CoreRequest
from onegov.core.security import Secret
from onegov.core.templates import render_macro
from onegov.org import _
from onegov.org.forms import AnalyticsSettingsForm
from onegov.org.forms import FooterSettingsForm
from onegov.org.forms import GeneralSettingsForm
from onegov.org.forms import HolidaySettingsForm
from onegov.org.forms import HomepageSettingsForm
from onegov.org.forms import MapSettingsForm
from onegov.org.forms import ModuleSettingsForm
from onegov.org.forms.settings import OrgTicketSettingsForm,\
    HeaderSettingsForm, FaviconSettingsForm, LinksSettingsForm,\
    NewsletterSettingsForm, LinkMigrationForm, LinkHealthCheckForm,\
    SocialMediaSettingsForm, EventSettingsForm, GeverSettingsForm,\
    OneGovApiSettingsForm
from onegov.org.management import LinkHealthCheck
from onegov.org.layout import DefaultLayout
from onegov.org.layout import SettingsLayout
from onegov.org.management import LinkMigration
from onegov.org.models import Organisation
from onegov.org.models import SwissHolidays
from onegov.api.models import ApiKey
from onegov.org.app import OrgApp
from onegov.user import UserCollection, User
from uuid import uuid4


@OrgApp.html(
    model=Organisation, name='settings', template='settings.pt',
    permission=Secret)
def view_settings(self, request, layout=None):
    layout = layout or SettingsLayout(self, request)

    def query_settings():
        q = Query('view').filter(model=Organisation)

        for action, fn in q(request.app):
            if 'setting' in action.predicates:
                setting = copy(action.predicates)
                setting['title'] = setting['setting']
                setting['link'] = request.link(self, name=setting['name'])

                yield setting

    settings = list(query_settings())
    settings.sort(key=lambda s: s.get('order', 0))

    return {
        'layout': layout,
        'title': _("Settings"),
        'settings': settings
    }


def handle_generic_settings(self, request, form, title, layout=None):
    layout = layout or SettingsLayout(self, request, title)
    request.include('fontpreview')

    if form.submitted(request):
        form.populate_obj(self)

        request.success(_("Your changes were saved"))
        return request.redirect(request.link(self, name='settings'))
    elif request.method == 'GET':
        form.process(obj=self)

    return {
        'layout': layout,
        'title': title,
        'form': form
    }


@OrgApp.form(
    model=Organisation, name='general-settings', template='form.pt',
    permission=Secret, form=GeneralSettingsForm, setting=_("General"),
    icon='fa-sliders', order=-1000)
def handle_general_settings(self, request, form, layout=None):
    return handle_generic_settings(self, request, form, _("General"), layout)


@OrgApp.form(
    model=Organisation, name='homepage-settings', template='form.pt',
    permission=Secret, form=HomepageSettingsForm, setting=_("Homepage"),
    icon='fa-home', order=-995)
def handle_homepage_settings(self, request, form, layout=None):
    return handle_generic_settings(self, request, form, _("Homepage"), layout)


@OrgApp.form(
    model=Organisation, name='favicon-settings', template='form.pt',
    permission=Secret, form=FaviconSettingsForm, setting=_("Favicon"),
    icon=' fa-external-link-square', order=-990)
def handle_favicon_settings(self, request, form, layout=None):
    return handle_generic_settings(self, request, form, _("Favicon"), layout)


@OrgApp.form(
    model=Organisation, name='social-media-settings', template='form.pt',
    permission=Secret, form=SocialMediaSettingsForm, setting=_("Social Media"),
    icon=' fa fa-share-alt', order=-985)
def handle_social_media_settings(self, request, form, layout=None):
    return handle_generic_settings(
        self, request, form, _("Social Media"), layout)


@OrgApp.form(
    model=Organisation, name='link-settings', template='form.pt',
    permission=Secret, form=LinksSettingsForm, setting=_("Links"),
    icon=' fa-link', order=-980)
def handle_links_settings(self, request, form, layout=None):
    return handle_generic_settings(self, request, form, _("Links"), layout)


@OrgApp.form(
    model=Organisation, name='newsletter-settings', template='form.pt',
    permission=Secret, form=NewsletterSettingsForm,
    setting=_("Newsletter"), order=-951, icon='far fa-paper-plane'
)
def handle_newsletter_settings(self, request, form, layout=None):
    return handle_generic_settings(
        self, request, form, _("Newsletter"), layout
    )


@OrgApp.form(
    model=Organisation, name='ticket-settings', template='form.pt',
    permission=Secret, form=OrgTicketSettingsForm,
    setting=_("Tickets"), order=-950, icon='fa-ticket'
)
def handle_ticket_settings(self, request, form, layout=None):
    resp = handle_generic_settings(
        self, request, form, _("Tickets"), layout)
    return resp


@OrgApp.form(
    model=Organisation, name='header-settings', template='form.pt',
    permission=Secret, form=HeaderSettingsForm, setting=_("Header"),
    icon='fa-window-maximize', order=-810)
def handle_header_settings(self, request, form, layout=None):
    layout = layout or SettingsLayout(self, request, _("Header"))
    request.include('many')
    return handle_generic_settings(self, request, form, _("Header"), layout)


@OrgApp.form(
    model=Organisation, name='footer-settings', template='form.pt',
    permission=Secret, form=FooterSettingsForm, setting=_("Footer"),
    icon='fa-window-minimize', order=-800)
def handle_footer_settings(self, request, form, layout=None):
    return handle_generic_settings(self, request, form, _("Footer"), layout)


@OrgApp.form(
    model=Organisation, name='module-settings', template='form.pt',
    permission=Secret, form=ModuleSettingsForm, setting=_("Modules"),
    icon='fa-sitemap', order=-700)
def handle_module_settings(self, request, form, layout=None):
    return handle_generic_settings(
        self, request, form, _("Modules"), layout)


@OrgApp.form(
    model=Organisation, name='map-settings', template='form.pt',
    permission=Secret, form=MapSettingsForm, setting=_("Map"),
    icon='fa-map-marker', order=-700)
def handle_map_settings(self, request, form, layout=None):
    return handle_generic_settings(self, request, form, _("Map"), layout)


@OrgApp.form(
    model=Organisation, name='analytics-settings', template='form.pt',
    permission=Secret, form=AnalyticsSettingsForm, setting=_("Analytics"),
    icon='fa-line-chart ', order=-600)
def handle_analytics_settings(self, request, form, layout=None):
    return handle_generic_settings(self, request, form, _("Analytics"), layout)


@OrgApp.form(
    model=Organisation, name='gever-credentials', template='form.pt',
    permission=Secret, form=GeverSettingsForm, setting="Gever API",
    icon='fa-key', order=400)
def handle_gever_settings(self, request, form, layout=None):
    return handle_generic_settings(self, request, form, "Gever API", layout)


@OrgApp.form(
    model=Organisation, name='holiday-settings', template='form.pt',
    permission=Secret, form=HolidaySettingsForm, setting=_("Holidays"),
    icon='fa-calendar-o', order=-500)
def handle_holiday_settings(self, request, form, layout=None):
    return handle_generic_settings(self, request, form, _("Holidays"), layout)


@OrgApp.form(model=Organisation, name='holiday-settings-preview',
             permission=Secret, form=HolidaySettingsForm)
def preview_holiday_settings(self, request, form, layout=None):
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
        msg = request.translate(_("No holidays defined"))
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
def handle_migrate_links(self, request, form, layout=None):

    domain = request.domain
    button_text = _('Migrate')
    test_results = None

    if form.submitted(request):
        test_only = form.test.data
        migration = LinkMigration(
            request,
            old_uri=form.old_domain.data,
            new_uri=request.domain
        )
        total, grouped = migration.migrate_site_collection(test_only)

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
def handle_link_health_check(self, request, form, layout=None):

    healthcheck = LinkHealthCheck(request)
    check_responses = None
    stats = None

    if form.submitted(request):
        link_type = form.scope.data
        healthcheck.link_type = link_type
        stats, check_responses = healthcheck.unhealthy_urls()

    url_max_len = 80

    def truncate(text):
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
    permission=Secret, form=EventSettingsForm, setting=_("Events"),
    icon='fa-calendar-alt', order=-700)
def handle_event_settings(self, request, form, layout=None):
    return handle_generic_settings(self, request, form, _("Events"), layout)


@OrgApp.form(
    model=Organisation, name='api-keys', template='api_keys.pt',
    permission=Secret, form=OneGovApiSettingsForm, setting=_("OneGov API"),
    icon='fa-key', order=1)
def handle_api_keys(self: Organisation, request: CoreRequest,
                    form: OneGovApiSettingsForm, layout=None):
    """Handles the generation of API access keys."""

    request.include('fontpreview')
    title = _("OneGov API")
    collection = UserCollection(request.session)
    user = collection.by_username(request.identity.userid)
    if not user:
        raise HTTPForbidden()

    if form.submitted(request):
        assert form.name.data is not None
        key = ApiKey(
            name=form.name.data,
            read_only=True,
            last_used=None,
            key=uuid4(),
            user=user,
        )
        request.session.add(key)
        request.session.flush()
        request.success(_("Your changes were saved"))

    layout = layout or SettingsLayout(self, request, title)

    def current_api_keys_by_user(
        request: CoreRequest, self: Organisation, user: User, layout
    ):
        for api_key in user.api_keys:
            api_key_delete_link = Link(
                text=Markup('<i class="fa fa-trash" aria-hidden="True"></i>'),
                url=layout.csrf_protected_url(
                    request.link(api_key, name='+delete')),
                traits=(
                    Confirm(
                        _("Do you really want to delete this API key?"),
                        _("This action cannot be undone."),
                        _("Delete"),
                        _("Cancel"),
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
        'api_keys_list': list(
            current_api_keys_by_user(request, self, user, layout)
        ),
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
def delete_api_key(self: ApiKey, request: CoreRequest):
    request.assert_valid_csrf_token()

    request.session.delete(self)
    request.session.flush()
    request.message(_("ApiKey deleted."), 'success')
