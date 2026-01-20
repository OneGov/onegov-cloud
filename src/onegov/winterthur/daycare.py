from __future__ import annotations

import textwrap
import yaml

from babel.numbers import format_decimal
from collections import defaultdict, OrderedDict
from functools import cached_property
from decimal import Decimal, localcontext
from markupsafe import Markup
from onegov.core.templates import PageTemplate
from onegov.core.utils import normalize_for_url
from onegov.directory import DirectoryCollection
from onegov.form import Form
from onegov.org.models import Organisation
from onegov.org.models.directory import ExtendedDirectoryEntryCollection
from onegov.winterthur import _
from ordered_set import OrderedSet
from wtforms.fields import BooleanField, DecimalField, Field, SelectField
from wtforms.validators import NumberRange, InputRequired, ValidationError


from typing import Any, Literal, NamedTuple, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from onegov.org.models import ExtendedDirectory, ExtendedDirectoryEntry
    from sqlalchemy.orm import Session
    from typing import Self
    from uuid import UUID
    from wtforms.form import BaseForm


SERVICE_DAYS = {
    'mo': 0,
    'di': 1,
    'mi': 2,
    'do': 3,
    'fr': 4,
    'sa': 5,
    'so': 6,
}

SERVICE_DAYS_LABELS = {
    0: _('Monday'),
    1: _('Tuesday'),
    2: _('Wednesday'),
    3: _('Thursday'),
    4: _('Friday'),
    5: _('Saturday'),
    6: _('Sunday'),
}

# http://babel.pocoo.org/en/latest/numbers.html#pattern-syntax
FORMAT = '#,##0.00########'


def round_to(n: Decimal, precision: str) -> Decimal:
    assert isinstance(precision, str)

    precision_dec = Decimal(precision)
    correction = Decimal('0.5') if n >= 0 else Decimal('-0.5')

    return int(n / precision_dec + correction) * precision_dec


def format_precise(amount: Decimal | None) -> str:
    if not amount:
        return '0.00'

    with localcontext() as ctx:
        ctx.prec = 28

        return format_decimal(amount, format=FORMAT, locale='de_CH')


def format_1_cent(amount: Decimal) -> str:
    return format_precise(round_to(amount, '0.01'))


def format_5_cents(amount: Decimal) -> str:
    return format_precise(round_to(amount, '0.05'))


class Daycare:

    def __init__(
        self,
        id: UUID,
        title: str,
        rate: Decimal | float | str,
        weeks: int
    ) -> None:
        self.id = id
        self.title = title
        self.rate = Decimal(rate)
        self.weeks = weeks

    @property
    def factor(self) -> Decimal:
        return Decimal(self.weeks) / Decimal('12')


class Service(NamedTuple):
    id: str
    title: str
    percentage: Decimal
    days: OrderedSet[int]


class Services:

    selected: dict[str, set[int]]

    def __init__(self, definition: str | None) -> None:
        if definition:
            self.available = OrderedDict(self.parse_definition(definition))
        else:
            self.available = OrderedDict()

        self.selected = defaultdict(set)

    @classmethod
    def from_org(cls, org: Organisation) -> Self:
        if 'daycare_settings' not in org.meta:
            return cls(None)

        if 'services' not in org.meta['daycare_settings']:
            return cls(None)

        return cls(org.meta['daycare_settings']['services'])

    @classmethod
    def from_session(cls, session: Session) -> Self:
        return cls.from_org(session.query(Organisation).one())

    @staticmethod
    def parse_definition(definition: str) -> Iterator[tuple[str, Service]]:
        for service in yaml.safe_load(definition):
            service_id = normalize_for_url(service['titel'])
            days = (d.strip() for d in service['tage'].split(','))

            yield service_id, Service(
                id=service_id,
                title=service['titel'],
                percentage=Decimal(service['prozent']),
                days=OrderedSet(SERVICE_DAYS[d.lower()[:2]] for d in days),
            )

    def select(self, service_id: str, day: int) -> None:
        self.selected[service_id].add(day)

    def deselect(self, service_id: str, day: int) -> None:
        self.selected[service_id].remove(day)

    def is_selected(self, service_id: str, day: int) -> bool:
        if service_id not in self.selected:
            return False

        return day in self.selected[service_id]

    @property
    def total(self) -> Decimal | Literal[0]:
        """ Returns the total percentage of used services. """
        return sum(
            self.available[s].percentage * len(self.selected[s])
            for s in self.selected
        )


class Result:

    def __init__(
        self,
        title: str,
        amount: Decimal | None = None,
        note: str | None = None,
        operation: str | None = None,
        important: bool = False,
        currency: str | None = 'CHF',
        output_format: Callable[[Decimal], str] | None = None
    ) -> None:

        self.title = title
        self.amount = amount
        self.note = textwrap.dedent(note or '').strip(' \n')
        self.operation = operation
        self.important = important
        self.currency = currency
        self.output_format = output_format or format_1_cent

    def __bool__(self) -> bool:
        return bool(self.amount)

    @property
    def readable_amount(self) -> str:
        assert self.amount is not None
        return self.output_format(self.amount)


class Block:

    results: list[Result]

    def __init__(self, id: str, title: str) -> None:
        self.id = id
        self.title = title
        self.results = []
        self.total = Decimal(0)

    def op(
        self,
        title: str,
        amount: Decimal | None = None,
        note: str | None = None,
        operation: str | None = None,
        important: bool = False,
        currency: str | None = 'CHF',
        output_format: Callable[[Decimal], str] | None = None,
        total_places: int = 2,
        amount_places: int = 2
    ) -> Decimal:

        if amount == 0:
            amount = Decimal('0')

        def limit_total(total: Decimal) -> Decimal:
            return total.quantize(Decimal(f'0.{"0" * (total_places - 1)}1'))

        def limit_amount(amount: Decimal) -> Decimal:
            return amount.quantize(Decimal(f'0.{"0" * (amount_places - 1)}1'))

        if operation is None:
            assert amount is not None
            self.total = amount

        elif operation == '+':
            assert amount is not None
            self.total += amount

        elif operation == '=':
            amount = self.total if amount is None else amount
            self.total = max(amount, Decimal('0'))

        elif operation == '-':
            assert amount is not None
            self.total -= amount

        elif operation in ('*', 'x', '×', '⋅'):
            assert amount is not None
            self.total *= amount

        elif operation in ('/', '÷'):
            assert amount is not None
            self.total /= amount

        # limit the amount and the total after the operation, not before
        self.total = limit_total(self.total)
        assert amount is not None
        amount = limit_amount(amount)

        self.results.append(Result(
            title=title,
            amount=amount,
            note=note,
            operation=operation,
            important=important,
            currency=currency,
            output_format=output_format,
        ))

        return self.total


class DirectoryDaycareAdapter:

    def __init__(self, directory: ExtendedDirectory) -> None:
        self.directory = directory

    @cached_property
    def fieldmap(self) -> dict[str, str | None]:
        fieldmap: dict[str, str | None] = {
            'daycare_rate': None,
            'daycare_weeks': None,
            'daycare_url': None,
        }

        for field in self.directory.basic_fields:

            if 'tarif' in field.label.lower():
                fieldmap['daycare_rate'] = field.id
                continue

            if 'woche' in field.label.lower():
                fieldmap['daycare_weeks'] = field.id
                continue

            if 'web' in field.label.lower():
                fieldmap['daycare_url'] = field.id
                continue

        return fieldmap

    def as_daycare(self, entry: ExtendedDirectoryEntry) -> Daycare:
        assert self.fieldmap['daycare_rate'] is not None
        assert self.fieldmap['daycare_weeks'] is not None
        return Daycare(
            id=entry.id,
            title=entry.title,
            rate=entry.values[self.fieldmap['daycare_rate']],
            weeks=entry.values[self.fieldmap['daycare_weeks']],
        )


class Settings:

    directory: str
    max_income: Decimal
    max_rate: Decimal
    max_subsidy: Decimal
    max_wealth: Decimal
    min_income: Decimal
    min_rate: Decimal
    rebate: Decimal
    services: str
    wealth_premium: Decimal
    # NOTE: This attribute is optional
    explanation: Markup

    def __init__(self, organisation: Organisation) -> None:
        settings = organisation.meta.get('daycare_settings', {})

        for key, value in settings.items():
            if key == 'explanation':
                # NOTE: We need to treat this as Markup, it would
                #       be cleaner if this proxy object used
                #       dict_property/dict_markup_property, we would
                #       need to do something special for is_valid
                #       however
                value = Markup(value)  # nosec: B704
            setattr(self, key, value)

    def is_valid(self) -> bool:
        keys = (
            'directory',
            'max_income',
            'max_rate',
            'max_subsidy',
            'max_wealth',
            'min_income',
            'min_rate',
            'rebate',
            'services',
            'wealth_premium',
        )

        for key in keys:
            if not hasattr(self, key):
                return False

        return True

    def factor(self, daycare: Daycare) -> Decimal:
        min_day_rate = daycare.rate - self.min_rate
        min_day_rate = min(min_day_rate, self.max_subsidy)

        factor = min_day_rate / (self.max_income - self.min_income)
        factor = factor.quantize(Decimal('0.000000001'))

        return factor


class SubsidyResult(NamedTuple):
    blocks: tuple[Block, ...]
    parent_share_per_month: str
    city_share_per_month: str
    total_per_month: str
    agenda: tuple[tuple[str, str | None, str], ...]


class DaycareSubsidyCalculator:

    def __init__(self, session: Session) -> None:
        self.session = session

    @cached_property
    def organisation(self) -> Organisation:
        return self.session.query(Organisation).one()

    @cached_property
    def settings(self) -> Settings:
        return Settings(self.organisation)

    @cached_property
    def directory(self) -> ExtendedDirectory:
        directory: ExtendedDirectory | None = (
            DirectoryCollection(self.session, type='extended')
            .by_id(self.settings.directory)
        )
        assert directory is not None
        return directory

    @cached_property
    def daycares(self) -> dict[str, Daycare]:
        adapter = DirectoryDaycareAdapter(self.directory)

        items = ExtendedDirectoryEntryCollection(self.directory).query()
        return {
            item.id.hex: adapter.as_daycare(item)
            for item in items
            if item.access == 'public'
        }

    def daycare_by_title(self, title: str) -> Daycare:
        return next(d for d in self.daycares.values() if d.title == title)

    def calculate_precisely(
        self,
        daycare: Daycare,
        services: Services,
        income: Decimal,
        wealth: Decimal,
        rebate: bool
    ) -> SubsidyResult:
        """ Creates a detailed calculation of the subsidy paid by Winterthur.

        The reslt is a list of tables with explanations.

        :param daycare:
            The selected daycare (a :class:`Daycare` instance).

        :param services:
            Services used (a :class:`Services` instance)

        :param income:
            The income as a decimal.

        :param wealth:
            The wealth as decimal.

        :param rebate:
            True if a rebate is applied

        Note, due to the specific nature of the content here, which is probably
        not going to be translated, we use German. For consistency we want to
        limit this, but with Winterthur these kinds of things crop up as the
        wording is quite specific and adding translations would just make
        this a lot harder.

        """

        cfg = self.settings
        fmt = format_precise

        # Base Rate
        # ---------
        base = Block('base', 'Berechnungsgrundlage für die Elternbeiträge')

        base.op(
            title='Steuerbares Einkommen',
            amount=income,
            note="""
                Steuerbares Einkommen gemäss letzter Veranlagung.
            """)

        base.op(
            title='Vermögenszuschlag',
            amount=max(
                (wealth - cfg.max_wealth)
                * cfg.wealth_premium
                / Decimal('100'),
                Decimal(0)),
            operation='+',
            note=f"""
                Der Vermögenszuschlag beträgt
                {fmt(cfg.wealth_premium).rstrip('0').rstrip('.')}% des
                Vermögens, für das tatsächlich Steuern anfallen
                (ab {fmt(cfg.max_wealth)} CHF).
            """)

        base.op(
            title='Massgebendes Gesamteinkommen',
            operation='=')

        base.op(
            title='Abzüglich Minimaleinkommen',
            operation='-',
            amount=cfg.min_income)

        base.op(
            title='Berechnungsgrundlage',
            operation='=')

        # Gross Contribution
        # ------------------
        gross = Block('gross', 'Berechnung des Brutto-Elternbeitrags')

        gross.op(
            title='Übertrag',
            amount=base.total)

        gross.op(
            title='Faktor',
            amount=cfg.factor(daycare),
            currency=None,
            operation='×',
            note="""
                Ihr Elternbeitrag wird aufgrund eines Faktors berechnet
                (Kita-Reglement Art. 20 Abs 3).
            """,
            output_format=format_precise,
            amount_places=10)

        gross.op(
            title='Einkommensabhängiger Elternbeitragsbestandteil',
            operation='=')

        gross.op(
            title='Mindestbeitrag Eltern',
            amount=cfg.min_rate,
            operation='+')

        gross.op(
            title='Elternbeitrag brutto',
            operation='=',
            amount=min(gross.total, daycare.rate))

        # Actual contribution
        # -------------------
        rebate_amount = (
            gross.total * cfg.rebate / 100
            if rebate else Decimal(0)
        )

        actual = Block('actual', (
            'Berechnung des Elternbeitrags und des '
            'städtischen Beitrags pro Tag'
        ))

        actual.op(
            title='Übertrag',
            amount=gross.total)

        actual.op(
            title='Zusatzbeitrag Eltern',
            amount=max(
                daycare.rate - cfg.max_subsidy - cfg.min_rate,
                Decimal(0)
            ),
            operation='+',
            note=f"""
                Zusatzbeitrag für Kitas, deren Tagestarif über
                {cfg.max_rate} CHF liegt.
            """)

        if actual.total >= rebate_amount and rebate_amount > 0:
            actual.op(
                title='Rabatt',
                amount=rebate_amount,
                operation='-',
                note=f"""
                    Bei einem Betreuungsumfang von insgesamt mehr als 2 ganzen
                    Tagen pro Woche gilt ein Rabatt von
                    {fmt(cfg.rebate).rstrip('0').rstrip('.')}%.
                """)

        parent_share_per_day = actual.op(
            title='Elternbeitrag pro Tag',
            operation='=',
            note="""
                Ihr Beitrag pro Tag (100%) und Kind.
            """,
            important=True)

        city_share_per_day = actual.op(
            title='Städtischer Beitrag pro Tag',
            amount=max(daycare.rate - parent_share_per_day, Decimal('0.00')),
            important=True,
            note="""
                Städtischer Beitrag für Ihr Kind pro Tag.
            """)

        # Monthly contribution
        # --------------------
        monthly = Block(
            'monthly', (
                'Berechnung des Elternbeitrags und des städtischen '
                'Beitrags pro Monat'
            )
        )

        monthly.op(
            title='Wochentarif',
            amount=parent_share_per_day * services.total / 100,
            note="""
                Wochentarif: Elternbeiträge der gewählten Betreuungstage.
            """)

        monthly.op(
            title='Faktor',
            amount=daycare.factor,
            currency=None,
            operation='×',
            note="""
                Faktor für jährliche Öffnungswochen Ihrer Kita.
            """,
            output_format=format_precise,
            amount_places=4)

        parent_share_per_month = monthly.op(
            title='Elternbeitrag pro Monat',
            operation='=',
            important=True,
            output_format=format_5_cents)

        city_share_per_month = monthly.op(
            title='Städtischer Beitrag pro Monat',
            amount=city_share_per_day * services.total / 100 * daycare.factor,
            important=True,
            output_format=format_5_cents)

        # Services table
        # --------------
        def services_table() -> Iterator[tuple[str, str | None, str]]:
            total = Decimal(0)
            total_percentage = Decimal(0)

            for day in SERVICE_DAYS.values():
                for service_id in services.selected:
                    if day in services.selected[service_id]:
                        service = services.available[service_id]
                        cost = parent_share_per_day * service.percentage / 100

                        total += cost
                        total_percentage += service.percentage

                        label = SERVICE_DAYS_LABELS[day]
                        yield (label, service.title, format_5_cents(cost))

            yield (_('Total'), None, format_5_cents(total))

        total = (
            round_to(parent_share_per_month, '0.05')
            + round_to(city_share_per_month, '0.05')
        )

        return SubsidyResult(
            blocks=(base, gross, actual, monthly),
            parent_share_per_month=format_5_cents(parent_share_per_month),
            city_share_per_month=format_5_cents(city_share_per_month),
            total_per_month=format_5_cents(total),
            agenda=tuple(services_table()),
        )

    # FIXME: What is this alias for? Do we actually need it?
    if TYPE_CHECKING:
        calculate = calculate_precisely
    else:
        def calculate(self, *args, **kwargs):
            return self.calculate_precisely(*args, **kwargs)


class DaycareServicesWidget:

    template = PageTemplate("""
        <table class="daycare-services">
            <thead>
                <tr>
                    <th></th>
                    <th tal:repeat="service this.services.available.values()">
                        <div class="daycare-services-title">
                            ${service.title}
                        </div>
                        <div class="daycare-services-percentage">
                            ${service.percentage}%
                        </div>
                    </th>
                </tr>
            </thead>
            <tbody>
                <tr tal:repeat="day this.days">
                    <th>
                        <strong class="show-for-small-only">
                            ${this.day_label(day)[:2]}
                        </strong>
                        <strong class="show-for-medium-up">
                            ${this.day_label(day)}
                        </strong>
                    </th>
                    <td tal:repeat="svc this.services.available.values()">
                        <label>
                            <input
                                type="checkbox"

                                id="${svc.id}-${day}"
                                name="${this.field.name}"
                                value="${svc.id}-${day}"

                                tal:attributes="
                                    checked this.is_selected(svc, day)
                                "
                            />
                        </label>
                    </td>
                </tr>
            </tbody>
        </table
    """)

    def __call__(self, field: DaycareServicesField, **kwargs: Any) -> Markup:
        self.field = field
        self.services = field.services

        return Markup(self.template.render(this=self))  # nosec: B704

    def is_selected(self, service: Service, day: int) -> bool:
        return self.services.is_selected(service.id, day)

    def day_label(self, day: int) -> str:
        return self.field.meta.request.translate(SERVICE_DAYS_LABELS[day])

    @property
    def days(self) -> OrderedSet[int]:
        days: OrderedSet[int] = OrderedSet()

        for service in self.services.available.values():
            for day in service.days:
                days.add(day)

        return days


class DaycareServicesField(Field):

    widget = DaycareServicesWidget()

    @cached_property
    def services(self) -> Services:
        return Services.from_session(self.meta.request.session)

    def process_formdata(self, valuelist: list[Any]) -> None:
        for value in valuelist:
            service_id, day = value.rsplit('-', maxsplit=1)
            self.services.select(service_id, int(day))

    def pre_validate(self, form: BaseForm) -> None:
        for day in SERVICE_DAYS.values():
            days = sum(
                1 for id in self.services.available
                if self.services.is_selected(id, day)
            )

            if days > 1:
                raise ValidationError(_('Each day may only be selected once.'))


class DaycareSubsidyCalculatorForm(Form):

    model: DaycareSubsidyCalculator

    daycare = SelectField(
        label=_('Select Daycare'),
        validators=(InputRequired(), ),
        choices=())

    services = DaycareServicesField(
        label=_('Care'),
        validators=(InputRequired(), ))

    income = DecimalField(
        label=_('Definite Taxable income'),
        validators=(InputRequired(), NumberRange(min=0)))

    wealth = DecimalField(
        label=_('Definite Taxable wealth'),
        validators=(InputRequired(), NumberRange(min=0)))

    rebate = BooleanField(
        label=_('Rebate'),
        description=_(
            'Does at least one child in your household attend the same '
            'daycare for more than two whole days a week?'
        ))

    def on_request(self) -> None:
        self.daycare.choices = list(self.daycare_choices)

    @property
    def daycare_choices(self) -> Iterator[tuple[str, str]]:

        def choice(daycare: Daycare) -> tuple[str, str]:
            label = _((
                '${title} / day rate CHF ${rate} / '
                '${weeks} weeks open per year'
            ), mapping={
                'title': daycare.title,
                'rate': daycare.rate,
                'weeks': daycare.weeks
            })

            return (daycare.id.hex, self.request.translate(label))

        for daycare in self.model.daycares.values():
            yield choice(daycare)

    @property
    def selected_daycare(self) -> Daycare | None:
        for daycare in self.model.daycares.values():
            if daycare.id.hex == self.daycare.data:
                return daycare
        return None
