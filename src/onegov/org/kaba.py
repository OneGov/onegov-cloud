from __future__ import annotations

import niquests
import secrets
import string
from datetime import datetime, timedelta, UTC
from sedate import to_timezone
from urllib3.util import Retry


from typing import Self, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.org.app import OrgApp
    from onegov.org.models.organisation import KabaConfiguration
    from onegov.reservation import Resource
    from wtforms.fields.choices import _Choice


class KabaApiError(Exception):
    def __init__(self, message: str, response: niquests.Response) -> None:
        super().__init__(message)
        self.message = message
        self.response = response


class KabaClient:

    def __init__(
        self,
        site_id: str,
        client_id: str,
        client_secret: str
    ) -> None:

        self.site_id = site_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.session = niquests.Session(
            retries=Retry(
                total=3,
                read=0,
                connect=3,
                status=3,
                other=0,
                backoff_factor=3,
                allowed_methods=None,
                status_forcelist=[429, 500, 502, 503, 504],
                respect_retry_after_header=True,
                retry_after_max=30,
            ),
            timeout=(5, 10)
        )
        self.base_url = 'https://api.resivo.io'
        self.api_version = 'v8'
        self.access_token: str
        self.access_token_expires = datetime.now(UTC)

    @classmethod
    def from_config(cls, config: KabaConfiguration | None) -> Self | None:
        if config is None:
            return None
        return cls(config.site_id, config.client_id, config.client_secret)

    @classmethod
    def from_app(cls, app: OrgApp) -> dict[str, Self]:
        return {
            raw_config.site_id: client
            for raw_config in app.org.kaba_configurations
            if (client := cls.from_config(raw_config.decrypt(app)))
        }

    @classmethod
    def from_resource(
        cls,
        resource: Resource,
        app: OrgApp
    ) -> dict[str, Self]:

        components = getattr(resource, 'kaba_components', [])
        site_ids = {site_id for site_id, _component in components}
        return {
            site_id: client
            for site_id in site_ids
            if (raw_config := app.org.get_kaba_configuration(site_id))
            if (client := cls.from_config(raw_config.decrypt(app)))
        }

    def maybe_refresh_access_token(self) -> None:
        if self.access_token_expires <= (now := datetime.now(UTC)):
            res = self.session.post(
                f'{self.base_url}/oauth2/token',
                data={
                    'grant_type': 'client_credentials',
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                },
                timeout=(5, 10)
            )
            self.raise_for_status(res)
            payload = res.json()
            self.access_token = payload['access_token']
            self.access_token_expires = now + timedelta(
                # NOTE: We expire the token slightly earlier than we would
                #       need to in order to avoid a race condition between
                #       checking if we need to refresh and emitting the
                #       request that uses the access token
                seconds=payload.get('expires_in', 300) - 30
            )

    def raise_for_status(self, res: niquests.Response) -> None:
        if res.ok:
            return

        error = res.json()
        raise KabaApiError(error['message'], res)

    def site_name(self) -> str:
        self.maybe_refresh_access_token()
        res = self.session.get(
            f'{self.base_url}/{self.api_version}/sites/{self.site_id}',
            auth=self.access_token,
            timeout=(5, 10)
        )
        self.raise_for_status(res)
        return res.json()['displayName']

    def component_choices(self) -> list[_Choice]:
        self.maybe_refresh_access_token()
        res = self.session.get(
            f'{self.base_url}/{self.site_id}/components?scope=all',
            auth=self.access_token,
            timeout=(5, 10)
        )
        self.raise_for_status(res)
        return [
            ([self.site_id, item['id']], item['displayName'])
            for item in res.json()
        ]

    @staticmethod
    def random_code() -> str:
        return ''.join(secrets.choice(string.digits) for _ in range(4))

    def create_pin_access(
        self,
        code: str,
        name: str,
        message: str,
        start: datetime,
        end: datetime,
        components: list[str]
    ) -> str:
        self.maybe_refresh_access_token()
        res = self.session.post(
            f'{self.base_url}/{self.site_id}/authorizations/pin-access',
            json={
                'displayName': name,
                'pinCodes': [{'pinCode': code, 'displayName': f'{name} PIN'}],
                'componentIds': components,
                'restrictions': {
                    # NOTE: We may no longer need to normalize the ISO format
                    #       like we did with exivo, double check and simplify
                    #       if possible.
                    'validFrom': to_timezone(
                        start, 'UTC'
                    ).isoformat(timespec='microseconds')[:-6] + 'Z',
                    'validTo': to_timezone(
                        end, 'UTC'
                    ).isoformat(timespec='microseconds')[:-6] + 'Z',
                },
                'accessRequestMessage': message,
            },
            auth=self.access_token,
            timeout=(5, 10)
        )
        self.raise_for_status(res)
        data = res.json()
        return data['id']

    def revoke_pin_access(self, auth_id: str) -> None:
        self.maybe_refresh_access_token()
        res = self.session.get(
            f'{self.base_url}/{self.site_id}/authorizations/{auth_id}',
            auth=self.access_token,
            timeout=(5, 10)
        )
        self.raise_for_status(res)
        data = res.json()
        if data.get('status') != 'active' or all(
            credential.get('isExpired') is True
            or credential.get('status') != 'active'
            for credential in data.get('credentials', ())
        ):
            return

        # NOTE: Just in case the previous request was slow
        self.maybe_refresh_access_token()
        res = self.session.delete(
            f'{self.base_url}/{self.site_id}/authorizations/{auth_id}/revoke',
            json={},
            auth=self.access_token,
            timeout=(5, 10)
        )
        self.raise_for_status(res)
