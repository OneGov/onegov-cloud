from onegov.election_day.models import Principal
from onegov.election_day.models.principal import cantons
from textwrap import dedent


SUPPORTED_YEARS = list(range(2002, 2017 + 1))

SUPPORTED_YEARS_MAP = list(range(2013, 2017 + 1))
SUPPORTED_YEARS_NO_MAP = list(set(SUPPORTED_YEARS) - set(SUPPORTED_YEARS_MAP))

SUPPORTED_YEARS_MAP_SG = list(range(2004, 2017 + 1))
SUPPORTED_YEARS_NO_MAP_SG = list(
    set(SUPPORTED_YEARS) - set(SUPPORTED_YEARS_MAP_SG)
)


def test_principal_load():
    principal = Principal.from_yaml(dedent("""
        name: Kanton Zug
        canton: zg
    """))

    assert principal.name == 'Kanton Zug'
    assert principal.logo is None
    assert principal.canton == 'zg'
    assert principal.municipality is None
    assert principal.color == '#000'
    assert principal.base is None
    assert principal.base_domain is None
    assert principal.analytics is None
    assert principal.use_maps is True
    assert principal.domain is 'canton'
    assert list(principal.available_domains.keys()) == ['federation', 'canton']
    assert principal.fetch == {}
    assert principal.webhooks == {}
    assert principal.sms_notification == None
    assert principal.email_notification == None
    assert principal.wabsti_import == False
    assert principal.pdf_signing == {}
    assert principal.open_data == {}

    principal = Principal.from_yaml(dedent("""
        name: Kanton Zug
        canton: zg
        base: 'http://www.zg.ch'
        analytics: "<script type=\\"text/javascript\\"></script>"
        use_maps: false
        wabsti_import: true
        fetch:
            steinhausen:
                - municipality
            baar:
                - municipality
        webhooks:
            'http://abc.com/1':
            'http://abc.com/2':
                My-Header: My-Value
        sms_notification: 'https://wab.zg.ch'
        email_notification: true
        pdf_signing:
            url: 'http://abc.com/3'
            login: user
            password: pass
            reason: election and vote results
        open_data:
            id: kanton-zug
            name: Staatskanzlei Kanton Zug
            mail: info@zg.ch
    """))

    assert principal.name == 'Kanton Zug'
    assert principal.logo is None
    assert principal.canton == 'zg'
    assert principal.municipality is None
    assert principal.color == '#000'
    assert principal.base == 'http://www.zg.ch'
    assert principal.base_domain == 'zg.ch'
    assert principal.analytics == '<script type="text/javascript"></script>'
    assert principal.use_maps is True
    assert principal.domain is 'canton'
    assert list(principal.available_domains.keys()) == ['federation', 'canton']
    assert principal.fetch == {
        'steinhausen': ['municipality'],
        'baar': ['municipality']
    }
    assert principal.webhooks == {
        'http://abc.com/1': None,
        'http://abc.com/2': {
            'My-Header': 'My-Value'
        }
    }
    assert principal.sms_notification == 'https://wab.zg.ch'
    assert principal.email_notification == True
    assert principal.wabsti_import == True
    assert principal.pdf_signing == {
        'url': 'http://abc.com/3',
        'login': 'user',
        'password': 'pass',
        'reason': 'election and vote results'
    }
    assert principal.open_data == {
        'id': 'kanton-zug',
        'name': 'Staatskanzlei Kanton Zug',
        'mail': 'info@zg.ch'
    }

    principal = Principal.from_yaml(dedent("""
        name: Stadt Bern
        municipality: '351'
    """))

    assert principal.name == 'Stadt Bern'
    assert principal.logo is None
    assert principal.canton is None
    assert principal.municipality == '351'
    assert principal.color == '#000'
    assert principal.base is None
    assert principal.base_domain is None
    assert principal.analytics is None
    assert principal.use_maps is False
    assert principal.domain is 'municipality'
    assert list(principal.available_domains.keys()) == [
        'federation', 'canton', 'municipality'
    ]
    assert principal.fetch == {}
    assert principal.webhooks == {}
    assert principal.sms_notification == None
    assert principal.email_notification == None
    assert principal.wabsti_import == False
    assert principal.pdf_signing == {}

    principal = Principal.from_yaml(dedent("""
        name: Stadt Bern
        municipality: '351'
        use_maps: true
    """))

    assert principal.name == 'Stadt Bern'
    assert principal.logo is None
    assert principal.canton is None
    assert principal.municipality == '351'
    assert principal.color == '#000'
    assert principal.base is None
    assert principal.base_domain is None
    assert principal.analytics is None
    assert principal.use_maps is True
    assert principal.domain is 'municipality'
    assert list(principal.available_domains.keys()) == [
        'federation', 'canton', 'municipality'
    ]
    assert principal.fetch == {}
    assert principal.webhooks == {}
    assert principal.sms_notification == None
    assert principal.email_notification == None
    assert principal.wabsti_import == False
    assert principal.pdf_signing == {}


def test_principal_municipalities():
    # Bern (municipalitites have districts, not municipalitites)
    principal = Principal(name='Bern', municipality='351')
    assert principal.municipalities == {}

    # Canton Zug
    principal = Principal(name='Zug', canton='zg')
    municipalities = {
        1701: {'name': 'Baar'},
        1702: {'name': 'Cham'},
        1703: {'name': 'Hünenberg'},
        1704: {'name': 'Menzingen'},
        1705: {'name': 'Neuheim'},
        1706: {'name': 'Oberägeri'},
        1707: {'name': 'Risch'},
        1708: {'name': 'Steinhausen'},
        1709: {'name': 'Unterägeri'},
        1710: {'name': 'Walchwil'},
        1711: {'name': 'Zug'},
    }
    assert principal.municipalities == {
        year: municipalities for year in SUPPORTED_YEARS
    }

    # All cantons
    for canton in cantons:
        principal = Principal(name=canton, canton=canton)
        for year in SUPPORTED_YEARS:
            assert principal.municipalities[year]


def test_principal_districts():
    # Canton Zug (cantons have municipalities, not districts)
    principal = Principal(name='Zug', canton='zg')
    assert principal.districts == {}

    # Municipality without districts
    principal = Principal(name='Kriens', municipality='1059')
    assert principal.districts == {
        year: {1059: {'name': 'Kriens'}} for year in SUPPORTED_YEARS
    }

    # Municipality with districts
    principal = Principal(name='Bern', municipality='351')
    districts = {
        1: {'name': 'Innere Stadt'},
        2: {'name': 'Länggasse/Felsenau'},
        3: {'name': 'Mattenhof/Weissenbühl'},
        4: {'name': 'Kirchenfeld/Schosshalde'},
        5: {'name': 'Breitenrain/Lorraine'},
        6: {'name': 'Bümpliz/Bethlehem'},
    }
    assert principal.districts == {year: districts for year in SUPPORTED_YEARS}


def test_principal_entities():
    principal = Principal(name='Zug', canton='zg')
    assert principal.entities == principal.municipalities

    principal = Principal(name='Kriens', municipality='1059')
    assert principal.entities == principal.districts

    principal = Principal(name='Bern', municipality='351')
    assert principal.entities == principal.districts


def test_principal_years_available():
    # Municipality without districts/map
    principal = Principal(name='Kriens', municipality='1059')
    assert not principal.is_year_available(2000)
    assert not principal.is_year_available(2000, map_required=False)
    for year in SUPPORTED_YEARS:
        assert not principal.is_year_available(year)
        assert principal.is_year_available(year, map_required=False)

    # Municipality with districts/map
    principal = Principal(name='Bern', municipality='351')
    assert not principal.is_year_available(2000)
    assert not principal.is_year_available(2000, map_required=False)
    for year in SUPPORTED_YEARS_NO_MAP:
        assert not principal.is_year_available(year)
        assert principal.is_year_available(year, map_required=False)
    for year in SUPPORTED_YEARS_MAP:
        assert principal.is_year_available(year)
        assert principal.is_year_available(year, map_required=False)

    # Cantons
    for canton in cantons - {'sg'}:
        principal = Principal(name=canton, canton=canton)

        for year in SUPPORTED_YEARS_NO_MAP:
            assert not principal.is_year_available(year)
            assert principal.is_year_available(year, map_required=False)
        for year in SUPPORTED_YEARS_MAP:
            assert principal.is_year_available(year)
            assert principal.is_year_available(year, map_required=False)

    # Canton SG
    principal = Principal(name='sg', canton='sg')
    for year in SUPPORTED_YEARS_NO_MAP_SG:
        assert not principal.is_year_available(year)
        assert principal.is_year_available(year, map_required=False)
    for year in SUPPORTED_YEARS_MAP_SG:
        assert principal.is_year_available(year)
        assert principal.is_year_available(year, map_required=False)


def test_principal_notifications_enabled():
    assert Principal(
        name='Kriens', municipality='1059'
    ).notifications == False

    assert Principal(
        name='Kriens', municipality='1059',
        webhooks={'a', 'b'}
    ).notifications == True

    assert Principal(
        name='Kriens', municipality='1059',
        sms_notification='https://wab.kriens.ch'
    ).notifications == True

    assert Principal(
        name='Kriens', municipality='1059',
        email_notification=True
    ).notifications == True

    assert Principal(
        name='Kriens', municipality='1059',
        webhooks={'a', 'b'},
        sms_notification='https://wab.kriens.ch',
        email_notification=True
    ).notifications == True
