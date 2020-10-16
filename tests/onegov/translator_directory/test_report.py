from io import BytesIO
import transaction

from onegov.file import FileCollection
from onegov.translator_directory.models.translator import Translator
from onegov.translator_directory.report import TranslatorVoucher
from tests.onegov.translator_directory.shared import translator_data
from tests.shared.utils import open_in_excel, create_image


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

    voucher = TranslatorVoucher(
        FakeRequest(),
        translator,
        logo=BytesIO(file.reference.file.read())
    )

    xlsx = voucher.create_document()
    open_in_excel(xlsx)
