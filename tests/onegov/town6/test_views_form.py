from tests.onegov.town6.common import step_class


def test_form_steps(client):
    page = client.get('/form/familienausweis')
    assert step_class(page, 1) == 'is-current'

    for name in ('ehefrau', 'ehemann'):
        page.form[f'personalien_{name}_vorname'] = 'L'
        page.form[f'personalien_{name}_name'] = 'L'
        page.form[f'personalien_{name}_ledigname'] = 'L'
        page.form[f'personalien_{name}_geburtsdatum'] = '2020-01-01'
        page.form[f'personalien_{name}_heimatort'] = '2020-01-01'

    page.form['eheschliessung_plz_ort_eheschliessung'] = 'Z'
    page.form['eheschliessung_datum_eheschliessung'] = '2020-01-01'
    page.form['versand_versand_strasse_inkl_hausnummer_'] = '2020-01-01'
    page.form['versand_versand_plz_ort'] = 'U'
    page.form['kontakt_bemerkungen_telefon'] = '044 444 44 44'
    page.form['kontakt_bemerkungen_e_mail'] = 'z@z.ch'

    page = page.form.submit().follow()
    assert step_class(page, 1) == 'is-complete'
    assert step_class(page, 2) == 'is-current'
    assert step_class(page, 3) == ''

    page = page.form.submit().follow()
    assert step_class(page, 1) == 'is-complete'
    assert step_class(page, 2) == 'is-complete'
    assert step_class(page, 3) == 'is-current'
