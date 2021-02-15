from datetime import date
from decimal import Decimal
from onegov.core.utils import Bunch
from onegov.swissvotes.collections import SwissVoteCollection
from onegov.swissvotes.external_resources import MfgPosters
from onegov.swissvotes.external_resources import SaPosters
from onegov.swissvotes.external_resources.posters import Posters
from psycopg2.extras import NumericRange
from pytest import raises
from unittest.mock import MagicMock
from unittest.mock import patch


xml = '''
<object>
    <field name="primaryMedia">
        <value>{}</value>
    </field>
</object>
'''


def test_posters_fetch(swissvotes_app):

    session = swissvotes_app.session()

    mfg_posters = MfgPosters('xxx')
    sa_posters = SaPosters()

    assert mfg_posters.fetch(session) == (0, 0, 0, set())
    assert sa_posters.fetch(session) == (0, 0, 0, set())

    votes = SwissVoteCollection(swissvotes_app)
    votes = SwissVoteCollection(swissvotes_app)
    kwargs = {
        'date': date(1990, 6, 2),
        'legislation_number': 4,
        'legislation_decade': NumericRange(1990, 1994),
        'title_de': "Vote DE",
        'title_fr': "Vote FR",
        'short_title_de': "V D",
        'short_title_fr': "V F",
        'votes_on_same_day': 2,
        '_legal_form': 1,
    }
    vote_1 = votes.add(
        id=1,
        bfs_number=Decimal('1'),
        posters_mfg_yea='1.1 1.2 1.3 1.4',
        posters_mfg_nay='',
        posters_sa_yea='1.5 1.6 1.7 1.8',
        posters_sa_nay='',
        **kwargs
    )
    vote_2 = votes.add(
        id=2,
        bfs_number=Decimal('2'),
        posters_mfg_yea='2.1',
        posters_mfg_nay='2.2',
        posters_sa_yea='2.3',
        posters_sa_nay='2.4',
        **kwargs
    )
    vote_3 = votes.add(
        id=3,
        bfs_number=Decimal('3'),
        posters_mfg_yea='',
        posters_mfg_nay='',
        posters_sa_yea='',
        posters_sa_nay='3.1',
        **kwargs
    )

    with patch(
        'onegov.swissvotes.external_resources.posters.get',
        return_value=MagicMock(content=xml.format('http://source/xxx'))
    ):
        assert mfg_posters.fetch(session) == (6, 0, 0, set())

        assert vote_1.posters_mfg_yea_imgs == {
            '1.1': 'https://source/xxx',
            '1.2': 'https://source/xxx',
            '1.3': 'https://source/xxx',
            '1.4': 'https://source/xxx'
        }
        assert vote_1.posters_mfg_nay_imgs == {}
        assert vote_2.posters_mfg_yea_imgs == {'2.1': 'https://source/xxx'}
        assert vote_2.posters_mfg_nay_imgs == {'2.2': 'https://source/xxx'}
        assert vote_3.posters_mfg_yea_imgs == {}
        assert vote_3.posters_mfg_nay_imgs == {}

        assert sa_posters.fetch(session) == (7, 0, 0, set())
        assert vote_1.posters_sa_yea_imgs == {
            '1.5': 'https://source/xxx',
            '1.6': 'https://source/xxx',
            '1.7': 'https://source/xxx',
            '1.8': 'https://source/xxx'
        }
        assert vote_1.posters_sa_nay_imgs == {}
        assert vote_2.posters_sa_yea_imgs == {'2.3': 'https://source/xxx'}
        assert vote_2.posters_sa_nay_imgs == {'2.4': 'https://source/xxx'}
        assert vote_3.posters_sa_yea_imgs == {}
        assert vote_3.posters_sa_nay_imgs == {'3.1': 'https://source/xxx'}

    vote_1.posters_mfg_yea = '1.1 1.2'  # -2
    vote_1.posters_mfg_nay = '1.9 1.10'  # +2

    vote_1.posters_sa_yea = '1.5 1.6'   # -2
    vote_1.posters_sa_nay = '1.11 1.12'  # +2
    vote_3.posters_sa_nay = ''  # -1

    with patch(
        'onegov.swissvotes.external_resources.posters.get',
        return_value=MagicMock(content=xml.format('http://source/yyy'))
    ):
        assert mfg_posters.fetch(session) == (2, 4, 2, set())
        assert vote_1.posters_mfg_yea_imgs == {
            '1.1': 'https://source/yyy',
            '1.2': 'https://source/yyy',
        }
        assert vote_1.posters_mfg_nay_imgs == {
            '1.9': 'https://source/yyy',
            '1.10': 'https://source/yyy',
        }
        assert vote_2.posters_mfg_yea_imgs == {'2.1': 'https://source/yyy'}
        assert vote_2.posters_mfg_nay_imgs == {'2.2': 'https://source/yyy'}
        assert vote_3.posters_mfg_yea_imgs == {}
        assert vote_3.posters_mfg_nay_imgs == {}

        assert sa_posters.fetch(session) == (2, 4, 3, set())
        assert vote_1.posters_sa_yea_imgs == {
            '1.5': 'https://source/yyy',
            '1.6': 'https://source/yyy',
        }
        assert vote_1.posters_sa_nay_imgs == {
            '1.11': 'https://source/yyy',
            '1.12': 'https://source/yyy',
        }
        assert vote_2.posters_sa_yea_imgs == {'2.3': 'https://source/yyy'}
        assert vote_2.posters_sa_nay_imgs == {'2.4': 'https://source/yyy'}
        assert vote_3.posters_sa_yea_imgs == {}
        assert vote_3.posters_sa_nay_imgs == {}

    with patch(
        'onegov.swissvotes.external_resources.posters.get',
        side_effect=Exception()
    ):
        assert mfg_posters.fetch(session) == (
            0, 0, 0, {vote_1.bfs_number, vote_2.bfs_number}
        )
        assert vote_1.posters_mfg_yea_imgs == {
            '1.1': 'https://source/yyy',
            '1.2': 'https://source/yyy',
        }
        assert vote_1.posters_mfg_nay_imgs == {
            '1.9': 'https://source/yyy',
            '1.10': 'https://source/yyy',
        }
        assert vote_2.posters_mfg_yea_imgs == {'2.1': 'https://source/yyy'}
        assert vote_2.posters_mfg_nay_imgs == {'2.2': 'https://source/yyy'}
        assert vote_3.posters_mfg_yea_imgs == {}
        assert vote_3.posters_mfg_nay_imgs == {}

        assert sa_posters.fetch(session) == (
            0, 0, 0, {vote_1.bfs_number, vote_2.bfs_number}
        )
        assert vote_1.posters_sa_yea_imgs == {
            '1.5': 'https://source/yyy',
            '1.6': 'https://source/yyy',
        }
        assert vote_1.posters_sa_nay_imgs == {
            '1.11': 'https://source/yyy',
            '1.12': 'https://source/yyy',
        }
        assert vote_2.posters_sa_yea_imgs == {'2.3': 'https://source/yyy'}
        assert vote_2.posters_sa_nay_imgs == {'2.4': 'https://source/yyy'}
        assert vote_3.posters_sa_yea_imgs == {}
        assert vote_3.posters_sa_nay_imgs == {}


def test_posters_meta_data_url():
    assert MfgPosters('xxx').meta_data_url('object') == (
        'https://www.emuseum.ch/objects/object/xml'
    )
    assert SaPosters().meta_data_url('object') == (
        'https://swissvotes.sozialarchiv.ch/object'
    )


def test_posters_parse_xml(session):

    class MyPosters(Posters):

        def meta_data_url(self, url):
            return url

    # parse xml
    posters = MyPosters()
    with raises(Exception):
        posters.parse_xml(Bunch(content=None))
    with raises(Exception):
        posters.parse_xml(Bunch(content=''))
    with raises(ValueError):
        posters.parse_xml(Bunch(content='<object></object>'))
    with raises(ValueError):
        posters.parse_xml(Bunch(content=xml.format('')))
    assert posters.parse_xml(Bunch(content=xml.format('url'))) == 'url'
