from datetime import date
from decimal import Decimal
from onegov.swissvotes.models import SwissVote
from onegov.swissvotes.views.vote import view_vote_percentages
from psycopg2.extras import NumericRange
from transaction import commit
from webtest import TestApp as Client
from webtest.forms import Upload
from translationstring import TranslationString
import re


def test_view_vote(swissvotes_app, sample_vote):
    swissvotes_app.session().add(sample_vote)
    commit()

    client = Client(swissvotes_app)
    client.get('/locale/de_CH').follow()

    page = client.get('/').maybe_follow().click("Abstimmungen")
    page = page.click("Details")
    assert "100.1" in page
    assert "Vote DE" in page
    assert "V D" in page
    assert "Keyword" in page
    assert "02.06.1990" in page
    assert "Obligatorisches Referendum" in page
    assert (
        "Wirtschaft &gt; Arbeit und Beschäftigung &gt; Arbeitsbedingungen"
    ) in page
    assert (
        "Sozialpolitik &gt; Soziale Gruppen &gt; "
        "Kinder und Jugendliche"
    ) in page
    assert (
        "Sozialpolitik &gt; Soziale Gruppen &gt; "
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
    assert "Pro Velo" in page
    assert "Pro Natura" in page
    assert "Greenpeace" in page
    assert "FDP.Die Liberalen Frauen" in page
    assert "Junge CVP" in page
    assert "22.2%" in page
    assert "Details" in page
    assert "Angenommen" in page
    assert "(40.01% Ja-Stimmen)" in page
    assert "(1.5 Ja, 24.5 Nein)" in page
    assert "20.01%" in page
    assert "Kampagnenmaterial Ja" in page

    swissvotes_app.session().query(SwissVote).one()._legal_form = 3
    commit()

    page = client.get('/').maybe_follow().click("Abstimmungen")
    page = page.click("Details")
    assert "Volksinitiative" in page
    assert "Initiator" in page
    assert "32 Tage" in page

    # Party strengths

    # Note: the lower table gets all actors whose paroles is not unknown
    # To get a sum of 100%, not ubrige is displayed but the percentage of
    # unknown paroles. Hence the percentage for Unknown paroles will be
    # displayed twice.
    page = page.click("Details")
    assert "Nationalratswahl 1990"
    assert "21.2%" not in page, 'Ubrige are included in unknown'
    assert "22.2%" in page
    assert "23.2%" in page
    assert "24.2%" in page
    assert "25.2%" in page
    assert "26.2%" in page
    assert "27.2%" in page
    assert len(re.findall(r'28\.2\%', str(page))) == 2
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
    assert "19.1%" not in page, "Recommendation:None => not displayed"
    assert "20.2%" not in page, "has code 9999, so not displayed"

    # Percentages
    page = client.get(page.request.url.replace('/strengths', '/percentages'))
    results = page.json['results']
    assert results[0] == {
        'text': 'Volk', 'text_label': '', 'empty': False,
        'yea': 40.0, 'yea_label': '40.0% Ja',
        'none': 0.0, 'none_label': '',
        'nay': 60.0, 'nay_label': '60.0% Nein',
    }
    assert results[1] == {
        'text': 'Stände', 'text_label': '', 'empty': False,
        'yea': 5.8, 'yea_label': '1.5 Ja',
        'none': 0.0, 'none_label': '',
        'nay': 94.2, 'nay_label': '24.5 Nein',
    }
    assert results[2] == {
        'text': '', 'text_label': '', 'empty': True,
        'yea': 0.0, 'yea_label': '',
        'none': 0.0, 'none_label': '',
        'nay': 0.0, 'nay_label': '',
    }
    assert results[3] == {
        'text': 'Bundesrat', 'text_label': 'Position des Bundesrats',
        'empty': False,
        'yea': True, 'yea_label': 'Befürwortend',
        'none': 0.0, 'none_label': '',
        'nay': 0.0, 'nay_label': '',
    }
    assert results[4] == {
        'text': 'Nationalrat', 'text_label': '', 'empty': False,
        'yea': 33.3, 'yea_label': '10 Ja',
        'none': 0.0, 'none_label': '',
        'nay': 66.7, 'nay_label': '20 Nein',
    }
    assert results[5] == {
        'text': 'Ständerat', 'text_label': '', 'empty': False,
        'yea': 42.9, 'yea_label': '30 Ja',
        'none': 0.0, 'none_label': '',
        'nay': 57.1, 'nay_label': '40 Nein',
    }
    assert results[6] == {
        'text': 'Parteiparolen',
        'text_label': 'Empfehlungen der politischen Parteien',
        'empty': False,
        'yea': 22.2,
        'yea_label': (
            'Wähleranteile der Parteien: Befürwortende Parteien 22.2%'
        ),
        'none': 54.6,
        'none_label': (
            'Wähleranteile der Parteien: Neutral/unbekannt 54.6%'
        ),
        'nay': 23.2,
        'nay_label': (
            'Wähleranteile der Parteien: Ablehnende Parteien 23.2%'
        ),
    }
    assert page.json['title'] == 'Vote DE'

    # Delete vote
    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()

    manage = client.get('/').maybe_follow().click("Abstimmungen")
    manage = manage.click("Details").click("Abstimmung löschen")
    manage.form.submit().follow()

    assert swissvotes_app.session().query(SwissVote).count() == 0


def test_view_deciding_question(swissvotes_app, sample_vote):
    del sample_vote.posters_yes_imgs
    sample_vote._legal_form = 5

    swissvotes_app.session().add(sample_vote)
    commit()

    client = Client(swissvotes_app)
    client.get('/locale/de_CH').follow()

    page = client.get('/').maybe_follow().click("Abstimmungen")
    page = page.click("Details")

    assert "Offizielle Chronologie" in page
    assert "Ergebnisübersicht Bundeskanzlei" in page
    assert "Ergebnisübersicht Bundeskanzlei" in page

    assert "Wähleranteil des Lagers für Bevorzugung der Initiative" in page
    assert "Abgelehnt" not in page
    assert "Angenommen"not in page
    assert "Ja" not in page
    assert "Nein" not in page


def test_vote_upload(swissvotes_app, attachments):
    names = attachments.keys()

    swissvotes_app.session().add(
        SwissVote(
            bfs_number=Decimal('100.1'),
            date=date(1990, 6, 2),
            legislation_number=4,
            legislation_decade=NumericRange(1990, 1994),
            title_de="Vote DE",
            title_fr="Vote FR",
            short_title_de="V D",
            short_title_fr="V F",
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
            f'{name}.png',  # ignored
            attachments[name].reference.file.read(),
            'image/png'  # ignored
        )
    manage = manage.form.submit().follow()
    assert "Anhänge aktualisiert" in manage

    for name in names:
        name = name.replace('_', '-')
        url = manage.pyquery(f'a.{name}')[0].attrib['href']
        page = client.get(
            url).maybe_follow()
        assert page.content_type in (
            'application/pdf',
            'application/zip',
            'application/vnd.ms-office',
            'application/octet-stream',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        assert page.content_length
        assert page.body
        assert page.content_disposition.startswith('inline; filename=100.1')

    # Fallback
    client.get('/locale/en_US').follow()
    manage = client.get('/').maybe_follow().click("Votes")
    manage = manage.click("Details")
    for name in names:
        name = name.replace('_', '-')
        page = client.get(
            manage.pyquery(f'a.{name}')[0].attrib['href']).maybe_follow()
        assert page.content_type in (
            'application/pdf',
            'application/zip',
            'application/vnd.ms-office',
            'application/octet-stream',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        assert page.content_length
        assert page.body
        assert page.content_disposition.startswith('inline; filename=100.1')


def test_vote_pagination(swissvotes_app):
    for day, number in ((1, '100'), (2, '101.1'), (2, '101.2'), (3, '102')):
        swissvotes_app.session().add(
            SwissVote(
                bfs_number=Decimal(number),
                date=date(1990, 6, day),
                legislation_number=4,
                legislation_decade=NumericRange(1990, 1994),
                title_de="Vote DE",
                title_fr="Vote FR",
                short_title_de="V D",
                short_title_fr="V F",
                keyword="Keyword",
                votes_on_same_day=2,
                _legal_form=3,
                initiator="Initiator",
            )
        )
    commit()

    client = Client(swissvotes_app)
    client.get('/locale/de_CH').follow()

    # 102
    page = client.get('/').maybe_follow().click("Abstimmungen")
    page = page.click("Details", index=0)
    assert "<td>102</td>" in page
    assert "Vorherige Abstimmung" in page
    assert "Nächste Abstimmung" not in page

    # 101.2
    page = page.click("Vorherige Abstimmung")
    assert "<td>101.2</td>" in page
    assert "Vorherige Abstimmung" in page
    assert "Nächste Abstimmung" in page

    # 101.1
    page = page.click("Vorherige Abstimmung")
    assert "<td>101.1</td>" in page
    assert "Vorherige Abstimmung" in page
    assert "Nächste Abstimmung" in page

    # 100
    page = page.click("Vorherige Abstimmung")
    assert "<td>100</td>" in page
    assert "Vorherige Abstimmung" not in page
    assert "Nächste Abstimmung" in page

    # 101.1
    page = page.click("Nächste Abstimmung")
    assert "<td>101.1</td>" in page

    # 101.2
    page = page.click("Nächste Abstimmung")
    assert "<td>101.2</td>" in page

    # 102
    page = page.click("Nächste Abstimmung")
    assert "<td>102</td>" in page


def test_vote_chart(session):
    class Request(object):
        def translate(self, text):
            if isinstance(text, TranslationString):
                return text.interpolate()
            return text

    empty = {
        'empty': True, 'text': '', 'text_label': '',
        'nay': 0.0, 'nay_label': '',
        'none': 0.0, 'none_label': '',
        'yea': 0.0, 'yea_label': ''
    }

    model = SwissVote()
    request = Request()
    assert view_vote_percentages(model, request) == {
        'results': [empty],
        'title': None
    }

    model.title_de = "Vote DE"
    model.title_fr = "Vote FR"
    model.short_title_de = "V D"
    model.short_title_fr = "V F"
    model._result_people_accepted = 0
    model._result_cantons_accepted = 3
    model._position_federal_council = 33
    model._position_national_council = 1
    model._position_council_of_states = 2
    data = view_vote_percentages(model, request)
    results = data['results']
    assert results[0] == {
        'empty': False,
        'text': 'People', 'text_label': '',
        'yea': 0.0, 'yea_label': '',
        'none': 0.0, 'none_label': '',
        'nay': True, 'nay_label': 'Rejected',
    }
    assert results[1] == {
        'empty': False,
        'text': 'Cantons', 'text_label': '',
        'yea': 0.0, 'yea_label': '',
        'none': True,
        'none_label': 'Majority of the cantons not necessary',
        'nay': 0.0, 'nay_label': '',
    }
    assert results[2] == empty
    assert results[3] == {
        'empty': False,
        'text': 'National Council', 'text_label': '',
        'yea': True, 'yea_label': 'Accepting',
        'none': 0.0, 'none_label': '',
        'nay': 0.0, 'nay_label': '',
    }
    assert results[4] == {
        'empty': False,
        'text': 'Council of States', 'text_label': '',
        'yea': 0.0, 'yea_label': '',
        'none': 0.0, 'none_label': '',
        'nay': True, 'nay_label': 'Rejecting',
    }
    assert data['title'] == 'Vote DE'

    model.result_people_yeas_p = Decimal('10.2')
    model.result_cantons_yeas = Decimal('23.5')
    model.result_cantons_nays = Decimal('2.5')
    model.position_national_council_yeas = Decimal('149')
    model.position_national_council_nays = Decimal('51')
    model.position_council_of_states_yeas = Decimal('43')
    model.position_council_of_states_nays = Decimal('3')
    model.national_council_share_yeas = Decimal('1.0')
    model.national_council_share_nays = Decimal('3.4')

    data = view_vote_percentages(model, request)
    results = data['results']
    assert results[0] == {
        'empty': False,
        'text': 'People', 'text_label': '',
        'yea': 10.2, 'yea_label': '10.2% yea',
        'none': 0.0, 'none_label': '',
        'nay': 89.8, 'nay_label': '89.8% nay',
    }
    assert results[1] == {
        'empty': False,
        'text': 'Cantons', 'text_label': '',
        'yea': 90.4, 'yea_label': '23.5 yea',
        'none': 0.0, 'none_label': '',
        'nay': 9.6, 'nay_label': '2.5 nay',
    }
    assert results[2] == empty
    assert results[3] == {
        'empty': False,
        'text': 'National Council', 'text_label': '',
        'yea': 74.5, 'yea_label': '149 yea',
        'none': 0.0, 'none_label': '',
        'nay': 25.5, 'nay_label': '51 nay',
    }
    assert results[4] == {
        'empty': False,
        'text': 'Council of States', 'text_label': '',
        'yea': 93.5, 'yea_label': '43 yea',
        'none': 0.0, 'none_label': '',
        'nay': 6.5, 'nay_label': '3 nay',
    }
    assert results[5] == {
        'empty': False,
        'text': 'Party slogans',
        'text_label': 'Recommendations by political parties',
        'yea': 1.0,
        'yea_label': (
            'Electoral shares of parties: '
            'Parties recommending Yes 1.0%'
        ),
        'none': 95.6,
        'none_label': (
            'Electoral shares of parties: neutral/unknown 95.6%'
        ),
        'nay': 3.4,
        'nay_label': (
            'Electoral shares of parties: Parties recommending No 3.4%'
        )
    }

    # Test deciding question
    model._legal_form = 5
    results = view_vote_percentages(model, request)['results']

    assert results[0] == {
        'empty': False,
        'text': 'People', 'text_label': '',
        'yea': 10.2, 'yea_label': '10.2% for the initiative',
        'none': 0.0, 'none_label': '',
        'nay': 89.8, 'nay_label': '89.8% for the counter-proposal',
    }
    assert results[1] == {
        'empty': False,
        'text': 'Cantons', 'text_label': '',
        'yea': 90.4, 'yea_label': '23.5 for the initiative',
        'none': 0.0, 'none_label': '',
        'nay': 9.6, 'nay_label': '2.5 for the counter-proposal',
    }

    assert results[2] == empty

    assert results[3] == {
        'empty': False,
        'text': 'National Council', 'text_label': '',
        'yea': 74.5, 'yea_label': '149 for the initiative',
        'none': 0.0, 'none_label': '',
        'nay': 25.5, 'nay_label': '51 for the counter-proposal',
    }
    assert results[4] == {
        'empty': False,
        'text': 'Council of States', 'text_label': '',
        'yea': 93.5, 'yea_label': '43 for the initiative',
        'none': 0.0, 'none_label': '',
        'nay': 6.5, 'nay_label': '3 for the counter-proposal',
    }
    assert results[5] == {
        'empty': False,
        'text': 'Party slogans',
        'text_label': 'Recommendations by political parties',
        'yea': 1.0,
        'yea_label': (
            'Electoral shares of parties: '
            'Parties preferring the initiative 1.0%'
        ),
        'none': 95.6,
        'none_label': (
            'Electoral shares of parties: neutral/unknown 95.6%'
        ),
        'nay': 3.4,
        'nay_label': (
            'Electoral shares of parties: '
            'Parties preferring the counter-proposal 3.4%'
        ),
    }
