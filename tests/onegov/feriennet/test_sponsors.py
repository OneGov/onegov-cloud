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
            'url': {
                'de': 'die-url',
                'fr': 'le-url'
            },
            'info': {
                'de': 'Partner',
                'fr': 'Partenaires'
            }
        }
    )

    de = sponsor.compiled(Bunch(locale='de_CH'))
    assert de.name == "Evilcorp"
    assert de.background is None
    assert de.logo == 'das-logo.png'
    assert de.banners == {
        'url': 'die-url',
        'info': 'Partner'
    }

    fr = sponsor.compiled(Bunch(locale='fr_CH'))
    assert fr.name == "Evilcorp"
    assert fr.background is None
    assert fr.logo == 'le-logo.png'
    assert fr.banners == {
        'url': 'le-url',
        'info': 'Partenaires'
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
                'src': {
                    'de': 'sponsors/CompanyOne-de.jpg',
                    'fr': 'sponsors/CompanyOne-fr.jpg'
                },
                'url': {
                    'de': 'https://www.company-one.ch',
                    'fr': 'https://www.company-one.ch/fr'
                }
            }
        },
        {
            'name': 'CompanyTwo',
            'banners': {
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


def test_random_sponsors_at_activities(client, scenario):
    client.login_admin()

    # Add activities for the list
    scenario.add_period(title="Ferienpass 2022", confirmed=True)
    for i in range(40):
        scenario.add_activity(
            title=f'Backen{i}',
            lead='Backen mit Johann.',
            state='accepted',
            location='Bäckerei Govikon, Rathausplatz, 4001 Govikon',
            tags=['Farm', 'Adventure'],
            content={}
        )
        scenario.add_occasion(
            age=(1, 11),
            cost=None,
            spots=(4, 5),
        )
    scenario.commit()

    data = [
        {
            'name': 'CompanyOne',
            'banners': {
                'src': {
                    'de': 'sponsors/CompanyOne-de.jpg',
                },
                'url': {
                    'de': 'https://www.company-one.ch',
                },
                'info': {
                    'de': 'main sponsor'
                }
            }
        },
        {
            'name': 'CompanyTwo',
            'banners': {
                'src': {
                    'de': 'sponsors/CompanyTwo-de.jpg',
                },
                'url': {
                    'de': 'https://www.company-two.ch',
                },
                'info': {
                    'de': 'other sponsor'
                }
            }
        },
        {
            'name': 'CompanyThree',
            'banners': {
                'src': {
                    'de': 'sponsors/CompanyThree-de.jpg',
                },
                'url': {
                    'de': 'https://www.company-three.ch',
                },
                'info': {
                    'de': 'other sponsor'
                }
            }
        }
    ]

    del client.app.sponsors
    client.app.sponsors = [Sponsor(**sponsor) for sponsor in data]

    page = client.get('/activities?pages=0-1')
    activities = page.pyquery('.banner p')
    activities = [a.text for a in activities]

    assert 'main sponsor' in activities[0]
    assert 'other sponsor' in activities[1]
    assert 'main sponsor' in activities[2]
    assert 'other sponsor' in activities[3]
