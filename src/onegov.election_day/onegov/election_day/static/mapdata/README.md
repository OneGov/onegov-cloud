# Mapdata

The mapdata used by onegov.election_day is originally from this excellent
repository: https://github.com/interactivethings/swiss-maps

To create an update set of data follow the instructions on the repository and
when ready generate the data with the following make command:

    make all PROPERTIES=id,name

The resulting files in the `/topo` folders are used as follows:

1. The files are renamed from `xx-municipalities.json` to `xx.json`, or
   from `xx-municipalities.json` to `xx.json`.

2. The resulting files are put into the folder of their respective year. For
   example: `static/mapdata/2015/*.json`

There's a python script which does all of this automatically:
https://github.com/seantis/swiss-maps/blob/master/generate.py