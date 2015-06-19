import textwrap

from onegov.election_day.model import Principal


def test_load_principal():
    principal = Principal.from_yaml(textwrap.dedent("""
        name: Foobar
        logo:
        canton: zg
    """))

    assert principal.name == 'Foobar'
