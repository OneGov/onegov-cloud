from onegov.feriennet import _
from onegov.core.security import Secret
from onegov.feriennet.app import FeriennetApp
from onegov.form import Form, merge_forms
from onegov.form.fields import MultiCheckboxField
from onegov.org.forms import SettingsForm
from onegov.org.models import Organisation
from onegov.org.views.settings import handle_settings
from wtforms.fields import BooleanField


def settings_form(model, request):

    class CustomFieldsForm(Form):
        show_political_municipality = BooleanField(
            label=_("Require the political municipality in the userprofile"))

        show_related_contacts = BooleanField(
            label=_((
                "Parents can see the contacts of other parents in "
                "the same activity"
            )))

        public_organiser_data = MultiCheckboxField(
            label=_("Public organiser data"),
            choices=(
                ('name', _("Name")),
                ('address', _("Address")),
                ('email', _("E-Mail")),
                ('phone', _("Phone")),
                ('website', _("Website"))
            )
        )

        def process_obj(self, obj):
            super().process_obj(obj)

            self.show_political_municipality.data = obj.meta.get(
                'show_political_municipality', False)

            self.show_related_contacts.data = obj.meta.get(
                'show_related_contacts', False)

            self.public_organiser_data.data = obj.meta.get(
                'public_organiser_data', request.app.public_organiser_data)

        def populate_obj(self, obj, *args, **kwargs):
            super().populate_obj(obj, *args, **kwargs)

            obj.meta['show_political_municipality']\
                = self.show_political_municipality.data

            obj.meta['show_related_contacts']\
                = self.show_related_contacts.data

            obj.meta['public_organiser_data']\
                = self.public_organiser_data.data

    return merge_forms(SettingsForm, CustomFieldsForm)


@FeriennetApp.form(model=Organisation, name='settings',
                   template='form.pt', permission=Secret, form=settings_form)
def custom_handle_settings(self, request, form):
    form.delete_field('homepage_cover')
    form.delete_field('homepage_structure')
    form.delete_field('redirect_homepage_to')

    return handle_settings(self, request, form)
