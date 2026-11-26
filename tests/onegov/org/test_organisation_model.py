from __future__ import annotations

from onegov.org.models import Organisation


def test_title_and_title_lines() -> None:
    org = Organisation(name='Govikon|City')
    assert org.title == 'Govikon City'
    assert org.title_lines == ('Govikon', 'City')

    # without a pipe the name is split on spaces
    spaced = Organisation(name='Stadt Govikon')
    assert spaced.title_lines == ('Stadt', 'Govikon')


def test_contact_and_opening_hours_html() -> None:
    org = Organisation(name='Govikon')
    org.meta = {}

    org.contact = 'Call us'
    assert 'Call us' in org.contact_html

    org.opening_hours = 'Mo-Fr 9-17'
    assert 'Mo-Fr 9-17' in org.opening_hours_html


def test_short_links_dict() -> None:
    org = Organisation(name='Govikon')
    org.meta = {}

    org.short_links = 'home: /home\nabout: /about\ninvalid line'
    assert org.short_links_dict == {'home': '/home', 'about': '/about'}
