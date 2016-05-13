from onegov.core.utils import sanitize_html
from onegov.form import Form
from onegov.form.validators import ValidFormDefinition
from onegov.town import _
from onegov.town.forms.reservation import RESERVED_FIELDS
from onegov.town.utils import annotate_html
from wtforms import RadioField, StringField, TextAreaField, validators
from wtforms.fields.html5 import DateField


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


class DateRangeForm(Form):
    """ A form providing a start/end date range. """

    start = DateField(
        label=_("Start"),
        validators=[validators.InputRequired()]
    )

    end = DateField(
        label=_("End"),
        validators=[validators.InputRequired()]
    )

    def validate(self):
        result = super().validate()

        if self.start.data and self.end.data:
            if self.start.data > self.end.data:
                message = _("The end date must be later than the start date")
                self.end.errors.append(message)
                result = False

        return result


class ResourceCleanupForm(DateRangeForm):
    """ Defines the form to remove multiple allocations. """


class ResourceExportForm(DateRangeForm):
    """ Defines the form to export reservations. """

    file_format = RadioField(
        label=_("Format"),
        choices=[
            ('csv', _("CSV File")),
            ('xlsx', _("Excel File")),
            ('json', _("JSON File"))
        ],
        default='csv',
        validators=[
            validators.InputRequired()
        ]
    )
