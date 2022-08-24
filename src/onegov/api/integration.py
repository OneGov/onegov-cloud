from morepath import App


class ApiApp(App):

    @property
    def rate_limit(self):
        """ The number of requests per timedelta in seconds.

        Since providing an API is not our main focus, we keep the rate limit
        rather low (<10 requests per minute) while still allowing small crawl
        bursts.
        """
        return 100, 15 * 60

    @property
    def rate_limit_cache(self):
        """ A cache for rate limits. """

        limit, expiration = self.rate_limit
        return self.get_cache('rate_limits', expiration)


@ApiApp.setting(section='api', name='endpoints')
def get_api_endpoints():
    return {}
