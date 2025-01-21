"""
Send E-Mail through Postmark

Adapted from `repoze.sendmail<https://github.com/repoze/repoze.sendmail>`_.

Usage::
    qp = PostmarkQueueProcessor(token, maildir, maildir, ..., limit=x)
    qp.send_messages()
"""
from __future__ import annotations

import json
import pycurl

from io import BytesIO
from .core import log, MailQueueProcessor


class PostmarkMailQueueProcessor(MailQueueProcessor):

    def __init__(
        self,
        postmark_token: str,
        *paths: str,
        limit: int | None = None
    ):
        super().__init__(*paths, limit=limit)

        # Keep a pycurl object around, to use HTTP keep-alive - though pycurl
        # is much worse in terms of it's API, the performance is *much* better
        # than requests and it supports modern features like HTTP/2 or HTTP/3
        self.url = 'https://api.postmarkapp.com/email/batch'
        self.curl = pycurl.Curl()
        self.curl.setopt(pycurl.TCP_KEEPALIVE, 1)
        self.curl.setopt(pycurl.URL, self.url)
        self.curl.setopt(pycurl.HTTPHEADER, [
            'Accept:application/json',
            'Content-Type:application/json',
            f'X-Postmark-Server-Token:{postmark_token}'
        ])
        self.curl.setopt(pycurl.POST, 1)

    def send(self, filename: str, payload: str) -> bool:
        """ Sends the mail and returns success as bool """
        code, body = self.send_request(payload)

        if 400 <= code < 600:
            raise RuntimeError(f'{code} calling {self.url}: {body}')

        result = json.loads(body)

        # If we don't get a list we definitely hit an error
        if not isinstance(result, list):
            log.error(f'Invalid API response in mail batch {filename}')
            return False

        # If any list entry contains errors we return failure
        success = True
        for index, status in enumerate(result, start=1):
            error_code = status.get('ErrorCode', 0)
            message = status.get('Message', f'ErrorCode: {error_code}')
            if error_code == 406:
                # inactive recipient, error can be ignored but still log it
                log.warning(
                    f'Inactive recipient in mail batch {filename} at '
                    f'index {index}: {message}'
                )
            elif error_code != 0:
                log.error(
                    f'Error in mail batch {filename} at index '
                    f'{index}: {message}'
                )
                success = False

        return success

    def send_request(self, payload: str) -> tuple[int, str]:
        """ Performes the API request using the given payload. """

        body = BytesIO()

        self.curl.setopt(pycurl.WRITEDATA, body)
        self.curl.setopt(pycurl.POSTFIELDS, payload)
        self.curl.perform()

        code = self.curl.getinfo(pycurl.RESPONSE_CODE)

        body.seek(0)
        body_str = body.read().decode('utf-8')

        return code, body_str
