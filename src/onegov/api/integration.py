from morepath import App


class ApiApp(App):

    def configure_api(self, **cfg):
        # todo: allow global enabling/disabling for all applications?
        pass

    # todo: allow instance specific settings, probably using the filestorage?


@ApiApp.setting(section='api', name='endpoints')
def get_api_endpoints():
    return {}
