from morepath import App


class ApiApp(App):

    def configure_api(self, **cfg):
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
    def rate_limit_cache(self):
        """ A cache for rate limits. """

        limit, expiration = self.rate_limit
        return self.get_cache('rate_limits', expiration)


@ApiApp.setting(section='api', name='endpoints')
def get_api_endpoints():
    return []
