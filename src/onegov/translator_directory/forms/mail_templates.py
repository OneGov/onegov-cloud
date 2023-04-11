from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.translator_directory import _
from onegov.translator_directory.constants import EMAIL_OR_MAIL


class MailTemplatesForm(Form):
    """ Defines the form for generating mail templates. """

    templates = ChosenSelectField(
        label=_('Chose a mail template to generate:'),
        choices=[]
    )

    email_or_mail = ChosenSelectField(
        label=_('Vorlage für Brief oder für E-Mail:'),
        choices=[EMAIL_OR_MAIL]
    )

    def on_request(self):
        self.templates.choices = self.request.app.mail_templates
