from onegov.form import Form
from onegov.form.validators import ValidFormDefinition
from onegov.org import _
from onegov.org.forms.fields import HtmlField
from wtforms import RadioField, StringField, TextAreaField, validators


class FormDefinitionForm(Form):
    """ Form to edit defined forms. """

    title = StringField(_("Title"), [validators.InputRequired()])

    lead = TextAreaField(
        label=_("Lead"),
        description=_("Describes what this form is about"),
        render_kw={'rows': 4})

    text = HtmlField(
        label=_("Text"))

    definition = TextAreaField(
        label=_("Definition"),
        validators=[validators.InputRequired(), ValidFormDefinition()],
        render_kw={'rows': 32, 'data-editor': 'form'})

    payment_method = RadioField(
        label=_("Payment Method"),
        validators=[validators.InputRequired()],
        default='free',
        choices=[
            ('manual', _("No credit card payments")),
            ('free', _("Credit card payments optional")),
            ('cc', _("Credit card payments required"))
        ])

    def ensure_valid_payment_method(self):
        if self.payment_method.data == 'manual':
            return

        if not self.request.app.default_payment_provider:
            self.payment_method.errors.append(_(
                "You need to setup a default payment provider to enable "
                "credit card payments"
            ))
            return False
