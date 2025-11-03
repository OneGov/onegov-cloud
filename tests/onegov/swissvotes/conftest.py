from __future__ import annotations

import pytest

from datetime import date
from decimal import Decimal
from io import BytesIO
from onegov.core.crypto import hash_password
from onegov.core.crypto import random_token
from onegov.core.orm.observer import ScopedPropertyObserver
from onegov.file.utils import as_fileintent
from onegov.pdf import Pdf
from onegov.swissvotes import SwissvotesApp
from onegov.swissvotes.models import Principal
from onegov.swissvotes.models import SwissVote
from onegov.swissvotes.models import SwissVoteFile
from onegov.swissvotes.models import TranslatablePageFile
from onegov.user import User
from tests.shared.utils import create_app
from tests.shared.utils import create_image
from transaction import commit
from xlsxwriter.workbook import Workbook


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from sqlalchemy.orm import Session


class TestApp(SwissvotesApp):
    __test__ = False
    maildir: str


def create_swissvotes_app(
    request: pytest.FixtureRequest,
    temporary_path: str
) -> TestApp:

    app = create_app(
        TestApp,
        request,
        use_maildir=True,
        depot_backend='depot.io.local.LocalFileStorage',
        depot_storage_path=str(temporary_path),
    )
    app.session_manager.set_locale('de_CH', 'de_CH')

    session = app.session()
    session.add(User(
        username='admin@example.org',
        password_hash=request.getfixturevalue('swissvotes_password'),
        role='admin'
    ))
    session.add(User(
        realname='Publisher',
        username='publisher@example.org',
        password_hash=request.getfixturevalue('swissvotes_password'),
        role='editor'
    ))
    session.add(User(
        realname='Editor',
        username='editor@example.org',
        password_hash=request.getfixturevalue('swissvotes_password'),
        role='member'
    ))

    commit()
    return app


def create_pdf(content: str) -> BytesIO:
    result = BytesIO()
    pdf = Pdf(result)
    pdf.init_report()
    pdf.p(content)
    pdf.generate()
    result.seek(0)
    return result


@pytest.fixture(scope='session')
def swissvotes_password() -> str:
    return hash_password('hunter2')


@pytest.fixture(scope="function")
def principal() -> Principal:
    return Principal()


@pytest.fixture(scope="function")
def swissvotes_app(
    request: pytest.FixtureRequest,
    temporary_path: str
) -> Iterator[TestApp]:
    app = create_swissvotes_app(request, temporary_path)
    yield app
    app.session_manager.dispose()


@pytest.fixture(scope="function")
def attachments(swissvotes_app: TestApp) -> dict[str, SwissVoteFile]:
    result = {}
    for name, content in (
        ('ad_analysis', "Inserateanalyse"),
        ('brief_description', "Kurzbeschreibung"),
        ('easyvote_booklet', "easyvote"),
        ('federal_council_message', "Message du Conseil fédéral"),
        ('foeg_analysis', "Medienanalyse fög"),
        ('parliamentary_initiative', "Initiative"),
        ('parliamentary_committee_report', "Bericht"),
        ('federal_council_opinion', "Stellungnahme"),
        ('parliamentary_debate', "Parlamentdebatte"),
        ('post_vote_poll_codebook', "Codebuch"),
        ('post_vote_poll_methodology', "Methodenbeschrieb"),
        ('post_vote_poll_report', "Technischer Bericht"),
        ('post_vote_poll', "Nachbefragung"),
        ('preliminary_examination', "Voruntersuchung"),
        ('realization', "Réalisation"),
        ('resolution', "Arrêté constatant le résultat"),
        ('voting_booklet', "Brochure explicative"),
        ('voting_text', "Abstimmungstext"),
    ):
        file = create_pdf(content)
        attachment = SwissVoteFile(id=random_token())
        attachment.reference = as_fileintent(file, name)
        result[name] = attachment

    for name in (
        'results_by_domain',
        'post_vote_poll_codebook_xlsx'
    ):
        file = BytesIO()
        workbook = Workbook(file)
        worksheet = workbook.add_worksheet('DATA')
        worksheet.write_row(0, 0, ['a', 'b'])
        worksheet.write_row(1, 0, [100, 200])
        workbook.close()
        file.seek(0)

        attachment = SwissVoteFile(id=random_token())
        attachment.reference = as_fileintent(file, name)
        result[name] = attachment

    for name in (
        'post_vote_poll_dataset',
    ):
        file = BytesIO()
        file.write(b'a,b\n100,200')

        attachment = SwissVoteFile(id=random_token())
        attachment.reference = as_fileintent(file, name)
        result[name] = attachment

    for name in (
        'post_vote_poll_dataset_sav',
    ):
        file = BytesIO()
        file.write(b'$FL2@(#) SPSS DATA FILE MS Windows Release 12.0 \x02')

        attachment = SwissVoteFile(id=random_token())
        attachment.reference = as_fileintent(file, name)
        result[name] = attachment

    for name in (
        'post_vote_poll_dataset_dta',
    ):
        file = BytesIO()
        file.write(b'<stata_dta><header><release>117</release> \x02')

        attachment = SwissVoteFile(id=random_token())
        attachment.reference = as_fileintent(file, name)
        result[name] = attachment

    return result


@pytest.fixture(scope="function")
def campaign_material(swissvotes_app: TestApp) -> dict[str, SwissVoteFile]:
    result = {}

    for name in ('yea-1.png', 'yea-2.png', 'nay-1.png', 'nay-2.png'):
        name = f'campaign_material_{name}'
        file = create_image()

        attachment = SwissVoteFile(id=random_token(), name=name)
        attachment.reference = as_fileintent(file, name)
        result[name] = attachment

    for name, content in (
        ('essay', 'Abhandlung'),
        ('leaflet', 'Volantino'),
        ('article', 'Article'),
        ('legal', 'Juridique'),
    ):
        name = f'campaign_material_other-{name}.pdf'
        file = create_pdf(content)
        attachment = SwissVoteFile(id=random_token(), name=name)
        attachment.reference = as_fileintent(file, name)
        result[name] = attachment

    return result


@pytest.fixture(scope="function")
def slider_images(swissvotes_app: TestApp) -> dict[str, TranslatablePageFile]:
    result = {}

    for name in ('1', '1-1', '2.1-x', '2.2-x', '2.3-x', 'n'):
        attachment = TranslatablePageFile(id=random_token())
        attachment.name = f'slider_images-{name}.png'
        attachment.reference = as_fileintent(create_image(), f'{name}.png')
        result[name] = attachment

    return result


@pytest.fixture(scope="function")
def attachment_urls() -> dict[str, dict[str, str]]:
    return {
        'de_CH': {
            'ad_analysis': 'inserateanalyse.pdf',
            'brief_description': 'kurzbeschreibung-de.pdf',
            'easyvote_booklet': 'easyvote-de.pdf',
            'federal_council_message': 'botschaft-de.pdf',
            'foeg_analysis': 'medienanalyse.pdf',
            'parliamentary_initiative': 'parlamentarische-initiative-de.pdf',
            'parliamentary_committee_report':
            'bericht-parlamentarische-kommission-de.pdf',
            'federal_council_opinion': 'stellungnahme-bundesrat-de.pdf',
            'parliamentary_debate': 'parlamentsberatung.pdf',
            'post_vote_poll_codebook_xlsx': 'nachbefragung-codebuch-de.xlsx',
            'post_vote_poll_codebook': 'nachbefragung-codebuch-de.pdf',
            'post_vote_poll_dataset_dta': 'nachbefragung.dta',
            'post_vote_poll_dataset_sav': 'nachbefragung.sav',
            'post_vote_poll_dataset': 'nachbefragung.csv',
            'post_vote_poll_methodology': 'nachbefragung-methode-de.pdf',
            'post_vote_poll_report': 'nachbefragung-technischer-bericht.pdf',
            'post_vote_poll': 'nachbefragung-de.pdf',
            'preliminary_examination': 'vorpruefung-de.pdf',
            'realization': 'zustandekommen-de.pdf',
            'resolution': 'erwahrung-de.pdf',
            'results_by_domain': 'staatsebenen-de.xlsx',
            'voting_booklet': 'brochure-de.pdf',
            'voting_text': 'abstimmungstext-de.pdf',
        },
        'fr_CH': {
            'brief_description': 'kurzbeschreibung-fr.pdf',
            'easyvote_booklet': 'easyvote-fr.pdf',
            'parliamentary_initiative': 'parlamentarische-initiative-fr.pdf',
            'parliamentary_committee_report':
            'bericht-parlamentarische-kommission-fr.pdf',
            'federal_council_opinion': 'stellungnahme-bundesrat-fr.pdf',
            'federal_council_message': 'botschaft-fr.pdf',
            'post_vote_poll_codebook_xlsx': 'nachbefragung-codebuch-fr.xlsx',
            'post_vote_poll_codebook': 'nachbefragung-codebuch-fr.pdf',
            'post_vote_poll_methodology': 'nachbefragung-methode-fr.pdf',
            'post_vote_poll': 'nachbefragung-fr.pdf',
            'preliminary_examination': 'vorpruefung-fr.pdf',
            'realization': 'zustandekommen-fr.pdf',
            'resolution': 'erwahrung-fr.pdf',
            'results_by_domain': 'staatsebenen-fr.xlsx',
            'voting_booklet': 'brochure-fr.pdf',
            'voting_text': 'abstimmungstext-fr.pdf',
        },
        'en_US': {}
    }


@pytest.fixture(scope='function')
def page_attachments_filenames() -> dict[str, dict[str, str]]:
    return {
        'de_CH': {
            'CODEBOOK': 'CODEBOOK.pdf',
            'DATASET CSV': 'DATASET CSV dd-mm-yyyy.csv',
            'DATASET XLSX': 'DATASET XLSX dd-mm-yyyy.xlsx',
            'REFERENCES': 'QUELLEN Kurzbeschreibungen.pdf',
        },
        'fr_CH': {
            'CODEBOOK': 'CODEBOOK.pdf',
            'DATASET CSV': 'DATASET CSV dd-mm-yyyy.csv',
            'DATASET XLSX': 'DATASET XLSX dd-mm-yyyy.xlsx',
            'REFERENCES': 'REFERENCES des descriptifs.pdf',
        },
        'en_US': {
            'CODEBOOK': 'CODEBOOK.pdf',
            'DATASET CSV': 'DATASET CSV dd-mm-yyyy.csv',
            'DATASET XLSX': 'DATASET XLSX dd-mm-yyyy.xlsx',
            'REFERENCES': 'REFERENCES for descriptions.pdf',
        }
    }


@pytest.fixture(scope="function")
def page_attachments(
    swissvotes_app: TestApp,
    page_attachments_filenames: dict[str, dict[str, str]]
) -> dict[str, dict[str, TranslatablePageFile]]:

    result: dict[str, dict[str, TranslatablePageFile]] = {}

    for locale in ('de_CH', 'fr_CH', 'en_US'):
        result[locale] = {}
        for name, content in (
            ('REFERENCES', 'Quellen'),
            ('CODEBOOK', 'Codebuch'),
        ):
            file = create_pdf(content)
            filename = page_attachments_filenames[locale][name]
            attachment = TranslatablePageFile(
                id=random_token(),
                name=f'{locale}-{filename}'
            )
            attachment.reference = as_fileintent(file, filename)
            result[locale][name] = attachment

        for name in ('DATASET XLSX',):
            file = BytesIO()
            workbook = Workbook(file)
            worksheet = workbook.add_worksheet('DATA')
            worksheet.write_row(0, 0, ['a', 'b'])
            worksheet.write_row(1, 0, [100, 200])
            workbook.close()
            file.seek(0)

            filename = page_attachments_filenames[locale][name]
            attachment = TranslatablePageFile(
                id=random_token(),
                name=f'{locale}-{filename}'
            )
            attachment.reference = as_fileintent(file, filename)
            result[locale][name] = attachment

        for name in ('DATASET CSV',):
            file = BytesIO()
            file.write(b'a,b\n100,200')

            filename = page_attachments_filenames[locale][name]
            attachment = TranslatablePageFile(
                id=random_token(),
                name=f'{locale}-{filename}'
            )
            attachment.reference = as_fileintent(file, filename)
            result[locale][name] = attachment

    return result


@pytest.fixture(scope="function")
def page_attachment_urls() -> dict[str, dict[str, str]]:
    return {
        'de_CH': {
            'CODEBOOK': 'codebook-de.pdf',
            'DATASET CSV': 'swissvotes_dataset.csv',
            'DATASET XLSX': 'swissvotes_dataset.xlsx',
            'REFERENCES': 'kurzbeschreibung-de.pdf',
        },
        'fr_CH': {
            'CODEBOOK': 'codebook-fr.pdf',
            'REFERENCES': 'kurzbeschreibung-fr.pdf',
        },
        'en_US': {
            'CODEBOOK': 'codebook-en.pdf',
            'REFERENCES': 'kurzbeschreibung-en.pdf',
        }
    }


@pytest.fixture(scope="function")
def postgres_version(session: Session) -> str:
    connection = session.connection()
    return connection.execute('show server_version;').fetchone()[0]


@pytest.fixture(scope="function")
def sample_vote() -> SwissVote:
    vote = SwissVote()
    vote.bfs_number = Decimal('100.1')
    vote.date = date(1990, 6, 2)
    vote.title_de = "Vote DE"
    vote.title_fr = "Vote FR"
    vote.short_title_de = "V D"
    vote.short_title_fr = "V F"
    vote.short_title_en = "V E"
    vote.keyword = "Keyword"
    vote._legal_form = 1
    vote._parliamentary_initiated = 0
    vote.initiator_de = "Initiator D"
    vote.initiator_fr = "Initiator F"
    vote.anneepolitique = "anneepolitique"
    vote.bfs_map_de = (
        "https://www.atlas.bfs.admin.ch/maps/12/map/mapIdOnly/1815_de.html"
    )
    vote.bfs_map_fr = "htt(ps://www.ap/mapIdOnly/1815[e.html}"
    vote.bfs_map_en = (
        "https://abstimmungen.admin.ch/en/details?proposalId=6660"
    )
    vote.bfs_dashboard_de = "https://dashboard.de"
    vote.bfs_dashboard_fr = "https://dashboard.fr"
    vote.bfs_dashboard_en = "https://dashboard.en"
    vote.posters_mfg_yea = (
        'https://yes.com/objects/1 '
        'https://yes.com/objects/2'
    )
    vote.posters_mfg_nay = (
        'https://no.com/objects/1 '
        'https://no.com/objects/2'
    )
    vote.posters_mfg_yea_imgs = {
        'https://yes.com/objects/1': 'https://detail.com/1'
    }
    vote.posters_bs_yea = (
        'https://yes.com/objects/5 '
        'https://yes.com/objects/6'
    )
    vote.posters_bs_nay = (
        'https://no.com/objects/5 '
        'https://no.com/objects/6'
    )
    vote.posters_bs_yea_imgs = {
        'https://yes.com/objects/5': 'https://detail.com/5'
    }
    vote.posters_bs_nay_imgs = {
        'https://no.com/objects/6': 'https://detail.com/6'
    }
    vote.posters_sa_yea = (
        'https://yes.com/objects/3 '
        'https://yes.com/objects/4'
    )
    vote.posters_sa_nay = (
        'https://no.com/objects/4 '
        'https://no.com/objects/3'
    )
    vote.posters_sa_nay_imgs = {
        'https://no.com/objects/3': 'https://detail.com/3',
        'https://no.com/objects/4': 'https://detail.com/4'
    }
    vote.link_curia_vista_de = 'https://curia.vista/de'
    vote.link_curia_vista_fr = 'https://curia.vista/fr'
    vote.link_easyvote_de = 'https://easy.vote/de'
    vote.link_easyvote_fr = 'https://easy.vote/fr'
    vote.link_bk_results_de = 'https://bk.results/de'
    vote.link_bk_results_fr = 'https://bk.results/fr'
    vote.link_bk_chrono_de = 'https://bk.chrono/de'
    vote.link_bk_chrono_fr = 'https://bk.chrono/fr'
    vote.link_federal_council_de = 'https://federal.council/de'
    vote.link_federal_council_fr = 'https://federal.council/fr'
    vote.link_federal_council_en = 'https://federal.council/en'
    vote.link_federal_departement_de = 'https://federal.departement/de'
    vote.link_federal_departement_fr = 'https://federal.departement/fr'
    vote.link_federal_departement_en = 'https://federal.departement/en'
    vote.link_federal_office_de = 'https://federal.office/de'
    vote.link_federal_office_fr = 'https://federal.office/fr'
    vote.link_federal_office_en = 'https://federal.office/en'
    vote.link_post_vote_poll_de = 'https://post.vote.poll/de'
    vote.link_post_vote_poll_fr = 'https://post.vote.poll/fr'
    vote.link_post_vote_poll_en = 'https://post.vote.poll/en'
    vote.link_campaign_yes_1_de = 'https://yes1.de'
    vote.link_campaign_yes_2_de = 'https://yes2.de'
    vote.link_campaign_yes_3_de = 'https://yes3.de'
    vote.link_campaign_no_1_de = 'https://no1.de'
    vote.link_campaign_no_2_de = 'https://no2.de'
    vote.link_campaign_no_3_de = 'https://no3.de'
    vote.link_campaign_yes_1_fr = 'https://yes1.fr'
    vote.link_campaign_yes_2_fr = 'https://yes2.fr'
    vote.link_campaign_yes_3_fr = 'https://yes3.fr'
    vote.link_campaign_no_1_fr = 'https://no1.fr'
    vote.link_campaign_no_2_fr = 'https://no2.fr'
    vote.link_campaign_no_3_fr = 'https://no3.fr'
    vote.media_ads_total = 3001
    vote.media_ads_yea_p = Decimal('30.06')
    vote.media_coverage_articles_total = 3007
    vote.media_coverage_tonality_total = Decimal('30.10')
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
    vote.result_turnout = Decimal('20.01')
    vote._result_people_accepted = 1
    vote.result_people_yeas_p = Decimal('40.01')
    vote._result_cantons_accepted = 1
    vote.result_cantons_yeas = Decimal('1.5')
    vote.result_cantons_nays = Decimal('24.5')
    vote._result_ag_accepted = 0
    vote._result_ai_accepted = 0
    vote._result_ar_accepted = 0
    vote._result_be_accepted = 0
    vote._result_bl_accepted = 0
    vote._result_bs_accepted = 0
    vote._result_fr_accepted = 0
    vote._result_ge_accepted = 0
    vote._result_gl_accepted = 0
    vote._result_gr_accepted = 0
    vote._result_ju_accepted = 0
    vote._result_lu_accepted = 0
    vote._result_ne_accepted = 0
    vote._result_nw_accepted = 0
    vote._result_ow_accepted = 0
    vote._result_sg_accepted = 0
    vote._result_sh_accepted = 0
    vote._result_so_accepted = 0
    vote._result_sz_accepted = 0
    vote._result_tg_accepted = 0
    vote._result_ti_accepted = 0
    vote._result_ur_accepted = 0
    vote._result_vd_accepted = 1
    vote._result_vs_accepted = 1
    vote._result_zg_accepted = 0
    vote.procedure_number = '24.557'
    vote._position_federal_council = 1
    vote._position_parliament = 1
    vote._position_national_council = 1
    vote.position_national_council_yeas = 10
    vote.position_national_council_nays = 20
    vote._position_council_of_states = 1
    vote.position_council_of_states_yeas = 30
    vote.position_council_of_states_nays = 40
    vote.duration_federal_assembly = 30
    vote.duration_initative_collection = 32
    vote.duration_referendum_collection = 35
    vote.signatures_valid = 40
    vote.recommendations = {
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
    vote.recommendations_other_yes_de = "Pro Velo D"
    vote.recommendations_other_yes_fr = "Pro Velo F"
    vote.recommendations_other_no_de = None
    vote.recommendations_other_no_fr = None
    vote.recommendations_other_free_de = "Pro Natura D, Greenpeace D"
    vote.recommendations_other_free_fr = "Pro Natura F, Greenpeace F"
    vote.recommendations_other_counter_proposal_de = "Pro Juventute D"
    vote.recommendations_other_counter_proposal_fr = "Pro Juventute F"
    vote.recommendations_other_popular_initiative_de = "Pro Senectute D"
    vote.recommendations_other_popular_initiative_fr = "Pro Senectute F"
    vote.recommendations_divergent = {
        'edu_vso': 1,
        'fdp_ti': 1,
        'fdp-fr_ch': 2,
        'jcvp_ch': 2,
    }
    vote.national_council_election_year = 1990
    vote.national_council_share_fdp = Decimal('01.10')
    vote.national_council_share_cvp = Decimal('02.10')
    vote.national_council_share_sps = Decimal('03.10')
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
    vote.national_council_share_mitte = Decimal('20.10')
    vote.national_council_share_ubrige = Decimal('21.20')
    vote.national_council_share_yeas = Decimal('22.20')
    vote.national_council_share_nays = Decimal('23.20')
    vote.national_council_share_neutral = Decimal('24.20')
    vote.national_council_share_none = Decimal('25.20')
    vote.national_council_share_empty = Decimal('26.20')
    vote.national_council_share_free_vote = Decimal('27.20')
    vote.national_council_share_unknown = Decimal('28.20')
    vote.campaign_material_metadata = {
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
    vote.campaign_finances_yea_total = 10000
    vote.campaign_finances_nay_total = 20000
    vote.campaign_finances_yea_donors_de = 'Donor 1 D, Donor 2 D'
    vote.campaign_finances_yea_donors_fr = 'Donor 1 F, Donor 2 F'
    vote.campaign_finances_nay_donors_de = 'Donor D'
    vote.campaign_finances_nay_donors_fr = 'Donor F'
    vote.campaign_finances_link_de = 'https://finances.de'
    vote.campaign_finances_link_fr = 'https://finances.fr'
    return vote


@pytest.fixture(scope="session", autouse=True)
def enter_observer_scope() -> None:
    """Ensures app specific observers are active"""
    ScopedPropertyObserver.enter_class_scope(SwissvotesApp)
