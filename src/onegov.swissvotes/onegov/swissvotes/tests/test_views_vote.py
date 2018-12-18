from datetime import date
from decimal import Decimal
from onegov.swissvotes.models import SwissVote
from psycopg2.extras import NumericRange
from transaction import commit
from webtest import TestApp as Client
from webtest.forms import Upload


def test_view_vote(swissvotes_app):
    swissvotes_app.session().add(
        SwissVote(
            bfs_number=Decimal('100.1'),
            date=date(1990, 6, 2),
            decade=NumericRange(1990, 1999),
            legislation_number=4,
            legislation_decade=NumericRange(1990, 1994),
            title="Vote",
            keyword="Keyword",
            votes_on_same_day=2,
            _legal_form=1,
            initiator="Initiator",
            anneepolitique="anneepolitique",
            descriptor_1_level_1=Decimal('4'),
            descriptor_1_level_2=Decimal('4.2'),
            descriptor_1_level_3=Decimal('4.21'),
            descriptor_2_level_1=Decimal('10'),
            descriptor_2_level_2=Decimal('10.3'),
            descriptor_2_level_3=Decimal('10.35'),
            descriptor_3_level_1=Decimal('10'),
            descriptor_3_level_2=Decimal('10.3'),
            descriptor_3_level_3=Decimal('10.33'),
            _result=1,
            result_eligible_voters=2,
            result_votes_empty=3,
            result_votes_invalid=4,
            result_votes_valid=5,
            result_votes_total=6,
            result_turnout=Decimal('20.01'),
            _result_people_accepted=1,
            result_people_yeas=8,
            result_people_nays=9,
            result_people_yeas_p=Decimal('40.01'),
            _result_cantons_accepted=1,
            result_cantons_yeas=Decimal('1.5'),
            result_cantons_nays=Decimal('24.5'),
            result_cantons_yeas_p=Decimal('60.01'),
            _department_in_charge=1,
            procedure_number=Decimal('24.557'),
            _position_federal_council=1,
            _position_parliament=1,
            _position_national_council=1,
            position_national_council_yeas=10,
            position_national_council_nays=20,
            _position_council_of_states=1,
            position_council_of_states_yeas=30,
            position_council_of_states_nays=40,
            duration_federal_assembly=30,
            duration_post_federal_assembly=31,
            duration_initative_collection=32,
            duration_initative_federal_council=33,
            duration_initative_total=34,
            duration_referendum_collection=35,
            duration_referendum_total=36,
            signatures_valid=40,
            signatures_invalid=41,
            _recommendation_fdp=1,
            _recommendation_cvp=1,
            _recommendation_sps=1,
            _recommendation_svp=1,
            _recommendation_lps=2,
            _recommendation_ldu=2,
            _recommendation_evp=2,
            _recommendation_csp=3,
            _recommendation_pda=3,
            _recommendation_poch=3,
            _recommendation_gps=4,
            _recommendation_sd=4,
            _recommendation_rep=4,
            _recommendation_edu=5,
            _recommendation_fps=5,
            _recommendation_lega=5,
            _recommendation_kvp=66,
            _recommendation_glp=66,
            _recommendation_bdp=None,
            _recommendation_mcg=9999,
            _recommendation_sav=1,
            _recommendation_eco=2,
            _recommendation_sgv=3,
            _recommendation_sbv_usp=3,
            _recommendation_sgb=3,
            _recommendation_travs=3,
            _recommendation_vsa=9999,
            national_council_election_year=1990,
            national_council_share_fdp=Decimal('01.10'),
            national_council_share_cvp=Decimal('02.10'),
            national_council_share_sp=Decimal('03.10'),
            national_council_share_svp=Decimal('04.10'),
            national_council_share_lps=Decimal('05.10'),
            national_council_share_ldu=Decimal('06.10'),
            national_council_share_evp=Decimal('07.10'),
            national_council_share_csp=Decimal('08.10'),
            national_council_share_pda=Decimal('09.10'),
            national_council_share_poch=Decimal('10.10'),
            national_council_share_gps=Decimal('11.10'),
            national_council_share_sd=Decimal('12.10'),
            national_council_share_rep=Decimal('13.10'),
            national_council_share_edu=Decimal('14.10'),
            national_council_share_fps=Decimal('15.10'),
            national_council_share_lega=Decimal('16.10'),
            national_council_share_kvp=Decimal('17.10'),
            national_council_share_glp=Decimal('18.10'),
            national_council_share_bdp=Decimal('19.10'),
            national_council_share_mcg=Decimal('20.20'),
            national_council_share_ubrige=Decimal('21.20'),
            national_council_share_yeas=Decimal('22.20'),
            national_council_share_nays=Decimal('23.20'),
            national_council_share_neutral=Decimal('24.20'),
            national_council_share_vague=Decimal('25.10'),
        )
    )
    commit()

    client = Client(swissvotes_app)
    client.get('/locale/de_CH').follow()

    page = client.get('/').maybe_follow().click("Abstimmungen")
    page = page.click("Details")
    assert "100.1" in page
    assert "Vote" in page
    assert "Keyword" in page
    assert "02.06.1990" in page
    assert "Obligatorisches Referendum" in page
    assert (
        "Wirtschaft &gt; Arbeit und Beschäftigung &gt; Arbeitsbedingungen"
    ) in page
    assert (
        "Soziale Fragen – Sozialpolitik &gt; Soziale Gruppen &gt; "
        "Kinder und Jugendliche"
    ) in page
    assert (
        "Soziale Fragen – Sozialpolitik &gt; Soziale Gruppen &gt; "
        "Stellung der Frau"
    ) in page
    assert "anneepolitique" in page
    assert "Befürwortend" in page
    assert "24.557" in page
    assert "30 Tage" in page
    assert "(10 Ja, 20 Nein)" in page
    assert "(30 Ja, 40 Nein)" in page
    assert "CVP" in page
    assert "FDP" in page
    assert "SPS" in page
    assert "SVP" in page
    assert "EVP" in page
    assert "LdU" in page
    assert "LPS" in page
    assert "CSP" in page
    assert "PdA" in page
    assert "POCH" in page
    assert "GPS" in page
    assert "REP" in page
    assert "SD" in page
    assert "EDU" in page
    assert "FPS" in page
    assert "Lega" in page
    assert "GLP" in page
    assert "KVP" in page
    assert "SAV" in page
    assert "eco" in page
    assert "SBV" in page
    assert "SGB" in page
    assert "SGV" in page
    assert "TravS" in page
    assert "22.2%" in page
    assert "Details" in page
    assert "Angenommen" in page
    assert "(40.01% Jastimmen)" in page
    assert "(1.5 Ja, 24.5 Nein)" in page
    assert "20.01%" in page

    swissvotes_app.session().query(SwissVote).one()._legal_form = 3
    commit()

    page = client.get('/').maybe_follow().click("Abstimmungen")
    page = page.click("Details")
    assert "Volksinitiative" in page
    assert "Initiator" in page
    assert "32 Tage" in page

    # Party strengths
    page = page.click("Details")
    assert "Nationalratswahl 1990"
    assert "21.2%" in page
    assert "22.2%" in page
    assert "23.2%" in page
    assert "24.2%" in page
    assert "25.1%" in page
    assert "1.1%" in page
    assert "2.1%" in page
    assert "3.1%" in page
    assert "4.1%" in page
    assert "5.1%" in page
    assert "6.1%" in page
    assert "7.1%" in page
    assert "8.1%" in page
    assert "9.1%" in page
    assert "10.1%" in page
    assert "11.1%" in page
    assert "12.1%" in page
    assert "13.1%" in page
    assert "14.1%" in page
    assert "15.1%" in page
    assert "16.1%" in page
    assert "17.1%" in page
    assert "18.1%" in page
    assert "19.1%" in page
    assert "20.2%" in page

    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()

    # Delete vote
    manage = client.get('/').maybe_follow().click("Abstimmungen")
    manage = manage.click("Details").click("Abstimmung löschen")
    manage = manage.form.submit().follow()

    assert swissvotes_app.session().query(SwissVote).count() == 0


def test_vote_upload(swissvotes_app, attachments):
    names = attachments.keys()

    swissvotes_app.session().add(
        SwissVote(
            bfs_number=Decimal('100.1'),
            date=date(1990, 6, 2),
            decade=NumericRange(1990, 1999),
            legislation_number=4,
            legislation_decade=NumericRange(1990, 1994),
            title="Vote",
            keyword="Keyword",
            votes_on_same_day=2,
            _legal_form=3,
            initiator="Initiator",
        )
    )
    commit()

    client = Client(swissvotes_app)
    client.get('/locale/de_CH').follow()

    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()

    manage = client.get('/').maybe_follow().click("Abstimmungen")
    manage = manage.click("Details").click("Anhänge verwalten")
    for name in names:
        manage.form[name] = Upload(
            f'{name}.pdf',
            attachments[name].reference.file.read(),
            'application/pdf'
        )
    manage = manage.form.submit().follow()
    assert "Anhänge aktualisiert" in manage

    for name in names:
        name = name.replace('_', '-')
        page = client.get(manage.pyquery(f'a.{name}')[0].attrib['href'])
        assert page.content_type == 'application/pdf'
        assert page.content_length
        assert page.body

    # Fallback
    client.get('/locale/en_US').follow()
    manage = client.get('/').maybe_follow().click("Votes")
    manage = manage.click("Details")
    for name in names:
        name = name.replace('_', '-')
        page = client.get(manage.pyquery(f'a.{name}')[0].attrib['href'])
        assert page.content_type == 'application/pdf'
        assert page.content_length
        assert page.body
