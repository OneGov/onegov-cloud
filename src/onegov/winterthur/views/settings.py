import textwrap

from onegov.core.security import Secret
from onegov.directory import Directory, DirectoryCollection
from onegov.form import Form
from onegov.form.fields import HtmlField
from onegov.org.models import Organisation
from onegov.org.views.settings import handle_generic_settings
from onegov.winterthur import _
from onegov.winterthur.app import WinterthurApp
from onegov.winterthur.daycare import Services
from wtforms.fields import BooleanField
from wtforms.fields import DecimalField
from wtforms.fields import RadioField
from wtforms.fields import TextAreaField
from wtforms.validators import InputRequired, ValidationError
from yaml.error import YAMLError


DEFAULT_LEGEND = """
<p>
    <b>1. Zahl</b><br>
    Direkt am Einsatz beteiligte Angehörige der Feuerwehr.
</p>
<p>
    <b>2. Zahl</b><br>
    Angehörige der Feuerwehr zur Sicherstellung der
    Einsatzbereitschaft auf der Wache.
</p>
<p>
    <b>Internationales Schutzzeichen Zivilschutz</b><br>
    An diesem Einsatz waren zusätzlich Angehörige der
    Zivilschutzorganisation Winterthur und Umgebung beteiligt.
</p>
"""


class WinterthurDaycareSettingsForm(Form):

    max_income = DecimalField(
        label=_("Maximum taxable income"),
        fieldset=_("Variables"),
        places=0,
        validators=[InputRequired()])

    max_wealth = DecimalField(
        label=_("Maximum taxable wealth"),
        fieldset=_("Variables"),
        places=0,
        validators=[InputRequired()])

    min_income = DecimalField(
        label=_("Minimum income"),
        fieldset=_("Variables"),
        places=0,
        validators=[InputRequired()])

    min_rate = DecimalField(
        label=_("Minimum day-rate"),
        fieldset=_("Variables"),
        places=0,
        validators=[InputRequired()])

    max_rate = DecimalField(
        label=_("Maximum day-rate"),
        fieldset=_("Variables"),
        places=0,
        validators=[InputRequired()])

    max_subsidy = DecimalField(
        label=_("Maximum subsidy"),
        fieldset=_("Variables"),
        places=0,
        validators=[InputRequired()])

    wealth_premium = DecimalField(
        label=_("Wealth premium (%)"),
        fieldset=_("Variables"),
        places=2,
        validators=[InputRequired()])

    rebate = DecimalField(
        label=_("Rebate (%)"),
        fieldset=_("Variables"),
        places=2,
        validators=[InputRequired()])

    services = TextAreaField(
        label=_("Care"),
        fieldset=_("Variables"),
        validators=[InputRequired()],
        render_kw={'rows': 32, 'data-editor': 'yaml'})

    directory = RadioField(
        label=_("Directory"),
        fieldset=_("Institutions"),
        validators=[InputRequired()],
        choices=None)

    explanation = HtmlField(
        label=_("Explanation"),
        fieldset=_("Details"),
        render_kw={'rows': 32})

    def populate_obj(self, obj, *args, **kwargs):
        super().populate_obj(obj, *args, **kwargs)
        obj.meta['daycare_settings'] = {
            k: v for k, v in self.data.items() if k != 'csrf_token'
        }

    def process_obj(self, obj):
        super().process_obj(obj)
        for k, v in obj.meta.get('daycare_settings', {}).items():
            if hasattr(self, k):
                getattr(self, k).data = v

        if not self.services.data or not self.services.data.strip():
            self.services.data = textwrap.dedent("""
                # Beispiel:
                #
                # - titel: "Ganzer Tag inkl. Mitagessen"
                #   tage: "Montag, Dienstag, Mittwoch, Donnerstag, Freitag"
                #   prozent: 100.00
            """)

    def validate_services(self, field):
        try:
            tuple(Services.parse_definition(field.data))
        except (YAMLError, TypeError, KeyError) as exception:
            raise ValidationError(
                _("Invalid services configuration")
            ) from exception

    def directory_choices(self):
        dirs = DirectoryCollection(self.request.session, type='extended')

        def choice(directory):
            return (
                directory.id.hex,
                directory.title
            )

        for d in dirs.query().order_by(Directory.order):
            yield choice(d)

    def on_request(self):
        self.directory.choices = list(self.directory_choices())


@WinterthurApp.form(model=Organisation, name='daycare-settings',
                    template='form.pt', permission=Secret,
                    form=WinterthurDaycareSettingsForm,
                    setting=_("Daycare Calculator"),
                    icon='fa-calculator')
def custom_handle_settings(self, request, form):
    return handle_generic_settings(self, request, form, _("Daycare Settings"))


class WinterthurMissionReportSettingsForm(Form):

    legend = HtmlField(
        label=_("Legend Text"))

    hide_civil_defence_field = BooleanField(
        label=_("Hide Civil Defence Field"))

    def populate_obj(self, obj, *args, **kwargs):
        super().populate_obj(obj, *args, **kwargs)

        obj.meta['mission_report_settings'] = {
            'hide_civil_defence_field': self.hide_civil_defence_field.data,
            'legend': self.legend.data,
        }

    def process_obj(self, obj):
        super().process_obj(obj)

        d = obj.meta.get('mission_report_settings') or {}

        self.hide_civil_defence_field.data = d.get(
            'hide_civil_defence_field', False)

        self.legend.data = d.get(
            'legend', DEFAULT_LEGEND)


@WinterthurApp.form(model=Organisation, name='mission-report-settings',
                    template='form.pt', permission=Secret,
                    form=WinterthurMissionReportSettingsForm,
                    setting=_("Mission Reports"),
                    icon='fa-ambulance')
def handle_mission_report_settings(self, request, form):
    return handle_generic_settings(
        self, request, form, _("Mission Reports"))
