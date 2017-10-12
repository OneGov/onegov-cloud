from freezegun import freeze_time
from onegov.core.utils import Bunch
from onegov.feriennet.sponsors import Sponsor


def test_translate_sponsor():

    sponsor = Sponsor(
        name="Evilcorp",
        logo={
            'de': 'das-logo.png',
            'fr': 'le-logo.png'
        },
        banners={
            'bookings': {
                'url': {
                    'de': 'die-url',
                    'fr': 'le-url'
                }
            }
        }
    )

    de = sponsor.compiled(Bunch(locale='de_CH'))
    assert de.name == "Evilcorp"
    assert de.background is None
    assert de.logo == 'das-logo.png'
    assert de.banners == {
        'bookings': {
            'url': 'die-url'
        }
    }

    fr = sponsor.compiled(Bunch(locale='fr_CH'))
    assert fr.name == "Evilcorp"
    assert fr.background is None
    assert fr.logo == 'le-logo.png'
    assert fr.banners == {
        'bookings': {
            'url': 'le-url'
        }
    }


def test_timestamp_sponsor():

    sponsor = Sponsor(
        name="Evilcorp",
        logo={
            'de': '{timestamp}',
            'fr': '{timestamp}'
        },
        banners='{timestamp}'
    )

    with freeze_time("2017-10-12 16:30"):
        de = sponsor.compiled(Bunch(locale='de_CH'))
        assert de.name == "Evilcorp"
        assert de.logo == '1507825800000'
        assert de.banners == '1507825800000'
