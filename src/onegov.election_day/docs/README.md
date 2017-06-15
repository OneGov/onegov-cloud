ongov.election_day
==================

Upload Formats
--------------

- EN: [Format Specification](format__en.md)
- DE: [Format Spezifikation](format__de.md)
- FR: [Spécifications de format](format__fr.md)
- IT: [Specifica Formato](format__it.md)
- RM: [Format Specificaziun](format__rm.md)

Download Format
---------------

- EN: [Format Specification](open_data_en.md)
- DE: [Format Spezifikation](open_data_de.md)
- FR: [Spécifications de format](open_data_fr.md)
- IT: [Specifica Formato](open_data_it.md)
- RM: [Specifica Formato](open_data_rm.md)

Embedding
---------

The web app containts different views which allows easy embedding of election
and vote results on a different site:

-   `{path_to_ballot}/map`: The vote result map.
-   `{path_to_election}/candidates-chart`: The candidates bar chart.
-   `{path_to_election}/lists-chart`: The lists bar chart.
-   `{path_to_election}/connections-chart`: The connections sankey chart.
-   `{path_to_election}/panachage-chart`: The panachage sankey chart.
-   `{path_to_election}/parties-chart`: The party results bar chart.

Make sure you serve the files with the embedding code with a web server!

The views include the https://github.com/davidjbradshaw/iframe-resizer.


Headerless Mode
---------------

The web app can be called in a headerless mode by browsing
`{root_path}?headerless`. In headerless mode, both the header and footer are
hidden. The headerless setting is stored in the browser session after the
initial call which means that browsing all further links are in headerless mode
as well. End the headerless mode with `{root_path}?headerful`.

To set the language, set the a cookie either by browsing to
`{root_path}/locale/xx` or directly (`locale: xxx`). Valid options are `de_CH`,
`fr_CH`, `it_CH` or `rm_CH`

The views include the https://github.com/davidjbradshaw/iframe-resizer.

REST Interface
--------------

The web app allows to upload results in the onegov format using a
multipart-POST-request to `[base_url]/upload` containing the following fields:

- `type`: The type of upload. This is either `vote`, `election` or `parties`.
- `id`: The ID of the election/vote. The ID is generated from the title and
  used in the URL as the last part before the view, for example
  wab.govikon.ch/vote/**energiegesetz-eng** or
  wab.govikon.ch/election/**nationalratswahlen-2015**/lists.
- `results`: The results. See the [format_descriptions](format__en.md)

A token must be provided using the passwort part of HTTP basic authentication.
An invalid authentication returns a `HTTP 401 Unauthorized`. The token can be
generated using the command line interface (`create-upload-token`).

Valid requests return a `HTTP 200 OK` together with the JSON body:

    {
    	"status": "success",
    	"errors": {}
    }


Invalid requests return a `HTTP 400 Bad Request` together with a JSON body
containing a list of errors (note that `filename` and `line` might be missing):

    {
        "status": "error",
        "errors": {
            "1": [{
                "line": 2,
                "filename": null,
                "message": "1 is unknown"
            }]
        }
    }

It is possible to set the language used for the error messages by setting the
`Accept-Language` header, possible values are: `de_CH`, `fr_CH`, `it_CH` and
`rm_CH`.


### cURL Example

    curl https://[base_url]/upload \
      --user :[token] \
      --header "Accept-Language: de_CH" \
      --form "type=election" \
      --form "id=test-election" \
      --form "results=@import/staenderatswahl-2015.csv"


WabstiCExport
-------------

The web app allows to upload results directly from the Wabsti export program.
First add the election/vote(s), then a datasource (the token hereby generated
is used for authentication later) and connect the election/votes using the
parameters used in Wabsti.

The files can then be uploaded by using a multipart-POST-request to
- `[base_url]/upload-wabsti-vote` for votes with the fields
  - `sg_gemeinden` (SG_Gemeinden.csv)
  - `sg_geschaefte` (SG_Geschaefte.csv)
  - `sgstatic_gemeinden` (SGStatic_Gemeinden.csv)
  - `sgstatic_geschaefte` (SGStatic_Geschaefte.csv)
- `[base_url]/upload-wabsti-majorz` for majorz elections with the fields
  - `wm_gemeinden` (WM_Gemeinden.csv)
  - `wm_kandidaten` (WM_Kandidaten.csv)
  - `wm_kandidatengde` (WM_KandidatenGde.csv)
  - `wm_wahl` (WM_Wahl.csv)
  - `wmstatic_gemeinden` (WMStatic_Gemeinden.csv)
- `[base_url]/upload-wabsti-proporz` for proporz elections with the fields
  - `wp_gemeinden` (WP_Gemeinden.csv)
  - `wp_kandidaten` (WP_Kandidaten.csv)
  - `wp_kandidatengde` (WP_KandidatenGde.csv)
  - `wp_listen` (WP_Listen.csv)
  - `wp_listengde` (WP_ListenGde.csv)
  - `wp_wahl` (WP_Wahl.csv)
  - `wpstatic_gemeinden` (WPStatic_Gemeinden.csv)
  - `wpstatic_kandidaten` (WPStatic_Kandidaten.csv)

The token must be provided using the passwort part of HTTP basic authentication.
An invalid authentication returns a `HTTP 403 Forbidden`, all other requests
return a `HTTP 200 OK` together with a JSON body containing a status and a list
of errors, for example:

    {
    	"status": "success",
    	"errors": {}
    }

or

    {
        "status": "error",
        "errors": {
            "1": [{
                "line": 2,
                "filename": null,
                "message": "1 is unknown"
            }]
        }
    }

It is possible to set the language used for the error messages by setting the
`Accept-Language` header, possible values are: `de_CH`, `fr_CH`, `it_CH`, `rm_CH`.


### cURL Examples

    curl https://[base_url]/upload-wabsti-vote \
      --user :[token] \
      --header "Accept-Language: de_CH" \
      --form "sg_gemeinden=@SG_Gemeinden.csv" \
      --form "sg_geschaefte=@SG_Geschaefte.csv" \
      --form "sgstatic_gemeinden=@SGStatic_Gemeinden.csv" \
      --form "sgstatic_geschaefte=@SGStatic_Geschaefte.csv"

    curl https://[base_url]/upload-wabsti-majorz \
      --user :[token] \
      --header "Accept-Language: de_CH" \
      --form "wm_gemeinden=@WM_Gemeinden.csv" \
      --form "wm_kandidaten=@WM_Kandidaten.csv" \
      --form "wm_kandidatengde=@WM_KandidatenGde.csv" \
      --form "wm_wahl=@WM_Wahl.csv" \
      --form "wmstatic_gemeinden=@WMStatic_Gemeinden.csv"

    curl https://[base_url]/upload-wabsti-proporz \
      --user :[token] \
      --header "Accept-Language: de_CH" \
      --form "wp_gemeinden=@WP_Gemeinden.csv" \
      --form "wp_kandidaten=@WP_Kandidaten.csv" \
      --form "wp_kandidatengde=@WP_KandidatenGde.csv" \
      --form "wp_listen=@WP_Listen.csv" \
      --form "wp_listengde=@WP_ListenGde.csv" \
      --form "wp_wahl=@WP_Wahl.csv" \
      --form "wpstatic_gemeinden=@WPStatic_Gemeinden.csv" \
      --form "wpstatic_kandidaten=@WPStatic_Kandidaten.csv"


Testing
-------

See [here](testing.md)
