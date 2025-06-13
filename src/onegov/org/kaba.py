from __future__ import annotations

import requests
import secrets
import string
from cryptography.fernet import InvalidToken
from sedate import to_timezone


from typing import Self, TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import datetime
    from onegov.org.app import OrgApp
    from onegov.reservation import Resource
    from wtforms.fields.choices import _Choice


class KabaApiError(Exception):
    def __init__(self, message: str, response: requests.Response) -> None:
        super().__init__(message)
        self.message = message
        self.response = response


class KabaClient:

    def __init__(
        self,
        site_id: str,
        api_key: str,
        api_secret: str
    ) -> None:

        self.site_id = site_id
        self.session = requests.Session()
        self.session.auth = (api_key, api_secret)
        self.base_url = 'https://api.exivo.io/v1'

    @classmethod
    def from_app(cls, app: OrgApp) -> Self | None:
        site_id = app.org.kaba_site_id
        api_key = app.org.kaba_api_key
        api_encrypted_secret = app.org.kaba_api_secret
        if not (site_id and api_key and api_encrypted_secret):
            return None

        try:
            api_secret = app.decrypt(bytes.fromhex(api_encrypted_secret))
        except InvalidToken:
            return None

        return cls(site_id, api_key, api_secret)

    @classmethod
    def from_resource(
        cls,
        resource: Resource,
        app: OrgApp
    ) -> Self | None:

        components = getattr(resource, 'kaba_components', [])
        if not components:
            return None

        return cls.from_app(app)

    def raise_for_status(self, res: requests.Response) -> None:
        if res.ok:
            return

        error = res.json()
        raise KabaApiError(error['message'], res)

    def site_name(self) -> str:
        res = self.session.get(
            f'{self.base_url}/{self.site_id}/info',
            timeout=(5, 10)
        )
        self.raise_for_status(res)
        return res.json()['name']

    def component_choices(self) -> list[_Choice]:
        res = self.session.get(
            f'{self.base_url}/{self.site_id}/component',
            timeout=(5, 10)
        )
        self.raise_for_status(res)
        return [
            (item['id'], item['identifier'])
            for item in res.json()
        ]

    @staticmethod
    def random_code() -> str:
        return ''.join(secrets.choice(string.digits) for _ in range(6))

    def create_visit(
        self,
        code: str,
        name: str,
        message: str,
        start: datetime,
        end: datetime,
        components: list[str]
    ) -> str:
        res = self.session.post(
            f'{self.base_url}/{self.site_id}/visit',
            json={
                'code': code,
                # NOTE: The API claims to support ISO 8601, but in fact it only
                #       supports UTC times with Z postfix instead of an offset.
                'validFrom': to_timezone(
                    start, 'UTC'
                ).isoformat(timespec='microseconds')[:-6] + 'Z',
                'validTo': to_timezone(
                    end, 'UTC'
                ).isoformat(timespec='microseconds')[:-6] + 'Z',
                'components': components,
                'name': name,
                'message': message,
            },
            timeout=(5, 10)
        )
        self.raise_for_status(res)
        data = res.json()
        return data['id']

    def revoke_visit(self, visit_id: str) -> None:
        res = self.session.post(
            f'{self.base_url}/{self.site_id}/visit/{visit_id}/revoke',
            json={},
            timeout=(5, 10)
        )
        self.raise_for_status(res)
