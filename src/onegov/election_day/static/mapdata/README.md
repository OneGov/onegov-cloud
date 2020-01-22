# Mapdata

## Municipalitites

The mapdata used by onegov.election_day is originally from this excellent
repository: https://github.com/interactivethings/swiss-maps

To create an update set of data follow the instructions on the repository and
when ready generate the data with the following make command:

    make all PROPERTIES=id,name

The resulting files in the `/topo` folders are used as follows:

1. The files are renamed from `xx-municipalities.json` to `xx.json`.

2. The resulting files are put into the folder of their respective year. For
   example: `static/mapdata/2015/*.json`

There's a python script which does all of this automatically:
https://github.com/seantis/swiss-maps/blob/master/generate.py

## Districts

You probably need to generate the needed maps yourself.

For example the districts of the town of Berne can be extracted from http://map.bern.ch/statistik as ArcGIS JSON, which can be converted to GeoJSON:

    ogr2ogr -f GeoJSON output.json input.json OGRGeoJSON

And then to TopoJSON

    topojson output.json > final.json

After that, simply add the `name` and `id` attributes to the districts.

# Further informations

https://gdal.org/drivers/vector/gpkg.html

https://medium.com/@GispoFinland/learn-spatial-sql-and-master-geopackage-with-qgis-3-16b1e17f0291

You can create the SQLite Statements with the aid of the database manager in QGIS after
loading the wanted data as geopackage.

GeoJSON: Section 4 of RFC7946 tells us that

> The coordinate reference system for all GeoJSON coordinates is a geographic coordinate 
> reference system, using the World Geodetic System 1984 (WGS 84) [WGS84] datum, with longitude > and latitude units of decimal degrees. This is equivalent to the coordinate reference system > identified by the Open Geospatial Consortium (OGC) URN urn:ogc:def:crs:OGC::CRS84
    
    ogr2ogr -sql "select * from TLM_HOHEITSGEBIET where ICC = 'CH'" -f GPKG boundaries.gpkg swissBOUNDARIES3D_1_3_LV03_LN02.gdb

Test a single two first builds:
    
    make clean
    make build/ch/municipalities.shp PROPERTIES=id,name YEAR=2020
    make build/zh/municipalities.shp PROPERTIES=id,name YEAR=2020
    
The outputted GeoJson does not have correct swiss coordinates. 