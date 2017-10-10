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

    de = sponsor.localized(Bunch(locale='de_CH'))
    assert de.name == "Evilcorp"
    assert de.background is None
    assert de.logo == 'das-logo.png'
    assert de.banners == {
        'bookings': {
            'url': 'die-url'
        }
    }

    fr = sponsor.localized(Bunch(locale='fr_CH'))
    assert fr.name == "Evilcorp"
    assert fr.background is None
    assert fr.logo == 'le-logo.png'
    assert fr.banners == {
        'bookings': {
            'url': 'le-url'
        }
    }
