from datetime import date
from decimal import Decimal
from io import BytesIO
from onegov.core.crypto import hash_password
from onegov.core.crypto import random_token
from onegov.file.utils import as_fileintent
from onegov.pdf import Pdf
from onegov.swissvotes import SwissvotesApp
from onegov.swissvotes.models import Principal
from onegov.swissvotes.models import SwissVote
from onegov.swissvotes.models import SwissVoteFile
from onegov.swissvotes.models import TranslatablePageFile
from onegov.user import User
from psycopg2.extras import NumericRange
from pytest import fixture
from tests.shared.utils import create_app
from tests.shared.utils import create_image
from transaction import commit
from xlsxwriter.workbook import Workbook


def create_swissvotes_app(request, temporary_path):
    app = create_app(
        SwissvotesApp,
        request,
        use_smtp=True,
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


@fixture(scope='session')
def swissvotes_password():
    return hash_password('hunter2')


@fixture(scope="function")
def principal():
    yield Principal()


@fixture(scope="function")
def swissvotes_app(request, temporary_path):
    app = create_swissvotes_app(request, temporary_path)
    yield app
    app.session_manager.dispose()


@fixture(scope="function")
def attachments(swissvotes_app):
    result = {}
    for name, content in (
        ('ad_analysis', "Inserateanalyse"),
        ('brief_description', "Kurschbeschreibung"),
        ('federal_council_message', "Message du Conseil fédéral"),
        ('foeg_analysis', "Medienanalyse fög"),
        ('parliamentary_debate', "Parlamentdebatte"),
        ('post_vote_poll_codebook', "Codebuch"),
        ('post_vote_poll_methodology', "Methodenbeschrieb"),
        ('post_vote_poll', "Nachbefragung"),
        ('preliminary_examination', "Voruntersuchung"),
        ('realization', "Réalisation"),
        ('resolution', "Arrêté constatant le résultat"),
        ('voting_booklet', "Brochure explicative"),
        ('voting_text', "Abstimmungstext"),
        ('post_vote_poll_report', "Technischer Bericht"),
    ):
        file = BytesIO()
        pdf = Pdf(file)
        pdf.init_report()
        pdf.p(content)
        pdf.generate()
        file.seek(0)

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

    yield result


@fixture(scope="function")
def campaign_material(swissvotes_app):
    result = {}

    for name in ('yea-1.png', 'yea-2.png', 'nay-1.png', 'nay-2.png'):
        name = f'campaign_material_{name}'
        file = create_image()

        attachment = SwissVoteFile(id=random_token(), name=name)
        attachment.reference = as_fileintent(file, name)
        result[name] = attachment

    yield result


@fixture(scope="function")
def slider_images(swissvotes_app):
    result = {}

    for name in ('1', '1-1', '2.1-x', '2.2-x', '2.3-x', 'n'):
        attachment = TranslatablePageFile(id=random_token())
        attachment.name = f'slider_images-{name}.png'
        attachment.reference = as_fileintent(create_image(), f'{name}.png')
        result[name] = attachment

    yield result


@fixture(scope="function")
def attachment_urls():
    yield {
        'de_CH': {
            'ad_analysis': 'inserateanalyse.pdf',
            'brief_description': 'kurzbeschreibung.pdf',
            'federal_council_message': 'botschaft-de.pdf',
            'foeg_analysis': 'medienanalyse.pdf',
            'parliamentary_debate': 'parlamentsberatung.pdf',
            'post_vote_poll_codebook': 'nachbefragung-codebuch-de.pdf',
            'post_vote_poll_codebook_xlsx': 'nachbefragung-codebuch-de.xlsx',
            'post_vote_poll_dataset': 'nachbefragung.csv',
            'post_vote_poll_dataset_sav': 'nachbefragung.sav',
            'post_vote_poll_dataset_dta': 'nachbefragung.dta',
            'post_vote_poll_methodology': 'nachbefragung-methode-de.pdf',
            'post_vote_poll_report': 'nachbefragung-technischer-bericht.pdf',
            'post_vote_poll': 'nachbefragung-de.pdf',
            'preliminary_examination': 'vorpruefung-de.pdf',
            'realization': 'zustandekommen-de.pdf',
            'resolution': 'erwahrung-de.pdf',
            'results_by_domain': 'staatsebenen.xlsx',
            'voting_booklet': 'brochure-de.pdf',
            'voting_text': 'abstimmungstext-de.pdf',
        },
        'fr_CH': {
            'federal_council_message': 'botschaft-fr.pdf',
            'post_vote_poll_codebook': 'nachbefragung-codebuch-fr.pdf',
            'post_vote_poll_codebook_xlsx': 'nachbefragung-codebuch-fr.xlsx',
            'post_vote_poll_methodology': 'nachbefragung-methode-fr.pdf',
            'post_vote_poll': 'nachbefragung-fr.pdf',
            'preliminary_examination': 'vorpruefung-fr.pdf',
            'realization': 'zustandekommen-fr.pdf',
            'resolution': 'erwahrung-fr.pdf',
            'voting_booklet': 'brochure-fr.pdf',
            'voting_text': 'abstimmungstext-fr.pdf',
        },
        'en_US': {}
    }


@fixture(scope='function')
def page_attachments_filenames():
    yield {
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


@fixture(scope="function")
def page_attachments(swissvotes_app, page_attachments_filenames):
    result = {}

    for locale in ('de_CH', 'fr_CH', 'en_US'):
        result[locale] = {}
        for name, content in (
            ('REFERENCES', 'Quellen'),
            ('CODEBOOK', 'Codebuch'),
        ):
            file = BytesIO()
            pdf = Pdf(file)
            pdf.init_report()
            pdf.p(content)
            pdf.generate()
            file.seek(0)

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

    yield result


@fixture(scope="function")
def page_attachment_urls():
    yield {
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


@fixture(scope="function")
def postgres_version(session):
    connection = session.connection()
    yield connection.execute('show server_version;').fetchone()[0]


@fixture(scope="function")
def sample_vote():
    vote = SwissVote()
    vote.bfs_number = Decimal('100.1')
    vote.date = date(1990, 6, 2)
    vote.legislation_number = 4
    vote.legislation_decade = NumericRange(1990, 1994)
    vote.title_de = "Vote DE"
    vote.title_fr = "Vote FR"
    vote.short_title_de = "V D"
    vote.short_title_fr = "V F"
    vote.keyword = "Keyword"
    vote.votes_on_same_day = 2
    vote._legal_form = 1
    vote.initiator = "Initiator"
    vote.anneepolitique = "anneepolitique"
    vote.bfs_map_de = (
        "https://www.atlas.bfs.admin.ch/maps/12/map/mapIdOnly/1815_de.html"
    )
    vote.bfs_map_fr = "htt(ps://www.ap/mapIdOnly/1815[e.html}"
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
    vote.posters_sa_yea = (
        'https://yes.com/objects/3 '
        'https://yes.com/objects/4'
    )
    vote.posters_sa_nay = (
        'https://no.com/objects/3 '
        'https://no.com/objects/4'
    )
    vote.posters_sa_nay_imgs = {
        'https://no.com/objects/3': 'https://detail.com/3'
    }
    vote.curia_vista_de = 'cv_de'
    vote.curia_vista_fr = 'cv_fr'
    vote.bkresults_de = 'bkr_de'
    vote.bkresults_fr = 'bkr_fr'
    vote.bkchrono_de = 'bkc_de'
    vote.bkchrono_fr = 'bkc_fr'
    vote.swissvoteslink = 'https://example.com/122.0'
    vote.post_vote_poll_link_de = 'https://post.vote.poll/de'
    vote.post_vote_poll_link_fr = 'https://post.vote.poll/fr'
    vote.post_vote_poll_link_en = 'https://post.vote.poll/en'
    vote.media_ads_total = 3001
    vote.media_ads_per_issue = Decimal('30.02')
    vote.media_ads_yea = 3003
    vote.media_ads_nay = 3004
    vote.media_ads_neutral = 3005
    vote.media_ads_yea_p = Decimal('30.06')
    vote.media_coverage_articles_total = 3007
    vote.media_coverage_articles_d = 3008
    vote.media_coverage_articles_f = 3009
    vote.media_coverage_tonality_total = Decimal('30.10')
    vote.media_coverage_tonality_d = Decimal('30.11')
    vote.media_coverage_tonality_f = Decimal('30.12')
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
    vote.duration_post_federal_assembly = 31
    vote.duration_initative_collection = 32
    vote.duration_initative_federal_council = 33
    vote.duration_initative_total = 34
    vote.duration_referendum_collection = 35
    vote.duration_referendum_total = 36
    vote.signatures_valid = 40
    vote.signatures_invalid = 41
    vote.recommendations = {
        'fdp': 1,
        'cvp': 1,
        'sps': 1,
        'svp': 1,
        'lps': 2,
        'ldu': 2,
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
        'acs': 1,
        'tcs': 1,
        'vcs': 1,
        'voev': 1
    }
    vote.recommendations_other_yes = "Pro Velo"
    vote.recommendations_other_no = None
    vote.recommendations_other_free = "Pro Natura, Greenpeace"
    vote.recommendations_divergent = {
        'edu_vso': 1,
        'fdp_ti': 1,
        'fdp-fr_ch': 2,
        'jcvp_ch': 2,
    }
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
    vote.national_council_share_mitte = Decimal('20.10')
    vote.national_council_share_ubrige = Decimal('21.20')
    vote.national_council_share_yeas = Decimal('22.20')
    vote.national_council_share_nays = Decimal('23.20')
    vote.national_council_share_neutral = Decimal('24.20')
    vote.national_council_share_none = Decimal('25.20')
    vote.national_council_share_empty = Decimal('26.20')
    vote.national_council_share_free_vote = Decimal('27.20')
    vote.national_council_share_unknown = Decimal('28.20')
    vote.national_council_share_vague = Decimal('28.20')
    return vote
