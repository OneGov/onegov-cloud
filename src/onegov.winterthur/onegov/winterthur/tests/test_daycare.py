import pytest
import textwrap
import transaction

from decimal import Decimal
from onegov.directory import DirectoryCollection
from onegov.directory import DirectoryConfiguration
from onegov.org.models import Organisation
from onegov.winterthur.daycare import DaycareSubsidyCalculator, Services


@pytest.fixture(scope='function')
def app(winterthur_app):
    app = winterthur_app

    session = app.session()

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
            order=('Name', ),
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
        'min_rate': Decimal('15'),
        'max_income': Decimal('75000'),
        'max_wealth': Decimal('154000'),
        'min_income': Decimal('20000'),
        'max_subsidy': Decimal('92'),
        'wealth_premium': Decimal('10.00'),
        'directory': directory.id.hex,
        'services': textwrap.dedent("""
            - titel: "Ganzer Tag inkl. Mitagessen"
              tage: "Montag, Dienstag, Mittwoch, Donnerstag, Freitag"
              prozent: 100.00

            - titel: "Vor- oder Nachmittag inkl. Mitagessen"
              tage: "Montag, Dienstag, Mittwoch, Donnerstag, Freitag"
              prozent: 75.00

            - titel: "Vor- oder Nachmittag ohne Mitagessen"
              tage: "Montag, Dienstag, Mittwoch, Donnerstag, Freitag"
              prozent: 50.00
        """)
    }

    transaction.commit()
    session.close_all()

    return app


def test_calculate_example_1(app):
    calculator = DaycareSubsidyCalculator(app.session())

    services = Services.from_org(app.org)
    services.select('ganzer-tag-inkl-mitagessen', 'mo')
    services.select('ganzer-tag-inkl-mitagessen', 'di')
    services.select('ganzer-tag-inkl-mitagessen', 'mi')
    services.select('ganzer-tag-inkl-mitagessen', 'do')
    services.select('ganzer-tag-inkl-mitagessen', 'fr')

    calculation = calculator.calculate(
        daycare=calculator.daycare_by_title("Fantasia"),
        services=services,
        income=Decimal('75000'),
        wealth=Decimal('150000'),
        rebate=True,
    )

    base, gross, net, actual, monthly = calculation.blocks

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
        ("Mindestbeitrag Eltern", "+", Decimal("15")),
        ("Elternbeitrag brutto", "=", Decimal("107")),
    ]

    results = [(r.title, r.operation, r.amount) for r in net.results]
    assert results == [
        ("Übertrag", None, Decimal('107')),
        ("Rabatt", "-", Decimal('5.35')),
        ("Elternbeitrag netto", "=", Decimal('101.65')),
    ]

    results = [(r.title, r.operation, r.amount) for r in actual.results]
    assert results == [
        ("Übertrag", None, Decimal('101.65')),
        ("Zusatzbeitrag Eltern", "+", Decimal('1')),
        ("Elternbeitrag pro Tag", "=", Decimal('102.65')),
        ("Städtischer Beitrag pro Tag", None, Decimal('5.35'))
    ]

    results = [(r.title, r.operation, r.amount) for r in monthly.results]
    assert results == [
        ("Wochentarif", None, Decimal('513.25')),
        ("Faktor", "×", Decimal('4.25')),
        ("Elternbeitrag pro Monat", "=", Decimal('2181.31')),
        ("Städtischer Beitrag pro Monat", None, Decimal('113.69')),
    ]


def test_calculate_example_2(app):
    calculator = DaycareSubsidyCalculator(app.session())

    services = Services.from_org(app.org)
    services.select('ganzer-tag-inkl-mitagessen', 'mo')
    services.select('ganzer-tag-inkl-mitagessen', 'di')
    services.select('ganzer-tag-inkl-mitagessen', 'mi')
    services.select('ganzer-tag-inkl-mitagessen', 'do')
    services.select('ganzer-tag-inkl-mitagessen', 'fr')

    calculation = calculator.calculate(
        daycare=calculator.daycare_by_title("Apfelblüte"),
        services=services,
        income=Decimal('25000'),
        wealth=Decimal('0'),
        rebate=False,
    )

    base, gross, net, actual, monthly = calculation.blocks

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
        ("Übertrag", Decimal('5000')),
        ("Faktor", Decimal("0.001672727")),
        ("Einkommensabhängiger Elternbeitragsbestandteil", Decimal("8.36")),
        ("Mindestbeitrag Eltern", Decimal("15")),
        ("Elternbeitrag brutto", Decimal("23.36")),
    ]

    results = [(r.title, r.amount) for r in net.results]
    assert results == [
        ("Übertrag", Decimal('23.36')),
        ("Rabatt", Decimal('0')),
        ("Elternbeitrag netto", Decimal('23.36')),
    ]

    results = [(r.title, r.amount) for r in actual.results]
    assert results == [
        ("Übertrag", Decimal('23.36')),
        ("Zusatzbeitrag Eltern", Decimal('0')),
        ("Elternbeitrag pro Tag", Decimal('23.36')),
        ("Städtischer Beitrag pro Tag", Decimal('83.64'))
    ]

    results = [(r.title, r.amount) for r in monthly.results]
    assert results == [
        ("Wochentarif", Decimal('116.80')),
        ("Faktor", Decimal('4.2500')),
        ("Elternbeitrag pro Monat", Decimal('496.40')),
        ("Städtischer Beitrag pro Monat", Decimal('1777.35')),
    ]


def test_calculate_example_3(app):
    calculator = DaycareSubsidyCalculator(app.session())

    services = Services.from_org(app.org)
    services.select('ganzer-tag-inkl-mitagessen', 'mo')

    calculation = calculator.calculate(
        daycare=calculator.daycare_by_title("Pinochio"),
        services=services,
        income=Decimal('61000'),
        wealth=Decimal('264000'),
        rebate=True,
    )

    base, gross, net, actual, monthly = calculation.blocks

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
        ("Übertrag", Decimal('52000')),
        ("Faktor", Decimal("0.001509091")),
        ("Einkommensabhängiger Elternbeitragsbestandteil", Decimal("78.47")),
        ("Mindestbeitrag Eltern", Decimal("15")),
        ("Elternbeitrag brutto", Decimal("93.47")),
    ]

    results = [(r.title, r.amount) for r in net.results]
    assert results == [
        ("Übertrag", Decimal('93.47')),
        ("Rabatt", Decimal('4.67')),
        ("Elternbeitrag netto", Decimal('88.80')),
    ]

    results = [(r.title, r.amount) for r in actual.results]
    assert results == [
        ("Übertrag", Decimal('88.80')),
        ("Zusatzbeitrag Eltern", Decimal('0')),
        ("Elternbeitrag pro Tag", Decimal('88.80')),
        ("Städtischer Beitrag pro Tag", Decimal('9.20'))
    ]

    results = [(r.title, r.amount) for r in monthly.results]
    assert results == [
        ("Wochentarif", Decimal('88.80')),
        ("Faktor", Decimal('4.0833')),
        ("Elternbeitrag pro Monat", Decimal('362.60')),
        ("Städtischer Beitrag pro Monat", Decimal('37.57')),
    ]


def test_caclulate_example_4(app):
    calculator = DaycareSubsidyCalculator(app.session())

    services = Services.from_org(app.org)
    services.select('ganzer-tag-inkl-mitagessen', 'mo')

    calculation = calculator.calculate(
        daycare=calculator.daycare_by_title("Luftibus"),
        services=services,
        income=Decimal('20000'),
        wealth=Decimal('10000'),
        rebate=True,
    )

    base, gross, net, actual, monthly = calculation.blocks

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
        ("Übertrag", Decimal('0')),
        ("Faktor", Decimal("0.001672727")),
        ("Einkommensabhängiger Elternbeitragsbestandteil", Decimal("0")),
        ("Mindestbeitrag Eltern", Decimal("15")),
        ("Elternbeitrag brutto", Decimal("15")),
    ]

    results = [(r.title, r.amount) for r in net.results]
    assert results == [
        ("Übertrag", Decimal('15')),
        ("Rabatt", Decimal('0.75')),
        ("Elternbeitrag netto", Decimal('15')),
    ]

    results = [(r.title, r.amount) for r in actual.results]
    assert results == [
        ("Übertrag", Decimal('15')),
        ("Zusatzbeitrag Eltern", Decimal('3')),
        ("Elternbeitrag pro Tag", Decimal('18')),
        ("Städtischer Beitrag pro Tag", Decimal('92'))
    ]

    results = [(r.title, r.amount) for r in monthly.results]
    assert results == [
        ("Wochentarif", Decimal('18')),
        ("Faktor", Decimal('4.25')),
        ("Elternbeitrag pro Monat", Decimal('76.50')),
        ("Städtischer Beitrag pro Monat", Decimal('391')),
    ]


def test_calculate_example_5(app):
    calculator = DaycareSubsidyCalculator(app.session())

    services = Services.from_org(app.org)
    services.select('ganzer-tag-inkl-mitagessen', 'mo')
    services.select('vor-oder-nachmittag-inkl-mitagessen', 'di')
    services.select('vor-oder-nachmittag-inkl-mitagessen', 'mi')

    calculation = calculator.calculate(
        daycare=calculator.daycare_by_title("Am Park"),
        services=services,
        income=Decimal('42000'),
        wealth=Decimal('15000'),
        rebate=False,
    )

    base, gross, net, actual, monthly = calculation.blocks

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
        ("Übertrag", Decimal('22000')),
        ("Faktor", Decimal("0.001672727")),
        ("Einkommensabhängiger Elternbeitragsbestandteil", Decimal("36.80")),
        ("Mindestbeitrag Eltern", Decimal("15")),
        ("Elternbeitrag brutto", Decimal("51.80")),
    ]

    results = [(r.title, r.amount) for r in net.results]
    assert results == [
        ("Übertrag", Decimal('51.80')),
        ("Rabatt", Decimal('0.0')),
        ("Elternbeitrag netto", Decimal('51.80')),
    ]

    results = [(r.title, r.amount) for r in actual.results]
    assert results == [
        ("Übertrag", Decimal('51.80')),
        ("Zusatzbeitrag Eltern", Decimal('13')),
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
