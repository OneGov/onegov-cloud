# Mapdata

## Municipalitites


To create an update set of data follow the instructions on the 
[swiss-map repository](https://github.com/seantis/swiss-maps.git).

1. Download the geodata [SwissBoundaries3D](https://shop.swisstopo.admin.ch/en/products/landscape/boundaries3D)
   and extract the FileGeoDatabase (*.gdb) in LV03 Coordinate system.
2. Take that geodatabase and add it to the swiss-maps Repo into the VCS.
3. Generate the TopoJson with `generate` script and add all json files
   to `static/mapdata/2021/.

## Districts

You probably need to generate the needed maps yourself.

For example the districts of the town of Berne can be extracted from http://map.bern.ch/statistik as ArcGIS JSON, which can be converted to GeoJSON:

    ogr2ogr -f GeoJSON output.json input.json OGRGeoJSON

And then to TopoJSON

    topojson output.json > final.json

After that, simply add the `name` and `id` attributes to the districts.
