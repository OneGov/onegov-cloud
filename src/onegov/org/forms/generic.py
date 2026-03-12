from __future__ import annotations

from dicttoxml import dicttoxml  # type:ignore[import-untyped]
from morepath.request import Response
from onegov.core.csv import convert_list_of_dicts_to_csv
from onegov.core.csv import convert_list_of_dicts_to_xlsx
from onegov.core.utils import normalize_for_url
from onegov.form import Form
from onegov.form.filters import as_float
from onegov.org import _
from wtforms.fields import BooleanField
from wtforms.fields import DateField
from wtforms.fields import DecimalField
from wtforms.fields import RadioField
from wtforms.fields import StringField
from wtforms.validators import InputRequired
from wtforms.validators import Optional
from wtforms.validators import ValidationError


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Sequence
    from onegov.core.orm.abstract import AdjacencyList
    from onegov.org.request import OrgRequest


class DateRangeForm(Form):
    """ A form providing a start/end date range. """

    start = DateField(
        label=_('Start'),
        validators=[InputRequired()]
    )

    end = DateField(
        label=_('End'),
        validators=[InputRequired()]
    )

    def validate(self) -> bool:  # type:ignore[override]
        result = super().validate()

        if self.start.data and self.end.data:
            if self.start.data > self.end.data:
                message = _('The end date must be later than the start date')
                assert isinstance(self.end.errors, list)
                self.end.errors.append(message)
                result = False

        return result


class ExportForm(Form):
    """ A form providing a choice of export formats. """

    file_format = RadioField(
        label=_('Format'),
        choices=[
            ('csv', _('CSV File')),
            ('xlsx', _('Excel File')),
            ('json', _('JSON File')),
            ('xml', _('XML File')),
        ],
        default='csv',
        validators=[
            InputRequired()
        ]
    )

    @property
    def format(self) -> str:
        return self.file_format.data

    def as_export_response(
        self,
        results: Sequence[dict[str, Any]],
        title: str = 'export',
        **kwargs: Any
    ) -> Response:
        """ Turns the given results (list of dicts) into a webob response
        with the currently selected file format.

        The additional keyword arguments are directly passed into the
        convert_list_of_dicts_to_* functions.

        For json and xml, these additional arguments are ignored.

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

        if self.format == 'xml':
            return Response(
                dicttoxml(results),
                content_type='text/xml',
                content_disposition='inline; filename={}.xml'.format(
                    normalize_for_url(title)
                ),
            )

        raise NotImplementedError()


class PaymentForm(Form):

    if TYPE_CHECKING:
        request: OrgRequest

    minimum_price_total = DecimalField(
        label=_('Minimum price total'),
        fieldset=_('Payments'),
        filters=(as_float, ),
        validators=[Optional()])

    payment_method = RadioField(
        label=_('Payment Method'),
        fieldset=_('Payments'),
        default='manual',
        validators=[InputRequired()],
        choices=[
            ('manual', _('No credit card payments')),
            ('free', _('Credit card payments optional')),
            ('cc', _('Credit card payments required'))
        ])

    def validate_minimum_price_total(self, field: DecimalField) -> None:
        if not float(self.minimum_price_total.data or 0) >= 0:
            raise ValidationError(_(
                'The price must be larger than zero'
            ))

    def validate_payment_method(self, field: RadioField) -> None:
        if self.payment_method.data == 'manual':
            return

        if not self.request.app.default_payment_provider:
            raise ValidationError(_(
                'You need to setup a default payment provider to enable '
                'credit card payments'
            ))


class ChangeAdjacencyListUrlForm(Form):
    name = StringField(
        label=_('URL path'),
        validators=[InputRequired()]
    )

    test = BooleanField(
        label=_('Test run'),
        default=True
    )

    def get_model(self) -> AdjacencyList:
        return self.model

    def validate_name(self, field: StringField) -> None:
        if not self.name.data:
            return

        model = self.get_model()

        if model.name == self.name.data:
            raise ValidationError(
                _('Please fill out a new name')
            )

        normalized_name = normalize_for_url(self.name.data)
        if not self.name.data == normalized_name:
            raise ValidationError(
                _('Invalid name. A valid suggestion is: ${name}',
                  mapping={'name': normalized_name})
            )

        if not model.parent_id:
            cls = model.__class__
            session = self.request.session
            query = session.query(cls).filter(
                cls.parent_id.is_(None),
                cls.name == normalized_name
            )
            if session.query(query.exists()).scalar():
                raise ValidationError(
                    _('An entry with the same name exists')
                )

            return

        assert model.parent is not None
        for child in model.parent.children:
            if child == self.model:
                continue
            if child.name == self.name.data:
                raise ValidationError(
                    _('An entry with the same name exists')
                )
