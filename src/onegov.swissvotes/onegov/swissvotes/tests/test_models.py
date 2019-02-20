from datetime import date
from decimal import Decimal
from io import BytesIO
from onegov.core.crypto import random_token
from onegov.file.utils import as_fileintent
from onegov.swissvotes.models.actor import Actor
from onegov.swissvotes.models.canton import Canton
from onegov.swissvotes.models.localized_file import LocalizedFile
from onegov.swissvotes.models.page import TranslatablePage
from onegov.swissvotes.models.page import TranslatablePageFile
from onegov.swissvotes.models.page import TranslatablePageMove
from onegov.swissvotes.models.policy_area import PolicyArea
from onegov.swissvotes.models.principal import Principal
from onegov.swissvotes.models.vote import SwissVote
from psycopg2.extras import NumericRange
from translationstring import TranslationString


class DummyRequest(object):
    def translate(self, text):
        if isinstance(text, TranslationString):
            return text.interpolate()
        return text


def test_actor():
    actor = Actor('csp')
    assert actor.name == 'csp'
    assert actor.abbreviation == 'actor-csp-abbreviation'
    assert isinstance(actor.abbreviation, TranslationString)
    assert actor.label == 'actor-csp-label'
    assert isinstance(actor.label, TranslationString)
    assert actor.html(DummyRequest()) == (
        '<span title="actor-csp-label">actor-csp-abbreviation</span>'
    )

    actor = Actor('xxx')
    assert actor.name == 'xxx'
    assert actor.abbreviation == 'XXX'
    assert not isinstance(actor.abbreviation, TranslationString)
    assert actor.label == 'XXX'
    assert not isinstance(actor.label, TranslationString)
    assert actor.html(DummyRequest()) == '<span title="XXX">XXX</span>'

    assert Actor('csp') == Actor('csp')
    assert Actor('csp') != Actor('xxx')


def test_canton():
    assert len(Canton.abbreviations()) == 26

    canton = Canton('lu')
    assert canton.abbreviation == 'lu'
    assert not isinstance(canton.abbreviation, TranslationString)
    assert canton.label == 'canton-lu-label'
    assert isinstance(canton.label, TranslationString)
    assert canton.html(DummyRequest()) == (
        '<span title="canton-lu-label">LU</span>'
    )

    canton = Canton('xxx')
    assert canton.abbreviation == 'xxx'
    assert not isinstance(canton.abbreviation, TranslationString)
    assert canton.label == 'XXX'
    assert not isinstance(canton.label, TranslationString)
    assert canton.html(DummyRequest()) == '<span title="XXX">XXX</span>'

    assert Canton('lu') == Canton('lu')
    assert Canton('lu') != Canton('xxx')


def test_localized_file():
    class SessionManager(object):
        def __init__(self):
            self.current_locale = 'de_CH'

    class MyClass(object):
        file = LocalizedFile()

        def __init__(self):
            self.session_manager = SessionManager()
            self.files = []

    class File(object):
        def __init__(self, name):
            self.name = name

    my = MyClass()
    assert my.file is None

    # Add CH
    my.file = File('A')
    assert my.file.name == 'file-de_CH'
    assert set(file.name for file in my.files) == {'file-de_CH'}

    # Add FR
    my.session_manager.current_locale = 'fr_CH'
    assert my.file is None

    my.file = File('B')
    assert my.file.name == 'file-fr_CH'
    assert set(file.name for file in my.files) == {'file-de_CH', 'file-fr_CH'}

    # Access unrestricted
    assert MyClass.__dict__['file'].__get_by_locale__(my, 'de_CH').name == \
        'file-de_CH'
    assert MyClass.__dict__['file'].__get_by_locale__(my, 'fr_CH').name == \
        'file-fr_CH'
    assert MyClass.__dict__['file'].__get_by_locale__(my, 'rm_CH') is None

    # Delete FR
    del my.file
    assert my.file is None
    assert set(file.name for file in my.files) == {'file-de_CH'}


def test_page(session):
    session.add(
        TranslatablePage(
            id='page',
            title_translations={'de_CH': "Titel", 'en': "Title"},
            content_translations={'de_CH': "Inhalt", 'en': "Content"}
        )
    )
    session.flush()

    page = session.query(TranslatablePage).one()
    assert page.id == 'page'
    assert page.title_translations == {'de_CH': "Titel", 'en': "Title"}
    assert page.content_translations == {'de_CH': "Inhalt", 'en': "Content"}
    assert page.order == 65536

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


def test_page_move(session):
    # test URL template
    move = TranslatablePageMove(None, None, None, None).for_url_template()
    assert move.direction == '{direction}'
    assert move.subject_id == '{subject_id}'
    assert move.target_id == '{target_id}'

    # test execute
    for order, id in enumerate(('about', 'contact', 'dataset')):
        session.add(
            TranslatablePage(
                id=id, order=order,
                title_translations={'en': id}, content_translations={'en': id}
            )
        )

    def ordering():
        query = session.query(TranslatablePage.id)
        query = query.order_by(TranslatablePage.order)
        return [r.id for r in query.all()]

    assert ordering() == ['about', 'contact', 'dataset']

    TranslatablePageMove(session, 'about', 'contact', 'below').execute()
    assert ordering() == ['contact', 'about', 'dataset']

    TranslatablePageMove(session, 'dataset', 'contact', 'above').execute()
    assert ordering() == ['dataset', 'contact', 'about']

    TranslatablePageMove(session, 'contact', 'dataset', 'above').execute()
    assert ordering() == ['contact', 'dataset', 'about']

    # invalid
    TranslatablePageMove(session, 'contact', 'contact', 'above').execute()
    assert ordering() == ['contact', 'dataset', 'about']

    TranslatablePageMove(session, 'kontact', 'about', 'above').execute()
    assert ordering() == ['contact', 'dataset', 'about']

    TranslatablePageMove(session, 'about', 'kontact', 'above').execute()
    assert ordering() == ['contact', 'dataset', 'about']


def test_page_file(swissvotes_app):
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


def test_policy_area(session):
    policy_area = PolicyArea('1')
    assert repr(policy_area) == '1'
    assert policy_area.level == 1
    assert policy_area.descriptor == 1
    assert policy_area.descriptor_path == [1]
    assert policy_area.descriptor_decimal == Decimal('1')
    assert policy_area.label == 'd-1-1'
    assert policy_area.label_path == ['d-1-1']
    assert policy_area.html(DummyRequest()) == '<span>d-1-1</span>'

    policy_area = PolicyArea('1.12')
    assert repr(policy_area) == '1.12'
    assert policy_area.level == 2
    assert policy_area.descriptor == 12
    assert policy_area.descriptor_path == [1, 12]
    assert policy_area.descriptor_decimal == Decimal('1.2')
    assert policy_area.label == 'd-2-12'
    assert policy_area.label_path == ['d-1-1', 'd-2-12']
    assert policy_area.html(DummyRequest()) == '<span>d-1-1 &gt; d-2-12</span>'

    policy_area = PolicyArea('1.12.121')
    assert repr(policy_area) == '1.12.121'
    assert policy_area.level == 3
    assert policy_area.descriptor == 121
    assert policy_area.descriptor_path == [1, 12, 121]
    assert policy_area.descriptor_decimal == Decimal('1.21')
    assert policy_area.label == 'd-3-121'
    assert policy_area.label_path == ['d-1-1', 'd-2-12', 'd-3-121']
    assert policy_area.html(DummyRequest()) == (
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


def test_principal(session):
    principal = Principal()
    assert principal


def test_vote(session):
    vote = SwissVote()
    vote.bfs_number = Decimal('100.1')
    vote.date = date(1990, 6, 2)
    vote.decade = NumericRange(1990, 1999)
    vote.legislation_number = 4
    vote.legislation_decade = NumericRange(1990, 1994)
    vote.title = "Vote"
    vote.keyword = "Keyowrd"
    vote.votes_on_same_day = 2
    vote._legal_form = 1
    vote.initiator = "Initiator"
    vote.anneepolitique = "anneepolitique"
    vote.descriptor_1_level_1 = Decimal('4')
    vote.descriptor_1_level_2 = Decimal('4.2')
    vote.descriptor_1_level_3 = Decimal('4.21')
    vote.descriptor_2_level_1 = Decimal('10')
    vote.descriptor_2_level_2 = Decimal('10.3')
    vote.descriptor_2_level_3 = Decimal('10.35')
    vote.descriptor_3_level_1 = Decimal('10')
    vote.descriptor_3_level_2 = Decimal('10.3')
    vote.descriptor_3_level_3 = Decimal('10.33')
    vote._result = 1
    vote.result_eligible_voters = 2
    vote.result_votes_empty = 3
    vote.result_votes_invalid = 4
    vote.result_votes_valid = 5
    vote.result_votes_total = 6
    vote.result_turnout = Decimal('20.01')
    vote._result_people_accepted = 1
    vote.result_people_yeas = 8
    vote.result_people_nays = 9
    vote.result_people_yeas_p = Decimal('40.01')
    vote._result_cantons_accepted = 1
    vote.result_cantons_yeas = Decimal('1.5')
    vote.result_cantons_nays = Decimal('24.5')
    vote.result_cantons_yeas_p = Decimal('60.01')
    vote.result_ag_eligible_voters = 101
    vote.result_ag_votes_valid = 102
    vote.result_ag_votes_total = 103
    vote.result_ag_turnout = Decimal('10.40')
    vote.result_ag_yeas = 105
    vote.result_ag_nays = 107
    vote.result_ag_yeas_p = Decimal('10.80')
    vote._result_ag_accepted = 0
    vote.result_ai_eligible_voters = 101
    vote.result_ai_votes_valid = 102
    vote.result_ai_votes_total = 103
    vote.result_ai_turnout = Decimal('10.40')
    vote.result_ai_yeas = 105
    vote.result_ai_nays = 107
    vote.result_ai_yeas_p = Decimal('10.80')
    vote._result_ai_accepted = 0
    vote.result_ar_eligible_voters = 101
    vote.result_ar_votes_valid = 102
    vote.result_ar_votes_total = 103
    vote.result_ar_turnout = Decimal('10.40')
    vote.result_ar_yeas = 105
    vote.result_ar_nays = 107
    vote.result_ar_yeas_p = Decimal('10.80')
    vote._result_ar_accepted = 0
    vote.result_be_eligible_voters = 101
    vote.result_be_votes_valid = 102
    vote.result_be_votes_total = 103
    vote.result_be_turnout = Decimal('10.40')
    vote.result_be_yeas = 105
    vote.result_be_nays = 107
    vote.result_be_yeas_p = Decimal('10.80')
    vote._result_be_accepted = 0
    vote.result_bl_eligible_voters = 101
    vote.result_bl_votes_valid = 102
    vote.result_bl_votes_total = 103
    vote.result_bl_turnout = Decimal('10.40')
    vote.result_bl_yeas = 105
    vote.result_bl_nays = 107
    vote.result_bl_yeas_p = Decimal('10.80')
    vote._result_bl_accepted = 0
    vote.result_bs_eligible_voters = 101
    vote.result_bs_votes_valid = 102
    vote.result_bs_votes_total = 103
    vote.result_bs_turnout = Decimal('10.40')
    vote.result_bs_yeas = 105
    vote.result_bs_nays = 107
    vote.result_bs_yeas_p = Decimal('10.80')
    vote._result_bs_accepted = 0
    vote.result_fr_eligible_voters = 101
    vote.result_fr_votes_valid = 102
    vote.result_fr_votes_total = 103
    vote.result_fr_turnout = Decimal('10.40')
    vote.result_fr_yeas = 105
    vote.result_fr_nays = 107
    vote.result_fr_yeas_p = Decimal('10.80')
    vote._result_fr_accepted = 0
    vote.result_ge_eligible_voters = 101
    vote.result_ge_votes_valid = 102
    vote.result_ge_votes_total = 103
    vote.result_ge_turnout = Decimal('10.40')
    vote.result_ge_yeas = 105
    vote.result_ge_nays = 107
    vote.result_ge_yeas_p = Decimal('10.80')
    vote._result_ge_accepted = 0
    vote.result_gl_eligible_voters = 101
    vote.result_gl_votes_valid = 102
    vote.result_gl_votes_total = 103
    vote.result_gl_turnout = Decimal('10.40')
    vote.result_gl_yeas = 105
    vote.result_gl_nays = 107
    vote.result_gl_yeas_p = Decimal('10.80')
    vote._result_gl_accepted = 0
    vote.result_gr_eligible_voters = 101
    vote.result_gr_votes_valid = 102
    vote.result_gr_votes_total = 103
    vote.result_gr_turnout = Decimal('10.40')
    vote.result_gr_yeas = 105
    vote.result_gr_nays = 107
    vote.result_gr_yeas_p = Decimal('10.80')
    vote._result_gr_accepted = 0
    vote.result_ju_eligible_voters = 101
    vote.result_ju_votes_valid = 102
    vote.result_ju_votes_total = 103
    vote.result_ju_turnout = Decimal('10.40')
    vote.result_ju_yeas = 105
    vote.result_ju_nays = 107
    vote.result_ju_yeas_p = Decimal('10.80')
    vote._result_ju_accepted = 0
    vote.result_lu_eligible_voters = 101
    vote.result_lu_votes_valid = 102
    vote.result_lu_votes_total = 103
    vote.result_lu_turnout = Decimal('10.40')
    vote.result_lu_yeas = 105
    vote.result_lu_nays = 107
    vote.result_lu_yeas_p = Decimal('10.80')
    vote._result_lu_accepted = 0
    vote.result_ne_eligible_voters = 101
    vote.result_ne_votes_valid = 102
    vote.result_ne_votes_total = 103
    vote.result_ne_turnout = Decimal('10.40')
    vote.result_ne_yeas = 105
    vote.result_ne_nays = 107
    vote.result_ne_yeas_p = Decimal('10.80')
    vote._result_ne_accepted = 0
    vote.result_nw_eligible_voters = 101
    vote.result_nw_votes_valid = 102
    vote.result_nw_votes_total = 103
    vote.result_nw_turnout = Decimal('10.40')
    vote.result_nw_yeas = 105
    vote.result_nw_nays = 107
    vote.result_nw_yeas_p = Decimal('10.80')
    vote._result_nw_accepted = 0
    vote.result_ow_eligible_voters = 101
    vote.result_ow_votes_valid = 102
    vote.result_ow_votes_total = 103
    vote.result_ow_turnout = Decimal('10.40')
    vote.result_ow_yeas = 105
    vote.result_ow_nays = 107
    vote.result_ow_yeas_p = Decimal('10.80')
    vote._result_ow_accepted = 0
    vote.result_sg_eligible_voters = 101
    vote.result_sg_votes_valid = 102
    vote.result_sg_votes_total = 103
    vote.result_sg_turnout = Decimal('10.40')
    vote.result_sg_yeas = 105
    vote.result_sg_nays = 107
    vote.result_sg_yeas_p = Decimal('10.80')
    vote._result_sg_accepted = 0
    vote.result_sh_eligible_voters = 101
    vote.result_sh_votes_valid = 102
    vote.result_sh_votes_total = 103
    vote.result_sh_turnout = Decimal('10.40')
    vote.result_sh_yeas = 105
    vote.result_sh_nays = 107
    vote.result_sh_yeas_p = Decimal('10.80')
    vote._result_sh_accepted = 0
    vote.result_so_eligible_voters = 101
    vote.result_so_votes_valid = 102
    vote.result_so_votes_total = 103
    vote.result_so_turnout = Decimal('10.40')
    vote.result_so_yeas = 105
    vote.result_so_nays = 107
    vote.result_so_yeas_p = Decimal('10.80')
    vote._result_so_accepted = 0
    vote.result_sz_eligible_voters = 101
    vote.result_sz_votes_valid = 102
    vote.result_sz_votes_total = 103
    vote.result_sz_turnout = Decimal('10.40')
    vote.result_sz_yeas = 105
    vote.result_sz_nays = 107
    vote.result_sz_yeas_p = Decimal('10.80')
    vote._result_sz_accepted = 0
    vote.result_tg_eligible_voters = 101
    vote.result_tg_votes_valid = 102
    vote.result_tg_votes_total = 103
    vote.result_tg_turnout = Decimal('10.40')
    vote.result_tg_yeas = 105
    vote.result_tg_nays = 107
    vote.result_tg_yeas_p = Decimal('10.80')
    vote._result_tg_accepted = 0
    vote.result_ti_eligible_voters = 101
    vote.result_ti_votes_valid = 102
    vote.result_ti_votes_total = 103
    vote.result_ti_turnout = Decimal('10.40')
    vote.result_ti_yeas = 105
    vote.result_ti_nays = 107
    vote.result_ti_yeas_p = Decimal('10.80')
    vote._result_ti_accepted = 0
    vote.result_ur_eligible_voters = 101
    vote.result_ur_votes_valid = 102
    vote.result_ur_votes_total = 103
    vote.result_ur_turnout = Decimal('10.40')
    vote.result_ur_yeas = 105
    vote.result_ur_nays = 107
    vote.result_ur_yeas_p = Decimal('10.80')
    vote._result_ur_accepted = 0
    vote.result_vd_eligible_voters = 101
    vote.result_vd_votes_valid = 102
    vote.result_vd_votes_total = 103
    vote.result_vd_turnout = Decimal('10.40')
    vote.result_vd_yeas = 105
    vote.result_vd_nays = 107
    vote.result_vd_yeas_p = Decimal('10.80')
    vote._result_vd_accepted = 1
    vote.result_vs_eligible_voters = 101
    vote.result_vs_votes_valid = 102
    vote.result_vs_votes_total = 103
    vote.result_vs_turnout = Decimal('10.40')
    vote.result_vs_yeas = 105
    vote.result_vs_nays = 107
    vote.result_vs_yeas_p = Decimal('10.80')
    vote._result_vs_accepted = 1
    vote.result_zg_eligible_voters = 101
    vote.result_zg_votes_valid = 102
    vote.result_zg_votes_total = 103
    vote.result_zg_turnout = Decimal('10.40')
    vote.result_zg_yeas = 105
    vote.result_zg_nays = 107
    vote.result_zg_yeas_p = Decimal('10.80')
    vote._result_zg_accepted = 0
    vote.result_zh_eligible_voters = 101
    vote.result_zh_votes_valid = 102
    vote.result_zh_votes_total = 103
    vote.result_zh_turnout = Decimal('10.40')
    vote.result_zh_yeas = 105
    vote.result_zh_nays = 107
    vote.result_zh_yeas_p = Decimal('10.80')
    vote._department_in_charge = 1
    vote.procedure_number = Decimal('24.557')
    vote._position_federal_council = 1
    vote._position_parliament = 1
    vote._position_national_council = 1
    vote.position_national_council_yeas = 10
    vote.position_national_council_nays = 20
    vote._position_council_of_states = 1
    vote.position_council_of_states_yeas = 30
    vote.position_council_of_states_nays = 40
    vote.duration_federal_assembly = 30
    vote.duration_post_federal_assembly = 31
    vote.duration_initative_collection = 32
    vote.duration_initative_federal_council = 33
    vote.duration_initative_total = 34
    vote.duration_referendum_collection = 35
    vote.duration_referendum_total = 36
    vote.signatures_valid = 40
    vote.signatures_invalid = 41
    vote._recommendation_fdp = 1
    vote._recommendation_cvp = 1
    vote._recommendation_sps = 1
    vote._recommendation_svp = 1
    vote._recommendation_lps = 2
    vote._recommendation_ldu = 2
    vote._recommendation_evp = 2
    vote._recommendation_csp = 3
    vote._recommendation_pda = 3
    vote._recommendation_poch = 3
    vote._recommendation_gps = 4
    vote._recommendation_sd = 4
    vote._recommendation_rep = 4
    vote._recommendation_edu = 5
    vote._recommendation_fps = 5
    vote._recommendation_lega = 5
    vote._recommendation_kvp = 66
    vote._recommendation_glp = 66
    vote._recommendation_bdp = None
    vote._recommendation_mcg = 9999
    vote._recommendation_sav = 1
    vote._recommendation_eco = 2
    vote._recommendation_sgv = 3
    vote._recommendation_sbv_usp = 3
    vote._recommendation_sgb = 3
    vote._recommendation_travs = 3
    vote._recommendation_vsa = 9999
    vote.national_council_election_year = 1990
    vote.national_council_share_fdp = Decimal('01.10')
    vote.national_council_share_cvp = Decimal('02.10')
    vote.national_council_share_sp = Decimal('03.10')
    vote.national_council_share_svp = Decimal('04.10')
    vote.national_council_share_lps = Decimal('05.10')
    vote.national_council_share_ldu = Decimal('06.10')
    vote.national_council_share_evp = Decimal('07.10')
    vote.national_council_share_csp = Decimal('08.10')
    vote.national_council_share_pda = Decimal('09.10')
    vote.national_council_share_poch = Decimal('10.10')
    vote.national_council_share_gps = Decimal('11.10')
    vote.national_council_share_sd = Decimal('12.10')
    vote.national_council_share_rep = Decimal('13.10')
    vote.national_council_share_edu = Decimal('14.10')
    vote.national_council_share_fps = Decimal('15.10')
    vote.national_council_share_lega = Decimal('16.10')
    vote.national_council_share_kvp = Decimal('17.10')
    vote.national_council_share_glp = Decimal('18.10')
    vote.national_council_share_bdp = Decimal('19.10')
    vote.national_council_share_mcg = Decimal('20.20')
    vote.national_council_share_ubrige = Decimal('21.20')
    vote.national_council_share_yeas = Decimal('22.20')
    vote.national_council_share_nays = Decimal('23.20')
    vote.national_council_share_neutral = Decimal('24.20')
    vote.national_council_share_vague = Decimal('25.10')
    session.add(vote)
    session.flush()

    vote = session.query(SwissVote).one()
    assert vote.id == 1
    assert vote.bfs_number == Decimal('100.10')
    assert vote.date == date(1990, 6, 2)
    assert vote.decade == NumericRange(1990, 1999)
    assert vote.legislation_number == 4
    assert vote.legislation_decade == NumericRange(1990, 1994)
    assert vote.title == "Vote"
    assert vote.keyword == "Keyowrd"
    assert vote.votes_on_same_day == 2
    assert vote._legal_form == 1
    assert vote.legal_form == "Mandatory referendum"
    assert vote.initiator == "Initiator"
    assert vote.anneepolitique == "anneepolitique"
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
    assert vote.result_eligible_voters == 2
    assert vote.result_votes_empty == 3
    assert vote.result_votes_invalid == 4
    assert vote.result_votes_valid == 5
    assert vote.result_votes_total == 6
    assert vote.result_turnout == Decimal('20.01')
    assert vote._result_people_accepted == 1
    assert vote.result_people_accepted == "Accepted"
    assert vote.result_people_yeas == 8
    assert vote.result_people_nays == 9
    assert vote.result_people_yeas_p == Decimal('40.01')
    assert vote._result_cantons_accepted == 1
    assert vote.result_cantons_accepted == "Accepted"
    assert vote.result_cantons_yeas == Decimal('1.5')
    assert vote.result_cantons_nays == Decimal('24.5')
    assert vote.result_cantons_yeas_p == Decimal('60.01')
    assert vote.result_ag_eligible_voters == 101
    assert vote.result_ag_votes_valid == 102
    assert vote.result_ag_votes_total == 103
    assert vote.result_ag_turnout == Decimal('10.40')
    assert vote.result_ag_yeas == 105
    assert vote.result_ag_nays == 107
    assert vote.result_ag_yeas_p == Decimal('10.80')
    assert vote._result_ag_accepted == 0
    assert vote.result_ag_accepted == "Rejected"
    assert vote.result_ai_eligible_voters == 101
    assert vote.result_ai_votes_valid == 102
    assert vote.result_ai_votes_total == 103
    assert vote.result_ai_turnout == Decimal('10.40')
    assert vote.result_ai_yeas == 105
    assert vote.result_ai_nays == 107
    assert vote.result_ai_yeas_p == Decimal('10.80')
    assert vote._result_ai_accepted == 0
    assert vote.result_ai_accepted == "Rejected"
    assert vote.result_ar_eligible_voters == 101
    assert vote.result_ar_votes_valid == 102
    assert vote.result_ar_votes_total == 103
    assert vote.result_ar_turnout == Decimal('10.40')
    assert vote.result_ar_yeas == 105
    assert vote.result_ar_nays == 107
    assert vote.result_ar_yeas_p == Decimal('10.80')
    assert vote._result_ar_accepted == 0
    assert vote.result_ar_accepted == "Rejected"
    assert vote.result_be_eligible_voters == 101
    assert vote.result_be_votes_valid == 102
    assert vote.result_be_votes_total == 103
    assert vote.result_be_turnout == Decimal('10.40')
    assert vote.result_be_yeas == 105
    assert vote.result_be_nays == 107
    assert vote.result_be_yeas_p == Decimal('10.80')
    assert vote._result_be_accepted == 0
    assert vote.result_be_accepted == "Rejected"
    assert vote.result_bl_eligible_voters == 101
    assert vote.result_bl_votes_valid == 102
    assert vote.result_bl_votes_total == 103
    assert vote.result_bl_turnout == Decimal('10.40')
    assert vote.result_bl_yeas == 105
    assert vote.result_bl_nays == 107
    assert vote.result_bl_yeas_p == Decimal('10.80')
    assert vote._result_bl_accepted == 0
    assert vote.result_bl_accepted == "Rejected"
    assert vote.result_bs_eligible_voters == 101
    assert vote.result_bs_votes_valid == 102
    assert vote.result_bs_votes_total == 103
    assert vote.result_bs_turnout == Decimal('10.40')
    assert vote.result_bs_yeas == 105
    assert vote.result_bs_nays == 107
    assert vote.result_bs_yeas_p == Decimal('10.80')
    assert vote._result_bs_accepted == 0
    assert vote.result_bs_accepted == "Rejected"
    assert vote.result_fr_eligible_voters == 101
    assert vote.result_fr_votes_valid == 102
    assert vote.result_fr_votes_total == 103
    assert vote.result_fr_turnout == Decimal('10.40')
    assert vote.result_fr_yeas == 105
    assert vote.result_fr_nays == 107
    assert vote.result_fr_yeas_p == Decimal('10.80')
    assert vote._result_fr_accepted == 0
    assert vote.result_fr_accepted == "Rejected"
    assert vote.result_ge_eligible_voters == 101
    assert vote.result_ge_votes_valid == 102
    assert vote.result_ge_votes_total == 103
    assert vote.result_ge_turnout == Decimal('10.40')
    assert vote.result_ge_yeas == 105
    assert vote.result_ge_nays == 107
    assert vote.result_ge_yeas_p == Decimal('10.80')
    assert vote._result_ge_accepted == 0
    assert vote.result_ge_accepted == "Rejected"
    assert vote.result_gl_eligible_voters == 101
    assert vote.result_gl_votes_valid == 102
    assert vote.result_gl_votes_total == 103
    assert vote.result_gl_turnout == Decimal('10.40')
    assert vote.result_gl_yeas == 105
    assert vote.result_gl_nays == 107
    assert vote.result_gl_yeas_p == Decimal('10.80')
    assert vote._result_gl_accepted == 0
    assert vote.result_gl_accepted == "Rejected"
    assert vote.result_gr_eligible_voters == 101
    assert vote.result_gr_votes_valid == 102
    assert vote.result_gr_votes_total == 103
    assert vote.result_gr_turnout == Decimal('10.40')
    assert vote.result_gr_yeas == 105
    assert vote.result_gr_nays == 107
    assert vote.result_gr_yeas_p == Decimal('10.80')
    assert vote._result_gr_accepted == 0
    assert vote.result_gr_accepted == "Rejected"
    assert vote.result_ju_eligible_voters == 101
    assert vote.result_ju_votes_valid == 102
    assert vote.result_ju_votes_total == 103
    assert vote.result_ju_turnout == Decimal('10.40')
    assert vote.result_ju_yeas == 105
    assert vote.result_ju_nays == 107
    assert vote.result_ju_yeas_p == Decimal('10.80')
    assert vote._result_ju_accepted == 0
    assert vote.result_ju_accepted == "Rejected"
    assert vote.result_lu_eligible_voters == 101
    assert vote.result_lu_votes_valid == 102
    assert vote.result_lu_votes_total == 103
    assert vote.result_lu_turnout == Decimal('10.40')
    assert vote.result_lu_yeas == 105
    assert vote.result_lu_nays == 107
    assert vote.result_lu_yeas_p == Decimal('10.80')
    assert vote._result_lu_accepted == 0
    assert vote.result_lu_accepted == "Rejected"
    assert vote.result_ne_eligible_voters == 101
    assert vote.result_ne_votes_valid == 102
    assert vote.result_ne_votes_total == 103
    assert vote.result_ne_turnout == Decimal('10.40')
    assert vote.result_ne_yeas == 105
    assert vote.result_ne_nays == 107
    assert vote.result_ne_yeas_p == Decimal('10.80')
    assert vote._result_ne_accepted == 0
    assert vote.result_ne_accepted == "Rejected"
    assert vote.result_nw_eligible_voters == 101
    assert vote.result_nw_votes_valid == 102
    assert vote.result_nw_votes_total == 103
    assert vote.result_nw_turnout == Decimal('10.40')
    assert vote.result_nw_yeas == 105
    assert vote.result_nw_nays == 107
    assert vote.result_nw_yeas_p == Decimal('10.80')
    assert vote._result_nw_accepted == 0
    assert vote.result_nw_accepted == "Rejected"
    assert vote.result_ow_eligible_voters == 101
    assert vote.result_ow_votes_valid == 102
    assert vote.result_ow_votes_total == 103
    assert vote.result_ow_turnout == Decimal('10.40')
    assert vote.result_ow_yeas == 105
    assert vote.result_ow_nays == 107
    assert vote.result_ow_yeas_p == Decimal('10.80')
    assert vote._result_ow_accepted == 0
    assert vote.result_ow_accepted == "Rejected"
    assert vote.result_sg_eligible_voters == 101
    assert vote.result_sg_votes_valid == 102
    assert vote.result_sg_votes_total == 103
    assert vote.result_sg_turnout == Decimal('10.40')
    assert vote.result_sg_yeas == 105
    assert vote.result_sg_nays == 107
    assert vote.result_sg_yeas_p == Decimal('10.80')
    assert vote._result_sg_accepted == 0
    assert vote.result_sg_accepted == "Rejected"
    assert vote.result_sh_eligible_voters == 101
    assert vote.result_sh_votes_valid == 102
    assert vote.result_sh_votes_total == 103
    assert vote.result_sh_turnout == Decimal('10.40')
    assert vote.result_sh_yeas == 105
    assert vote.result_sh_nays == 107
    assert vote.result_sh_yeas_p == Decimal('10.80')
    assert vote._result_sh_accepted == 0
    assert vote.result_sh_accepted == "Rejected"
    assert vote.result_so_eligible_voters == 101
    assert vote.result_so_votes_valid == 102
    assert vote.result_so_votes_total == 103
    assert vote.result_so_turnout == Decimal('10.40')
    assert vote.result_so_yeas == 105
    assert vote.result_so_nays == 107
    assert vote.result_so_yeas_p == Decimal('10.80')
    assert vote._result_so_accepted == 0
    assert vote.result_so_accepted == "Rejected"
    assert vote.result_sz_eligible_voters == 101
    assert vote.result_sz_votes_valid == 102
    assert vote.result_sz_votes_total == 103
    assert vote.result_sz_turnout == Decimal('10.40')
    assert vote.result_sz_yeas == 105
    assert vote.result_sz_nays == 107
    assert vote.result_sz_yeas_p == Decimal('10.80')
    assert vote._result_sz_accepted == 0
    assert vote.result_sz_accepted == "Rejected"
    assert vote.result_tg_eligible_voters == 101
    assert vote.result_tg_votes_valid == 102
    assert vote.result_tg_votes_total == 103
    assert vote.result_tg_turnout == Decimal('10.40')
    assert vote.result_tg_yeas == 105
    assert vote.result_tg_nays == 107
    assert vote.result_tg_yeas_p == Decimal('10.80')
    assert vote._result_tg_accepted == 0
    assert vote.result_tg_accepted == "Rejected"
    assert vote.result_ti_eligible_voters == 101
    assert vote.result_ti_votes_valid == 102
    assert vote.result_ti_votes_total == 103
    assert vote.result_ti_turnout == Decimal('10.40')
    assert vote.result_ti_yeas == 105
    assert vote.result_ti_nays == 107
    assert vote.result_ti_yeas_p == Decimal('10.80')
    assert vote._result_ti_accepted == 0
    assert vote.result_ti_accepted == "Rejected"
    assert vote.result_ur_eligible_voters == 101
    assert vote.result_ur_votes_valid == 102
    assert vote.result_ur_votes_total == 103
    assert vote.result_ur_turnout == Decimal('10.40')
    assert vote.result_ur_yeas == 105
    assert vote.result_ur_nays == 107
    assert vote.result_ur_yeas_p == Decimal('10.80')
    assert vote._result_ur_accepted == 0
    assert vote.result_ur_accepted == "Rejected"
    assert vote.result_vd_eligible_voters == 101
    assert vote.result_vd_votes_valid == 102
    assert vote.result_vd_votes_total == 103
    assert vote.result_vd_turnout == Decimal('10.40')
    assert vote.result_vd_yeas == 105
    assert vote.result_vd_nays == 107
    assert vote.result_vd_yeas_p == Decimal('10.80')
    assert vote._result_vd_accepted == 1
    assert vote.result_vd_accepted == "Accepted"
    assert vote.result_vs_eligible_voters == 101
    assert vote.result_vs_votes_valid == 102
    assert vote.result_vs_votes_total == 103
    assert vote.result_vs_turnout == Decimal('10.40')
    assert vote.result_vs_yeas == 105
    assert vote.result_vs_nays == 107
    assert vote.result_vs_yeas_p == Decimal('10.80')
    assert vote._result_vs_accepted == 1
    assert vote.result_vs_accepted == "Accepted"
    assert vote.result_zg_eligible_voters == 101
    assert vote.result_zg_votes_valid == 102
    assert vote.result_zg_votes_total == 103
    assert vote.result_zg_turnout == Decimal('10.40')
    assert vote.result_zg_yeas == 105
    assert vote.result_zg_nays == 107
    assert vote.result_zg_yeas_p == Decimal('10.80')
    assert vote._result_zg_accepted == 0
    assert vote.result_zg_accepted == "Rejected"
    assert vote.result_zh_eligible_voters == 101
    assert vote.result_zh_votes_valid == 102
    assert vote.result_zh_votes_total == 103
    assert vote.result_zh_turnout == Decimal('10.40')
    assert vote.result_zh_yeas == 105
    assert vote.result_zh_nays == 107
    assert vote.result_zh_yeas_p == Decimal('10.80')
    assert vote._result_zh_accepted is None
    assert vote.result_zh_accepted is None
    assert vote._department_in_charge == 1
    assert vote.department_in_charge == \
        "Federal Department of Foreign Affairs (FDFA)"
    assert vote.procedure_number == Decimal('24.557')
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
    assert vote.duration_post_federal_assembly == 31
    assert vote.duration_initative_collection == 32
    assert vote.duration_initative_federal_council == 33
    assert vote.duration_initative_total == 34
    assert vote.duration_referendum_collection == 35
    assert vote.duration_referendum_total == 36
    assert vote.signatures_valid == 40
    assert vote.signatures_invalid == 41
    assert vote._recommendation_fdp == 1
    assert vote._recommendation_cvp == 1
    assert vote._recommendation_sps == 1
    assert vote._recommendation_svp == 1
    assert vote._recommendation_lps == 2
    assert vote._recommendation_ldu == 2
    assert vote._recommendation_evp == 2
    assert vote._recommendation_csp == 3
    assert vote._recommendation_pda == 3
    assert vote._recommendation_poch == 3
    assert vote._recommendation_gps == 4
    assert vote._recommendation_sd == 4
    assert vote._recommendation_rep == 4
    assert vote._recommendation_edu == 5
    assert vote._recommendation_fps == 5
    assert vote._recommendation_lega == 5
    assert vote._recommendation_kvp == 66
    assert vote._recommendation_glp == 66
    assert vote._recommendation_bdp is None
    assert vote._recommendation_mcg == 9999
    assert vote._recommendation_sav == 1
    assert vote._recommendation_eco == 2
    assert vote._recommendation_sgv == 3
    assert vote._recommendation_sbv_usp == 3
    assert vote._recommendation_sgb == 3
    assert vote._recommendation_travs == 3
    assert vote._recommendation_vsa == 9999
    assert vote.national_council_election_year == 1990
    assert vote.national_council_share_fdp == Decimal('01.10')
    assert vote.national_council_share_cvp == Decimal('02.10')
    assert vote.national_council_share_sp == Decimal('03.10')
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
    assert vote.national_council_share_ubrige == Decimal('21.20')
    assert vote.national_council_share_yeas == Decimal('22.20')
    assert vote.national_council_share_nays == Decimal('23.20')
    assert vote.national_council_share_neutral == Decimal('24.20')
    assert vote.national_council_share_vague == Decimal('25.10')

    assert vote.policy_areas == [
        PolicyArea('4.42.421'),
        PolicyArea('10.103.1035'),
        PolicyArea('10.103.1033')
    ]

    assert vote.results_cantons['Rejected'] == [
        Canton('ag'),
        Canton('ai'),
        Canton('ar'),
        Canton('be'),
        Canton('bl'),
        Canton('bs'),
        Canton('fr'),
        Canton('ge'),
        Canton('gl'),
        Canton('gr'),
        Canton('ju'),
        Canton('lu'),
        Canton('ne'),
        Canton('nw'),
        Canton('ow'),
        Canton('sg'),
        Canton('sh'),
        Canton('so'),
        Canton('sz'),
        Canton('tg'),
        Canton('ti'),
        Canton('ur'),
        Canton('zg'),
        # Canton('zh'),
    ]
    assert vote.results_cantons['Accepted'] == [
        Canton('vd'),
        Canton('vs'),
    ]

    assert list(vote.recommendations_parties.keys()) == [
        'Yea', 'Nay', 'None', 'Empty', 'Free vote', 'Neutral'
    ]
    assert vote.recommendations_parties['Yea'] == [
        Actor('cvp'),
        Actor('fdp'),
        Actor('sps'),
        Actor('svp'),
    ]
    assert vote.recommendations_parties['Nay'] == [
        Actor('evp'),
        Actor('ldu'),
        Actor('lps'),
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
        'Yea', 'Nay', 'None'
    ]
    assert vote.recommendations_associations['Yea'] == [Actor('sav')]
    assert vote.recommendations_associations['Nay'] == [Actor('eco')]
    assert vote.recommendations_associations['None'] == [
        Actor('sbv-usp'),
        Actor('sgb'),
        Actor('sgv'),
        Actor('travs'),
    ]

    assert vote.has_national_council_share_data is True


def test_vote_codes():
    assert SwissVote.codes('legal_form')[2] == "Optional referendum"
    assert SwissVote.codes('result')[0] == "Rejected"
    assert SwissVote.codes('result_people_accepted')[0] == "Rejected"
    assert SwissVote.codes('result_cantons_accepted')[0] == "Rejected"
    assert SwissVote.codes('result_ai_accepted')[1] == "Accepted"
    assert SwissVote.codes('department_in_charge')[8] == \
        "Federal Chancellery (FCh)"
    assert SwissVote.codes('position_federal_council')[3] == "Neutral"
    assert SwissVote.codes('position_parliament')[2] == "Rejecting"
    assert SwissVote.codes('position_national_council')[2] == "Rejecting"
    assert SwissVote.codes('position_council_of_states')[2] == "Rejecting"
    assert SwissVote.codes('recommendation')[5] == "Free vote"


def test_vote_attachments(swissvotes_app, attachments):
    session = swissvotes_app.session()
    session.add(
        SwissVote(
            bfs_number=Decimal('100.1'),
            date=date(1990, 6, 2),
            decade=NumericRange(1990, 1999),
            legislation_number=4,
            legislation_decade=NumericRange(1990, 1994),
            title="Vote",
            keyword="Keyowrd",
            votes_on_same_day=2,
            _legal_form=1,
        )
    )
    session.flush()

    vote = session.query(SwissVote).one()
    assert vote.voting_text is None
    assert vote.federal_council_message is None
    assert vote.parliamentary_debate is None
    assert vote.voting_booklet is None
    assert vote.resolution is None
    assert vote.realization is None
    assert vote.files == []
    assert vote.searchable_text_de_CH is None
    assert vote.searchable_text_fr_CH is None

    assert vote.indexed_files == {
        'federal_council_message',
        'parliamentary_debate',
        'realization',
        'voting_text',
    }

    vote.voting_text = attachments['voting_text']
    session.flush()

    assert len(vote.files) == 1
    assert vote.voting_text.name == 'voting_text-de_CH'
    assert "abstimmungstex" in vote.searchable_text_de_CH
    assert vote.searchable_text_fr_CH is None

    swissvotes_app.session_manager.current_locale = 'fr_CH'

    vote.realization = attachments['realization']
    session.flush()

    assert len(vote.files) == 2
    assert vote.voting_text is None
    assert vote.realization.name == 'realization-fr_CH'
    assert "réalis" in vote.searchable_text_fr_CH


def test_vote_percentages():
    # todo:
    pass
