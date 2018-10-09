import os

from AIS import AIS as AISBase
from AIS import PDF
from onegov.file.sign.generic import SigningService
from uuid import uuid4


class AIS(AISBase):
    """ Customises AIS to always remember the last issued request_id. """

    def _request_id(self):
        self.last_request_id = uuid4().hex
        return self.last_request_id

    def post(self, payload):

        # this should always hold true, unless a new release of AIS.py
        # changes something at which point we'd have to have a look
        #
        # see also https://github.com/camptocamp/AIS.py/issues/7
        #
        if self.last_request_id not in payload:
            raise RuntimeError("Unexpected AIS Payload")

        return super().post(payload)


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
        with self.materialise(infile) as fp:
            pdf = PDF(fp.name)
            self.client.sign_one_pdf(pdf)

        with open(pdf.out_filename, 'rb') as fp:
            for chunk in iter(lambda: fp.read(4096), b''):
                outfile.write(chunk)

        return f'swisscom_ais/{self.customer}/{self.client.last_request_id}'
