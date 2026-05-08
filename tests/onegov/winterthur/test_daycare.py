from __future__ import annotations

import pytest
import textwrap
import transaction

from decimal import Decimal
from onegov.directory import DirectoryCollection
from onegov.directory import DirectoryConfiguration
from onegov.org.models import Organisation
from onegov.winterthur.daycare import (
    DaycareSubsidyCalculator, Services, SERVICE_DAYS)
from sqlalchemy.orm.session import close_all_sessions


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.org.models import ExtendedDirectory
    from .conftest import TestApp


@pytest.fixture(scope='function')
def app(winterthur_app: TestApp) -> TestApp:
    app = winterthur_app

    session = app.session()

    dirs: DirectoryCollection[ExtendedDirectory]
    dirs = DirectoryCollection(session, type='extended')
    directory = dirs.add(
        title="Daycare Centers",
        structure=textwrap.dedent("""
            Name *= ___
            Webseite = https://
            Tagestarif *= 0..1000
            Öffnungswochen *= 0..52
        """),
        configuration=DirectoryConfiguration(
            title="[Name]",
            order=['Name'],
        ))

    # Some actual daycare centers in Winterthur
    directory.add(values=dict(
        name="Pinochio",
        tagestarif=98,
        offnungswochen=49,
        webseite="",
    ))

    directory.add(values=dict(
        name="Fantasia",
        tagestarif=108,
        offnungswochen=51,
        webseite="",
    ))

    directory.add(values=dict(
        name="Kinderhaus",
        tagestarif=110,
        offnungswochen=50,
        webseite="",
    ))

    directory.add(values=dict(
        name="Luftibus",
        tagestarif=110,
        offnungswochen=51,
        webseite="",
    ))

    directory.add(values=dict(
        name="Child Care Corner",
        tagestarif=125,
        offnungswochen=51,
        webseite="",
    ))

    directory.add(values=dict(
        name="Apfelblüte",
        tagestarif=107,
        offnungswochen=51,
        webseite="",
    ))

    directory.add(values=dict(
        name="Am Park",
        tagestarif=120,
        offnungswochen=49,
        webseite="",
    ))

    org = session.query(Organisation).one()
    org.meta['daycare_settings'] = {
        'rebate': Decimal('5.00'),
        'max_rate': Decimal('107'),
        'min_rate': Decimal('15.85'),
        'max_income': Decimal('75000'),
        'max_wealth': Decimal('154000'),
        'min_income': Decimal('20000'),
        'max_subsidy': Decimal('92'),
        'wealth_premium': Decimal('10.00'),
        'directory': directory.id.hex,
        'services': textwrap.dedent("""
            - titel: "Ganzer Tag inkl. Mittagessen"
              tage: "Montag, Dienstag, Mittwoch, Donnerstag, Freitag"
              prozent: 100.00

            - titel: "Vor- oder Nachmittag inkl. Mittagessen"
              tage: "Montag, Dienstag, Mittwoch, Donnerstag, Freitag"
              prozent: 75.00

            - titel: "Vor- oder Nachmittag ohne Mittagessen"
              tage: "Montag, Dienstag, Mittwoch, Donnerstag, Freitag"
              prozent: 50.00
        """)
    }

    transaction.commit()
    close_all_sessions()

    return app


def test_calculate_example_1(app: TestApp) -> None:
    calculator = DaycareSubsidyCalculator(app.session())

    services = Services.from_org(app.org)
    services.select('ganzer-tag-inkl-mittagessen', SERVICE_DAYS['mo'])
    services.select('ganzer-tag-inkl-mittagessen', SERVICE_DAYS['di'])
    services.select('ganzer-tag-inkl-mittagessen', SERVICE_DAYS['mi'])
    services.select('ganzer-tag-inkl-mittagessen', SERVICE_DAYS['do'])
    services.select('ganzer-tag-inkl-mittagessen', SERVICE_DAYS['fr'])

    calculation = calculator.calculate(
        daycare=calculator.daycare_by_title("Fantasia"),
        services=services,
        income=Decimal('75000'),
        wealth=Decimal('150000'),
        rebate=True,
    )

    base, gross, actual, monthly = calculation.blocks

    # note, these results slightly differ from the output, as the rounding
    # only happens when the numbers are rendered
    results = [(r.title, r.operation, r.amount) for r in base.results]
    assert results == [
        ("Steuerbares Einkommen", None, Decimal('75000')),
        ("Vermögenszuschlag", "+", Decimal('0')),
        ("Massgebendes Gesamteinkommen", "=", Decimal('75000')),
        ("Abzüglich Minimaleinkommen", "-", Decimal('20000')),
        ("Berechnungsgrundlage", "=", Decimal('55000')),
    ]

    results = [(r.title, r.operation, r.amount) for r in gross.results]
    assert results == [
        ("Übertrag", None, Decimal('55000')),
        ("Faktor", "×", Decimal("0.001672727")),
        ("Einkommensabhängiger Elternbeitragsbestandteil", "=", Decimal("92")),
        ("Mindestbeitrag Eltern", "+", Decimal("15.85")),
        ("Elternbeitrag brutto", "=", Decimal("107.85")),
    ]

    results = [(r.title, r.operation, r.amount) for r in actual.results]
    assert results == [
        ("Übertrag", None, Decimal('107.85')),
        ("Zusatzbeitrag Eltern", "+", Decimal('0.15')),
        ("Rabatt", "-", Decimal('5.39')),
        ("Elternbeitrag pro Tag", "=", Decimal('102.61')),
        ("Städtischer Beitrag pro Tag", None, Decimal('5.39'))
    ]

    results = [(r.title, r.operation, r.amount) for r in monthly.results]
    assert results == [
        ("Wochentarif", None, Decimal('513.05')),
        ("Faktor", "×", Decimal('4.25')),
        ("Elternbeitrag pro Monat", "=", Decimal('2180.46')),
        ("Städtischer Beitrag pro Monat", None, Decimal('114.54')),
    ]


def test_calculate_example_2(app: TestApp) -> None:
    calculator = DaycareSubsidyCalculator(app.session())

    services = Services.from_org(app.org)
    services.select('ganzer-tag-inkl-mittagessen', SERVICE_DAYS['mo'])
    services.select('ganzer-tag-inkl-mittagessen', SERVICE_DAYS['di'])
    services.select('ganzer-tag-inkl-mittagessen', SERVICE_DAYS['mi'])
    services.select('ganzer-tag-inkl-mittagessen', SERVICE_DAYS['do'])
    services.select('ganzer-tag-inkl-mittagessen', SERVICE_DAYS['fr'])

    calculation = calculator.calculate(
        daycare=calculator.daycare_by_title("Apfelblüte"),
        services=services,
        income=Decimal('25000'),
        wealth=Decimal('0'),
        rebate=False,
    )

    base, gross, actual, monthly = calculation.blocks

    # note, these results slightly differ from the output, as the rounding
    # only happens when the numbers are rendered
    results = [(r.title, r.amount) for r in base.results]
    assert results == [
        ("Steuerbares Einkommen", Decimal('25000')),
        ("Vermögenszuschlag", Decimal('0')),
        ("Massgebendes Gesamteinkommen", Decimal('25000')),
        ("Abzüglich Minimaleinkommen", Decimal('20000')),
        ("Berechnungsgrundlage", Decimal('5000')),
    ]

    results = [(r.title, r.amount) for r in gross.results]
    assert results == [
        ("Übertrag", Decimal('5000.00')),
        ("Faktor", Decimal("0.0016572730")),
        ("Einkommensabhängiger Elternbeitragsbestandteil", Decimal("8.29")),
        ("Mindestbeitrag Eltern", Decimal("15.85")),
        ("Elternbeitrag brutto", Decimal("24.14")),
    ]

    results = [(r.title, r.amount) for r in actual.results]
    assert results == [
        ("Übertrag", Decimal('24.14')),
        ("Zusatzbeitrag Eltern", Decimal('0.00')),
        ("Elternbeitrag pro Tag", Decimal('24.14')),
        ("Städtischer Beitrag pro Tag", Decimal('82.86'))
    ]

    results = [(r.title, r.amount) for r in monthly.results]
    assert results == [
        ("Wochentarif", Decimal('120.70')),
        ("Faktor", Decimal('4.2500')),
        ("Elternbeitrag pro Monat", Decimal('512.98')),
        ("Städtischer Beitrag pro Monat", Decimal('1760.78')),
    ]


def test_calculate_example_3(app: TestApp) -> None:
    calculator = DaycareSubsidyCalculator(app.session())

    services = Services.from_org(app.org)
    services.select('ganzer-tag-inkl-mittagessen', SERVICE_DAYS['mo'])

    calculation = calculator.calculate(
        daycare=calculator.daycare_by_title("Pinochio"),
        services=services,
        income=Decimal('61000'),
        wealth=Decimal('264000'),
        rebate=True,
    )

    base, gross, actual, monthly = calculation.blocks

    # note, these results slightly differ from the output, as the rounding
    # only happens when the numbers are rendered
    results = [(r.title, r.amount) for r in base.results]
    assert results == [
        ("Steuerbares Einkommen", Decimal('61000')),
        ("Vermögenszuschlag", Decimal('11000')),
        ("Massgebendes Gesamteinkommen", Decimal('72000')),
        ("Abzüglich Minimaleinkommen", Decimal('20000')),
        ("Berechnungsgrundlage", Decimal('52000')),
    ]

    results = [(r.title, r.amount) for r in gross.results]
    assert results == [
        ("Übertrag", Decimal('52000.00')),
        ("Faktor", Decimal("0.0014936360")),
        ("Einkommensabhängiger Elternbeitragsbestandteil", Decimal("77.67")),
        ("Mindestbeitrag Eltern", Decimal("15.85")),
        ("Elternbeitrag brutto", Decimal("93.52")),
    ]

    results = [(r.title, r.amount) for r in actual.results]
    assert results == [
        ("Übertrag", Decimal('93.52')),
        ("Zusatzbeitrag Eltern", Decimal('0.00')),
        ("Rabatt", Decimal('4.68')),
        ("Elternbeitrag pro Tag", Decimal('88.84')),
        ("Städtischer Beitrag pro Tag", Decimal('9.16'))
    ]

    results = [(r.title, r.amount) for r in monthly.results]
    assert results == [
        ("Wochentarif", Decimal('88.84')),
        ("Faktor", Decimal('4.0833')),
        ("Elternbeitrag pro Monat", Decimal('362.76')),
        ("Städtischer Beitrag pro Monat", Decimal('37.40')),
    ]


def test_caclulate_example_4(app: TestApp) -> None:
    calculator = DaycareSubsidyCalculator(app.session())

    services = Services.from_org(app.org)
    services.select('ganzer-tag-inkl-mittagessen', SERVICE_DAYS['mo'])

    calculation = calculator.calculate(
        daycare=calculator.daycare_by_title("Luftibus"),
        services=services,
        income=Decimal('20000'),
        wealth=Decimal('10000'),
        rebate=True,
    )

    base, gross, actual, monthly = calculation.blocks

    # note, these results slightly differ from the output, as the rounding
    # only happens when the numbers are rendered
    results = [(r.title, r.amount) for r in base.results]
    assert results == [
        ("Steuerbares Einkommen", Decimal('20000')),
        ("Vermögenszuschlag", Decimal('0')),
        ("Massgebendes Gesamteinkommen", Decimal('20000')),
        ("Abzüglich Minimaleinkommen", Decimal('20000')),
        ("Berechnungsgrundlage", Decimal('0')),
    ]

    results = [(r.title, r.amount) for r in gross.results]
    assert results == [
        ("Übertrag", Decimal('0.00')),
        ("Faktor", Decimal("0.0016727270")),
        ("Einkommensabhängiger Elternbeitragsbestandteil", Decimal("0.00")),
        ("Mindestbeitrag Eltern", Decimal("15.85")),
        ("Elternbeitrag brutto", Decimal("15.85")),
    ]

    results = [(r.title, r.amount) for r in actual.results]
    assert results == [
        ("Übertrag", Decimal('15.85')),
        ("Zusatzbeitrag Eltern", Decimal('2.15')),
        ("Rabatt", Decimal('0.79')),
        ("Elternbeitrag pro Tag", Decimal('17.21')),
        ("Städtischer Beitrag pro Tag", Decimal('92.79'))
    ]

    results = [(r.title, r.amount) for r in monthly.results]
    assert results == [
        ("Wochentarif", Decimal('17.21')),
        ("Faktor", Decimal('4.25')),
        ("Elternbeitrag pro Monat", Decimal('73.14')),
        ("Städtischer Beitrag pro Monat", Decimal('394.36')),
    ]


def test_calculate_example_5(app: TestApp) -> None:
    calculator = DaycareSubsidyCalculator(app.session())

    services = Services.from_org(app.org)
    services.select('ganzer-tag-inkl-mittagessen', SERVICE_DAYS['mo'])
    services.select('vor-oder-nachmittag-inkl-mittagessen', SERVICE_DAYS['di'])
    services.select('vor-oder-nachmittag-inkl-mittagessen', SERVICE_DAYS['mi'])

    calculation = calculator.calculate(
        daycare=calculator.daycare_by_title("Am Park"),
        services=services,
        income=Decimal('42000'),
        wealth=Decimal('15000'),
        rebate=False,
    )

    base, gross, actual, monthly = calculation.blocks

    # note, these results slightly differ from the output, as the rounding
    # only happens when the numbers are rendered
    results = [(r.title, r.amount) for r in base.results]
    assert results == [
        ("Steuerbares Einkommen", Decimal('42000')),
        ("Vermögenszuschlag", Decimal('0')),
        ("Massgebendes Gesamteinkommen", Decimal('42000')),
        ("Abzüglich Minimaleinkommen", Decimal('20000')),
        ("Berechnungsgrundlage", Decimal('22000')),
    ]

    results = [(r.title, r.amount) for r in gross.results]
    assert results == [
        ("Übertrag", Decimal('22000.00')),
        ("Faktor", Decimal("0.0016727270")),
        ("Einkommensabhängiger Elternbeitragsbestandteil", Decimal("36.80")),
        ("Mindestbeitrag Eltern", Decimal("15.85")),
        ("Elternbeitrag brutto", Decimal("52.65")),
    ]

    results = [(r.title, r.amount) for r in actual.results]
    assert results == [
        ("Übertrag", Decimal('52.65')),
        ("Zusatzbeitrag Eltern", Decimal('12.15')),
        ("Elternbeitrag pro Tag", Decimal('64.80')),
        ("Städtischer Beitrag pro Tag", Decimal('55.20'))
    ]

    results = [(r.title, r.amount) for r in monthly.results]
    assert results == [
        ("Wochentarif", Decimal('162')),
        ("Faktor", Decimal('4.0833')),
        ("Elternbeitrag pro Monat", Decimal('661.50')),
        ("Städtischer Beitrag pro Monat", Decimal('563.50')),
    ]
