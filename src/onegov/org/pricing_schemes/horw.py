from __future__ import annotations

from datetime import timedelta
from onegov.form import move_fields
from onegov.form.fields import FieldTable
from onegov.org import _, log
from onegov.reservation import Resource, ResourcePricingScheme
from wtforms.fields import DecimalField
from wtforms.validators import InputRequired, NumberRange


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection
    from decimal import Decimal
    from onegov.form import Form
    from onegov.form.parser.core import RadioField
    from onegov.org.request import OrgRequest
    from onegov.reservation import Reservation


class HorwHorwerhalle(
    ResourcePricingScheme,
    name='horw_horwerhalle',
    label='Horwerhalle (exkl. Küche/Bühne)',
    content_names=(
        'horw_horwerhalle_price_table',
        'horw_horwerhaller_non_profit_field',
        'horw_horwerhaller_wirtschaft_field',
    )
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

        data = (reservation.data or {})
        non_profit = submission_data.get(data.get(
            'horw_horwerhaller_non_profit_field',
            'horwer_non_profit_organisation'
        )) == 'Ja'
        wirtschaft = submission_data.get(data.get(
            'horw_horwerhaller_wirtschaft_field',
            'mit_wirtschaft'
        )) == 'Ja'
        table = data.get('horw_horwerhalle_price_table')
        if table is None:
            table = resource.content.get('horw_horwerhalle_price_table')
        if table is None:
            log.error(
                f'Pricing table missing for pricing scheme horw_horwerhalle '
                f'on reservation {reservation.id}'
            )
            return None

        start, end = reservation.start, reservation.end
        assert start is not None and end is not None
        # special-case where it is always free
        if non_profit and not wirtschaft and start.weekday() < 5:
            return None

        two_hours, half_day, full_day = table[
            (0 if non_profit else 2) + (1 if wirtschaft else 0)
        ]
        duration = end + timedelta(microseconds=1) - start
        if duration < timedelta(hours=2):
            return two_hours
        elif duration < timedelta(hours=5):
            return half_day
        else:
            return full_day

    @classmethod
    def extend_form[T: Form](
        cls,
        form_class: type[T],
        request: OrgRequest
    ) -> type[T]:

        class StadtSchulenZugForm(form_class):  # type:ignore
            horw_horwerhalle_price_table = FieldTable(
                DecimalField(validators=[InputRequired(), NumberRange(min=0)]),
                ['2 h', '½ Tag', '1 Tag'],
                [
                    'Horwer Non-Profit ohne Wirtschaft',
                    'Horwer Non-Profit mit Wirtschaft',
                    'Übrige ohne Wirtschaft',
                    'Übrige mit Wirtschaft'
                ],
                label='Preistabelle',
                fieldset=_('Payments'),
                depends_on=(
                    'pricing_method', 'pricing_scheme',
                    'pricing_scheme', cls.name
                )
            )

            def process_obj(self, obj: object) -> None:
                super().process_obj(obj)
                if not request.POST and isinstance(obj, Resource):
                    self.horw_horwerhalle_price_table.data = obj.content.get(
                        'horw_horwerhalle_price_table')

            def populate_obj(
                self,
                obj: Resource,
                exclude: Collection[str] | None = None,
                include: Collection[str] | None = None
            ) -> None:
                exclude = {'horw_horwerhalle_price_table', *(exclude or ())}
                super().populate_obj(obj, exclude, include)
                obj.content['horw_horwerhalle_price_table'] = (
                    self.horw_horwerhalle_price_table.data)
                if field := self.get_non_profit_field():
                    obj.content[
                        'horw_horwerhaller_non_profit_field'
                    ] = field.id
                elif 'horw_horwerhaller_non_profit_field' in obj.content:
                    del obj.content['horw_horwerhaller_non_profit_field']
                if field := self.get_wirtschaft_field():
                    obj.content[
                        'horw_horwerhaller_wirtschaft_field'
                    ] = field.id
                elif 'horw_horwerhaller_wirtschaft_field' in obj.content:
                    del obj.content['horw_horwerhaller_wirtschaft_field']

            def get_non_profit_field(self) -> RadioField | None:
                parsed = self['parsed'].data
                if parsed is None:
                    return None

                for field in parsed.fields:
                    if field.type != 'radio':
                        continue
                    if 'Non-Profit' in field.label:
                        return field
                return None

            def get_wirtschaft_field(self) -> RadioField | None:
                parsed = self['parsed'].data
                if parsed is None:
                    return None

                for field in parsed.fields:
                    if field.type != 'radio':
                        continue
                    if 'Wirtschaft' in field.label:
                        return field
                return None

            def ensure_valid_form_definition(self) -> bool | None:
                if 'pricing_scheme' not in self:
                    return None

                if self['pricing_method'].data != 'pricing_scheme':
                    return None

                if self['pricing_scheme'].data != 'horw_horwerhalle':
                    return None

                if self['parsed'].errors:
                    # if we failed to parse, don't pile on more errors
                    return None

                non_profit_field = self.get_non_profit_field()
                if (
                    non_profit_field is None
                    or not any(
                        choice.label == 'Ja'
                        for choice in non_profit_field.choices
                    )
                ):
                    self['parsed'].errors.append(
                        'Mit Preisschema "Horwerhalle" braucht es ein Feld '
                        'mit "Non-Profit" im Namen, mit einer "Ja" Antwort, '
                        'welche bedeutet, dass es sich um eine Horwer '
                        'Non-Profit Organisation handelt.'
                    )
                    return False
                elif not non_profit_field.required:
                    self['parsed'].errors.append(
                        f'Mit Preisschema "Horwerhalle" darf das Feld '
                        f'"{non_profit_field.label}" nicht optional sein.'
                    )
                    return False

                wirtschaft_field = self.get_wirtschaft_field()
                if (
                    wirtschaft_field is not None
                    and not any(
                        choice.label == 'Ja'
                        for choice in wirtschaft_field.choices
                    )
                ):
                    self['parsed'].errors.append(
                        'Mit Preisschema "Horwerhalle" braucht ein Feld '
                        'mit "Wirtschaft" im Namen, eine "Ja" Antwort, '
                        'welche bedeutet, dass die Halle mit Wirtschaft '
                        'reserviert wird.'
                    )
                    return False
                return None

        return move_fields(
            StadtSchulenZugForm,
            ('horw_horwerhalle_price_table',),
            after='pricing_scheme'
        )
