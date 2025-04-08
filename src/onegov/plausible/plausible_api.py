from __future__ import annotations
import logging
from typing import Any

import requests
from requests import HTTPError

log = logging.getLogger('onegov.plausible')


class PlausibleAPI:

    def __init__(self, site_id: str | None = None, api_key: str = '') -> None:
        """
        Initialize Plausible API client
        For details about the API see https://plausible.io/docs/stats-api

        """
        # plausible url
        self.url = 'https://analytics.seantis.ch/api/v2/query'

        self.site_id = site_id

        # api key from https://analytics.seantis.ch/settings/api-keys
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

    def _send_request(self, payload: dict[str, Any]) -> dict[Any, Any]:
        """
        Send request to Plausible API

        """
        if not self.site_id:
            log.error('Site Id not configured')
            return {'results': []}

        try:
            response = requests.post(
                self.url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
        except HTTPError:
            if response.status_code == 401:
                log.exception(
                    'Unauthorized: Invalid API key or insufficient permissions'
                )
            else:
                log.exception('HTTP error occurred')
        except Exception:
            log.exception('An error occurred')

        return response.json()

    def get_stats(self) -> list[str]:
        """
        Get basic stats from Plausible API

        """
        figures = ['-', '-', '-', '-']
        metrics = ['visitors', 'visits', 'pageviews', 'views_per_visit',
                   'visit_duration']
        date_range = '30d'

        payload = {
            'site_id': self.site_id,
            'metrics': metrics,
            'date_range': date_range,
            'filters': [],
            'dimensions': []
        }

        r = self._send_request(payload)

        results = r.get('results', [])
        if not results:
            return figures

        figures = results[0].get('metrics', figures)

        # convert last figure from seconds to minutes
        figures[-1] = (
            str(round(int(figures[-1]) / 60, 1))) if figures[-1] else '0'

        return figures

    def get_top_pages(self, limit: int = 10) -> dict[str, int]:
        """
        Get top pages from Plausible API

        """
        metrics = ['visitors']
        date_range = '30d'
        dimensions = ['event:page']

        payload = {
            'site_id': self.site_id,
            'metrics': metrics,
            'date_range': date_range,
            'dimensions': dimensions,
            'pagination': {
                'limit': limit
            }
        }

        r = self._send_request(payload)

        results = r.get('results', [])
        if not results:
            return {}
        return {
            result['dimensions'][0]: result['metrics'][0] for result in results
        }
