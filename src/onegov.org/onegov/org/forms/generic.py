from morepath.request import Response
from onegov.form import Form
from onegov.org import _
from onegov.core.csv import convert_list_of_dicts_to_csv
from onegov.core.csv import convert_list_of_dicts_to_xlsx
from onegov.core.utils import normalize_for_url
from wtforms import RadioField, validators
from wtforms.fields.html5 import DateField


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


class ExportForm(Form):
    """ A form providing a choice of export formats. """

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

    @property
    def format(self):
        return self.file_format.data

    def as_export_response(self, results, title='export', **kwargs):
        """ Turns the given results (list of dicts) into a webob response
        with the currently selected fiel format.

        The additional keyword arguments are directly passed into the
        convert_list_of_dicts_to_* functions.

        For json, these additional arguments are ignored.

        """

        if self.format == 'json':
            return Response(
                json_body=results,
                content_type='application/json'
            )

        if self.format == 'csv':
            return Response(
                convert_list_of_dicts_to_csv(results, **kwargs),
                content_type='text/plain'
            )

        if self.format == 'xlsx':
            return Response(
                convert_list_of_dicts_to_xlsx(results, **kwargs),
                content_type=(
                    'application/vnd.openxmlformats'
                    '-officedocument.spreadsheetml.sheet'
                ),
                content_disposition='inline; filename={}.xlsx'.format(
                    normalize_for_url(title)
                )
            )

        raise NotImplemented()
