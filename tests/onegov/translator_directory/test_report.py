import pytest

from onegov.translator_directory.models.translator import Translator
from onegov.translator_directory.report import TranslatorVoucher
from tests.onegov.translator_directory.shared import translator_data
from tests.shared.utils import open_in_excel


def test_translator_voucher(client):

    translator = Translator(**translator_data)

    class FakeRequest:

        app = client.app
        is_manager = False
        is_admin = True
        is_member = False

        def translate(self, value):
            return value

        def include(self, value):
            pass

    report = TranslatorVoucher(
        FakeRequest(),
        translator
    )

    file = report.create_document('random_gen_password')
    open_in_excel(file)
