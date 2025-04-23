from __future__ import annotations

import requests
import secrets
import string


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import datetime
    from wtforms.fields.choices import _Choice


class KabaApiError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message


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

    def raise_for_status(self, res: requests.Response) -> None:
        if res.ok:
            return

        error = res.json()
        raise KabaApiError(
            error['code'],
            error['message'],
        )

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

    def random_code(self) -> str:
        return ''.join(secrets.choice(string.digits) for _ in range(6))

    def create_visit(
        self,
        code: str,
        name: str,
        message: str,
        start: datetime,
        end: datetime,
        components: list[str]
    ) -> tuple[str, str]:
        res = self.session.post(
            f'{self.base_url}/{self.site_id}/visit',
            json={
                'code': code,
                'validFrom': start.isoformat(),
                'validTo': end.isoformat(),
                'components': components,
                'name': name,
                'message': message,
            },
            timeout=(5, 10)
        )
        self.raise_for_status(res)
        data = res.json()
        return data['id'], data['link']

    def revoke_visit(self, visit_id: str) -> None:
        res = self.session.post(
            f'{self.base_url}/{self.site_id}/visit/{visit_id}/revoke',
            json={},
            timeout=(5, 10)
        )
        self.raise_for_status(res)
