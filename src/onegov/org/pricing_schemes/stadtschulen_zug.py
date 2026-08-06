from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from onegov.form import move_fields
from onegov.form.fields import FieldTable
from onegov.org import _, log
from onegov.reservation import Resource, ResourcePricingScheme
from wtforms.fields import DecimalField
from wtforms.validators import InputRequired, NumberRange


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection
    from onegov.form import Form
    from onegov.org.request import OrgRequest
    from onegov.reservation import Reservation


CATEGORIES = ('A', 'B', 'C')


class StadtschulenZug(
    ResourcePricingScheme,
    name='stadtschulen_zug',
    label='Freizeitbetreuungsanlagen'
):

    @classmethod
    def reservation_unit_price(
        cls,
        reservation: Reservation,
        resource: Resource,
        submission_data: dict[str, Any] | None
    ) -> Decimal | None:
        if submission_data is None:
            return None

        category = submission_data.get('kategorie')
        if category:
            category = category[0]
        if category not in CATEGORIES:
            log.error(
                f'Reservation for pricing scheme stadtschulen_zug is missing '
                f'a valid category, we were given {category}. This probably '
                f'means we have a validation bug for this pricing scheme. We '
                f'will fallback to category C.'
            )
            category = 'C'

        col = CATEGORIES.index(category)
        table = (reservation.data or {}).get('stadtschulen_zug_price_table')
        if table is None:
            table = resource.content.get('stadtschulen_zug_price_table')
        if table is None:
            log.error(
                f'Pricing table missing for pricing scheme stadtschulen_zug '
                f'on reservation {reservation.id}'
            )
            return None

        base_rates, hourly_rates, daily_maxes = table
        start, end = reservation.start, reservation.end
        assert start is not None and end is not None
        duration = end + timedelta(microseconds=1) - start
        hours = Decimal(duration.total_seconds()) / Decimal('3600')
        extra_hours = max(0, hours - 4)
        fee = base_rates[col] + extra_hours * hourly_rates[col]
        return min(fee, daily_maxes[col])

    @classmethod
    def extend_form[T: Form](
        cls,
        form_class: type[T],
        request: OrgRequest
    ) -> type[T]:

        class StadtSchulenZugForm(form_class):  # type:ignore
            stadtschulen_zug_price_table = FieldTable(
                DecimalField(validators=[InputRequired(), NumberRange(min=0)]),
                ['A', 'B', 'C'],
                [
                    'Grundtarif (bis 4 Stunden)',
                    'Jede weitere Stunde',
                    'Max. pro Tag'
                ],
                label='Preistabelle',
                fieldset=_('Payments'),
                depends_on=('pricing_scheme', cls.name)
            )

            def process_obj(self, obj: object) -> None:
                super().process_obj(obj)
                if not request.POST and isinstance(obj, Resource):
                    self.stadtschulen_zug_price_table.data = obj.content.get(
                        'stadtschulen_zug_price_table')

            def populate_obj(
                self,
                obj: Resource,
                exclude: Collection[str] | None = None,
                include: Collection[str] | None = None
            ) -> None:
                exclude = {'stadtschulen_zug_price_table', *(exclude or ())}
                super().populate_obj(obj, exclude, include)
                obj.content['stadtschulen_zug_price_table'] = (
                    self.stadtschulen_zug_price_table.data)

            @property
            def allocation_data(self) -> dict[str, Any]:
                data = super().allocation_data
                if (
                    'pricing_scheme' in self
                    and self['pricing_scheme'].data == 'stadtschulen_zug'
                ):
                    data['stadtschulen_zug_price_table'] = (
                        self.stadtschulen_zug_price_table.data)
                return data

            def apply_data(self, data: dict[str, Any] | None) -> None:
                super().apply_data(data)
                if data and data.get('pricing_scheme') == 'stadtschulen_zug':
                    if 'stadtschulen_zug_price_table' in data:
                        self.stadtschulen_zug_price_table.data = (
                            data['stadtschulen_zug_price_table'])

            def ensure_valid_form_definition(self) -> bool | None:
                if 'pricing_scheme' not in self:
                    return None

                if self['pricing_method'].data != 'pricing_scheme':
                    return None

                if self['pricing_scheme'].data != 'stadtschulen_zug':
                    return None

                if self['parsed'].errors:
                    # if we failed to parse, don't pile on more errors
                    return None

                parsed = self['parsed'].data
                field = {
                    field.id: field
                    for field in (parsed.fields if parsed else ())
                }.get('kategorie')
                if (
                    field is None
                    or field.type != 'radio'
                    or not all(
                        choice.label.startswith(('A', 'B', 'C'))
                        for choice in field.choices
                    )
                ):
                    self['parsed'].errors.append(
                        'Mit Preisschema "Freizeitbetreuungsanlagen" braucht '
                        'es ein Feld mit Name "Kategorie", in welchem alle '
                        'Optionen mit einem der drei Kategorie-Codes "A", "B" '
                        'oder "C" beginnen.'
                    )
                    return False
                elif not field.required:
                    self['parsed'].errors.append(
                        'Mit Preisschema "Freizeitbetreuungsanlagen" darf '
                        'das Feld "Kategorie" nicht optional sein. '
                        '(Bitte "Kategorie * =" verwenden)'
                    )
                    return False
                return None

        return move_fields(
            StadtSchulenZugForm,
            ('stadtschulen_zug_price_table',),
            after='pricing_scheme'
        )
