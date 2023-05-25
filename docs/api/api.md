# OneGov Cloud API

## Agency

The headless Agency API offers the following views:

- Agencies
- People
- Memberships

Currently, three cantons offer an api for their agencies.

- [Canton Appenzell Ausserrhoden](https://staatskalender.ar.ch/api/)
- [Canton Basel Stadt](https://staatskalender.bs.ch/api/)
- [Canton Zug](https://staka.zug.ch/api)

## Agencies View

The agencies view provides information about all the existing agencies
within the organisation. Each agency offers several data fields like title,
portrait, contact information, geolocation and more. Furthermore, the agency
api provides links to organigram, parent and child agencies as well as
memberships if given.

`curl https://[base_url]/agencies`

### Agency Query Fields

The agencies api support the following query fields:

| Query Fields | Description                                                    |
|--------------|--------------------------------------------------------------------|
| title        | queries for an agency title (name)                                 |
| updated_lt   | queries agencies updated before date specified (lower than)        |
| updated_le   | queries agencies updated before or at date specified (lower equal) |
| updated_eq   | queries agencies updated at date specified (equal)                 |
| updated_ge   | queries agencies updated after or date specified (greater equal)   |
| updated_gt   | queries agencies updated after date specified (greater than)       |

`curl https://[base_url]/agencies?name=datenschutzbeauftragter`
`curl https://[base_url]/agencies?updated.ge=2023-05-12T11:04:00`

> NOTE: Multiple query fields can be combined using the '&'

### Example

Here an example for the office 'Datenschutzbeautragter' where we query for
the agencies title (or part of the title)

Request:

`curl https://[base_url]/agencies?title=datenschutzbeauftragter`

Result:
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

`curl https://[base_url]/people?first_name=moritz`
`curl https://[base_url]/people?updated.gt=2023-05-12T11:04:00`

> NOTE: Multiple query fields can be applied using the '&'

### Example

Here an example for a person with first name Ursula and last name Meier a
really common name last name in switzerland.

Request:

`curl https://[base_url]/people?last_name=meier&first_name=ursula`

Result:
A collection+JSON of items if found including paging

```
{
    "collection": {
        "version": "1.0",
        "href": "http://localhost:8080/onegov_agency/bs/api/people",
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
                "href": "http://localhost:8080/onegov_agency/bs/api/people/7ef422f15f394b0fa0b3f337f52bbafb",
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
        ]
    }
}
```

## Election Day

Please refer to
[Election Day API](src/onegov/election_day/static/docs/api/README.md)
