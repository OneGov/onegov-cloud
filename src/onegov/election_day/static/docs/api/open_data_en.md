Elections & Votes: Open Data
============================

Terms of use
------------

Open use. Must provide the source.

- You may use this dataset for non-commercial purposes.
- You may use this dataset for commercial purposes.
- You must provide the source (author, title and link to the dataset).

Introduction
------------

There are JSON alternatives for all important views. All responses contain the `Last-Modified` HTTP Header with the last time, the data has change (i.e. the last time, results of an election or vote have been uploaded).

"Municipality" might refer to a district, ward, etc.

Contents
--------

1. [Summarized results](#1-summarized-results)
2. [Election results](#2-election-results)
3. [Vote results](#3-vote-results)

1 Summarized results
--------------------

```
URL (latest): /json
URL (archive by year): /archive/{year}/json
URL (archive by date): /archive/{year}-{month}-{day}/json
URL (election): /election/{id}/summary
URL (vote): /vote/{id}/summary
```

The summarized results displayed at the home page (only the results of latest votes and elections) and the archive (browsable by year or date) is also available as JSON. The data contains some global informations and for every election and vote the following commong information:

Name|Description
---|---
`type`|`election` for elections, `election_compound` for election compounds, `vote` for votes.
`title`|An object containing the translated titles.
`date`|The date (ISO 8601).
`domain`|The domain of influence (federation, canton, ...).
`url`|A link to the detailed view.
`completed`|True, if the vote or election is completed.
`progress`|An object containing the number already counted municipalities/elections (`counted`) and the total number of municipalities/elections (`total`).
`last_modified`|Last time, the data has changed (ISO 8601).
`turnout`|Voter turnout in per cent.

Vote results contain the following additional information:

Name|Description
---|---
`answer`|The answer of the vote: `accepted`, `rejected`, `proposal` or `counter-proposal`.
`yeas_percentage`|Yeas percentage.
`nays_percentage`|Nays percentage.
`local` (*optional*)|Federal and cantonal votes within a communal instance may contain additionally the results of the municipality in the form of an object with `answer`, `yeas_percentage` and `nays_percentage`.

Election results contain the following additional information:

Name|Description
---|---
`elected`|A list with the elected candidates.

Election compound results contain the following additional information:

Name|Description
---|---
`elected`|A list with the elected candidates.
`elections`|A list with links to the elections.

2 Election results
------------------

### Processed results

```
URL: /election/{id}/json
```

Returns the data of the main view in a structured form.

### Raw data

#### Candidate results

```
URL: /election/{id}/data-{format}
```

The raw data of the candidates are available in the following formats:

Format|URL
---|---
JSON|`/data-json`
CSV|`/data-csv`

The following fields are included in all formats:

Name|Description
---|---
`election_id`|ID of the election. Used in the URL.
`election_title_{locale}`|Translated titles, for example `title_de_ch` for the German title.
`election_short_title_{locale}`|Translated short titles, for example `title_de_ch` for the German short title.
`election_date`|The date of the election (an ISO 8601 date string).
`election_domain`|federal (`federation`), cantonal (`canton`), regional (`region`) or communal (`municipality`)
`election_type`|proportional (`proporz`) or majority system (`majorz`)
`election_mandates`|The number of mandates/seats.
`election_absolute_majority`|The absolute majority. Only relevant for elections based on majority system.
`election_status`|Interim results (`interim`), final results (`final`) or unknown (`unknown`).
`entity_id`|The id of the municipality/locale. A value `0` represents the expats. A value `0` represents the expats.
`entity_name`|The name of the municipality.
`entity_district`|The district of the municipality.
`entity_counted`|`True` if the result was counted.
`entity_eligible_voters`|The number of people eligible to vote for this municipality.
`entity_expats`|Number of expats for this municipality.
`entity_received_ballots`|The number of received ballots for this municipality.
`entity_blank_ballots`|The number of blank ballots for this municipality.
`entity_invalid_ballots`|The number of invalid ballots for this municipality.
`entity_unaccounted_ballots`|The number of unaccounted ballots for this municipality.
`entity_accounted_ballots`|The number of accounted ballots for this municipality.
`entity_blank_votes`|The number of blank votes for this municipality.
`entity_invalid_votes`|The number of invalid votes for this municipality. Zero for elections based on proportional representation.
`entity_accounted_votes`|The number of accounted votes for this municipality.
`list_name`|The name of the list this candidate appears on. Only relevant for elections based on proportional representation.
`list_id`|The id of the list this candidate appears on. Only relevant for elections based on proportional representation.
`list_color`|The color of the list as a hexadecimal value, e.g. `#a6b784`.
`list_number_of_mandates`|The number of mandates this list has got. Only relevant for elections based on proportional representation.
`list_votes`|The number of votes this list has got. Only relevant for elections based on proportional representation.
`list_connection`|The ID of the list connection this list is connected to. Only relevant for elections based on proportional representation.
`list_connection_parent`|The ID of the parent list connection this list is connected to. Only relevant for elections based on proportional representation.
`list_panachage_votes_from_list_XX`|The number of votes the list got from the list with `list_id = XX`. A `list_id` with the value `999` marks the votes from the blank list. Does not contain votes from the own list.
`candidate_family_name`|The family name of the candidate.
`candidate_first_name`|The first name of the candidate.
`candidate_id`|The ID of the candidate.
`candidate_elected`|True if the candidate has been elected.
`candidate_party`|The name of the party.
`candidate_party_color`|The color of the party as a hexadecimal value, e.g. `#a6b784`.
`candidate_gender`|The gender of the candidate: `female`, `male` or `undetermined`.
`candidate_year_of_birth`|The year of the candidate.
`candidate_votes`|The number of votes this candidate got.
`candidate_panachage_votes_from_list_XX`|The number of votes the candidate got from the list with `list_id = XX`. A `list_id` with the value `999` marks the votes from the blank list.

Election compounds contain the following additional fields:

Name|Description
---|---
`compound_id`|ID of the election compound. Used in the URL.
`compound_title_{locale}`|Translated titles, for example `title_de_ch` for the German title.
`compound_short_title_{locale}`|Translated short titles, for example `title_de_ch` for the German short title.
`compound_date`|The date of the election compound (an ISO 8601 date string).
`compound_mandates`|The total number of mandates/seats.

Not yet counted municipalities are not included.

### Party results

```
URL: /election/{id}/data-parties-{format}
```

The raw data of the parties are available in the following formats:

Format|URL
---|---
JSON|`/data-parties-json`
CSV|`/data-parties-csv`

The following fields are included in all formats:

Name|Description
---|---
`domain`|The domain of influence to which the line applies. Optional.
`domain_segment`|The unit of the domain of influence to which the line applies. Optional.
`year`|The year of the election.
`total_votes`|The total votes of the election.
`name`|The name of the party in the default language.
`name_{locale}`|Translated name of the party, e.g. `name_de_ch` for the German name.
`id`|ID of the party.
`color`|The color of the party as a hexadecimal value, e.g. `#a6b784`.
`mandates`|The number of mandates.
`votes`|The number of votes.
`voters_count`|Voters count. The cumulative number of votes per total number of mandates per election. For election compounds only.
`voters_count_percentage`|Voters count (percentage). The cumulative number of votes per total number of mandates per election (percentage). For election compounds only.
`panachage_votes_from_{XX}`|The number of votes the party got from the party with `id = XX`. An `id` with the value `999` marks the votes from the blank list.

3 Vote results
--------------

### Processed results

```
URL: /vote/{id}/json
```

Returns the data of the main view in a structured form.

### Raw data

```
URL: /vote/{id}/{data-format}
```

The raw data used to display the results of votes is available in the following formats:

Format|URL
---|---
JSON|`/data-json`
CSV|`/data-csv`

The following fields are in `JSON` and `CSV` formats:

Name|Description
---|---
`id`|ID of the vote. Used in the URL.
`title_{locale}`|Translated titles, for example `title_de_ch` for the German title.
`short_title_{locale}`|Translated short titles, for example `title_de_ch` for the German title.
`date`|The date of the vote (an ISO 8601 date string).
`shortcode`|Internal shortcode (defines the ordering of votes on the same day).
`domain`|`federation` for federal, `canton` for cantonal votes.
`status`|Interim results (`interim`), final results (`final`) or unknown (`unknown`).
`answer`|The answer of the vote: `accepted`, `rejected`, `proposal` or `counter-proposal`.
`type`|Type: `proposal`, `counter-proposal` or `tie-breaker`.
`ballot_answer`| The answer by type: `accepted` or `rejected` for `type=proposal` and `type=counter-proposal`;
`proposal` or `counter-proposal` for `type=tie-breaker`.
`district`|The district of the municipality.
`name`|The name of the municipality.
`entity_id`|The id of the municipality. A value `0` represents the expats.
`counted`|True if the result was counted, False if the result not known yet (the voting counts are not final yet).
`yeas`|The number of yes votes.
`nays`|The number of no votes.
`invalid`|The number of invalid votes.
`empty`|The number of empty votes.
`eligible_voters`|The number of people eligible to vote.
`expats`|Number of expats.

4 Sitemap
---------

```
URL: /sitemap.xml
```

Returns a sitemap in XML format (https://www.sitemaps.org/protocol.html)

```
URL: /sitemap.json
```

Returns the sitemap as JSON.
