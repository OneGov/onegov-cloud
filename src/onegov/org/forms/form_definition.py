from __future__ import annotations

from onegov.core.utils import normalize_for_url
from onegov.form import Form, merge_forms, FormDefinitionCollection
from onegov.form.fields import URLPanelField
from onegov.form.validators import (
    Optional, ValidFormDefinition, ValidSurveyDefinition)
from onegov.org import _
from onegov.org.forms.fields import HtmlField
from onegov.org.forms.generic import PaymentForm
from wtforms.fields import BooleanField
from wtforms.fields import EmailField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.validators import InputRequired


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.org.request import OrgRequest


class FormDefinitionBaseForm(Form):
    request: OrgRequest

    title = StringField(_('Title'), [InputRequired()])

    lead = TextAreaField(
        label=_('Lead'),
        description=_('Describes what this form is about'),
        render_kw={'rows': 4})

    text = HtmlField(
        label=_('Text'))

    group = StringField(
        label=_('Group'),
        description=_('Used to group the form in the overview'))

    definition = TextAreaField(
        label=_('Definition'),
        description='do bruchts text',
        fieldset=_('Form Definition'),
        validators=[InputRequired(), ValidFormDefinition()],
        render_kw={'rows': 32, 'data-editor': 'form'},
        default='E-Mail *= @@@')

    formcode_doc_link = URLPanelField(
        label=_('Link to Formcode Documentation'),
        fieldset=_('Form Definition'),
        render_kw={'readonly': True},
        validators=[Optional()],
        text='https://onegov.github.io/onegov-cloud/formcode.html',
        kind='panel',
        hide_label=False
    )

    pick_up = TextAreaField(
        label=_('Pick-Up'),
        fieldset=_('Pick-Up'),
        description=_('Describes how this resource can be picked up. '
                      'This text is used on the ticket status page to '
                      'inform the user')
    )

    reply_to = EmailField(
        label=_('E-Mail Reply Address (Reply-To)'),
        fieldset=_('Tickets'),
        description=_('Replies to automated e-mails go to this address.')
    )

    show_vat = BooleanField(
        label=_('Show VAT'),
        description=_(
            'By default VAT is not shown, even when configured '
            'in the VAT settings.'
        ),
        fieldset=_('Payments')
    )

    def on_request(self) -> None:
        if not self.request.app.org.vat_rate:
            self.delete_field('show_vat')


if TYPE_CHECKING:
    # we help mypy understand merge_forms this way, eventually we should
    # write a mypy plugin for merge_forms/move_fields, that does the same
    # substitution
    class FormDefinitionForm(FormDefinitionBaseForm, PaymentForm):
        pass
else:
    class FormDefinitionForm(merge_forms(
        FormDefinitionBaseForm,
        PaymentForm
    )):
        pass


class SurveyDefinitionForm(Form):
    """ Form to create surveys. """

    # This class is needed to hide forbidden fields from the form editor
    css_class = 'survey-definition'

    title = StringField(_('Title'), [InputRequired()])

    lead = TextAreaField(
        label=_('Lead'),
        description=_('Short description of the survey'),
        render_kw={'rows': 4})

    text = HtmlField(
        label=_('Text'))

    group = StringField(
        label=_('Group'),
        description=_('Used to group the form in the overview'))

    definition = TextAreaField(
        label=_('Definition'),
        validators=[InputRequired(), ValidSurveyDefinition()],
        render_kw={'rows': 32, 'data-editor': 'form'})


class FormDefinitionUrlForm(Form):

    name = StringField(
        label=_('URL path'),
        validators=[InputRequired()]
    )

    def ensure_correct_name(self) -> bool | None:
        if not self.name.data:
            return None

        assert isinstance(self.name.errors, list)
        if self.model.name == self.name.data:
            self.name.errors.append(
                _('Please fill out a new name')
            )
            return False

        normalized_name = normalize_for_url(self.name.data)
        if self.name.data != normalized_name:
            self.name.errors.append(
                _('Invalid name. A valid suggestion is: ${name}',
                  mapping={'name': normalized_name})
            )
            return False

        other_entry = FormDefinitionCollection(self.request.session).by_name(
            normalized_name)
        if other_entry:
            self.name.errors.append(_('An entry with the same name exists'))
            return False
        return None
