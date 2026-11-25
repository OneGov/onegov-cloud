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
    from onegov.form.parser.core import RadioField
    from onegov.form.parser.form import ParsedForm
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

        def get_non_profit_field(form: Form) -> RadioField | None:
            parsed: ParsedForm | None = form['parsed'].data
            if parsed is None:
                return None

            for field in parsed.fields:
                if field.type != 'radio':
                    continue
                if 'Non-Profit' in field.label:
                    return field
            return None

        def get_wirtschaft_field(form: Form) -> RadioField | None:
            parsed: ParsedForm | None = form['parsed'].data
            if parsed is None:
                return None

            for field in parsed.fields:
                if field.type != 'radio':
                    continue
                if 'Wirtschaft' in field.label:
                    return field
            return None

        class HorwerhalleForm(form_class):  # type:ignore
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
                description=(
                    'Horwer Non-Profit ohne Wirtschaft sind unter der Woche '
                    'automatisch kostenlos.'
                ),
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
                if field := get_non_profit_field(self):
                    obj.content[
                        'horw_horwerhaller_non_profit_field'
                    ] = field.id
                elif 'horw_horwerhaller_non_profit_field' in obj.content:
                    del obj.content['horw_horwerhaller_non_profit_field']
                if field := get_wirtschaft_field(self):
                    obj.content[
                        'horw_horwerhaller_wirtschaft_field'
                    ] = field.id
                elif 'horw_horwerhaller_wirtschaft_field' in obj.content:
                    del obj.content['horw_horwerhaller_wirtschaft_field']

            def ensure_valid_horw_horwerhalle_form_definition(
                self
            ) -> bool | None:
                if 'pricing_scheme' not in self:
                    return None

                if self['pricing_method'].data != 'pricing_scheme':
                    return None

                if self['pricing_scheme'].data != 'horw_horwerhalle':
                    return None

                if self['parsed'].errors:
                    # if we failed to parse, don't pile on more errors
                    return None

                non_profit_field = get_non_profit_field(self)
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

                wirtschaft_field = get_wirtschaft_field(self)
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
            HorwerhalleForm,
            ('horw_horwerhalle_price_table',),
            after='pricing_scheme'
        )


class HorwVillaKraemerstein(
    ResourcePricingScheme,
    name='horw_villa_kraemerstein',
    label='Villa Krämerstein',
    content_names=(
        'horw_villa_kraemerstein_price_table',
        'horw_villa_kraemerstein_horwer_field',
        'horw_villa_kraemerstein_anlagen_field',
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
        horwer = submission_data.get(data.get(
            'horw_villa_kraemerstein_horwer_field',
            'horwer_organisation_oder_in_horw_wohnhafte_privatperson'
        )) == 'Ja'
        anlagen = submission_data.get(data.get(
            'horw_villa_kraemerstein_anlagen_field',
            'raumlichkeiten_und_anlagen'
        ))
        wirtschaft = isinstance(anlagen, str) and 'Küche' in anlagen
        table = data.get('horw_villa_kraemerstein_price_table')
        if table is None:
            table = resource.content.get('horw_villa_kraemerstein_price_table')
        if table is None:
            log.error(
                f'Pricing table missing for pricing scheme '
                f'horw_villa_kraemerstein on reservation {reservation.id}'
            )
            return None

        start, end = reservation.start, reservation.end
        assert start is not None and end is not None
        saturday = start.weekday() == 5
        two_hours, half_day, full_day = table[
            (0 if horwer else 2) + (1 if wirtschaft else 0)
        ][3 if saturday else None:None if saturday else 3]
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

        def get_horwer_field(form: Form) -> RadioField | None:
            parsed: ParsedForm | None = form['parsed'].data
            if parsed is None:
                return None

            for field in parsed.fields:
                if field.type != 'radio':
                    continue
                if 'Horwer Organisation' in field.label:
                    return field
            return None

        def get_anlagen_field(form: Form) -> RadioField | None:
            parsed: ParsedForm | None = form['parsed'].data
            if parsed is None:
                return None

            for field in parsed.fields:
                if field.type != 'radio':
                    continue
                if 'Anlagen' in field.label:
                    return field
            return None

        class VillaKraemersteinForm(form_class):  # type:ignore
            horw_villa_kraemerstein_price_table = FieldTable(
                DecimalField(validators=[InputRequired(), NumberRange(min=0)]),
                [
                    'Fr. 2 h', 'Fr. ½ Tag', 'Fr. 1 Tag',
                    'Sa. 2 h', 'Sa. ½ Tag', 'Sa. 1 Tag'
                ],
                [
                    'Horwer ohne Küche',
                    'Horwer mit Küche',
                    'Auswärtige ohne Küche',
                    'Auswärtige mit Küche'
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
                    self.horw_villa_kraemerstein_price_table.data = (
                        obj.content.get('horw_villa_kraemerstein_price_table'))

            def populate_obj(
                self,
                obj: Resource,
                exclude: Collection[str] | None = None,
                include: Collection[str] | None = None
            ) -> None:
                exclude = {
                    'horw_villa_kraemerstein_price_table',
                    *(exclude or ())
                }
                super().populate_obj(obj, exclude, include)
                obj.content['horw_villa_kraemerstein_price_table'] = (
                    self.horw_villa_kraemerstein_price_table.data)
                if field := get_horwer_field(self):
                    obj.content[
                        'horw_villa_kraemerstein_horwer_field'
                    ] = field.id
                elif 'horw_villa_kraemerstein_horwer_field' in obj.content:
                    del obj.content['horw_villa_kraemerstein_horwer_field']
                if field := get_anlagen_field(self):
                    obj.content[
                        'horw_villa_kraemerstein_anlagen_field'
                    ] = field.id
                elif 'horw_villa_kraemerstein_anlagen_field' in obj.content:
                    del obj.content['horw_villa_kraemerstein_anlagen_field']

            def ensure_valid_horw_villa_kraemerstein_form_definition(
                self
            ) -> bool | None:
                if 'pricing_scheme' not in self:
                    return None

                if self['pricing_method'].data != 'pricing_scheme':
                    return None

                if self['pricing_scheme'].data != 'horw_villa_kraemerstein':
                    return None

                if self['parsed'].errors:
                    # if we failed to parse, don't pile on more errors
                    return None

                horwer_field = get_horwer_field(self)
                if (
                    horwer_field is None
                    or not any(
                        choice.label == 'Ja'
                        for choice in horwer_field.choices
                    )
                ):
                    self['parsed'].errors.append(
                        'Mit Preisschema "Villa Krämerstein" braucht es ein '
                        'Feld mit "Horwer Organisation" im Namen, mit einer '
                        '"Ja" Antwort, welche bedeutet, dass es sich um eine '
                        'Horwer Organisation oder in Horw wohnhafte '
                        'Privatperson handelt.'
                    )
                    return False
                elif not horwer_field.required:
                    self['parsed'].errors.append(
                        f'Mit Preisschema "Villa Krämerstein" darf das Feld '
                        f'"{horwer_field.label}" nicht optional sein.'
                    )
                    return False

                anlagen_field = get_anlagen_field(self)
                if (
                    anlagen_field is None
                    or len(anlagen_field.choices) != 2
                    or sum(
                        'Küche' in choice.label
                        for choice in anlagen_field.choices
                    ) != 1
                ):
                    self['parsed'].errors.append(
                        'Mit Preisschema "Villa Krämerstein" braucht ein Feld '
                        'mit "Anlagen" im Namen, und genau zwei Optionen, '
                        'wobei eine der Optionen das Wort "Küche" beinhalten '
                        'muss.'
                    )
                    return False
                return None

        return move_fields(
            VillaKraemersteinForm,
            ('horw_villa_kraemerstein_price_table',),
            after='pricing_scheme'
        )


class HorwAussensportanlagen(
    ResourcePricingScheme,
    name='horw_aussensportanlagen',
    label='Rasenspielfeld / Allwetterplatz / Leichtathletikanlage',
    content_names=(
        'horw_aussensportanlagen_price_table',
        'horw_aussensportanlagen_non_profit_field',
        'horw_aussensportanlagen_wirtschaft_field',
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
            'horw_aussensportanlagen_non_profit_field',
            'horwer_non_profit_organisation'
        )) == 'Ja'
        wirtschaft = submission_data.get(data.get(
            'horw_aussensportanlagen_wirtschaft_field',
            'mit_wirtschaft'
        )) == 'Ja'
        table = data.get('horw_aussensportanlagen_price_table')
        if table is None:
            table = resource.content.get(
                'horw_aussensportanlagen_price_table')
        if table is None:
            log.error(
                f'Pricing table missing for pricing scheme '
                f'horw_aussensportanlagen on reservation {reservation.id}'
            )
            return None

        start, end = reservation.start, reservation.end
        assert start is not None and end is not None
        weekend = start.weekday() >= 5
        # special-case where it is always free
        if non_profit and not wirtschaft and not weekend:
            return None

        two_hours, half_day, full_day = table[
            (0 if non_profit else 2) + (1 if wirtschaft else 0)
        ]
        duration = end + timedelta(microseconds=1) - start
        if duration < timedelta(hours=2):
            price = two_hours
            weekday_discount = Decimal(40)
        elif duration < timedelta(hours=5):
            price = half_day
            weekday_discount = Decimal(80)
        else:
            price = full_day
            weekday_discount = Decimal(160)

        # special-case where it is cheaper by a fixed amount
        if not weekend and not non_profit and not wirtschaft:
            price -= weekday_discount
        return price

    @classmethod
    def extend_form[T: Form](
        cls,
        form_class: type[T],
        request: OrgRequest
    ) -> type[T]:

        def get_non_profit_field(form: Form) -> RadioField | None:
            parsed: ParsedForm | None = form['parsed'].data
            if parsed is None:
                return None

            for field in parsed.fields:
                if field.type != 'radio':
                    continue
                if 'Non-Profit' in field.label:
                    return field
            return None

        def get_wirtschaft_field(form: Form) -> RadioField | None:
            parsed: ParsedForm | None = form['parsed'].data
            if parsed is None:
                return None

            for field in parsed.fields:
                if field.type != 'radio':
                    continue
                if 'Wirtschaft' in field.label:
                    return field
            return None

        class AussensportanlagenForm(form_class):  # type:ignore
            horw_aussensportanlagen_price_table = FieldTable(
                DecimalField(validators=[InputRequired(), NumberRange(min=0)]),
                ['2 h', '½ Tag', '1 Tag'],
                [
                    'Horwer Non-Profit ohne Wirtschaft',
                    'Horwer Non-Profit mit Wirtschaft',
                    'Übrige ohne Wirtschaft',
                    'Übrige mit Wirtschaft'
                ],
                label='Preistabelle (Wochenende)',
                description=(
                    'Horwer Non-Profit ohne Wirtschaft sind unter der Woche '
                    'kostenlos, Übrige ohne Wirtschaft erhalten unter der '
                    'Woche einen Rabatt von 40 / 80 / 160 CHF.'
                ),
                fieldset=_('Payments'),
                depends_on=(
                    'pricing_method', 'pricing_scheme',
                    'pricing_scheme', cls.name
                )
            )

            def process_obj(self, obj: object) -> None:
                super().process_obj(obj)
                if not request.POST and isinstance(obj, Resource):
                    self.horw_aussensportanlagen_price_table.data = (
                        obj.content.get(
                            'horw_aussensportanlagen_price_table'))

            def populate_obj(
                self,
                obj: Resource,
                exclude: Collection[str] | None = None,
                include: Collection[str] | None = None
            ) -> None:
                exclude = {
                    'horw_aussensportanlagen_price_table',
                    *(exclude or ())
                }
                super().populate_obj(obj, exclude, include)
                obj.content['horw_aussensportanlagen_price_table'] = (
                    self.horw_aussensportanlagen_price_table.data)
                if field := get_non_profit_field(self):
                    obj.content[
                        'horw_aussensportanlagen_non_profit_field'
                    ] = field.id
                elif 'horw_aussensportanlagen_non_profit_field' in obj.content:
                    del obj.content['horw_aussensportanlagen_non_profit_field']
                if field := get_wirtschaft_field(self):
                    obj.content[
                        'horw_aussensportanlagen_wirtschaft_field'
                    ] = field.id
                elif 'horw_aussensportanlagen_wirtschaft_field' in obj.content:
                    del obj.content['horw_aussensportanlagen_wirtschaft_field']

            def ensure_valid_horw_aussensportanlagen_form_definition(
                self
            ) -> bool | None:
                if 'pricing_scheme' not in self:
                    return None

                if self['pricing_method'].data != 'pricing_scheme':
                    return None

                if self['pricing_scheme'].data != 'horw_aussensportanlagen':
                    return None

                if self['parsed'].errors:
                    # if we failed to parse, don't pile on more errors
                    return None

                non_profit_field = get_non_profit_field(self)
                if (
                    non_profit_field is None
                    or not any(
                        choice.label == 'Ja'
                        for choice in non_profit_field.choices
                    )
                ):
                    self['parsed'].errors.append(
                        'Mit Preisschema "Aussensportanlagen" braucht es ein '
                        'Feld mit "Non-Profit" im Namen, mit einer "Ja" '
                        'Antwort, welche bedeutet, dass es sich um eine '
                        'Horwer Non-Profit Organisation handelt.'
                    )
                    return False
                elif not non_profit_field.required:
                    self['parsed'].errors.append(
                        f'Mit Preisschema "Aussensportanlagen" darf das Feld '
                        f'"{non_profit_field.label}" nicht optional sein.'
                    )
                    return False

                wirtschaft_field = get_wirtschaft_field(self)
                if (
                    wirtschaft_field is None
                    or not any(
                        choice.label == 'Ja'
                        for choice in wirtschaft_field.choices
                    )
                ):
                    self['parsed'].errors.append(
                        'Mit Preisschema "Aussensportanlagen" braucht es ein '
                        'Feld mit "Wirtschaft" im Namen, mit einer "Ja" '
                        'Antwort, welche bedeutet, dass die Anlage mit '
                        'Wirtschaft reserviert wird.'
                    )
                    return False
                elif not wirtschaft_field.required:
                    self['parsed'].errors.append(
                        f'Mit Preisschema "Aussensportanlagen" darf das Feld '
                        f'"{wirtschaft_field.label}" nicht optional sein.'
                    )
                    return False
                return None

        return move_fields(
            AussensportanlagenForm,
            ('horw_aussensportanlagen_price_table',),
            after='pricing_scheme'
        )


class HorwAulaZentrum(
    ResourcePricingScheme,
    name='horw_aula_zentrum',
    label='Aula Schulhaus Zentrum',
    content_names=(
        'horw_aula_zentrum_price_table',
        'horw_aula_zentrum_non_profit_field',
        'horw_aula_zentrum_dauerbelegung_field',
    )
):

    weekday_discount = Decimal(40)

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
            'horw_aula_zentrum_non_profit_field',
            'horwer_non_profit_organisation'
        )) == 'Ja'
        dauerbelegung = submission_data.get(data.get(
            'horw_aula_zentrum_dauerbelegung_field',
            'dauerbelegung'
        )) == 'Ja'
        table = data.get('horw_aula_zentrum_price_table')
        if table is None:
            table = resource.content.get('horw_aula_zentrum_price_table')
        if table is None:
            log.error(
                f'Pricing table missing for pricing scheme '
                f'horw_aula_zentrum on reservation {reservation.id}'
            )
            return None

        start, end = reservation.start, reservation.end
        assert start is not None and end is not None
        weekend = start.weekday() >= 5
        two_hours, half_day, full_day = table[
            (0 if non_profit else 2) + (1 if dauerbelegung else 0)
        ]
        duration = end + timedelta(microseconds=1) - start
        if duration < timedelta(hours=2):
            price = two_hours
        elif duration < timedelta(hours=5):
            price = half_day
        else:
            price = full_day

        if not weekend and non_profit and not dauerbelegung:
            price -= cls.weekday_discount
        return price

    @classmethod
    def extend_form[T: Form](
        cls,
        form_class: type[T],
        request: OrgRequest
    ) -> type[T]:

        def get_non_profit_field(form: Form) -> RadioField | None:
            parsed: ParsedForm | None = form['parsed'].data
            if parsed is None:
                return None

            for field in parsed.fields:
                if field.type != 'radio':
                    continue
                if 'Non-Profit' in field.label:
                    return field
            return None

        def get_dauerbelegung_field(form: Form) -> RadioField | None:
            parsed: ParsedForm | None = form['parsed'].data
            if parsed is None:
                return None

            for field in parsed.fields:
                if field.type != 'radio':
                    continue
                if 'Dauerbelegung' in field.label:
                    return field
            return None

        class AulaZentrumForm(form_class):  # type:ignore
            horw_aula_zentrum_price_table = FieldTable(
                DecimalField(validators=[InputRequired(), NumberRange(min=0)]),
                ['2 h', '½ Tag', '1 Tag'],
                [
                    'Horwer Non-Profit Einzelbelegung',
                    'Horwer Non-Profit Dauerbelegung',
                    'Übrige Einzelbelegung',
                    'Übrige Dauerbelegung'
                ],
                label='Preistabelle (Wochenende)',
                description=(
                    'Horwer Non-Profit Einzelbelegungen erhalten unter der '
                    'Woche einen Rabatt von 40 CHF.'
                ),
                fieldset=_('Payments'),
                depends_on=(
                    'pricing_method', 'pricing_scheme',
                    'pricing_scheme', cls.name
                )
            )

            def process_obj(self, obj: object) -> None:
                super().process_obj(obj)
                if not request.POST and isinstance(obj, Resource):
                    self.horw_aula_zentrum_price_table.data = (
                        obj.content.get('horw_aula_zentrum_price_table'))

            def populate_obj(
                self,
                obj: Resource,
                exclude: Collection[str] | None = None,
                include: Collection[str] | None = None
            ) -> None:
                exclude = {'horw_aula_zentrum_price_table', *(exclude or ())}
                super().populate_obj(obj, exclude, include)
                obj.content['horw_aula_zentrum_price_table'] = (
                    self.horw_aula_zentrum_price_table.data)
                if field := get_non_profit_field(self):
                    obj.content[
                        'horw_aula_zentrum_non_profit_field'
                    ] = field.id
                elif 'horw_aula_zentrum_non_profit_field' in obj.content:
                    del obj.content['horw_aula_zentrum_non_profit_field']
                if field := get_dauerbelegung_field(self):
                    obj.content[
                        'horw_aula_zentrum_dauerbelegung_field'
                    ] = field.id
                elif 'horw_aula_zentrum_dauerbelegung_field' in obj.content:
                    del obj.content['horw_aula_zentrum_dauerbelegung_field']

            def ensure_valid_horw_aula_zentrum_form_definition(
                self
            ) -> bool | None:
                if 'pricing_scheme' not in self:
                    return None

                if self['pricing_method'].data != 'pricing_scheme':
                    return None

                if self['pricing_scheme'].data != 'horw_aula_zentrum':
                    return None

                if self['parsed'].errors:
                    # if we failed to parse, don't pile on more errors
                    return None

                non_profit_field = get_non_profit_field(self)
                if (
                    non_profit_field is None
                    or not any(
                        choice.label == 'Ja'
                        for choice in non_profit_field.choices
                    )
                ):
                    self['parsed'].errors.append(
                        'Mit Preisschema "Aula Schulhaus Zentrum" braucht es '
                        'ein Feld mit "Non-Profit" im Namen, mit einer "Ja" '
                        'Antwort, welche bedeutet, dass es sich um eine '
                        'Horwer Non-Profit Organisation handelt.'
                    )
                    return False
                elif not non_profit_field.required:
                    self['parsed'].errors.append(
                        f'Mit Preisschema "Aula Schulhaus Zentrum" darf das '
                        f'Feld "{non_profit_field.label}" nicht optional sein.'
                    )
                    return False

                dauerbelegung_field = get_dauerbelegung_field(self)
                if (
                    dauerbelegung_field is None
                    or not any(
                        choice.label == 'Ja'
                        for choice in dauerbelegung_field.choices
                    )
                ):
                    self['parsed'].errors.append(
                        'Mit Preisschema "Aula Schulhaus Zentrum" braucht es '
                        'ein Feld mit "Dauerbelegung" im Namen, mit einer '
                        '"Ja" Antwort, welche bedeutet, dass es sich um eine '
                        'Dauerbelegung handelt.'
                    )
                    return False
                elif not dauerbelegung_field.required:
                    self['parsed'].errors.append(
                        f'Mit Preisschema "Aula Schulhaus Zentrum" darf das '
                        f'Feld "{dauerbelegung_field.label}" nicht optional '
                        f'sein.'
                    )
                    return False
                return None

        return move_fields(
            AulaZentrumForm,
            ('horw_aula_zentrum_price_table',),
            after='pricing_scheme'
        )


class HorwSaalEgli(
    ResourcePricingScheme,
    name='horw_saal_egli',
    label='Saal Egli',
    content_names=(
        'horw_saal_egli_category_field',
        'horw_saal_egli_anlagen_field',
    )
):

    kategorien = (
        'Horwer Non-Profit-Organisationen (Vereine)',
        'Übrige Organisationen und Privatpersonen',
        'Auswärtige',
    )
    anlagen = (
        'Saal Egli mit Foyer',
        'Saal Egli mit Foyer, Küche und Geräte',
        'Saal Egli mit Foyer, Küche, Geräte und Geschirr',
    )
    # NOTE: We hardcode the prices here since we're only using this scheme
    #       for a single room, if we end up needing parametrization in the
    #       future, we can create a new version and deprecate this scheme.
    # room -> category -> weekday/weekend -> 2 h, ½ Tag, 1 Tag
    prices = (
        (
            ((30, 50, 80), (50, 70, 100)),
            ((70, 100, 150), (100, 150, 200)),
            ((150, 200, 300), (200, 300, 400)),
        ),
        (
            ((40, 60, 90), (60, 80, 110)),
            ((80, 110, 160), (110, 160, 210)),
            ((160, 210, 320), (210, 320, 450)),
        ),
        (
            ((50, 70, 100), (70, 90, 120)),
            ((90, 120, 170), (120, 170, 220)),
            ((170, 220, 350), (220, 350, 480)),
        ),
    )

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
        kategorie = submission_data.get(data.get(
            'horw_saal_egli_category_field',
            'kategorie'
        ))
        anlagen = submission_data.get(data.get(
            'horw_saal_egli_anlagen_field',
            'raumlichkeiten_und_anlagen'
        ))
        if kategorie not in cls.kategorien or anlagen not in cls.anlagen:
            return None

        start, end = reservation.start, reservation.end
        assert start is not None and end is not None
        weekend = start.weekday() >= 5
        two_hours, half_day, full_day = (
            cls.prices[cls.anlagen.index(anlagen)][
                cls.kategorien.index(kategorie)
            ][1 if weekend else 0])
        duration = end + timedelta(microseconds=1) - start
        if duration < timedelta(hours=2):
            return Decimal(two_hours)
        elif duration < timedelta(hours=5):
            return Decimal(half_day)
        else:
            return Decimal(full_day)

    @classmethod
    def extend_form[T: Form](
        cls,
        form_class: type[T],
        request: OrgRequest
    ) -> type[T]:

        kategorien = cls.kategorien
        anlagen = cls.anlagen

        def get_field(
            form: Form,
            options: tuple[str, ...]
        ) -> RadioField | None:
            parsed: ParsedForm | None = form['parsed'].data
            if parsed is None:
                return None

            for field in parsed.fields:
                if field.type != 'radio':
                    continue
                if {choice.label for choice in field.choices} == set(
                    options
                ):
                    return field
            return None

        class SaalEgliForm(form_class):  # type:ignore

            def populate_obj(
                self,
                obj: Resource,
                exclude: Collection[str] | None = None,
                include: Collection[str] | None = None
            ) -> None:
                super().populate_obj(obj, exclude, include)
                if field := get_field(self, kategorien):
                    obj.content['horw_saal_egli_category_field'] = field.id
                elif 'horw_saal_egli_category_field' in obj.content:
                    del obj.content['horw_saal_egli_category_field']
                if field := get_field(self, anlagen):
                    obj.content['horw_saal_egli_anlagen_field'] = field.id
                elif 'horw_saal_egli_anlagen_field' in obj.content:
                    del obj.content['horw_saal_egli_anlagen_field']

            def ensure_valid_horw_saal_egli_form_definition(
                self
            ) -> bool | None:
                if 'pricing_scheme' not in self:
                    return None

                if self['pricing_method'].data != 'pricing_scheme':
                    return None

                if self['pricing_scheme'].data != 'horw_saal_egli':
                    return None

                if self['parsed'].errors:
                    # if we failed to parse, don't pile on more errors
                    return None

                for options in (kategorien, anlagen):
                    field = get_field(self, options)
                    if field is None:
                        self['parsed'].errors.append(
                            'Mit Preisschema "Saal Egli" braucht es ein '
                            'Auswahlfeld mit genau den folgenden Optionen: '
                            + ', '.join(f'"{option}"' for option in options)
                        )
                        return False
                    elif not field.required:
                        self['parsed'].errors.append(
                            f'Mit Preisschema "Saal Egli" darf das Feld '
                            f'"{field.label}" nicht optional sein.'
                        )
                        return False
                return None

        return SaalEgliForm
