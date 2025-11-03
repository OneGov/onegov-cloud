from __future__ import annotations

from datetime import date
from decimal import Decimal
from io import BytesIO
from onegov.core.crypto import random_token
from onegov.core.orm.abstract import MoveDirection
from onegov.core.utils import Bunch
from onegov.file.utils import as_fileintent
from onegov.swissvotes.models import Actor
from onegov.swissvotes.models import ColumnMapperDataset
from onegov.swissvotes.models import ColumnMapperMetadata
from onegov.swissvotes.models import PolicyArea
from onegov.swissvotes.models import Principal
from onegov.swissvotes.models import Region
from onegov.swissvotes.models import SwissVote
from onegov.swissvotes.models import SwissVoteFile
from onegov.swissvotes.models import TranslatablePage
from onegov.swissvotes.models import TranslatablePageFile
from onegov.swissvotes.models import TranslatablePageMove
from onegov.swissvotes.models.file import FileSubCollection
from onegov.swissvotes.models.file import LocalizedFile
from onegov.swissvotes.models.vote import Poster
from tests.shared.utils import use_locale
from translationstring import TranslationString


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from .conftest import TestApp


class DummyRequest:
    locale = 'de_CH'

    def translate(self, text: str) -> str:
        if isinstance(text, TranslationString):
            return text.interpolate()
        return text

    def link(self, target: object, suffix: str | None = None) -> str:
        return f'{target}/{suffix}' if suffix else f'{target}'


def test_model_actor() -> None:
    actor = Actor('csp')
    assert actor.name == 'csp'
    assert actor.abbreviation == 'actor-csp-abbreviation'
    assert isinstance(actor.abbreviation, TranslationString)
    assert actor.label == 'actor-csp-label'
    assert isinstance(actor.label, TranslationString)
    assert actor.html(DummyRequest()) == (  # type: ignore[arg-type]
        '<span title="actor-csp-label">actor-csp-abbreviation</span>'
    )

    actor = Actor('xxx')
    assert actor.name == 'xxx'
    assert actor.abbreviation == 'xxx'
    assert not isinstance(actor.abbreviation, TranslationString)
    assert actor.label == 'xxx'
    assert not isinstance(actor.label, TranslationString)
    assert actor.html(DummyRequest()) == '<span title="xxx">xxx</span>'  # type: ignore[arg-type]

    assert Actor('csp') == Actor('csp')
    assert Actor('csp') != Actor('xxx')


def test_model_canton() -> None:
    assert len(Region.cantons()) == 26

    canton = Region('lu')
    assert canton.name == 'lu'
    assert canton.abbreviation == 'LU'
    assert not isinstance(canton.abbreviation, TranslationString)
    assert canton.label == 'canton-lu-label'
    assert isinstance(canton.label, TranslationString)
    assert canton.html(DummyRequest()) == (  # type: ignore[arg-type]
        '<span title="canton-lu-label">LU</span>'
    )

    canton = Region('xxx')
    assert canton.name == 'xxx'
    assert canton.abbreviation == 'xxx'
    assert not isinstance(canton.abbreviation, TranslationString)
    assert canton.label == 'xxx'
    assert not isinstance(canton.label, TranslationString)
    assert canton.html(DummyRequest()) == '<span title="xxx">xxx</span>'  # type: ignore[arg-type]

    assert Region('lu') == Region('lu')
    assert Region('lu') != Region('xxx')


def test_model_localized_file() -> None:
    class SessionManager:
        def __init__(self) -> None:
            self.current_locale = 'de_CH'

    class MyClass:
        file = LocalizedFile('pdf', 'title', {})

        def __init__(self) -> None:
            self.session_manager = SessionManager()
            self.files: list[File] = []

    class File:
        def __init__(self, name: str) -> None:
            self.name = name

    my: Any = MyClass()
    assert my.file is None

    # Add CH
    my.file = File('A')
    assert my.file.name == 'file-de_CH'
    assert set(file.name for file in my.files) == {'file-de_CH'}

    # Add FR
    with use_locale(my, 'fr_CH'):
        assert my.file is None
        my.file = File('B')

        assert my.file.name == 'file-fr_CH'
        assert set(file.name for file in my.files) == {
            'file-de_CH', 'file-fr_CH'
        }

        # Access unrestricted
        by_locale = MyClass.__dict__['file'].__get_by_locale__
        assert by_locale(my, 'de_CH').name == 'file-de_CH'
        assert by_locale(my, 'fr_CH').name == 'file-fr_CH'
        assert by_locale(my, 'rm_CH') is None

        # Delete FR
        del my.file
        assert my.file is None
        assert set(file.name for file in my.files) == {'file-de_CH'}


def test_model_file_subcollection() -> None:
    class MyClass:
        files = [Bunch(name='a'), Bunch(name='x_b'), Bunch(name='x_a')]
        x = FileSubCollection()

    assert MyClass().x == [Bunch(name='x_a'), Bunch(name='x_b')]  # type: ignore[type-var]


def test_model_page(session: Session) -> None:
    session.add(
        TranslatablePage(  # type: ignore[misc]
            id='page',
            title_translations={'de_CH': "Titel", 'en': "Title"},
            content_translations={'de_CH': "Inhalt", 'en': "Content"},
            show_timeline=True
        )
    )
    session.flush()

    page = session.query(TranslatablePage).one()
    assert page.id == 'page'
    assert page.title_translations == {'de_CH': "Titel", 'en': "Title"}
    assert page.content_translations == {'de_CH': "Inhalt", 'en': "Content"}
    assert page.order == 65536
    assert page.show_timeline is True

    session.add(
        TranslatablePage(
            id='page-1',
            title_translations={'de_CH': "Titel", 'en': "Title"},
            content_translations={'de_CH': "Inhalt", 'en': "Content"},
            order=2
        )
    )
    session.add(
        TranslatablePage(
            id='page-2',
            title_translations={'de_CH': "Titel", 'en': "Title"},
            content_translations={'de_CH': "Inhalt", 'en': "Content"},
            order=1
        )
    )
    assert [page.id for page in page.siblings] == ['page-2', 'page-1', 'page']


def test_model_page_move(session: Session) -> None:
    # test execute
    for order, id in enumerate(('about', 'contact', 'dataset')):
        session.add(
            TranslatablePage(
                id=id, order=order,
                title_translations={'en': id}, content_translations={'en': id}
            )
        )

    def ordering() -> list[str]:
        query = session.query(TranslatablePage.id)
        query = query.order_by(TranslatablePage.order)
        return [page_id for page_id, in query]

    assert ordering() == ['about', 'contact', 'dataset']

    TranslatablePageMove(
        session, 'about', 'contact', MoveDirection.below
    ).execute()
    assert ordering() == ['contact', 'about', 'dataset']

    TranslatablePageMove(
        session, 'dataset', 'contact', MoveDirection.above
    ).execute()
    assert ordering() == ['dataset', 'contact', 'about']

    TranslatablePageMove(
        session, 'contact', 'dataset', MoveDirection.above
    ).execute()
    assert ordering() == ['contact', 'dataset', 'about']

    # invalid
    TranslatablePageMove(
        session, 'contact', 'contact', MoveDirection.above
    ).execute()
    assert ordering() == ['contact', 'dataset', 'about']

    TranslatablePageMove(
        session, 'kontact', 'about', MoveDirection.above
    ).execute()
    assert ordering() == ['contact', 'dataset', 'about']

    TranslatablePageMove(
        session, 'about', 'kontact', MoveDirection.above
    ).execute()
    assert ordering() == ['contact', 'dataset', 'about']


def test_model_page_file(swissvotes_app: TestApp) -> None:
    session = swissvotes_app.session()

    page = TranslatablePage(
        id='page',
        title_translations={'de_CH': "Titel", 'en': "Title"},
        content_translations={'de_CH': "Inhalt", 'en': "Content"}
    )
    session.add(page)
    session.flush()

    assert page.files == []

    attachment = TranslatablePageFile(id=random_token())
    attachment.name = 'de_CH-test.txt'
    attachment.reference = as_fileintent(BytesIO(b'test'), 'test.txt')
    page.files.append(attachment)
    session.flush()

    file = session.query(TranslatablePage).one().files[0]
    assert file.name == 'de_CH-test.txt'
    assert file.filename == 'test.txt'
    assert file.locale == 'de_CH'


def test_model_swissvotes_file(swissvotes_app: TestApp) -> None:
    session = swissvotes_app.session()

    vote = SwissVote(
        bfs_number=Decimal('100.1'),
        date=date(1990, 6, 2),
        title_de="Vote DE",
        title_fr="Vote FR",
        short_title_de="V D",
        short_title_fr="V F",
        keyword="Keyword",
        _legal_form=1,
    )
    session.add(vote)
    session.flush()

    assert vote.files == []

    attachment = SwissVoteFile(id=random_token())
    attachment.name = 'xxx-de_CH'
    attachment.reference = as_fileintent(BytesIO(b'test'), 'test.txt')
    vote.files.append(attachment)
    session.flush()

    file = vote.files[0]
    assert file.name == 'xxx-de_CH'
    assert file.filename == 'test.txt'
    assert file.locale == 'de_CH'


def test_model_policy_area(session: Session) -> None:
    policy_area = PolicyArea('1')
    assert repr(policy_area) == '1'
    assert policy_area.level == 1
    assert policy_area.descriptor == 1
    assert policy_area.descriptor_path == [1]
    assert policy_area.descriptor_decimal == Decimal('1')
    assert policy_area.label == 'd-1-1'
    assert policy_area.label_path == ['d-1-1']
    assert policy_area.html(DummyRequest()) == '<span>d-1-1</span>'  # type: ignore[arg-type]

    policy_area = PolicyArea('1.12')
    assert repr(policy_area) == '1.12'
    assert policy_area.level == 2
    assert policy_area.descriptor == 12
    assert policy_area.descriptor_path == [1, 12]
    assert policy_area.descriptor_decimal == Decimal('1.2')
    assert policy_area.label == 'd-2-12'
    assert policy_area.label_path == ['d-1-1', 'd-2-12']
    assert policy_area.html(DummyRequest()) == '<span>d-1-1 &gt; d-2-12</span>'  # type: ignore[arg-type]

    policy_area = PolicyArea('1.12.121')
    assert repr(policy_area) == '1.12.121'
    assert policy_area.level == 3
    assert policy_area.descriptor == 121
    assert policy_area.descriptor_path == [1, 12, 121]
    assert policy_area.descriptor_decimal == Decimal('1.21')
    assert policy_area.label == 'd-3-121'
    assert policy_area.label_path == ['d-1-1', 'd-2-12', 'd-3-121']
    assert policy_area.html(DummyRequest()) == (  # type: ignore[arg-type]
        '<span>d-1-1 &gt; d-2-12 &gt; d-3-121</span>'
    )

    assert repr(PolicyArea([1])) == '1'
    assert repr(PolicyArea([1, 12])) == '1.12'
    assert repr(PolicyArea([1, 12, 121])) == '1.12.121'

    assert repr(PolicyArea(Decimal('1'), 1)) == '1'
    assert repr(PolicyArea(Decimal('1.2'), 2)) == '1.12'
    assert repr(PolicyArea(Decimal('1.21'), 3)) == '1.12.121'

    assert PolicyArea(Decimal('10.23'), 3).label_path == [
        'd-1-10', 'd-2-102', 'd-3-1023'
    ]

    assert PolicyArea('1.12.121') == PolicyArea([1, 12, 121])


def test_model_principal(session: Session) -> None:
    principal = Principal()
    assert principal


def test_model_vote_properties(
    session: Session,
    sample_vote: SwissVote
) -> None:

    session.add(sample_vote)
    session.flush()
    session.expunge_all()

    vote = session.query(SwissVote).one()
    assert vote.id == 1
    assert vote.bfs_number == Decimal('100.10')
    assert vote.number_of_cantons == 22
    assert vote.date == date(1990, 6, 2)
    assert vote.title_de == "Vote DE"
    assert vote.title_fr == "Vote FR"
    assert vote.title == "Vote DE"
    assert vote.short_title_de == "V D"
    assert vote.short_title_fr == "V F"
    assert vote.short_title_en == "V E"
    assert vote.short_title == "V D"
    assert vote.keyword == "Keyword"
    assert vote._legal_form == 1
    assert vote.legal_form == "Mandatory referendum"
    assert vote._parliamentary_initiated == 0
    assert vote.initiator_de == "Initiator D"
    assert vote.initiator_fr == "Initiator F"
    assert vote.initiator == "Initiator D"
    assert vote.recommendations_other_yes_de == "Pro Velo D"
    assert vote.recommendations_other_yes_fr == "Pro Velo F"
    assert vote.recommendations_other_yes == "Pro Velo D"
    assert vote.recommendations_other_no_de is None
    assert vote.recommendations_other_no_fr is None
    assert vote.recommendations_other_no is None
    assert vote.recommendations_other_free_de == "Pro Natura D, Greenpeace D"
    assert vote.recommendations_other_free_fr == "Pro Natura F, Greenpeace F"
    assert vote.recommendations_other_free == "Pro Natura D, Greenpeace D"
    assert vote.recommendations_other_counter_proposal_de == "Pro Juventute D"
    assert vote.recommendations_other_counter_proposal_fr == "Pro Juventute F"
    assert vote.recommendations_other_counter_proposal == "Pro Juventute D"
    assert vote.recommendations_other_popular_initiative_de == \
        "Pro Senectute D"
    assert vote.recommendations_other_popular_initiative_fr == \
        "Pro Senectute F"
    assert vote.recommendations_other_popular_initiative == "Pro Senectute D"
    assert vote.anneepolitique == "anneepolitique"
    assert vote.bfs_map_de == (
        "https://www.atlas.bfs.admin.ch/maps/12/map/mapIdOnly/1815_de.html"
    )
    assert vote.bfs_map_fr == "htt(ps://www.ap/mapIdOnly/1815[e.html}"
    assert vote.bfs_map == (
        "https://www.atlas.bfs.admin.ch/maps/12/map/mapIdOnly/1815_de.html"
    )
    assert vote.bfs_map_host == "https://www.atlas.bfs.admin.ch"
    assert vote.bfs_dashboard == "https://dashboard.de"
    assert vote.posters_mfg_yea == (
        'https://yes.com/objects/1 '
        'https://yes.com/objects/2'
    )
    assert vote.posters_mfg_nay == (
        'https://no.com/objects/1 '
        'https://no.com/objects/2'
    )
    assert vote.posters_bs_yea == (
        'https://yes.com/objects/5 '
        'https://yes.com/objects/6'
    )
    assert vote.posters_bs_nay == (
        'https://no.com/objects/5 '
        'https://no.com/objects/6'
    )
    assert vote.posters_sa_yea == (
        'https://yes.com/objects/3 '
        'https://yes.com/objects/4'
    )
    assert vote.posters_sa_nay == (
        'https://no.com/objects/4 '
        'https://no.com/objects/3'
    )
    assert vote.posters_mfg_yea_imgs == {
        'https://yes.com/objects/1': 'https://detail.com/1'
    }
    assert vote.posters_mfg_nay_imgs == {}
    assert vote.posters_bs_yea_imgs == {
        'https://yes.com/objects/5': 'https://detail.com/5',
    }
    assert vote.posters_bs_nay_imgs == {
        'https://no.com/objects/6': 'https://detail.com/6',
    }
    assert vote.posters_sa_yea_imgs == {}
    assert vote.posters_sa_nay_imgs == {
        'https://no.com/objects/3': 'https://detail.com/3',
        'https://no.com/objects/4': 'https://detail.com/4'
    }
    assert vote.link_bk_chrono == 'https://bk.chrono/de'
    assert vote.link_bk_results == 'https://bk.results/de'
    assert vote.link_curia_vista == 'https://curia.vista/de'
    assert vote.link_easyvote == 'https://easy.vote/de'
    assert vote.link_federal_council == 'https://federal.council/de'
    assert vote.link_federal_departement == 'https://federal.departement/de'
    assert vote.link_federal_office == 'https://federal.office/de'
    assert vote.link_post_vote_poll == 'https://post.vote.poll/de'
    assert vote.link_campaign_yes_1 == 'https://yes1.de'
    assert vote.link_campaign_yes_2 == 'https://yes2.de'
    assert vote.link_campaign_yes_3 == 'https://yes3.de'
    assert vote.link_campaign_no_1 == 'https://no1.de'
    assert vote.link_campaign_no_2 == 'https://no2.de'
    assert vote.link_campaign_no_3 == 'https://no3.de'
    assert vote.media_ads_total == 3001
    assert vote.media_ads_yea_p == Decimal('30.06')
    assert vote.media_coverage_articles_total == 3007
    assert vote.media_coverage_tonality_total == Decimal('30.10')
    assert vote.campaign_links == {
        'Campaign for a No': [
            'https://no1.de', 'https://no2.de', 'https://no3.de'
        ],
        'Campaign for a Yes': [
            'https://yes1.de', 'https://yes2.de', 'https://yes3.de'
        ]
    }
    assert vote.campaign_material_metadata == {
        'article': {
            'title': 'Article',
            'doctype': ['article']
        },
        'essay': {
            'title': 'Essay',
            'position': 'no'
        },
        'leaflet': {
            'title': 'Pamphlet',
            'date_year': 1970,
            'language': ['de']
        }
    }
    assert vote.campaign_finances_yea_total == 10000
    assert vote.campaign_finances_nay_total == 20000
    assert vote.campaign_finances_yea_donors == 'Donor 1 D, Donor 2 D'
    assert vote.campaign_finances_nay_donors == 'Donor D'
    assert vote.campaign_finances_link == 'https://finances.de'

    # localized properties
    with use_locale(vote, 'fr_CH'):
        assert vote.title == "Vote FR"
        assert vote.short_title == "V F"
        assert vote.initiator == "Initiator F"
        assert vote.bfs_map == "htt(ps://www.ap/mapIdOnly/1815[e.html}"
        assert vote.bfs_map_host == ""  # parsing error
        assert vote.bfs_dashboard == "https://dashboard.fr"
        assert vote.link_bk_chrono == 'https://bk.chrono/fr'
        assert vote.link_bk_results == 'https://bk.results/fr'
        assert vote.link_curia_vista == 'https://curia.vista/fr'
        assert vote.link_easyvote == 'https://easy.vote/fr'
        assert vote.link_federal_council == 'https://federal.council/fr'
        assert vote.link_federal_departement == (
            'https://federal.departement/fr'
        )
        assert vote.link_federal_office == 'https://federal.office/fr'
        assert vote.link_post_vote_poll == 'https://post.vote.poll/fr'
        assert vote.link_campaign_yes_1 == 'https://yes1.fr'
        assert vote.link_campaign_yes_2 == 'https://yes2.fr'
        assert vote.link_campaign_yes_3 == 'https://yes3.fr'
        assert vote.link_campaign_no_1 == 'https://no1.fr'
        assert vote.link_campaign_no_2 == 'https://no2.fr'
        assert vote.link_campaign_no_3 == 'https://no3.fr'
        del vote.campaign_links
        assert vote.campaign_links == {
            'Campaign for a No': [
                'https://no1.fr', 'https://no2.fr', 'https://no3.fr'
            ],
            'Campaign for a Yes': [
                'https://yes1.fr', 'https://yes2.fr', 'https://yes3.fr'
            ]
        }
        assert vote.campaign_finances_yea_donors == 'Donor 1 F, Donor 2 F'
        assert vote.campaign_finances_nay_donors == 'Donor F'
        assert vote.campaign_finances_link == 'https://finances.fr'

    with use_locale(vote, 'en_US'):
        assert vote.title == "Vote DE"
        assert vote.short_title == "V E"
        assert vote.bfs_map == (
            "https://abstimmungen.admin.ch/en/details?proposalId=6660"
        )
        assert vote.bfs_map_host == "https://abstimmungen.admin.ch"
        assert vote.bfs_dashboard == "https://dashboard.en"
        assert vote.link_bk_chrono == 'https://bk.chrono/de'
        assert vote.link_bk_results == 'https://bk.results/de'
        assert vote.link_curia_vista == 'https://curia.vista/de'
        assert vote.link_easyvote == 'https://easy.vote/de'
        assert vote.link_federal_council == 'https://federal.council/en'
        assert vote.link_federal_departement == (
            'https://federal.departement/en'
        )
        assert vote.link_federal_office == 'https://federal.office/en'
        assert vote.link_post_vote_poll == 'https://post.vote.poll/en'
        assert vote.link_campaign_yes_1 == 'https://yes1.de'
        assert vote.link_campaign_yes_2 == 'https://yes2.de'
        assert vote.link_campaign_yes_3 == 'https://yes3.de'
        assert vote.link_campaign_no_1 == 'https://no1.de'
        assert vote.link_campaign_no_2 == 'https://no2.de'
        assert vote.link_campaign_no_3 == 'https://no3.de'

    # descriptors
    assert vote.descriptor_1_level_1 == Decimal('4')
    assert vote.descriptor_1_level_2 == Decimal('4.2')
    assert vote.descriptor_1_level_3 == Decimal('4.21')
    assert vote.descriptor_2_level_1 == Decimal('10')
    assert vote.descriptor_2_level_2 == Decimal('10.3')
    assert vote.descriptor_2_level_3 == Decimal('10.35')
    assert vote.descriptor_3_level_1 == Decimal('10')
    assert vote.descriptor_3_level_2 == Decimal('10.3')
    assert vote.descriptor_3_level_3 == Decimal('10.33')
    assert vote._result == 1
    assert vote.result == "Accepted"
    assert vote.result_turnout == Decimal('20.01')
    assert vote._result_people_accepted == 1
    assert vote.result_people_accepted == "Accepted"
    assert vote.result_people_yeas_p == Decimal('40.01')
    assert vote._result_cantons_accepted == 1
    assert vote.result_cantons_accepted == "Accepted"
    assert vote.result_cantons_yeas == Decimal('1.5')
    assert vote.result_cantons_nays == Decimal('24.5')
    assert vote._result_ag_accepted == 0
    assert vote.result_ag_accepted == "Rejected"
    assert vote._result_ai_accepted == 0
    assert vote.result_ai_accepted == "Rejected"
    assert vote._result_ar_accepted == 0
    assert vote.result_ar_accepted == "Rejected"
    assert vote._result_be_accepted == 0
    assert vote.result_be_accepted == "Rejected"
    assert vote._result_bl_accepted == 0
    assert vote.result_bl_accepted == "Rejected"
    assert vote._result_bs_accepted == 0
    assert vote.result_bs_accepted == "Rejected"
    assert vote._result_fr_accepted == 0
    assert vote.result_fr_accepted == "Rejected"
    assert vote._result_ge_accepted == 0
    assert vote.result_ge_accepted == "Rejected"
    assert vote._result_gl_accepted == 0
    assert vote.result_gl_accepted == "Rejected"
    assert vote._result_gr_accepted == 0
    assert vote.result_gr_accepted == "Rejected"
    assert vote._result_ju_accepted == 0
    assert vote.result_ju_accepted == "Rejected"
    assert vote._result_lu_accepted == 0
    assert vote.result_lu_accepted == "Rejected"
    assert vote._result_ne_accepted == 0
    assert vote.result_ne_accepted == "Rejected"
    assert vote._result_nw_accepted == 0
    assert vote.result_nw_accepted == "Rejected"
    assert vote._result_ow_accepted == 0
    assert vote.result_ow_accepted == "Rejected"
    assert vote._result_sg_accepted == 0
    assert vote.result_sg_accepted == "Rejected"
    assert vote._result_sh_accepted == 0
    assert vote.result_sh_accepted == "Rejected"
    assert vote._result_so_accepted == 0
    assert vote.result_so_accepted == "Rejected"
    assert vote._result_sz_accepted == 0
    assert vote.result_sz_accepted == "Rejected"
    assert vote._result_tg_accepted == 0
    assert vote.result_tg_accepted == "Rejected"
    assert vote._result_ti_accepted == 0
    assert vote.result_ti_accepted == "Rejected"
    assert vote._result_ur_accepted == 0
    assert vote.result_ur_accepted == "Rejected"
    assert vote._result_vd_accepted == 1
    assert vote.result_vd_accepted == "Accepted"
    assert vote._result_vs_accepted == 1
    assert vote.result_vs_accepted == "Accepted"
    assert vote._result_zg_accepted == 0
    assert vote.result_zg_accepted == "Rejected"
    assert vote._result_zh_accepted is None
    assert vote.result_zh_accepted is None
    assert vote.procedure_number == '24.557'
    assert vote._position_federal_council == 1
    assert vote.position_federal_council == "Accepting"
    assert vote._position_parliament == 1
    assert vote.position_parliament == "Accepting"
    assert vote._position_national_council == 1
    assert vote.position_national_council == "Accepting"
    assert vote.position_national_council_yeas == 10
    assert vote.position_national_council_nays == 20
    assert vote._position_council_of_states == 1
    assert vote.position_council_of_states == "Accepting"
    assert vote.position_council_of_states_yeas == 30
    assert vote.position_council_of_states_nays == 40
    assert vote.duration_federal_assembly == 30
    assert vote.duration_initative_collection == 32
    assert vote.duration_referendum_collection == 35
    assert vote.signatures_valid == 40
    assert vote.recommendations == {
        'fdp': 1,
        'cvp': 8,
        'sps': 1,
        'svp': 1,
        'lps': 2,
        'ldu': 9,
        'evp': 2,
        'csp': 3,
        'pda': 3,
        'poch': 3,
        'gps': 4,
        'sd': 4,
        'rep': 4,
        'edu': 5,
        'fps': 5,
        'lega': 5,
        'kvp': 66,
        'glp': 66,
        'bdp': None,
        'mcg': 9999,
        'sav': 1,
        'eco': 2,
        'sgv': 3,
        'sbv-usp': 3,
        'sgb': 3,
        'travs': 3,
        'vsa': 9999,
        'vpod': 1,
        'ssv': 1,
        'gem': 1,
        'kdk': 1,
        'vdk': 1,
        'endk': 1,
        'fdk': 1,
        'edk': 1,
        'gdk': 1,
        'ldk': 1,
        'sodk': 1,
        'kkjpd': 1,
        'bpuk': 1,
        'sbk': 1,
        'acs': 8,
        'tcs': 9,
        'vcs': 1,
        'voev': 1
    }
    assert vote.recommendations_divergent == {
        'edu_vso': 1,
        'fdp_ti': 1,
        'fdp-fr_ch': 2,
        'jcvp_ch': 2,
    }
    assert vote.national_council_election_year == 1990
    assert vote.national_council_share_fdp == Decimal('01.10')
    assert vote.national_council_share_cvp == Decimal('02.10')
    assert vote.national_council_share_sps == Decimal('03.10')
    assert vote.national_council_share_svp == Decimal('04.10')
    assert vote.national_council_share_lps == Decimal('05.10')
    assert vote.national_council_share_ldu == Decimal('06.10')
    assert vote.national_council_share_evp == Decimal('07.10')
    assert vote.national_council_share_csp == Decimal('08.10')
    assert vote.national_council_share_pda == Decimal('09.10')
    assert vote.national_council_share_poch == Decimal('10.10')
    assert vote.national_council_share_gps == Decimal('11.10')
    assert vote.national_council_share_sd == Decimal('12.10')
    assert vote.national_council_share_rep == Decimal('13.10')
    assert vote.national_council_share_edu == Decimal('14.10')
    assert vote.national_council_share_fps == Decimal('15.10')
    assert vote.national_council_share_lega == Decimal('16.10')
    assert vote.national_council_share_kvp == Decimal('17.10')
    assert vote.national_council_share_glp == Decimal('18.10')
    assert vote.national_council_share_bdp == Decimal('19.10')
    assert vote.national_council_share_mcg == Decimal('20.20')
    assert vote.national_council_share_mitte == Decimal('20.10')
    assert vote.national_council_share_ubrige == Decimal('21.20')
    assert vote.national_council_share_yeas == Decimal('22.20')
    assert vote.national_council_share_nays == Decimal('23.20')
    assert vote.national_council_share_neutral == Decimal('24.20')
    assert vote.national_council_share_none == Decimal('25.20')
    assert vote.national_council_share_empty == Decimal('26.20')
    assert vote.national_council_share_free_vote == Decimal('27.20')
    assert vote.national_council_share_unknown == Decimal('28.20')

    assert vote.policy_areas == [
        PolicyArea('4.42.421'),
        PolicyArea('10.103.1035'),
        PolicyArea('10.103.1033')
    ]

    assert vote.results_cantons['Rejected'] == [
        Region('ag'),
        Region('ai'),
        Region('ar'),
        Region('be'),
        Region('bl'),
        Region('bs'),
        Region('fr'),
        Region('ge'),
        Region('gl'),
        Region('gr'),
        Region('ju'),
        Region('lu'),
        Region('ne'),
        Region('nw'),
        Region('ow'),
        Region('sg'),
        Region('sh'),
        Region('so'),
        Region('sz'),
        Region('tg'),
        Region('ti'),
        Region('ur'),
        Region('zg'),
        # Region('zh'),
    ]
    assert vote.results_cantons['Accepted'] == [
        Region('vd'),
        Region('vs'),
    ]

    # recommendations
    assert list(vote.recommendations_parties.keys()) == [
        'Yea',
        'Preference for the popular initiative',
        'Nay',
        'Preference for the counter-proposal',
        'Empty',
        'Free vote',
        'None',
        'Neutral'
    ]
    assert vote.recommendations_parties['Yea'] == [
        Actor('fdp'),
        Actor('sps'),
        Actor('svp'),
    ]
    assert vote.recommendations_parties[
        'Preference for the counter-proposal'
    ] == [
        Actor('cvp'),
    ]
    assert vote.recommendations_parties['Nay'] == [
        Actor('evp'),
        Actor('lps'),
    ]
    assert vote.recommendations_parties[
        'Preference for the popular initiative'
    ] == [
        Actor('ldu'),
    ]
    assert vote.recommendations_parties['None'] == [
        Actor('csp'),
        Actor('pda'),
        Actor('poch'),
    ]
    assert vote.recommendations_parties['Empty'] == [
        Actor('gps'),
        Actor('rep'),
        Actor('sd'),
    ]
    assert vote.recommendations_parties['Free vote'] == [
        Actor('edu'),
        Actor('fps'),
        Actor('lega'),
    ]
    assert vote.recommendations_parties['Neutral'] == [
        Actor('glp'),
        Actor('kvp')
    ]
    assert list(vote.recommendations_associations.keys()) == [
        'Yea',
        'Preference for the popular initiative',
        'Nay',
        'Preference for the counter-proposal',
        'Free vote',
        'None',
    ]
    assert vote.recommendations_associations['Yea'] == [
        Actor('bpuk'),
        Actor('edk'),
        Actor('endk'),
        Actor('fdk'),
        Actor('gdk'),
        Actor('gem'),
        Actor('kdk'),
        Actor('kkjpd'),
        Actor('ldk'),
        Actor('sav'),
        Actor('sbk'),
        Actor('sodk'),
        Actor('ssv'),
        Actor('vcs'),
        Actor('vdk'),
        Actor('voev'),
        Actor('vpod'),
        Actor('Pro Velo D')
    ]
    assert vote.recommendations_associations[
        'Preference for the counter-proposal'
    ] == [
        Actor('acs'),
        Actor('Pro Juventute D'),
    ]
    assert vote.recommendations_associations['Nay'] == [Actor('eco')]
    assert vote.recommendations_associations[
        'Preference for the popular initiative'
    ] == [
        Actor('tcs'),
        Actor('Pro Senectute D'),
    ]
    assert vote.recommendations_associations['None'] == [
        Actor('sbv-usp'),
        Actor('sgb'),
        Actor('sgv'),
        Actor('travs'),
    ]
    assert vote.recommendations_associations['Free vote'] == [
        Actor('Pro Natura D'),
        Actor('Greenpeace D'),
    ]
    assert list(vote.recommendations_divergent_parties.keys()) == [
        'Yea', 'Nay'
    ]
    assert vote.recommendations_divergent_parties['Yea'] == [
        (Actor('edu'), Region('vso')),
        (Actor('fdp'), Region('ti')),
    ]
    assert vote.recommendations_divergent_parties['Nay'] == [
        (Actor('fdp-fr'), Region('ch')),
        (Actor('jcvp'), Region('ch')),
    ]

    # localized recommendations
    with use_locale(vote, 'fr_CH'):
        del vote.recommendations_associations
        assert vote.recommendations_associations[
            'Preference for the popular initiative'
        ] == [
            Actor('tcs'),
            Actor('Pro Senectute F'),
        ]
        assert vote.recommendations_associations['Free vote'] == [
            Actor('Pro Natura F'),
            Actor('Greenpeace F'),
        ]

    # other
    assert vote.has_national_council_share_data is True

    assert vote.posters(DummyRequest()) == {  # type: ignore[arg-type]
        'nay': [
            Poster(
                thumbnail='https://detail.com/4',
                image='https://detail.com/4',
                url='https://no.com/objects/4',
                label='Link Social Archives'
            ),
            Poster(
                thumbnail='https://detail.com/3',
                image='https://detail.com/3',
                url='https://no.com/objects/3',
                label='Link Social Archives'
            ),
            Poster(
                thumbnail='https://detail.com/6',
                image='https://detail.com/6',
                url='https://no.com/objects/6',
                label='Link Basel Poster Collection'
            )
        ],
        'yea': [
            Poster(
                thumbnail='https://detail.com/1',
                image='https://detail.com/1',
                url='https://yes.com/objects/1',
                label='Link eMuseum.ch'
            ),
            Poster(
                thumbnail='https://detail.com/5',
                image='https://detail.com/5',
                url='https://yes.com/objects/5',
                label='Link Basel Poster Collection'
            )
        ]
    }


def test_model_vote_codes() -> None:
    assert SwissVote.codes('legal_form')[2] == "Optional referendum"
    assert SwissVote.codes('result')[0] == "Rejected"
    assert SwissVote.codes('result_people_accepted')[0] == "Rejected"
    assert SwissVote.codes('result_cantons_accepted')[0] == "Rejected"
    assert SwissVote.codes('result_ai_accepted')[1] == "Accepted"
    assert SwissVote.codes('position_federal_council')[3] == "None"
    assert SwissVote.codes('position_parliament')[2] == "Rejecting"
    assert SwissVote.codes('position_national_council')[2] == "Rejecting"
    assert SwissVote.codes('position_council_of_states')[2] == "Rejecting"
    assert SwissVote.codes('recommendation')[5] == "Free vote"
    assert SwissVote.metadata_codes('position')['no'] == "No"
    assert SwissVote.metadata_codes('language')['mixed'] == "Mixed"
    assert SwissVote.metadata_codes('doctype')['leaflet'] == "Pamphlet"


def test_model_vote_search_term_expression(swissvotes_app: TestApp) -> None:
    expression = SwissVote.search_term_expression
    assert expression(None) == ''
    assert expression('') == ''
    assert expression('*') == ''
    assert expression('* *') == ''
    assert expression('* a *') == 'a'
    assert expression('*   a *  b *') == 'a <-> b'
    assert expression('a,1.$b !c*d*') == 'a,1.b <-> cd:*'
    assert expression('AHV Mehrwertsteuer') == 'AHV <-> Mehrwertsteuer'
    assert expression('AHV Mehrwert*') == 'AHV <-> Mehrwert:*'


def test_model_vote_attachments(
    swissvotes_app: TestApp,
    attachments: dict[str, SwissVoteFile],
    campaign_material: dict[str, SwissVoteFile]
) -> None:

    session = swissvotes_app.session()
    session.add(
        SwissVote(
            bfs_number=Decimal('100.1'),
            date=date(1990, 6, 2),
            title_de="Vote DE",
            title_fr="Vote FR",
            short_title_de="V D",
            short_title_fr="V F",
            keyword="Keyword",
            _legal_form=1,
        )
    )
    session.flush()

    vote = session.query(SwissVote).one()
    assert vote.ad_analysis is None
    assert vote.brief_description is None
    assert vote.easyvote_booklet is None
    assert vote.federal_council_message is None
    assert vote.foeg_analysis is None
    assert vote.leewas_post_vote_poll_results is None
    assert vote.parliamentary_initiative is None
    assert vote.parliamentary_committee_report is None
    assert vote.federal_council_opinion is None
    assert vote.parliamentary_debate is None
    assert vote.post_vote_poll is None
    assert vote.post_vote_poll_codebook is None
    assert vote.post_vote_poll_codebook_xlsx is None
    assert vote.post_vote_poll_dataset is None
    assert vote.post_vote_poll_dataset_dta is None
    assert vote.post_vote_poll_dataset_sav is None
    assert vote.post_vote_poll_methodology is None
    assert vote.post_vote_poll_report is None
    assert vote.preliminary_examination is None
    assert vote.realization is None
    assert vote.resolution is None
    assert vote.results_by_domain is None
    assert vote.voting_booklet is None
    assert vote.voting_text is None
    assert vote.files == []
    assert vote.searchable_text_de_CH is None
    assert vote.searchable_text_fr_CH is None

    assert set(vote.localized_files().keys()) == {
        'ad_analysis',
        'brief_description',
        'campaign_finances_xlsx',
        'easyvote_booklet',
        'federal_council_message',
        'foeg_analysis',
        'leewas_post_vote_poll_results',
        'parliamentary_initiative',
        'parliamentary_committee_report',
        'federal_council_opinion',
        'parliamentary_debate',
        'post_vote_poll_codebook_xlsx',
        'post_vote_poll_codebook',
        'post_vote_poll_dataset_dta',
        'post_vote_poll_dataset_sav',
        'post_vote_poll_dataset',
        'post_vote_poll_methodology',
        'post_vote_poll_report',
        'post_vote_poll',
        'preliminary_examination',
        'realization',
        'resolution',
        'results_by_domain',
        'voting_booklet',
        'voting_text'
    }

    assert vote.indexed_files == {
        'brief_description',
        'federal_council_message',
        'parliamentary_debate',
        'preliminary_examination',
        'realization',
        'voting_text',
    }

    # Upload de_CH
    vote.ad_analysis = attachments['ad_analysis']
    vote.brief_description = attachments['brief_description']
    vote.parliamentary_debate = attachments['parliamentary_debate']
    vote.voting_text = attachments['voting_text']
    session.flush()
    session.refresh(vote)

    # undo mypy narrowing
    vote = vote

    assert len(vote.files) == 4
    assert vote.ad_analysis is not None
    assert vote.ad_analysis.name == 'ad_analysis-de_CH'
    assert vote.ad_analysis.extract == 'Inserateanalyse'
    assert vote.ad_analysis.stats == {'pages': 1, 'words': 1}
    assert vote.ad_analysis.language == 'german'
    assert vote.brief_description is not None
    assert vote.brief_description.name == 'brief_description-de_CH'
    assert vote.brief_description.extract == 'Kurzbeschreibung'
    assert vote.brief_description.stats == {'pages': 1, 'words': 1}
    assert vote.brief_description.language == 'german'
    assert vote.parliamentary_debate is not None
    assert vote.parliamentary_debate.name == 'parliamentary_debate-de_CH'
    assert vote.parliamentary_debate.extract == 'Parlamentdebatte'
    assert vote.parliamentary_debate.stats == {'pages': 1, 'words': 1}
    assert vote.parliamentary_debate.language == 'german'
    assert vote.voting_text is not None
    assert vote.voting_text.name == 'voting_text-de_CH'
    assert vote.voting_text.extract == 'Abstimmungstext'
    assert vote.voting_text.stats == {'pages': 1, 'words': 1}
    assert vote.voting_text.language == 'german'
    assert "abstimmungstex" in vote.searchable_text_de_CH
    assert "kurzbeschreib" in vote.searchable_text_de_CH
    assert "parlamentdebatt" in vote.searchable_text_de_CH
    assert vote.searchable_text_fr_CH == ''
    assert vote.search('Inserateanalysen') == [vote.ad_analysis]
    assert vote.search('Kurzbeschreibung') == [vote.brief_description]
    assert vote.search('Parlamentdebatte') == [vote.parliamentary_debate]
    assert vote.search('Abstimmungstext') == [vote.voting_text]

    # Upload fr_CH
    with use_locale(swissvotes_app, 'fr_CH'):
        vote.realization = attachments['realization']
        session.flush()

        # undo mypy narrowing
        vote = vote

        assert len(vote.files) == 5
        assert vote.voting_text is None
        assert vote.realization is not None
        assert vote.realization.name == 'realization-fr_CH'
        assert vote.realization.stats == {'pages': 1, 'words': 1}
        assert vote.realization.language == 'french'

        assert "abstimmungstex" in vote.searchable_text_de_CH
        assert "kurzbeschreib" in vote.searchable_text_de_CH
        assert "parlamentdebatt" in vote.searchable_text_de_CH
        assert "réalis" in vote.searchable_text_fr_CH
        assert vote.search('Réalisation') == [vote.realization]

        del vote.realization
        vote.federal_council_message = attachments['federal_council_message']
        vote.resolution = attachments['resolution']
        vote.voting_booklet = attachments['voting_booklet']
        session.flush()

        assert len(vote.files) == 7
        assert vote.voting_text is None
        assert vote.federal_council_message is not None
        assert vote.federal_council_message.name == (
            'federal_council_message-fr_CH'
        )
        assert vote.federal_council_message.stats == {'pages': 1, 'words': 4}
        assert vote.federal_council_message.language == 'french'
        assert vote.resolution is not None
        assert vote.resolution.name == 'resolution-fr_CH'
        assert vote.resolution.stats == {'pages': 1, 'words': 4}
        assert vote.resolution.language == 'french'
        assert vote.voting_booklet is not None
        assert vote.voting_booklet.name == 'voting_booklet-fr_CH'
        assert vote.voting_booklet.stats == {'pages': 1, 'words': 2}
        assert vote.voting_booklet.language == 'french'
        assert "abstimmungstex" in vote.searchable_text_de_CH
        assert "kurzbeschreib" in vote.searchable_text_de_CH
        assert "parlamentdebatt" in vote.searchable_text_de_CH
        assert "réalis" not in vote.searchable_text_fr_CH
        assert "conseil" in vote.searchable_text_fr_CH
        assert "fédéral" in vote.searchable_text_fr_CH
        assert vote.search('Conseil fédéral') == [vote.federal_council_message]
        assert vote.search('Messages') == [vote.federal_council_message]
        assert vote.search('constatant') == [vote.resolution]
        assert vote.search('brochure') == [vote.voting_booklet]

        assert vote.get_file('ad_analysis').name == 'ad_analysis-de_CH'  # type: ignore[union-attr]
        assert vote.get_file('ad_analysis', 'fr_CH').name == (  # type: ignore[union-attr]
            'ad_analysis-de_CH'
        )
        assert vote.get_file('ad_analysis', 'en_US').name == (  # type: ignore[union-attr]
            'ad_analysis-de_CH'
        )
        assert vote.get_file('ad_analysis', fallback=False) is None
        assert vote.get_file('ad_analysis', 'en_US', fallback=False) is None
        assert vote.get_file('realization') is None
        assert vote.get_file('resolution').name == 'resolution-fr_CH'  # type: ignore[union-attr]
        assert vote.get_file('resolution', 'fr_CH').name == 'resolution-fr_CH'  # type: ignore[union-attr]
        assert vote.get_file('resolution', 'de_CH') is None

        # Additional campaing material
        vote.campaign_material_metadata = {
            'campaign_material_other-essay': {'language': ['de', 'it']},
            'campaign_material_other-leaflet': {'language': ['it', 'en']},
            'campaign_material_other-legal': {'language': ['fr', 'it']},
        }
        assert vote.campaign_material_yea == []
        assert vote.campaign_material_nay == []
        assert vote.campaign_material_other == []

        vote.files.append(campaign_material['campaign_material_yea-1.png'])
        vote.files.append(campaign_material['campaign_material_yea-2.png'])
        vote.files.append(campaign_material['campaign_material_nay-1.png'])
        vote.files.append(campaign_material['campaign_material_nay-2.png'])
        vote.files.append(
            campaign_material['campaign_material_other-essay.pdf']
        )
        vote.files.append(
            campaign_material['campaign_material_other-leaflet.pdf']
        )
        vote.files.append(
            campaign_material['campaign_material_other-article.pdf']
        )
        vote.files.append(
            campaign_material['campaign_material_other-legal.pdf']
        )
        session.flush()

        assert [file.filename for file in vote.campaign_material_yea] == [
            'campaign_material_yea-1.png', 'campaign_material_yea-2.png'
        ]
        assert [file.filename for file in vote.campaign_material_nay] == [
            'campaign_material_nay-1.png', 'campaign_material_nay-2.png'
        ]
        files = {
            file.name.split('-')[1].split('.')[0]: file
            for file in vote.campaign_material_other
        }
        assert files['essay'].filename == 'campaign_material_other-essay.pdf'
        assert files['essay'].extract == 'Abhandlung'
        assert files['essay'].stats == {'pages': 1, 'words': 1}
        assert files['essay'].language == 'german'
        assert files['leaflet'].filename == (
            'campaign_material_other-leaflet.pdf'
        )
        assert files['leaflet'].extract == 'Volantino'
        assert files['leaflet'].stats == {'pages': 1, 'words': 1}
        assert files['leaflet'].language == 'italian'
        assert files['article'].filename == (
            'campaign_material_other-article.pdf'
        )
        assert files['article'].language == 'english'
        assert files['article'].extract == 'Article'
        assert files['legal'].stats == {'pages': 1, 'words': 1}
        assert files['legal'].filename == 'campaign_material_other-legal.pdf'
        assert files['legal'].language == 'french'
        assert files['legal'].extract == 'Juridique'
        assert files['legal'].stats == {'pages': 1, 'words': 1}
        assert 'abhandl' in vote.searchable_text_de_CH
        assert 'volantin' in vote.searchable_text_it_CH
        assert 'articl' in vote.searchable_text_en_US
        assert vote.search('Abhandlung') == [files['essay']]
        assert vote.search('Abhandlungen') == [files['essay']]
        assert vote.search('Volantino') == [files['leaflet']]
        assert vote.search('Volantini') == [files['leaflet']]
        assert vote.search('Article') == [files['article']]
        assert vote.search('Articles') == [files['article']]
        assert vote.search('Juridique') == [files['legal']]
        assert vote.search('Juridiques') == [files['legal']]

        assert vote.posters(DummyRequest())['yea'] == [  # type: ignore[arg-type]
            Poster(
                thumbnail=f'{file}/thumbnail',
                image=f'{file}',
                url=None,
                label='Swissvotes database'
            )
            for file in vote.campaign_material_yea
        ]
        assert vote.posters(DummyRequest())['nay'] == [  # type: ignore[arg-type]
            Poster(
                thumbnail=f'{file}/thumbnail',
                image=f'{file}',
                url=None,
                label='Swissvotes database'
            )
            for file in vote.campaign_material_nay
        ]


def test_model_column_mapper_dataset() -> None:
    mapper = ColumnMapperDataset()
    vote = SwissVote()

    mapper.set_value(vote, 'bfs_number', Decimal('100.1'))
    mapper.set_value(vote, 'date', date(2019, 1, 1))
    mapper.set_value(vote, 'title_de', 'title de')
    mapper.set_value(vote, 'title_fr', 'title fr')
    mapper.set_value(vote, 'short_title_de', 'short title de')
    mapper.set_value(vote, 'short_title_fr', 'short title fr')
    mapper.set_value(vote, 'short_title_en', 'short title en')
    mapper.set_value(vote, 'keyword', 'keyword')
    mapper.set_value(vote, '_legal_form', 4)
    mapper.set_value(vote, '!i!recommendations!fdp', 66)
    mapper.set_value(vote, '!t!content!link_bk_results_de', 'http://a.b')

    assert vote.bfs_number == Decimal('100.1')
    assert vote.date == date(2019, 1, 1)
    assert vote.title_de == 'title de'
    assert vote.title_fr == 'title fr'
    assert vote.short_title_de == 'short title de'
    assert vote.short_title_fr == 'short title fr'
    assert vote.short_title_en == 'short title en'
    assert vote.keyword == 'keyword'
    assert vote.legal_form == 'Direct counter-proposal'
    assert vote.get_recommendation('fdp') == 'Neutral'

    assert mapper.get_value(vote, 'bfs_number'), Decimal('100.1')
    assert mapper.get_value(vote, 'date') == date(2019, 1, 1)
    assert mapper.get_value(vote, 'title_de') == 'title de'
    assert mapper.get_value(vote, 'title_fr') == 'title fr'
    assert mapper.get_value(vote, 'short_title_de') == 'short title de'
    assert mapper.get_value(vote, 'short_title_fr') == 'short title fr'
    assert mapper.get_value(vote, 'short_title_en') == 'short title en'
    assert mapper.get_value(vote, 'keyword') == 'keyword'
    assert mapper.get_value(vote, '_legal_form') == 4
    assert mapper.get_value(vote, '!i!recommendations!fdp') == 66
    assert mapper.get_value(vote, '!t!content!link_bk_results_de') == (
        'http://a.b'
    )

    assert list(mapper.get_values(vote))[:22] == [
        Decimal('100.1'),
        date(2019, 1, 1),
        'short title de',
        'short title fr',
        'short title en',
        'title de',
        'title fr',
        'keyword',
        4,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    ]
    assert list(mapper.get_items(vote))[:22] == [
        ('bfs_number', Decimal('100.1')),
        ('date', date(2019, 1, 1)),
        ('short_title_de', 'short title de'),
        ('short_title_fr', 'short title fr'),
        ('short_title_en', 'short title en'),
        ('title_de', 'title de'),
        ('title_fr', 'title fr'),
        ('keyword', 'keyword'),
        ('_legal_form', 4),
        ('anneepolitique', None),
        ('!t!content!link_bk_chrono_de', None),
        ('!t!content!link_bk_chrono_fr', None),
        ('descriptor_1_level_1', None),
        ('descriptor_1_level_2', None),
        ('descriptor_1_level_3', None),
        ('descriptor_2_level_1', None),
        ('descriptor_2_level_2', None),
        ('descriptor_2_level_3', None),
        ('descriptor_3_level_1', None),
        ('descriptor_3_level_2', None),
        ('descriptor_3_level_3', None),
        ('_position_federal_council', None),
    ]
    assert list(mapper.items())[:22] == [
        ('bfs_number', 'anr', 'NUMERIC(8, 2)', False, 8, 2),
        ('date', 'datum', 'DATE', False, None, None),
        ('short_title_de', 'titel_kurz_d', 'TEXT', False, None, None),
        ('short_title_fr', 'titel_kurz_f', 'TEXT', False, None, None),
        ('short_title_en', 'titel_kurz_e', 'TEXT', True, None, None),
        ('title_de', 'titel_off_d', 'TEXT', False, None, None),
        ('title_fr', 'titel_off_f', 'TEXT', False, None, None),
        ('keyword', 'stichwort', 'TEXT', True, None, None),
        ('_legal_form', 'rechtsform', 'INTEGER', False, None, None),
        ('anneepolitique', 'anneepolitique', 'TEXT', True, None, None),
        (
            '!t!content!link_bk_chrono_de', 'bkchrono-de', 'TEXT', True, None,
            None
        ),
        (
            '!t!content!link_bk_chrono_fr', 'bkchrono-fr', 'TEXT', True, None,
            None
        ),
        ('descriptor_1_level_1', 'd1e1', 'NUMERIC(8, 4)', True, 8, 4),
        ('descriptor_1_level_2', 'd1e2', 'NUMERIC(8, 4)', True, 8, 4),
        ('descriptor_1_level_3', 'd1e3', 'NUMERIC(8, 4)', True, 8, 4),
        ('descriptor_2_level_1', 'd2e1', 'NUMERIC(8, 4)', True, 8, 4),
        ('descriptor_2_level_2', 'd2e2', 'NUMERIC(8, 4)', True, 8, 4),
        ('descriptor_2_level_3', 'd2e3', 'NUMERIC(8, 4)', True, 8, 4),
        ('descriptor_3_level_1', 'd3e1', 'NUMERIC(8, 4)', True, 8, 4),
        ('descriptor_3_level_2', 'd3e2', 'NUMERIC(8, 4)', True, 8, 4),
        ('descriptor_3_level_3', 'd3e3', 'NUMERIC(8, 4)', True, 8, 4),
        ('_position_federal_council', 'br-pos', 'INTEGER', True, None, None),
    ]
    assert list(mapper.items())[305] == (
        '!i!recommendations_divergent!gps_ar', 'pdev-gps_AR', 'INTEGER',
        True, None, None
    )


def test_model_column_mapper_metadata() -> None:
    mapper = ColumnMapperMetadata()
    data: dict[str, Any] = {}

    mapper.set_value(data, 'n:f:bfs_number', Decimal('100.1'))
    mapper.set_value(data, 't:f:filename', 'Dateiname')
    mapper.set_value(data, 't:t:title', 'Titel')
    mapper.set_value(data, 't:t:position', 'Ja')
    mapper.set_value(data, 't:t:author', 'Autor')
    mapper.set_value(data, 't:t:editor', 'Herausgeber')
    mapper.set_value(data, 'i:t:date_year', 1970)
    mapper.set_value(data, 'i:t:date_month', None)
    mapper.set_value(data, 'i:t:date_day', 31)
    mapper.set_value(data, 't:t:language!de', 'x')
    mapper.set_value(data, 't:t:language!en', True)
    mapper.set_value(data, 't:t:language!fr', '')
    mapper.set_value(data, 't:t:language!it', None)
    mapper.set_value(data, 't:t:doctype!argument', 'x')
    mapper.set_value(data, 't:t:doctype!article', True)
    mapper.set_value(data, 't:t:doctype!release', '')
    mapper.set_value(data, 't:t:doctype!lecture', None)

    assert data == {
        'author': 'Autor',
        'bfs_number': Decimal('100.1'),
        'date_day': 31,
        'date_month': None,
        'date_year': 1970,
        'doctype': ['argument', 'article'],
        'editor': 'Herausgeber',
        'filename': 'Dateiname',
        'language': ['de', 'en'],
        'position': 'yes',
        'title': 'Titel'
    }

    assert list(mapper.items()) == [
        ('n:f:bfs_number', 'Abst-Nummer', 'NUMERIC', False, 8, 2),
        ('t:f:filename', 'Dateiname', 'TEXT', False, None, None),
        ('t:t:title', 'Titel des Dokuments', 'TEXT', True, None, None),
        ('t:t:position', 'Position zur Vorlage', 'TEXT', True, None, None),
        ('t:t:author', 'AutorIn (Nachname Vorname) des Dokuments', 'TEXT',
         True, None, None),
        ('t:t:editor', 'AuftraggeberIn/HerausgeberIn des Dokuments '
         '(typischerweise Komitee/Verband/Partei)', 'TEXT', True, None, None),
        ('i:t:date_year', 'Datum Jahr', 'INTEGER', True, None, None),
        ('i:t:date_month', 'Datum Monat', 'INTEGER', True, None, None),
        ('i:t:date_day', 'Datum Tag', 'INTEGER', True, None, None),
        ('t:t:language!de', 'Sprache DE', 'TEXT', True, None, None),
        ('t:t:language!en', 'Sprache EN', 'TEXT', True, None, None),
        ('t:t:language!fr', 'Sprache FR', 'TEXT', True, None, None),
        ('t:t:language!it', 'Sprache IT', 'TEXT', True, None, None),
        ('t:t:language!rm', 'Sprache RR', 'TEXT', True, None, None),
        ('t:t:language!mixed', 'Sprache Gemischt', 'TEXT', True, None, None),
        ('t:t:language!other', 'Sprache Anderes', 'TEXT', True, None, None),
        ('t:t:doctype!argument', 'Typ ARGUMENTARIUM', 'TEXT', True, None,
         None),
        ('t:t:doctype!letter', 'Typ BRIEF', 'TEXT', True, None, None),
        ('t:t:doctype!documentation', 'Typ DOKUMENTATION', 'TEXT', True, None,
         None),
        ('t:t:doctype!leaflet', 'Typ FLUGBLATT', 'TEXT', True, None, None),
        ('t:t:doctype!release', 'Typ MEDIENMITTEILUNG', 'TEXT', True, None,
         None),
        ('t:t:doctype!memberships', 'Typ MITGLIEDERVERZEICHNIS', 'TEXT', True,
         None, None),
        ('t:t:doctype!article', 'Typ PRESSEARTIKEL', 'TEXT', True, None, None),
        ('t:t:doctype!legal', 'Typ RECHTSTEXT', 'TEXT', True, None, None),
        ('t:t:doctype!lecture', 'Typ REFERATSTEXT', 'TEXT', True, None, None),
        ('t:t:doctype!statistics', 'Typ STATISTIK', 'TEXT', True, None, None),
        ('t:t:doctype!other', 'Typ ANDERES', 'TEXT', True, None, None),
        ('t:t:doctype!website', 'Typ WEBSITE', 'TEXT', True, None, None)
    ]


def test_model_recommendation_order() -> None:
    recommendations = SwissVote.codes('recommendation')
    assert list(recommendations.keys()) == [
        1, 9, 2, 8, 4, 5, 3, 66, 9999, None
    ]


def test_model_recommendations_parties(sample_vote: SwissVote) -> None:
    grouped = sample_vote.recommendations_parties
    codes = SwissVote.codes('recommendation')
    # Remove entries in codes for unknown and actor no longer exists
    del codes[9999]
    del codes[None]
    assert list(grouped.keys()) == list(codes.values())


def test_model_sorted_actors_list(sample_vote: SwissVote) -> None:
    sorted_actors = sample_vote.sorted_actors_list
    assert sorted_actors
    for i in range(len(sorted_actors) - 2):
        actor = sorted_actors[i]
        next_actor = sorted_actors[i + 1]
        actual_rec = sample_vote.get_recommendation(actor)
        next_rec = sample_vote.get_recommendation(next_actor)
        if actual_rec == next_rec:
            assert sample_vote.get_actors_share(
                actor) > sample_vote.get_actors_share(next_actor)
