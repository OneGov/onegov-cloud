""" The settings view, defining things like the logo or color of the org. """

from onegov.core.security import Secret
from onegov.form import Form, merge_forms, move_fields
from onegov.org import _
from onegov.org.forms import HomepageSettingsForm
from onegov.org.models import Organisation
from onegov.org.views.settings import handle_homepage_settings
from onegov.town.app import TownApp
from wtforms import BooleanField, StringField


def get_custom_settings_form(model, request):

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

        hide_publications = BooleanField(
            label=_("Hide Publications on Homepage"))

    return move_fields(
        form_class=merge_forms(HomepageSettingsForm, CustomFieldsForm),
        fields=(
            'online_counter_label',
            'reservations_label',
            'daypass_label',
            'publications_label',
            'hide_publications',
        ),
        after='homepage_image_6'
    )


@TownApp.form(model=Organisation, name='homepage-settings', template='form.pt',
              permission=Secret, form=get_custom_settings_form,
              setting=_("Homepage"), icon='fa-home', order=-900)
def custom_handle_settings(self, request, form):

    form.delete_field('homepage_cover')
    form.delete_field('homepage_structure')
    form.delete_field('redirect_homepage_to')

    return handle_homepage_settings(self, request, form)
