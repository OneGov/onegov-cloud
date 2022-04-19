import os

from AIS import AIS, PDF
from contextlib import suppress
from onegov.file.sign.generic import SigningService
from io import UnsupportedOperation


class SwisscomAIS(SigningService, service_name='swisscom_ais'):
    """ Sign PDFs using Swisscom's All-In Signing Service. """

    def __init__(self, customer, key_static, cert_file, cert_key):
        if not os.path.exists(cert_file):
            raise FileNotFoundError(cert_file)

        if not os.path.exists(cert_key):
            raise FileNotFoundError(cert_key)

        cert_file = os.path.abspath(cert_file)
        cert_key = os.path.abspath(cert_key)

        self.customer = customer
        self.client = AIS(customer, key_static, cert_file, cert_key)

    def sign(self, infile, outfile):
        with suppress(UnsupportedOperation):
            infile.seek(0)

        pdf = PDF(infile, out_stream=outfile)
        self.client.sign_one_pdf(pdf)

        return f'swisscom_ais/{self.customer}/{self.client.last_request_id}'
