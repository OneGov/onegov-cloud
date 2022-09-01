from markupsafe import Markup


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
        request = (
            'http://geodesy.geo.admin.ch/reframe/wgs84tolv95?'
            f'easting={coordinates.lon}&northing={coordinates.lat}&format=json'
        )

        return Markup(f"""
            <link href="https://map.geo.bs.ch/api.css" rel="stylesheet">
            <script src="https://map.geo.bs.ch/api.js?version=2"></script>
            <script>
                window.onload = function() {{
                    fetch('{request}').then((response) => response.json())
                        .then((data) => (
                            show_agency_map(data)
                        ));
                    function show_agency_map(data) {{
                        var map = new mapbs.Map({{
                            div: 'map-bs', // id of the div element for the map
                            zoom: 8,
                            backgroundLayers: ['Grundkarte farbig'],
                            center: [data['easting'],
                            data['northing']]
                        }});
                        map.addMarker();
                    }}
                }};
            </script>
            <div class="agency-map" id='map-bs'></div>
        """)
