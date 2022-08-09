import requests
from wtforms.widgets.core import HTMLString


class AgencyMapDefault():
    """ The standard map for displaying agency addresses"""

    def get_position(address):
        coordinates = (2611484, 1267592)
        return coordinates

    def map_html_string(address):
        return HTMLString(f"""
            <iframe class="agency-map" src="
                https://map.geo.admin.ch/embed.html?
                X={AgencyMapDefault.get_position(address)[0]}
                &Y={AgencyMapDefault.get_position(address)[1]}
                &lang=de&topic=ech&bgLayer=voidLayer&crosshair=bowl
                &layers=ch.kantone.cadastralwebmap-farbe&catalogNodes=532,614&zoom=10
                ">
            </iframe>
        """)


class AgencyMapBs():

    def get_position(address):
        api = ("https://search.geo.bs.ch/search?partitionlimit=10"
               "&maxresults=90&outputformat=centroid&term=")
        response = requests.get(f"{api}{address}")
        if response.status_code == 200:
            pos = response.json()[0]['geom']
            pos = pos[7:-1].split(' ')
            return pos
        else:
            return False

    def map_html_string(address):
        return HTMLString(f"""
            <link href="https://map.geo.bs.ch/api.css" rel="stylesheet">
            <script src="https://map.geo.bs.ch/api.js?version=2"></script>
            <script>
                window.onload = function() {{
                    var map = new mapbs.Map({{
                        div: 'map', // id of the div element to put the map in
                        zoom: 4,
                        backgroundLayers: ['Grundkarte farbig'],
                        center: [{AgencyMapBs.get_position(address)[0]},
                        {AgencyMapBs.get_position(address)[1]}]
                    }});
                    map.addMarker({{
                        position: [{AgencyMapBs.get_position(address)[0]},
                        {AgencyMapBs.get_position(address)[1]}],
                        size: [14, 14],
                        icon: 'https://map.geo.bs.ch//static-ngeo/api/apihelp/img/info.png'
                    }});
                }};
            </script>
            <div class="agency-map" id='map'></div>
        """)
