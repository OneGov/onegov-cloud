from onegov.core.html import sanitize_html
from onegov.form import Form, merge_forms
from onegov.form.validators import ValidFormDefinition
from onegov.org import _
from onegov.org.forms.generic import DateRangeForm, ExportForm
from onegov.org.forms.reservation import RESERVED_FIELDS
from onegov.org.utils import annotate_html
from wtforms import StringField, TextAreaField, validators


class ResourceForm(Form):
    """ Defines the form for all resources. """
    title = StringField(_("Title"), [validators.InputRequired()])

    lead = TextAreaField(
        label=_("Lead"),
        description=_("Describes what this reservation resource is about"),
        render_kw={'rows': 4})

    group = StringField(
        label=_("Group"),
        description=_("Used to group the resource in the overview")
    )

    text = TextAreaField(
        label=_("Text"),
        render_kw={'class_': 'editor'},
        filters=[sanitize_html, annotate_html])

    definition = TextAreaField(
        label=_("Extra Fields Definition"),
        validators=[
            validators.Optional(),
            ValidFormDefinition(
                require_email_field=False,
                reserved_fields=RESERVED_FIELDS
            )
        ],
        render_kw={'rows': 32, 'data-editor': 'form'}
    )


class ResourceCleanupForm(DateRangeForm):
    """ Defines the form to remove multiple allocations. """


class ResourceExportForm(merge_forms(DateRangeForm, ExportForm)):
    """ Resource export form with start/end date. """
