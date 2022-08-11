import io
import os

from AIS import AIS, PDF
from contextlib import suppress
from onegov.file.sign.generic import SigningService


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
        with suppress(io.UnsupportedOperation):
            infile.seek(0)

        # NOTE: We gain nothing from a chunked read, since we need to
        #       keep the entire file in memory anyways.
        inout_stream = io.BytesIO(infile.read())

        pdf = PDF(inout_stream=inout_stream)
        self.client.sign_one_pdf(pdf)

        # NOTE: Same with the chunked write, the file is already in memory
        outfile.write(inout_stream.getvalue())

        return f'swisscom_ais/{self.customer}/{self.client.last_request_id}'
