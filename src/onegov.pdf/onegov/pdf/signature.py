from base64 import b64decode
from base64 import b64encode
from requests import get
from requests import post


class LexworkSigner(object):
    """ Allows the sign PDFs using the lexwork PDF signing interface. """

    def __init__(self, host, login, password):
        self.host = host.rstrip('/')
        self.login = login
        self.password = password

    def url(self, endpoint):
        return '{}/admin_interface/{}.json'.format(self.host, endpoint)

    @property
    def headers(self):
        return {
            'X-LEXWORK-LOGIN': self.login,
            'X-LEXWORK-PASSWORD': self.password
        }

    @property
    def signing_reasons(self):
        """ List all possible signing reasons for the given credentials."""

        response = get(self.url('pdf_signature_reasons'), headers=self.headers)
        response.raise_for_status()
        return response.json().get('result')

    def sign(self, file, filename, reason):
        """ Signs the given file. """

        file.seek(0)
        data = b64encode(file.read()).decode('utf-8')

        response = post(
            self.url('pdf_signature_jobs'),
            headers=self.headers,
            json={
                'pdf_signature_job': {
                    'file_name': filename,
                    'data': data,
                    'reason_for_signature': reason
                }
            }
        )
        response.raise_for_status()
        return b64decode(response.json()['result']['signed_data'])
