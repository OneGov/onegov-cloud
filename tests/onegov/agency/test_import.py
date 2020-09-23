import pytest

from onegov.agency.data_import import split_address_on_new_line


@pytest.mark.parametrize('addr,result', [
    ('Rg 16, PS 1532, 4001 Basel', 'Rg 16<br>PS 1532<br>4001 Basel'),
    ('Rg 16,PS 1532, 4001 Basel', 'Rg 16<br>PS 1532<br>4001 Basel'),
    ('Rg 16, PS 1532,4001 Basel', 'Rg 16<br>PS 1532<br>4001 Basel'),
    ('H W-S 40, 4059 Basel', 'H W-S 40<br>4059 Basel'),
    ('M de H, H d V, B p 3, F-68333 H C',
     'M de H<br>H d V<br>B p 3<br>F-68333 H C'),

])
def test_parse_address_bs(addr, result):
    assert result == split_address_on_new_line(addr)
