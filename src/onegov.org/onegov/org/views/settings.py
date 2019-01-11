""" The settings view, defining things like the logo or color of the org. """

from copy import copy
from dectate import Query
from onegov.core.security import Secret
from onegov.core.templates import render_macro
from onegov.org import _
from onegov.org.app import OrgApp
from onegov.org.forms import AnalyticsSettingsForm
from onegov.org.forms import FooterSettingsForm
from onegov.org.forms import GeneralSettingsForm
from onegov.org.forms import HolidaySettingsForm
from onegov.org.forms import HomepageSettingsForm
from onegov.org.forms import MapSettingsForm
from onegov.org.forms import ModuleSettingsForm
from onegov.org.layout import DefaultLayout
from onegov.org.layout import SettingsLayout
from onegov.org.models import Organisation
from onegov.org.models import SwissHolidays


@OrgApp.html(
    model=Organisation, name='settings', template='settings.pt',
    permission=Secret)
def view_settings(self, request):
    layout = SettingsLayout(self, request)

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


def handle_generic_settings(self, request, form, title):
    layout = SettingsLayout(self, request, title)

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
def handle_general_settings(self, request, form):
    return handle_generic_settings(self, request, form, _("General"))


@OrgApp.form(
    model=Organisation, name='homepage-settings', template='form.pt',
    permission=Secret, form=HomepageSettingsForm, setting=_("Homepage"),
    icon='fa-home', order=-900)
def handle_homepage_settings(self, request, form):
    return handle_generic_settings(self, request, form, _("Homepage"))


@OrgApp.form(
    model=Organisation, name='footer-settings', template='form.pt',
    permission=Secret, form=FooterSettingsForm, setting=_("Footer"),
    icon='fa-window-minimize', order=-800)
def handle_footer_settings(self, request, form):
    return handle_generic_settings(self, request, form, _("Footer"))


@OrgApp.form(
    model=Organisation, name='module-settings', template='form.pt',
    permission=Secret, form=ModuleSettingsForm, setting=_("Modules"),
    icon='fa-sitemap', order=-700)
def handle_module_settings(self, request, form):
    return handle_generic_settings(self, request, form, _("Modules"))


@OrgApp.form(
    model=Organisation, name='map-settings', template='form.pt',
    permission=Secret, form=MapSettingsForm, setting=_("Map"),
    icon='fa-map-marker', order=-700)
def handle_map_settings(self, request, form):
    return handle_generic_settings(self, request, form, _("Map"))


@OrgApp.form(
    model=Organisation, name='analytics-settings', template='form.pt',
    permission=Secret, form=AnalyticsSettingsForm, setting=_("Analytics"),
    icon='fa-line-chart ', order=-600)
def handle_analytics_settings(self, request, form):
    return handle_generic_settings(self, request, form, _("Analytics"))


@OrgApp.form(
    model=Organisation, name='holiday-settings', template='form.pt',
    permission=Secret, form=HolidaySettingsForm, setting=_("Holidays"),
    icon='fa-calendar-o', order=-500)
def handle_holiday_settings(self, request, form):
    return handle_generic_settings(self, request, form, _("Holidays"))


@OrgApp.form(model=Organisation, name='holiday-settings-preview',
             permission=Secret, form=HolidaySettingsForm)
def preview_holiday_settings(self, request, form):
    layout = DefaultLayout(self, request)

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
