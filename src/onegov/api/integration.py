from morepath import App


class ApiApp(App):

    def configure_api(self, **cfg):
        # todo: allow global enabling/disabling for all applications?
        pass

    # todo: allow instance specific settings, probably using the filestorage?

    @property
    def rate_limit(self):
        """ The number of requests per timedelta in seconds. """
        return 10000, 15 * 60 * 60

    @property
    def rate_limit_cache(self):
        """ A cache for rate limits. """

        limit, expiration = self.rate_limit
        return self.get_cache('rate_limits', expiration)


@ApiApp.setting(section='api', name='endpoints')
def get_api_endpoints():
    return {}
