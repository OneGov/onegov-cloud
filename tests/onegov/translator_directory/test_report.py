import os
from uuid import uuid4

import transaction

from onegov.file import FileCollection
from onegov.translator_directory.models.translator import Translator
from onegov.translator_directory.report import TranslatorVoucher
from tests.onegov.translator_directory.shared import translator_data
from tests.shared.utils import create_image


def test_translator_voucher(client):
    app = client.app
    translator = Translator(**translator_data)
    files = FileCollection(app.session())
    file_id = files.add('logo.png', create_image()).id
    transaction.commit()
    file = files.by_id(file_id)

    class FakeRequest:

        app = client.app
        is_manager = False
        is_admin = True
        is_member = False

        def translate(self, value):
            return value

        def include(self, value):
            pass

    excerpt_path = os.path.join(app.static_files[0], 'law_zug.png')
    logo_path = os.path.join(app.static_files[0], 'logo_abrechnungsexcel.png')

    voucher = TranslatorVoucher(
        FakeRequest(),
        translator,
        logo=logo_path,
        law_excerpt_path=excerpt_path
    )

    xlsx = voucher.create_document(protect_pw=str(uuid4()))
