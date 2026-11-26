from __future__ import annotations

from onegov.agency.data_import import (
    agency_id_agency_lu,
    agency_id_person_lu,
    br,
    check_skip,
    check_skip_people,
    cleaned,
    get_address,
    get_agency_portrait,
    get_email,
    get_phone,
    get_plz_city,
    get_web_address,
    p,
    split_address_on_new_line,
    v_,
)
from types import SimpleNamespace


from typing import Any


def _line(**kwargs: object) -> Any:
    return SimpleNamespace(**kwargs)


def test_v_() -> None:
    assert v_(None) is None
    assert v_('NULL') is None
    assert v_('   ') is None
    assert v_('  value  ') == 'value'


def test_cleaned() -> None:
    upper = cleaned(str.upper)
    assert upper(None) is None
    assert upper('NULL') is None
    assert upper('  abc ') == 'ABC'


def test_get_phone() -> None:
    assert get_phone(None) is None
    # 00 prefix -> +
    assert get_phone('0041 44 123 45 67') == '+41 44 123 45 67'
    # 10 digit CH number
    assert get_phone('044 123 45 67') == '+41 44 123 45 67'
    # 9 digit lu number gets country digits
    assert get_phone('412345678') == '+41 41 234 56 78'
    # already international -> unchanged
    assert get_phone('+41 44 123 45 67') == '+41 44 123 45 67'


def test_markup_helpers() -> None:
    assert str(p('x')) == '<p>x</p>'
    assert str(br('x')) == 'x<br>'


def test_split_address_on_new_line() -> None:
    assert str(split_address_on_new_line('A, B')) == 'A<br>B'
    assert str(split_address_on_new_line('A, B', newline=True)) == 'A<br>B<br>'


def test_get_address() -> None:
    # both equal -> single block
    both = _line(standortadresse='A, B', postadresse='A, B')
    assert str(get_address(both)) == 'A<br>B<br>'

    # different -> both blocks
    diff = _line(standortadresse='A', postadresse='C')
    assert str(get_address(diff)) == 'A<br><br>C<br>'

    # only post address
    only_post = _line(standortadresse=None, postadresse='C')
    assert str(get_address(only_post)) == 'C<br>'

    # neither
    assert get_address(_line(standortadresse=None, postadresse=None)) is None


def test_get_agency_portrait() -> None:
    line = _line(
        standortadresse='Street 1', postadresse=None,
        telzentrale='044 123 45 67', faxzentrale=None,
        emailneutral=None, homepageurl='http://example.org',
        stadtplanurl=None, oeffnungszeiten=None,
        wahlperiode='2020-2024', bemerkung=None,
    )
    portrait = get_agency_portrait(line)
    assert portrait is not None
    text = str(portrait)
    assert text.startswith('<p>')
    assert 'Tel.:' in text
    assert 'Homepage' in text
    assert 'Wahlperiode: 2020-2024' in text

    # empty line -> None
    empty = _line(
        standortadresse=None, postadresse=None, telzentrale=None,
        faxzentrale=None, emailneutral=None, homepageurl=None,
        stadtplanurl=None, oeffnungszeiten=None, wahlperiode=None,
        bemerkung=None,
    )
    assert get_agency_portrait(empty) is None


def test_get_plz_city() -> None:
    assert get_plz_city('6000', 'Luzern') == '6000 Luzern'
    assert get_plz_city(None, 'Luzern') == 'Luzern'
    assert get_plz_city('6000', None) == '6000'
    assert get_plz_city(None, None) is None


def test_get_web_address() -> None:
    assert get_web_address('') is None
    assert get_web_address('http://example.org') == 'http://example.org'
    assert get_web_address('example.org') == 'http://example.org'


def test_get_email_skip_paths() -> None:
    # no email
    assert get_email(_line(e_mail_adresse=None), 'anna', 'alpha') is None

    # placeholder address is skipped
    assert get_email(
        _line(e_mail_adresse='@lu.ch'), 'anna', 'alpha') is None

    # personal address containing both names is skipped
    assert get_email(
        _line(e_mail_adresse='anna.alpha@lu.ch', rownumber=1),
        'anna', 'alpha') is None


def test_check_skip() -> None:
    assert check_skip(_line(
        department='zNeu', vorname='A', nachname='B')) is True
    assert check_skip(_line(
        department='X', vorname='Zi. Anna', nachname='B')) is True
    assert check_skip(_line(
        department='X', vorname='A', nachname='WG')) is True
    assert check_skip(_line(
        department='X', vorname='', nachname='')) is True
    assert check_skip(_line(
        department='X', vorname='Anna', nachname='Alpha')) is False


def test_check_skip_people() -> None:
    # Telefonist is kept
    assert check_skip_people(_line(
        nachname='Telefonist', vorname='', funktion='')) is False
    # Telefon is skipped
    assert check_skip_people(_line(
        nachname='', vorname='', funktion='Telefon')) is True
    # normal person kept
    assert check_skip_people(_line(
        nachname='Alpha', vorname='Anna', funktion='Chef')) is False


def test_agency_id_helpers() -> None:
    assert agency_id_agency_lu(['Dep', 'Sub', None, 'Unit']) == \
        'dep__sub__unit'

    line = _line(
        department='Dep', dienststelle__alternativ_=None,
        dienststelle='Dienst', abteilung='Abt',
        unterabteilung='Unter', unterabteilung_2=None,
    )
    assert agency_id_person_lu(line) == 'dep__dienst__abt__unter'
