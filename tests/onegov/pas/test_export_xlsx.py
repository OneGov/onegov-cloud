from datetime import date, datetime
from decimal import Decimal
import transaction
from onegov.pas.models import (
    Party,
    Parliamentarian,
    ParliamentarianRole,
    RateSet,
    Commission,
    SettlementRun,
    Attendence,
)
import io
from openpyxl import load_workbook  # type: ignore[import-untyped]


def test_export_salary_xlsx(client_with_es, session):
    client = client_with_es
    client.login_admin()

    # Setup test data
    with transaction.manager:
        rate_set = RateSet(
            year=2024,
            cost_of_living_adjustment=Decimal('2.0'),  # 2%
            plenary_none_member_halfday=Decimal('100'),
            commission_normal_member_initial=Decimal('50'),
            study_normal_member_halfhour=Decimal('20'),
            shortest_all_member_halfhour=Decimal('15')
        )
        session.add(rate_set)

        parliamentarian1 = Parliamentarian(
            first_name='Peter',
            last_name='Muster',
            gender='male',
            personnel_number='PN123'
        )
        parliamentarian2 = Parliamentarian(
            first_name='Petra',
            last_name='Musterfrau',
            gender='female',
            personnel_number='PN456'
        )
        session.add_all([parliamentarian1, parliamentarian2])

        party = Party(name='Test Party')
        session.add(party)

        role1 = ParliamentarianRole(
            parliamentarian=parliamentarian1,
            role='member',
            party=party,
            start=date(2024, 1, 1)
        )
        role2 = ParliamentarianRole(
            parliamentarian=parliamentarian2,
            role='member',
            party=party,
            start=date(2024, 1, 1)
        )
        session.add_all([role1, role2])

        commission = Commission(name='Finance Commission', type='normal')
        session.add(commission)

        attendances = [
            Attendence(
                parliamentarian=parliamentarian1, date=date(2024, 1, 10),
                duration=240, type='plenary'  # 100 * 1.02 = 102
            ),
            Attendence(
                parliamentarian=parliamentarian1, date=date(2024, 1, 15),
                duration=120, type='commission', commission=commission
                # 50 * 1.02 = 51
            ),
            Attendence(
                parliamentarian=parliamentarian2, date=date(2024, 2, 5),
                duration=60, type='study', commission=commission
                # (20 * 2) * 1.02 = 40.80
            ),
            Attendence(
                parliamentarian=parliamentarian2, date=date(2024, 2, 10),
                duration=30, type='shortest'
                # 15 * 1.02 = 15.30
            ),
        ]
        session.add_all(attendances)

        settlement_run = SettlementRun(
            name='Q1 2024',
            start=date(2024, 1, 1),
            end=date(2024, 3, 31),
            active=True
        )
        session.add(settlement_run)
        session.flush()
        transaction.commit()

    # Navigate to the settlement run page and click the export link
    page = client.get(f'/settlement-runs/{settlement_run.id}')
    export_link = page.pyquery('a:contains("Salary Export (XLSX)")').attr('href')
    response = client.get(export_link)

    assert response.status_code == 200
    assert response.content_type == \
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    # Parse the XLSX content
    workbook = load_workbook(filename=io.BytesIO(response.body))
    sheet = workbook['DATA']
    rows = list(sheet.rows)

    # Check headers
    expected_headers = [
        'Personalnummer', 'Vertragsnummer', 'Lohnart / Lohnarten Nr.',
        None, None, None, None, None, None, None, None, None,
        'Betrag', None, None, None,
        'Bemerkung/Lohnartentext, welche auf der Lohnabrechnung erscheint',
        None, 'Fibu-Konto', 'Kostenstelle / Kostenträger',
        None, None, None, None, None,
        'Angabe zum Jahr und zum Quartal', 'Exportdatum'
    ]
    assert [cell.value for cell in rows[0]] == expected_headers

    # Check data rows (order might vary, so check specific values)
    # Expected data: PN, LohnartNr, Betrag, LohnartText, JahrQuartal, ExportDatum
    # Note: Betrag is Decimal, ExportDatum is datetime
    export_date_str = datetime.now().date().strftime('%d.%m.%Y')
    year_quarter_str = "2024 Q1"

    expected_data_points = {
        'PN123': [
            ('2405', Decimal('102.00'), 'Sitzungsentschädigung KR'),
            ('2410', Decimal('51.00'),
             'Kommissionsentschädigung KR inkl. Kürzestsitzungen')
        ],
        'PN456': [
            ('2421', Decimal('40.80'), 'Aktenstudium Kantonsrat'),
            ('2410', Decimal('15.30'),
             'Kommissionsentschädigung KR inkl. Kürzestsitzungen')
        ]
    }

    found_rows = 0
    for row in rows[1:]:
        pn = row[0].value
        lohnart_nr = row[2].value
        betrag = row[12].value
        lohnart_text = row[16].value
        jq = row[25].value
        ed_cell = row[26].value
        ed = ed_cell.strftime('%d.%m.%Y') if isinstance(ed_cell, datetime) \
            else ed_cell

        assert jq == year_quarter_str
        assert ed == export_date_str

        matched = False
        if pn in expected_data_points:
            for i, (exp_lnr, exp_betrag, exp_ltext) in \
                    enumerate(expected_data_points[pn]):
                if lohnart_nr == exp_lnr and \
                   Decimal(str(betrag)).quantize(Decimal('0.01')) == exp_betrag and \
                   lohnart_text == exp_ltext:
                    expected_data_points[pn].pop(i)
                    if not expected_data_points[pn]:
                        del expected_data_points[pn]
                    found_rows += 1
                    matched = True
                    break
        assert matched, f"Unexpected row: {pn}, {lohnart_nr}, {betrag}"

    assert found_rows == 4, "Not all expected data points were found"
    assert not expected_data_points, \
        f"Some expected data points were not found: {expected_data_points}"
