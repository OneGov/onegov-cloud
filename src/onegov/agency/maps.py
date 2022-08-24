from markupsafe import Markup
import requests


class AgencyMapDefault():
    """ The standard map for displaying agency addresses"""

    def map_html_string(coordinates):
        return Markup(f"""
            <div class="marker-map agency-map"
                data-lat="{coordinates.lat}"
                data-lon="{coordinates.lon}"
                data-zoom="{coordinates.zoom}">
            </div>
        """)


class AgencyMapBs():

    def map_html_string(coordinates):
        response = requests.get((
            'http://geodesy.geo.admin.ch/reframe/wgs84tolv95?'
            f'easting={coordinates.lon}&northing={coordinates.lat}&format=json'
        ))
        coordinates_ch = response.json()

        return Markup(f"""
            <link href="https://map.geo.bs.ch/api.css" rel="stylesheet">
            <script src="https://map.geo.bs.ch/api.js?version=2"></script>
            <script>
                window.onload = function() {{
                    var map = new mapbs.Map({{
                        div: 'map', // id of the div element to put the map in
                        zoom: 8,
                        backgroundLayers: ['Grundkarte farbig'],
                        center: [{coordinates_ch['easting']},
                        {coordinates_ch['northing']}]
                    }});
                    map.addMarker();
                }};
            </script>
            <div class="agency-map" id='map'></div>
        """)
