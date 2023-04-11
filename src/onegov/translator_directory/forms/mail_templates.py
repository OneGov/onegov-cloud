from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.translator_directory import _


class MailTemplatesForm(Form):
    """ Defines the form for generating mail templates. """

    templates = ChosenSelectField(
        label=_('Chose a mail template to generate:'),
        choices=[]
    )

    def on_request(self):
        self.templates.choices = self.request.app.mail_templates
