from __future__ import annotations

import requests
from base64 import b64encode


from typing import Any


class GeverClientCAS:
    """ Gever Client that uses CAS for authenticating.
    Its purpose is to permit a user to access multiple applications
    while providing their credentials (such as user ID and password)
    only once.
    """

    def __init__(self, username: str, password: str, service_url: str):

        self.portal_session = requests.Session()
        self.service_session = requests.Session()
        self.portal_session.headers.update({'Accept': 'application/json'})
        self.service_session.headers.update({'Accept': 'application/json'})

        self.username = username
        self.password = password
        self.service_url = service_url
        last_char = service_url[-1]
        self.portal_url = (service_url + 'portal' if last_char == '/'
                           else service_url + '/portal')
        self.login_url = self.portal_url + '/api/login'
        self.ticket_url = self.portal_url + '/api/cas/tickets'

    def request(
        self,
        method: str,
        url: str,
        # FIXME: This should probably add annotations for the keyword
        #        arguments we're using
        **kwargs: Any
    ) -> requests.Response:

        # First request will always need to obtain a token first
        if 'Authorization' not in self.service_session.headers:
            self.obtain_token()

        # Optimistically attempt to dispatch request
        # url needs a slash at the end
        response = self.service_session.request(method, url, **kwargs)
        if self.token_has_expired(response):
            # We got an 'Access token expired' response => refresh token
            self.obtain_token()
            # Re-dispatch the request that previously failed
            response = self.service_session.request(method, url, **kwargs)

        return response

    def token_has_expired(self, response: requests.Response) -> bool:
        status = response.status_code

        if status == 401:
            return True

        return False

    def obtain_token(self) -> None:

        # Login to portal using /api/login endpoint
        self.portal_session.post(
            self.login_url,
            json={'username': self.username, 'password': self.password}
        )
        # Get CSRF token that was returned by server in a cookie
        csrf_token = self.portal_session.cookies['csrftoken']

        # Send the CSRF token as a request header in subsequent requests
        self.portal_session.headers.update({'X-CSRFToken': csrf_token})
        self.portal_session.headers.update({'Referer': self.portal_url})

        # Once logged in to the portal, get a CAS ticket
        ticket_response = self.portal_session.post(
            self.ticket_url,
            json={'service': self.service_url + '/'}
        )
        ticket = ticket_response.json()['ticket']

        # Use ticket to authenticate to the @caslogin endpoint on the service
        login_response = self.portal_session.post(
            self.service_url + '/@caslogin',
            json={'ticket': ticket, 'service': self.service_url + '/'}
        )

        # Get the JWT token from the @caslogin response, and send
        # it as a Bearer token in subsequent requests to the service
        token = login_response.json()['token']
        self.service_session.headers['Authorization'] = f'Bearer {token}'

    def upload_file(
        self,
        file: bytes,
        filename: str | bytes,
        endpoint: str
    ) -> requests.Response:

        def _base64_str(s: str | bytes) -> str:
            if not isinstance(s, bytes):
                s = s.encode('utf-8')
            return b64encode(s).decode('utf-8')

        def _prepare_metadata(
            filename: str | bytes,
            content_type: str | bytes,
            _type: str | bytes | None = None
        ) -> str:
            return 'filename {},content-type {}{}'.format(
                _base64_str(filename),
                _base64_str(content_type),
                ', @type ' + _base64_str(_type) if _type else '',
            )

        file_size = len(file)
        if not isinstance(file, bytes) or file_size == 0:
            raise ValueError(f'Invalid Argument: {type(file)}')

        metadata = _prepare_metadata(
            filename, 'application/pdf', 'opengever.document.document'
        )

        headers = {
            'Accept': 'application/json',
            'Tus-Resumable': '1.0.0',
            'Upload-Length': str(file_size),
            'Upload-Metadata': metadata,
        }
        last_char = endpoint[-1]
        endpoint += '@tus-upload' if last_char == '/' else '/@tus-upload'

        resp = self.request(
            'POST', endpoint, headers=headers
        )

        if not (resp.status_code == 201 and 'Location' in resp.headers.keys()):
            return resp  # fail early

        # The server will return a temporary upload URL 'location' in header
        location = resp.headers['Location']
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/offset+octet-stream',
            'Upload-Offset': '0',
            'Tus-Resumable': '1.0.0',
        }

        resp = self.request(
            'PATCH', location, headers=headers, data=file
        )
        return resp
