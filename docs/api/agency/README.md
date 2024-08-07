# OneGov Agency API

The headless Agency API offers the following views:

- [Agencies](#agencies-view)
- [People](#people-view)
- [Memberships](#membership-view)

We implement the called Collection+JSON standard established by Mike
Amundsen. For details please refer to [media types - collection & json](http://amundsen.com/media-types/collection/format/)

## Agencies View

The agencies view provides information about all the existing agencies
within the organisation. Each agency offers several data fields like title,
portrait, contact information, geolocation and more. Furthermore, the agency
api provides links to organigram, parent and child agencies as well as
memberships if given.

`curl https://[base_url]/agencies`

### Agency Query Fields

The agencies api support the following query fields:

| Query Fields | Description                                                        |
|--------------|--------------------------------------------------------------------|
| title        | queries for an agency with given title                             |
| parent       | queries for child agencies of agency specified                     |
| updated_lt   | queries agencies updated before date specified (lower than)        |
| updated_le   | queries agencies updated before or at date specified (lower equal) |
| updated_eq   | queries agencies updated at date specified (equal)                 |
| updated_ge   | queries agencies updated after or date specified (greater equal)   |
| updated_gt   | queries agencies updated after date specified (greater than)       |


### cURL Example

`curl https://[base_url]/agencies?title=datenschutzbeauftragter`

`curl https://[base_url]/agencies?parent=1`

`curl https://[base_url]/agencies?updated.ge=2023-05-12T11:04:00`

> NOTE: Multiple query fields can be combined using the '&'

Here an example for the office 'Datenschutzbeautragter' where we query for
the agencies title (or part of the title)

Request:

`curl https://[base_url]/agencies?title=datenschutzbeauftragter`

Response:
A collection+JSON of items if found including paging

```
{
    "collection": {
        "version": "1.0",
        "href": "http://[base_url]/api/agencies",
        "links": [
            {
                "rel": "prev",
                "href": null
            },
            {
                "rel": "next",
                "href": null
            }
        ],
        "items": [
            {
                "href": "http://[base_url]/api/agencies/1732",
                "data": [
                    {
                        "name": "title",
                        "value": "Datenschutzbeauftragter"
                    },
                    {
                        "name": "portrait",
                        "value": "<p>Henric Petri-Strasse 15<br><br>Postfach 205<br>4010 Basel<br><br>Tel.: <a><a href=\"tel:+41 61 201 16 40\">+41 61 201 16 40</a> </a><br><a href=\"mailto:datenschutz@dsb.bs.ch\">datenschutz@dsb.bs.ch</a><br><a href=\"http://www.dsb.bs.ch\" rel=\"nofollow\">Homepage</a><br></p>"
                    },
                    {
                        "name": "location_address",
                        "value": ""
                    },
                    {
                        "name": "location_code_city",
                        "value": ""
                    },
                    {
                        "name": "modified",
                        "value": "2023-04-14T16:38:18.197623+00:00"
                    },
                    {
                        "name": "postal_address",
                        "value": ""
                    },
                    {
                        "name": "postal_code_city",
                        "value": ""
                    },
                    {
                        "name": "website",
                        "value": ""
                    },
                    {
                        "name": "email",
                        "value": ""
                    },
                    {
                        "name": "phone",
                        "value": ""
                    },
                    {
                        "name": "phone_direct",
                        "value": ""
                    },
                    {
                        "name": "opening_hours",
                        "value": ""
                    },
                    {
                        "name": "geo_location",
                        "value": {
                            "lon": 7.592757,
                            "lat": 47.551977,
                            "zoom": 12
                        }
                    }
                ],
                "links": [
                    {
                        "rel": "organigram",
                        "href": null
                    },
                    {
                        "rel": "parent",
                        "href": null
                    },
                    {
                        "rel": "children",
                        "href": "http://[base_url]/api/agencies?parent=1732"
                    },
                    {
                        "rel": "memberships",
                        "href": "http://[base_url]/api/memberships?agency=1732"
                    }
                ]
            }
        ]
    }
}
```

## People View

The people view provides information about all people in relation with agencies
within the organisation. Each person offers several data fields like
first and last name, academic title, function within the organisation,
contact information and more. Additionally, the people api provides links to
a picture, website and memberships to agencies memberships if given.

`curl https://[base_url]/people`

### People Query Fields

The people api supports the following query fields that can be combined:

| Query Fields | Description                                                    |
|--------------|----------------------------------------------------------------|
| first_name   | queries for people with specific firstname                     |
| last_name    | queries for people with specific lastname                      |
| updated_lt   | queries people updated before date specified (lower than)      |
| updated_le   | queries people updated before or date specified (lower equal)  |
| updated_eq   | queries people updated at date specified (equal)               |
| updated_ge   | queries people updated after or date specified (greater equal) |
| updated_gt   | queries people updated after date specified (greater than)     |

### cURL Example

`curl https://[base_url]/people?first_name=moritz`

`curl https://[base_url]/people?updated.gt=2023-05-12T11:04:00`

> NOTE: Multiple query fields can be applied using the '&'

Here an example for a person with first name Ursula and last name Meier a
really common name last name in switzerland.

Request:

`curl https://[base_url]/people?last_name=meier&first_name=ursula`

Response:
A collection+JSON of items if found including paging

```
{
    "collection": {
        "version": "1.0",
        "href": "http://[base_url]/api/people",
        "links": [
            {
                "rel": "prev",
                "href": null
            },
            {
                "rel": "next",
                "href": null
            }
        ],
        "items": [
            {
                "href": "http://[base_url]/api/people/7ef422f15f394b0fa0b3f337f52bbafb",
                "data": [
                    {
                        "name": "academic_title",
                        "value": null
                    },
                    {
                        "name": "born",
                        "value": null
                    },
                    {
                        "name": "email",
                        "value": "u.m@ch.ch"
                    },
                    {
                        "name": "first_name",
                        "value": "Ursula"
                    },
                    {
                        "name": "function",
                        "value": "Team Leiterin"
                    },
                    {
                        "name": "last_name",
                        "value": "Meier"
                    },
                    {
                        "name": "location_address",
                        "value": ""
                    },
                    {
                        "name": "location_code_city",
                        "value": ""
                    },
                    {
                        "name": "notes",
                        "value": null
                    },
                    {
                        "name": "parliamentary_group",
                        "value": null
                    },
                    {
                        "name": "phone",
                        "value": null
                    },
                    {
                        "name": "phone_direct",
                        "value": null
                    },
                    {
                        "name": "political_party",
                        "value": null
                    },
                    {
                        "name": "postal_address",
                        "value": ""
                    },
                    {
                        "name": "postal_code_city",
                        "value": ""
                    },
                    {
                        "name": "profession",
                        "value": null
                    },
                    {
                        "name": "salutation",
                        "value": "Frau"
                    },
                    {
                        "name": "title",
                        "value": "Meier Ursula"
                    },
                    {
                        "name": "website",
                        "value": ""
                    },
                    {
                        "name": "modified",
                        "value": "2023-04-14T16:38:44.915859+00:00"
                    }
                ],
                "links": [
                    {
                        "rel": "picture_url",
                        "href": null
                    },
                    {
                        "rel": "website",
                        "href": "www.ursulameier.ch"
                    },
                    {
                        "rel": "memberships",
                        "href": "http://[base_url]/api/memberships?
                        person=[hash]"
                    }
                ]
            },
            ...
        ],
        "template": {
            "data": [
                {
                    "name":"academic_title",
                    "prompt":"Akademischer Titel"
                },
                ...
            ]
        }
    }
}
```

### Submit a person mutation

The endpoints for individual people support PUT requests to modify existing entries. This will open a pending mutation in the ticket system.

The available fields are given via the top-level `template` attribute on the collection. `submitter_email` is a required field. Just like when submitting a mutation manually, you only need to supply the values that need to be changed or a general comment via the `submitter_message` field.

The PUT endpoint supports formdata as well as the collection+json format and requires a [valid JWT Token](#authorization).

#### cURL example (formdata)

Here an example for submitting a mutation request of a person's last name to Meyer using simple form data.

Request:

```
curl http://localhost:8080/onegov_agency/zg/api/people/ccfffd1c28ac4e9093c784bc735b1232 \
    -X PUT \
    -H "Authorization: Bearer $OGC_TOKEN" \
    -F 'submitter_email=submitter@example.com' \
    -F 'last_name=Meyer'
```

Response:
An empty 200 success response if successful

#### cURL example (collection+json)

Here an example for submitting a mutation request of a person's last name to Meyer using the collection+json data format.

Request:

```
curl https://[base_url]/people/7ef422f15f394b0fa0b3f337f52bbafb \
    -X PUT \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/vnd.collection+json" \
    -d '{"template": {"data": [
    {"name": "submitter_email", "value": "submitter@example.com"},
    {"name": "last_name", "value": "Meyer"}]}}'
```

Response:
An empty 200 success response if successful

## Membership View

The membership view provides information about all the existing memberships
between people and agencies within the organisation. Each membership has
data points and links to its person and agency.

`curl https://[base_url]/memberships`

### Membership Query Fields

The agencies api support the following query fields:

| Query Fields | Description                                                            |
|--------------|------------------------------------------------------------------------|
| agency       | queries memberships of agency with given id                            |
| person       | queries all memberships of person with given uid                       |
| updated_lt   | queries memberships updated before date specified (lower than)         |
| updated_le   | queries memberships updated before or at date specified (lower equal)  |
| updated_eq   | queries memberships updated at date specified (equal)                  |
| updated_ge   | queries memberships updated after or date specified (greater equal)    |
| updated_gt   | queries memberships updated after date specified (greater than)        |


### cURL Example

`curl https://staka.zug.ch/api/memberships?agency=1`

`curl https://staka.zug.ch/api/memberships?person=ccfffd1c28ac4e9093c784bc735b1231`

> NOTE: Multiple query fields can be combined using the '&'

Here an example for all memberships of agency with id 4

Request:

`curl https://staka.zug.ch/api/memberships?agency=4`

Response:
A collection+JSON of items if found

```
{
    "collection": {
        "version": "1.0",
        "href": "https://[base_url]/api/memberships",
        "links": [
            {
                "rel": "prev",
                "href": null
            },
            {
                "rel": "next",
                "href": null
            }
        ],
        "items": [
            {
                "href": "https://[base_url]/api/memberships/e049cc9e1cad422a9dc160fe1af69a78",
                "data": [
                    {
                        "name": "title",
                        "value": "Bundesrätin"
                    },
                    {
                        "name": "modified",
                        "value": "2023-01-24T14:22:59.624376+00:00"
                    }
                ],
                "links": [
                    {
                        "rel": "agency",
                        "href": "https://[base_url]/api/agencies/4"
                    },
                    {
                        "rel": "person",
                        "href": "https://[base_url]/api/people/c6bbb982060a4545826c54ab204e4b73"
                    }
                ]
            },
            {
                "href": "https://[base_url]/api/memberships/e8c11e7e948146e7ba91478df5be648d",
                "data": [
                    {
                        "name": "title",
                        "value": "Vizepräsidentin"
                    },
                    {
                        "name": "modified",
                        "value": "2023-01-24T14:22:52.088620+00:00"
                    }
                ],
                "links": [
                    {
                        "rel": "agency",
                        "href": "https://[base_url]/api/agencies/4"
                    },
                    {
                        "rel": "person",
                        "href": "https://[base_url]/api/people/26afa54b28924461b3dc8bc4ff4dd063"
                    }
                ]
            },
            {
                "href": "https://[base_url]/api/memberships/949bfde4090c4d4c9ec14960ad88a115",
                "data": [
                    {
                        "name": "title",
                        "value": "Bundesrat"
                    },
                    {
                        "name": "modified",
                        "value": "2023-01-24T14:23:02.998538+00:00"
                    }
                ],
                "links": [
                    {
                        "rel": "agency",
                        "href": "https://[base_url]/api/agencies/4"
                    },
                    {
                        "rel": "person",
                        "href": "https://[base_url]/api/people/0d0a38d7e3cb4c008bf8c06bc74bd9b0"
                    }
                ]
            },
            ...
        ]
    }
}
```

## Authorization

The API employs token-based authentication, which allows for unrestricted usage of the API without encountering rate-limiting restrictions.
A token will be valid for one hour, afterward you have to request a new one.

To authenticate via a token, you need an access key generated by the user.

1. In the settings generate an API access key.

Open The Settings:
![Settings](../_static/settings.png)

![Api Settings](../_static/settings_api.png)

![Api Keys](../_static/api_keys.png)

Here you can add a key, by supplying a name and clicking the blue submit button.
The key will be generated and displayed (see red box in image above).

Once you have a key, you can request a token. The token is used for all other requests.

2. To request a token, make a GET to `/api/authenticate` and provide the API access key via Bearer token or HTTP basic authentication in the username part (the password part is not used).
3. The token must be provided with all requests using a Bearer token or the username part of the HTTP basic authentication (the password part is not used).

### cURL example (Bearer token):

```bash
#/bin/bash

# Get the token
JSON=$(curl -H 'Authorization: Bearer <your api access key from UI>' \
    <your api url>/api/authenticate)

TOKEN=$(echo $JSON | sed "s/{.*\"token\":\"\([^\"]*\).*}/\1/g")

# Make a request with the token to any endpoint
curl -X GET \
   -H "Authorization: Bearer $TOKEN" \
   <your api url>/api/agencies
```

### cURL example (HTTP basic authentication):

```bash
#/bin/bash

# Get the token
JSON=$(curl -u <your api access key from UI>: \
    --silent <your api url>/api/authenticate)

TOKEN=$(echo $JSON | sed "s/{.*\"token\":\"\([^\"]*\).*}/\1/g")

# Make a request with the token to any endpoint
curl -X GET \
   -u $(echo -n "$TOKEN:") \
   --silent <your api url>/api/agencies
```
