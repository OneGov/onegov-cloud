from __future__ import annotations

import json
from typing import TYPE_CHECKING

from freezegun import freeze_time

if TYPE_CHECKING:
    from .conftest import Client


def test_parliamentarians(client: Client) -> None:
    client.login_admin()

    # ris views not enabled
    assert client.get('/parliamentarian', status=404)
    assert client.get('/parliamentarian/new', status=404)

    # enable ris and configure interest tie categories
    settings = client.get('/ris-enable')
    settings.form['ris_enabled'] = True
    settings.form['ris_interest_tie_categories'] = 'Work; Leisure and Fun;'
    settings.form.submit()

    # add parliamentary groups
    groups = client.get('/parliamentary-groups')
    assert 'Noch keine Fraktionen erfasst' in groups

    page = client.get('/parliamentary-groups/new')
    page.form['name'] = 'Die Moderne Fraktion'
    page = page.form.submit().follow()
    assert 'Die Moderne Fraktion' in page

    page = client.get('/parliamentary-groups/new')
    page.form['name'] = 'Old Party Fraktion'
    page = page.form.submit().follow()
    assert 'Old Party Fraktion' in page

    edit = page.click('Bearbeiten')
    edit.form['description'] = 'We the old once!'
    page = edit.form.submit().follow()
    assert 'We the old once!' in page

    # add commissions
    commissions = client.get('/commissions')
    assert 'Keine aktiven Kommissionen' in commissions

    page = client.get('/commissions/new')
    page.form['name'] = 'Verkehrskommission'
    page = page.form.submit().follow()
    assert 'Verkehrskommission' in page

    edit = page.click('Bearbeiten')
    edit.form['description'] = 'Commission for ...'
    page = edit.form.submit().follow()
    assert 'Commission for ...' in page

    parliamentarian_pages = []
    with freeze_time("2025-11-03 8:00"):
        page = client.get('/parliamentarians')
        assert ('Keine Filterergebnisse gefunden oder noch keine '
                'Parlamentarier erfasst') in page

        # filter keywords
        for keyword in ['Aktiv', 'Inaktiv', 'Partei']:
            assert keyword in page

        # add parliamentarian
        new = client.get('/parliamentarians/new')
        new.form['first_name'] = 'Funny'
        new.form['last_name'] = 'Comedian'
        new.form['email_primary'] = 'funny.comedian@fun.org'
        new.form['party'] = 'Die Moderne'
        new.form['interest_ties'] = json.dumps({  # many field
            'values': [{
                'interest_tie': 'Manager',
                'category': 'Work'
            }]
        })
        parliamentarian = new.form.submit().follow()
        parliamentarian_pages.append(parliamentarian)
        assert 'Funny' in parliamentarian
        assert 'Comedian' in parliamentarian
        assert 'funny.comedian@fun.org' in parliamentarian
        assert 'Die Moderne' in parliamentarian
        assert 'Manager' in parliamentarian
        assert 'Work' in parliamentarian

        # edit parliamentarian
        edit = parliamentarian.click('Bearbeiten')
        edit.form['first_name'] = 'Laugh'
        edit.form['interest_ties'] = json.dumps({  # many field
            'values': [{
                'interest_tie': 'Manager',
                'category': 'Work'
            }, {
                'interest_tie': 'Talented Sailor',
                'category': 'Leisure and Fun'
            }]
        })
        parliamentarian = edit.form.submit().follow()
        assert 'Laugh' in parliamentarian
        assert 'Manager' in parliamentarian
        assert 'Work' in parliamentarian
        assert 'Talented Sailor' in parliamentarian
        assert 'Leisure and Fun' in parliamentarian

        # add role
        role = parliamentarian.click('Neue Fraktionsfunktion')
        options = role.form['parliamentary_group_id'].options
        id = next(
            (opt[0] for opt in options if opt[2] == 'Die Moderne Fraktion'))
        role.form['parliamentary_group_id'] = id
        role.form['parliamentary_group_role'] = 'member'
        parliamentarian = role.form.submit().follow()
        assert 'Neue Rolle hinzugefügt' in parliamentarian
        assert 'Mitglied Parlament' in parliamentarian
        assert 'Mitglied Fraktion' in parliamentarian
        assert 'Partei' in parliamentarian
        assert 'Die Moderne Fraktion' in parliamentarian

        # add commission
        commission = parliamentarian.click('Neue Kommissionsfunktion')
        options = commission.form['commission_id'].options
        id = next(
            (opt[0] for opt in options if opt[2] == 'Verkehrskommission'))
        commission.form['commission_id'] = id
        commission.form['role'] = 'member'
        parliamentarian = commission.form.submit().follow()
        assert 'Neue Rolle hinzugefügt' in parliamentarian
        assert 'Mitglied' in parliamentarian
        assert 'Verkehrskommission' in parliamentarian

        # add another parliamentarian
        new = client.get('/parliamentarians/new')
        new.form['first_name'] = 'Old'
        new.form['last_name'] = 'Man'
        new.form['email_primary'] = 'old.man@cov.org'
        new.form['party'] = 'Old Party'
        parliamentarian = new.form.submit().follow()
        parliamentarian_pages.append(parliamentarian)
        assert 'Old' in parliamentarian
        assert 'Man' in parliamentarian
        assert 'old.man@cov.org' in parliamentarian
        assert 'Old Party' in parliamentarian

        # add role
        role = parliamentarian.click('Neue Fraktionsfunktion')
        options = role.form['parliamentary_group_id'].options
        id = next(
            (opt[0] for opt in options if opt[2] == 'Old Party Fraktion'))
        role.form['parliamentary_group_id'] = id
        role.form['parliamentary_group_role'] = 'member'
        parliamentarian = role.form.submit().follow()
        assert 'Neue Rolle hinzugefügt' in parliamentarian
        assert 'Mitglied Parlament' in parliamentarian
        assert 'Mitglied Fraktion' in parliamentarian
        assert 'Old Party' in parliamentarian

        # Test filters on overview
        page = client.get('/parliamentarians')  # default filter = active
        assert 'Comedian Laugh' in page
        assert 'Die Moderne' in page
        assert 'Man Old' in page
        assert 'Old Party' in page
        page = client.get('/parliamentarians?active=0')
        assert 'Comedian Laugh' not in page
        assert 'Man Old' not in page
        page = client.get('/parliamentarians?party=Die+Moderne')
        assert 'Comedian Laugh' in page
        assert 'Die Moderne' in page
        assert 'Man Old' not in page
        page = client.get('/parliamentarians?party=Old+Party')
        assert 'Comedian Laugh' not in page
        assert 'Man Old' in page
        assert 'Old Party' in page
        page = client.get(
            '/parliamentarians?party=Old+Party&party=Die+Moderne')
        assert 'Comedian Laugh' in page
        assert 'Die Moderne' in page
        assert 'Man Old' in page
        assert 'Old Party' in page

        # delete parliamentarians
        for parliamentarian in parliamentarian_pages:
            parliamentarian.click('Löschen')
        page = client.get('/parliamentarians')
        assert ('Keine Filterergebnisse gefunden oder noch keine '
                'Parlamentarier erfasst') in page

    # delete commissions
    client.get('/commissions').click('Verkehrskommission').click('Löschen')
    commissions = client.get('/commissions')
    assert 'Keine aktiven Kommissionen' in commissions

    # delete parliamentary groups
    (client.get('/parliamentary-groups')
     .click('Die Moderne Fraktion').click('Löschen'))
    (client.get('/parliamentary-groups')
     .click('Old Party').click('Löschen'))
    groups = client.get('/parliamentary-groups')
    assert 'Noch keine Fraktionen erfasst' in groups
