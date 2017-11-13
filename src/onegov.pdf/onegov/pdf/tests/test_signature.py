from io import BytesIO
from onegov.pdf import LexworkSigner
from unittest.mock import MagicMock
from unittest.mock import patch


def test_pdf_signing_reasons():
    signer = LexworkSigner(
        host='http://abcd.ef',
        login='abcd',
        password='1234',
    )

    args = {'json.return_value': {'result': ['a', 'b', 'c']}}
    with patch(
        'onegov.pdf.signature.get', return_value=MagicMock(**args)
    ) as get:
        assert signer.signing_reasons == ['a', 'b', 'c']
        assert get.called
        assert get.call_args[0][0] == (
            'http://abcd.ef/admin_interface/pdf_signature_reasons.json'
        )
        assert get.call_args[1]['headers']['X-LEXWORK-LOGIN'] == 'abcd'
        assert get.call_args[1]['headers']['X-LEXWORK-PASSWORD'] == '1234'


def test_sign_pdf(temporary_directory):
    signer = LexworkSigner(
        host='http://abcd.ef',
        login='abcd',
        password='1234',
    )

    file = BytesIO()
    file.write('PDF'.encode('utf-8'))
    file.seek(0)

    args = {'json.return_value': {'result': {'signed_data': 'U0lHTkVE'}}}
    with patch(
        'onegov.pdf.signature.post', return_value=MagicMock(**args)
    ) as post:
        assert signer.sign(file, 'test.pdf', 'why').decode('utf-8') == 'SIGNED'
        assert post.called
        assert post.call_args[0][0] == (
            'http://abcd.ef/admin_interface/pdf_signature_jobs.json'
        )
        assert post.call_args[1]['headers']['X-LEXWORK-LOGIN'] == 'abcd'
        assert post.call_args[1]['headers']['X-LEXWORK-PASSWORD'] == '1234'
        assert post.call_args[1]['json'] == {
            'pdf_signature_job': {
                'file_name': 'test.pdf',
                'data': 'UERG',
                'reason_for_signature': 'why'
            }
        }
