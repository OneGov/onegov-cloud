""" The settings view, defining things like the logo or color of the org. """

from onegov.core.security import Secret
from onegov.form import Form, merge_forms, move_fields
from onegov.org import _
from onegov.org.forms import SettingsForm
from onegov.org.models import Organisation
from onegov.org.views.settings import handle_settings
from onegov.town.app import TownApp
from wtforms import StringField


def get_custom_settings_form(model, request):

    class CustomFieldsForm(Form):
        online_counter_label = StringField(
            label=_("Online Counter Label"),
            description=_("Forms and applications"),
            fieldset=_("Homepage")
        )
        reservations_label = StringField(
            label=_("Reservations Label"),
            description=_("Daypasses and rooms"),
            fieldset=_("Homepage")
        )
        daypass_label = StringField(
            label=_("SBB Daypass Label"),
            description=_("Generalabonnement for Towns"),
            fieldset=_("Homepage")
        )

    return move_fields(
        form_class=merge_forms(SettingsForm, CustomFieldsForm),
        fields=(
            'online_counter_label',
            'reservations_label',
            'daypass_label'
        ),
        after='homepage_image_6'
    )


@TownApp.form(model=Organisation, name='einstellungen', template='form.pt',
              permission=Secret, form=get_custom_settings_form)
def custom_handle_settings(self, request, form):

    form.delete_field('homepage_cover')
    form.delete_field('homepage_structure')

    return handle_settings(self, request, form)
