import tempfile

from morepath.request import Response
from onegov.core.csv import convert_list_of_dicts_to_csv, \
    merge_multiple_excel_files_into_one, convert_list_of_dicts_to_xlsx_names
from onegov.core.csv import convert_list_of_dicts_to_xlsx
from onegov.core.utils import normalize_for_url
from onegov.form import Form
from onegov.org import _
from wtforms.fields import BooleanField
from wtforms.fields import DateField
from wtforms.fields import RadioField
from wtforms.fields import StringField
from wtforms.validators import InputRequired


class DateRangeForm(Form):
    """ A form providing a start/end date range. """

    start = DateField(
        label=_("Start"),
        validators=[InputRequired()]
    )

    end = DateField(
        label=_("End"),
        validators=[InputRequired()]
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
            InputRequired()
        ]
    )

    @property
    def format(self):
        return self.file_format.data

    def as_export_response(self, results, title='export', **kwargs):
        """ Turns the given results (list of dicts) into a webob response
        with the currently selected file format.

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

        raise NotImplementedError()


class ExportToExcelWorksheets(Form):
    """ A form providing the export of multiple reservations into Worksheets
    """

    file_format = RadioField(
        label=_("Format"),
        choices=[
            ('xlsx', _("Excel File")),
        ],
        default='xlsx',
        validators=[
            InputRequired()
        ]
    )

    @property
    def format(self):
        return self.file_format.data

    def as_multiple_export_response(self, keys, results, titles):
        if self.format == 'xlsx':
            xlsx_files = [convert_list_of_dicts_to_xlsx_names(result,
                                                              key=key,
                                                              title=title)
                          for key, result, title in zip(keys, results, titles)]

            with tempfile.TemporaryFile() as tmp:
                absolute_path = merge_multiple_excel_files_into_one(xlsx_files)

                with open(absolute_path, mode="rb") as f:
                    tmp.write(f.read())

                tmp.seek(0)
                return Response(
                    tmp.read(),
                    content_type=(
                        'application/vnd.openxmlformats'
                        '-officedocument.spreadsheetml.sheet'
                    ),
                    content_disposition='inline; filename={}'.format(
                        'all-resources-export'
                    )
                )

        raise NotImplementedError()


class PaymentMethodForm(Form):
    payment_method = RadioField(
        label=_("Payment Method"),
        fieldset=_("Payments"),
        default='manual',
        validators=[InputRequired()],
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


class ChangeAdjacencyListUrlForm(Form):
    name = StringField(
        label=_('URL path'),
        validators=[InputRequired()]
    )

    test = BooleanField(
        label=_('Test run'),
        default=True
    )

    def get_model(self):
        return self.model

    def ensure_correct_name(self):
        if not self.name.data:
            return

        model = self.get_model()

        if model.name == self.name.data:
            self.name.errors.append(
                _('Please fill out a new name')
            )
            return False

        normalized_name = normalize_for_url(self.name.data)
        if not self.name.data == normalized_name:
            self.name.errors.append(
                _('Invalid name. A valid suggestion is: ${name}',
                  mapping={'name': normalized_name})
            )
            return False

        if not model.parent_id:
            cls = model.__class__
            query = self.request.session.query(cls)
            query = query.filter(
                cls.parent_id.is_(None),
                cls.name == normalized_name
            )
            if query.first():
                self.name.errors.append(
                    _("An entry with the same name exists")
                )
                return False
            return

        for child in model.parent.children:
            if child == self.model:
                continue
            if child.name == self.name.data:
                self.name.errors.append(
                    _("An entry with the same name exists")
                )
                return False
