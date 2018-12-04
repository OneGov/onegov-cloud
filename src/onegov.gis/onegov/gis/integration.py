from more.webassets import WebassetsApp


class MapboxApp(WebassetsApp):
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


@MapboxApp.webasset_path()
def get_js_path():
    return 'assets/js'


@MapboxApp.webasset_path()
def get_css_path():
    return 'assets/css'


@MapboxApp.webasset('leaflet', filters={'css': ['datauri', 'custom-rcssmin']})
def get_leaflet_asset():
    yield 'leaflet.css'
    yield 'leaflet-easybutton.css'
    yield 'leaflet-control-geocoder.css'
    yield 'leaflet-integration.css'
    yield 'leaflet.js'
    yield 'leaflet-sleep.js'
    yield 'leaflet-easybutton.js'
    yield 'leaflet-control-geocoder.js'
    yield 'leaflet-integration.js'


@MapboxApp.webasset('proj4js')
def get_proj4js_asset():
    yield 'proj4js.js'
    yield 'proj4js-leaflet.js'


@MapboxApp.webasset('geo-mapbox')
def get_geo_mapbox():
    yield 'leaflet'


@MapboxApp.webasset('geo-vermessungsamt-winterthur')
def get_geo_vermessungsamt_winterthur():
    yield 'leaflet'
    yield 'proj4js'
    yield 'geo-vermessungsamt-winterthur.js'


@MapboxApp.webasset('geo-zugmap-ortsplan')
def get_geo_zugmap_ortsplan():
    yield 'leaflet'
    yield 'proj4js'
    yield 'geo-zugmap.js'
    yield 'geo-zugmap-ortsplan.js'


@MapboxApp.webasset('geo-zugmap-luftbild')
def get_geo_zugmap_luftbild():
    yield 'leaflet'
    yield 'proj4js'
    yield 'geo-zugmap.js'
    yield 'geo-zugmap-luftbild.js'


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
