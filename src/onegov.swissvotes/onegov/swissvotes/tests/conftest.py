from io import BytesIO
from onegov_testing.utils import create_app
from onegov.core.crypto import hash_password
from onegov.core.crypto import random_token
from onegov.file.utils import as_fileintent
from onegov.pdf import Pdf
from onegov.swissvotes import SwissvotesApp
from onegov.swissvotes.models import Principal
from onegov.swissvotes.models import SwissVoteFile
from onegov.user import User
from pytest import fixture
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
        ('parliamentary_debate', "Parlamentdebatte"),
        ('realization', "Réalisation"),
        ('resolution', "Arrêté constatant le résultat"),
        ('voting_booklet', "Brochure explicative"),
        ('voting_text', "Abstimmungstext"),
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
    ):
        file = BytesIO()
        workbook = Workbook(file)
        worksheet = workbook.add_worksheet()
        worksheet.write_row(0, 0, ['a', 'b'])
        worksheet.write_row(1, 0, [100, 200])
        workbook.close()
        file.seek(0)

        attachment = SwissVoteFile(id=random_token())
        attachment.reference = as_fileintent(file, name)
        result[name] = attachment

    yield result


@fixture(scope="function")
def postgres_version(session):
    connection = session.connection()
    yield connection.execute('show server_version;').fetchone()[0]
