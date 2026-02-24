from __future__ import annotations

from morepath import App


from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from onegov.core import cache


class ApiApp(App):

    if TYPE_CHECKING:
        # forward declare Framework.get_cache
        def get_cache(
            self,
            name: str,
            expiration_time: float
        ) -> cache.RedisCacheRegion: ...

    def configure_api(self, **cfg: Any) -> None:
        """ Configures the API.

        The following configuration options are accepted:

        :rate_limit:
            A tuple with number of request per expiration time in seconds.

        Since providing an API is not our main focus, we keep the rate limit
        rather low (<10 requests per minute) while still allowing small crawl
        bursts by default.

        """
        self.rate_limit = (
            cfg.get('api_rate_limit', {}).get('requests', 100),
            cfg.get('api_rate_limit', {}).get('expiration', 15 * 60)
        )

    @property
    def rate_limit_cache(self) -> cache.RedisCacheRegion:
        """ A cache for rate limits. """

        _limit, expiration = self.rate_limit
        return self.get_cache('rate_limits', expiration)


@ApiApp.setting(section='api', name='endpoints')
def get_api_endpoints() -> list[str]:
    return []
