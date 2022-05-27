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
                },
                'info': {
                    'de': 'Partner',
                    'fr': 'Partenaires'
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
            'url': 'die-url',
            'info': 'Partner'
        }
    }

    fr = sponsor.compiled(Bunch(locale='fr_CH'))
    assert fr.name == "Evilcorp"
    assert fr.background is None
    assert fr.logo == 'le-logo.png'
    assert fr.banners == {
        'bookings': {
            'url': 'le-url',
            'info': 'Partenaires'
        }
    }


def test_sponsors(client, scenario):
    client.login_admin()

    scenario.add_period(
        title='Testperiod',
        phase='wishlist',
        active=True,
        confirmable=True,
        finalizable=True,
    )
    scenario.commit()
    scenario.refresh()

    data = [
        {
            'name': 'CompanyOne',
            'banners': {
                'bookings': {
                    'src': {
                        'de': 'sponsors/CompanyOne-de.jpg',
                        'fr': 'sponsors/CompanyOne-fr.jpg'
                    },
                    'url': {
                        'de': 'https://www.company-one.ch',
                        'fr': 'https://www.company-one.ch/fr'
                    }
                },
                'invoices': {
                    'src': {
                        'de': 'sponsors/CompanyOne-de.jpg',
                        'fr': 'sponsors/CompanyOne-fr.jpg'
                    },
                    'url': {
                        'de': 'https://www.company-one.ch',
                        'fr': 'https://www.company-one.ch/fr'
                    }
                }
            }
        },
        {
            'name': 'CompanyTwo',
            'banners': {
                'bookings': {
                    'src': {
                        'fr': 'sponsors/CompanyTwo-fr.jpg',
                        'de': None
                    },
                    'url': {
                        'fr': 'https://www.company-two.ch',
                        'de': None
                    },
                    'info': {
                        'fr': 'Partenaiere',
                        'de': None
                    }
                },
                'invoices': {
                    'src': {
                        'fr': 'sponsors/Companytwo-fr.jpg',
                        'de': None
                    },
                    'url': {
                        'fr': 'https://www.company-two.ch',
                        'de': None
                    },
                    'info': {
                        'fr': 'Partenaiere',
                        'de': None
                    }
                }
            }
        }
    ]

    del client.app.sponsors
    client.app.sponsors = [Sponsor(**sponsor) for sponsor in data]

    # Check if there's a banner and that the company with only french
    # banners doesn't cause a problem and doesn't show up
    page = client.get('/')
    page = page.click('Wunschliste')
    assert "CompanyOne" in page
    assert "ConpanyTwo" not in page
    assert "Partenaiere" not in page


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
