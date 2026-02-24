from __future__ import annotations

from more.webassets import WebassetsApp


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from onegov.core.request import CoreRequest
    from webob.response import Response


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

    def configure_mapbox(
        self,
        *,
        mapbox_token: str | None = None,
        **cfg: Any
    ) -> None:
        """ Configures the mapbox.

        The following configuration options are accepted:

        :mapbox_token:
            The public mapbox token to be used for the mapbox api.

        """
        assert (mapbox_token or 'pk').startswith('pk'), """
            Only public mapbox tokens are allowed!
        """
        self.mapbox_token = mapbox_token


@MapboxApp.webasset_path()
def get_js_path() -> str:
    return 'assets/js'


@MapboxApp.webasset_path()
def get_css_path() -> str:
    return 'assets/css'


@MapboxApp.webasset('leaflet', filters={'css': ['datauri', 'custom-rcssmin']})
def get_leaflet_asset() -> Iterator[str]:
    yield 'leaflet.css'
    yield 'leaflet-easybutton.css'
    yield 'leaflet-control-geocoder.css'
    yield 'leaflet-control-locate.css'
    yield 'leaflet-integration.css'
    yield 'leaflet.js'
    yield 'leaflet-sleep.js'
    yield 'leaflet-easybutton.js'
    yield 'leaflet-control-geocoder.js'
    yield 'leaflet-control-locate.js'
    yield 'leaflet-integration.js'


@MapboxApp.webasset('proj4js')
def get_proj4js_asset() -> Iterator[str]:
    yield 'proj4js.js'
    yield 'proj4js-leaflet.js'


@MapboxApp.webasset('geo-mapbox')
def get_geo_mapbox() -> Iterator[str]:
    yield 'leaflet'


@MapboxApp.webasset('geo-vermessungsamt-winterthur')
def get_geo_vermessungsamt_winterthur() -> Iterator[str]:
    yield 'leaflet'
    yield 'proj4js'
    yield 'geo-vermessungsamt-winterthur.js'


@MapboxApp.webasset('geo-zugmap-basisplan')
def get_geo_zugmap_basisplan() -> Iterator[str]:
    yield 'leaflet'
    yield 'proj4js'
    yield 'geo-zugmap.js'


@MapboxApp.webasset('geo-zugmap-orthofoto')
def get_geo_zugmap_orthofoto() -> Iterator[str]:
    yield 'leaflet'
    yield 'proj4js'
    yield 'geo-zugmap-orthofoto.js'


@MapboxApp.webasset('geo-bs')
def get_geo_bs() -> Iterator[str]:
    yield 'leaflet'
    yield 'proj4js'
    yield 'geo-bs.js'


@MapboxApp.webasset('geo-admin')
def get_geo_admin() -> Iterator[str]:
    yield 'leaflet'
    yield 'proj4js'
    yield 'geo-admin.js'


@MapboxApp.webasset('geo-admin-aerial')
def get_geo_admin_aerial() -> Iterator[str]:
    yield 'leaflet'
    yield 'proj4js'
    yield 'geo-admin-aerial.js'


@MapboxApp.tween_factory()
def inject_mapbox_api_token_tween_factory(
    app: MapboxApp,
    handler: Callable[[CoreRequest], Response]
) -> Callable[[CoreRequest], Response]:

    replacement = '<body data-mapbox-token="{}"'.format(app.mapbox_token)
    replacement_b = replacement.encode('utf-8')

    def inject_mapbox_api_token_tween(request: CoreRequest) -> Response:

        response = handler(request)

        if getattr(request.app, 'mapbox_token', None):
            response.body = response.body.replace(
                b'<body',
                replacement_b,
                1  # only replace the first occurrence
            )

        return response

    return inject_mapbox_api_token_tween
