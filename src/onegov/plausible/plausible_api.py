from __future__ import annotations
import logging
from typing import Any

import requests
from requests import HTTPError

log = logging.getLogger('onegov.plausible')


class PlausibleAPI:

    def __init__(self, site_id: str | None = None) -> None:
        """
        Initialize Plausible API client
        For details about the API see https://plausible.io/docs/stats-api

        """
        # plausible url
        self.url = 'https://analytics.seantis.ch/api/v2/query'

        # api key from https://analytics.seantis.ch/settings/api-keys
        api_key = (
            'eR9snr0RzrglMLrKqVPNQ_IYL3dD6hyOX0-2gyRMlxSSSTk5bg6NjORWtbNEMoHU')

        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        self.site_id = site_id

    def _send_request(self, payload: dict[str, Any]) -> dict[Any, Any]:
        """
        Send request to Plausible API

        """
        if not self.site_id:
            log.error('Site Id not configured')
            return {'results': []}

        try:
            response = requests.post(
                self.url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
        except HTTPError as http_err:
            if response.status_code == 401:
                log.error('Unauthorized: Invalid API key or insufficient '
                          'permissions', exc_info=http_err)
            else:
                log.error('HTTP error occurred', exc_info=http_err)
        except Exception as err:
            log.error('An error occurred', exc_info=err)

        return response.json()

    def get_stats(self) -> dict[str, int] | dict[str, str]:
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
            return {}

        figures = results[0].get('metrics', figures)

        # convert last figure from seconds to minutes
        figures[-1] = (
            str(round(int(figures[-1]) / 60, 1))) if figures[-1] else '0'

        texts = [
            'Unique Visitors in the Last Month',
            'Total Visits in the Last Month',
            'Total Page Views in the Last Month',
            'Number of Page Views per Visit',
            'Average Visit Duration in Minutes'
        ]

        return {text: figures[i] for i, text in enumerate(texts)}

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
