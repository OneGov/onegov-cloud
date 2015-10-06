import textwrap

from onegov.election_day.models import Principal


def test_load_principal():
    principal = Principal.from_yaml(textwrap.dedent("""
        name: Foobar
        logo:
        canton: zg
        color: '#000'
    """))

    assert principal.name == 'Foobar'
