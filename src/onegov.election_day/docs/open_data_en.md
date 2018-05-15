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
`type`|`election` for elections, `vote` for votes.
`title`|An object containing the translated titles.
`date`|The date (ISO 8601).
`domain`|The domain of influence (federation, canton, ...).
`url`|A link to the detailed view.
`completed`|True, if the vote or election is completed.
`progress`|An object containing the number already counted municipalities (`counted`) and the total number of municipalities (`total`).

Vote results contain the following additional information:

Name|Description
---|---
`answer`|The answer of the vote: `accepted`, `rejected`, `proposal` or `counter-proposal`.
`yeas_percentage`|Yeas percentage.
`nays_percentage`|Nays percentage.
`local` (*optional*)|Federal and cantonal votes within a communal instance may contain additionally the results of the municipality in the form of an object with `answer`, `yeas_percentage` and `nays_percentage`.

2 Election results
------------------

### Processed results

```
URL: /election/{id}/json
```

Returns the data of the main view in a structured form.

### Raw data

```
URL: /election/{id}/{data-format}
```

The raw data used to display the results of elections is available in the following formats:

Format|URL
---|---
JSON|`/data-json`
CSV|`/data-csv`

The following fields are included in all formats:

Name|Description
---|---
`election_title_{locale}`|Translated titles, for example `title_de_ch` for the German title.
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
`list_number_of_mandates`|The number of mandates this list has got. Only relevant for elections based on proportional representation.
`list_votes`|The number of votes this list has got. Only relevant for elections based on proportional representation.
`list_connection`|The ID of the list connection this list is connected to. Only relevant for elections based on proportional representation.
`list_connection_parent`|The ID of the parent list connection this list is connected to. Only relevant for elections based on proportional representation.
`candidate_family_name`|The family name of the candidate.
`candidate_first_name`|The first name of the candidate.
`candidate_id`|The ID of the candidate.
`candidate_elected`|True if the candidate has been elected.
`candidate_votes`|The number of votes this candidate got.
`panachage_votes_from_list_XX`|The number of votes the list got from the list with `list_id = XX`. A `list_id` with the value `999` marks the votes from the blank list.

Not yet counted municipalities are not included.

### Party results

```
URL: /election/{id}/{data-parties}
```

The raw data is available as CSV. The following fields are included:

Name|Description
---|---
`year`|The year of the election.
`total_votes`|The total votes of the election.
`name`|The name of the party.
`id`|ID of the party.
`color`|The color of the party.
`mandates`|The number of mandates.
`votes`|The number of votes.
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

The following fields are included in all formats:

Name|Description
---|---
`title_{locale}`|Translated titles, for example `title_de_ch` for the German title.
`date`|The date of the vote (an ISO 8601 date string).
`shortcode`|Internal shortcode (defines the ordering of votes on the same day).
`domain`|`federation` for federal, `canton` for cantonal votes.
`status`|Interim results (`interim`), final results (`final`) or unknown (`unknown`).
`type`|`proposal`, `counter-proposal` or `tie-breaker`.
`entity_id`|The id of the municipality. A value `0` represents the expats.
`name`|The name of the municipality.
`district`|The district of the municipality.
`counted`|True if the result was counted, False if the result not known yet (the voting counts are not final yet).
`yeas`|The number of yes votes.
`nays`|The number of no votes.
`invalid`|The number of invalid votes.
`empty`|The number of empty votes.
`eligible_voters`|The number of people eligible to vote.
