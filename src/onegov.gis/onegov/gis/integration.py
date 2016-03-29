import morepath


class MapboxApp(morepath.App):
    """ Provides mapbox integration
    :class:`onegov.core.framework.Framework` based applications.

    Doesn't do much except serve the mapbox public token, so we can store it
    in configuration and not with the source. Not that this token is inherently
    unsafe and must be the *public* token.

    Do not use private tokens!

    If we wanted to avoid this we would have to use a mapbox proxy server,
    which seems a bit too much. If we detect abuse of the public token we
    just switch to a new one. If it must be we can even automatically rotate
    the token regularly.

    """

    def configure_mapbox(self, **cfg):
        """ Configures the mapbox.

        The following configuration options are accepted:

        :mapbox_token:
            The public mapbox token to be used for the mapbox api.

        """
        assert cfg.get('mapbox_token', 'pk').startswith('pk'), """
            Only public mapbox tokens are allowed!
        """
        self.mapbox_token = cfg.get('mapbox_token', None)


@MapboxApp.tween_factory()
def inject_mapbox_api_token_tween_factory(app, handler):

    replacement = '<body data-mapbox-token="{}"'.format(app.mapbox_token)
    replacement = replacement.encode('utf-8')

    def inject_mapbox_api_token_tween(request):

        response = handler(request)

        if request.app.mapbox_token:
            response.body = response.body.replace(
                b'<body',
                replacement,
                1  # only replace the first occurrence
            )

        return response

    return inject_mapbox_api_token_tween
