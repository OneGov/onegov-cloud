from __future__ import annotations

import pytest

from onegov.agency.data_import import (split_address_on_new_line,
                                       parse_alliance_name)


@pytest.mark.parametrize('addr,result', [
    ('Rg 16, PS 1532, 4001 Basel', 'Rg 16<br>PS 1532<br>4001 Basel'),
    ('Rg 16,PS 1532, 4001 Basel', 'Rg 16<br>PS 1532<br>4001 Basel'),
    ('Rg 16, PS 1532,4001 Basel', 'Rg 16<br>PS 1532<br>4001 Basel'),
    ('H W-S 40, 4059 Basel', 'H W-S 40<br>4059 Basel'),
    ('M de H, H d V, B p 3, F-68333 H C',
     'M de H<br>H d V<br>B p 3<br>F-68333 H C'),

])
def test_parse_address_bs(addr: str, result: str) -> None:
    assert result == split_address_on_new_line(addr)


@pytest.mark.parametrize('alliance_name,first_name,result', [
    ('Müller Moritz', '', ('Müller', 'Moritz')),
    ('Müller Moritz Max', '', ('Müller', 'Moritz Max')),
    ('Omlin Christine', '', ('Omlin', 'Christine')),
    ('Iten-Weber Debi', '', ('Iten-Weber', 'Debi')),
    ('Owen Bradshaw Daniel', 'Daniel', ('Owen Bradshaw', 'Daniel')),
    ('Widmer Frank Cecile Ladina', 'Cecile Ladina',
     ('Widmer Frank', 'Cecile Ladina')),
    ('Achermann-Bachmann Carmen Daria', '',
     ('Achermann-Bachmann', 'Carmen Daria')),
])
def test_parse_alliance_name(
    alliance_name: str,
    first_name: str,
    result: tuple[str, str]
) -> None:
    assert parse_alliance_name(alliance_name, first_name) == result
