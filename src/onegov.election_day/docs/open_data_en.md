# Elections & Votes: Open Data

## Introduction

There are JSON alternatives for all important views. All responses contain the `Last-Modified` HTTP Header with the last time, the data has change (i.e. the last time, results of an election or vote have been uploaded).

"Municipality" might refer to a district, ward, etc.


## Contents

1. [Summarized results](#summarized-results)
2. [Election results](#election-results)
3. [Vote results](#vote-results)

## Summarized results

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
type|`election` for elections, `vote` for votes.
title|An object containing the translated titles.
date|The date (ISO 8601).
domain|The domain of influence (federation, canton, ...).
url|A link to the detailed view.
progess|An object containing the number already counted municipalities (`counted`) and the total number of municipalities (`total`).

Vote results contain the following additional information:

Name|Description
---|---
answer|The answer of the vote: `accepted`, `rejected`, `proposal` or `counter-proposal`.
yeas_percentage|Yeas percentage.
nays_percentage|Nays percentage.

## Election results

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
XLSX|`/data-xlsx`

The following fields are included in all formats:

Name|Description
---|---
election_title|Title of the election.
election_date|The date of the election (an ISO 8601 date string).
election_type|`proporz` for proportional, `majorz` for majority system.
election_mandates|The number of mandates.
election_absolute_majority|The absolute majority. Only relevant for elections based on majority system.
election_counted_entities|The number of already counted municipalities.
election_total_entities|The total number of municipalities.
entity_name|The name of the municipality.
entity_id|The id of the municipality/locale.
entity_elegible_voters|The number of people eligible to vote for this municipality.
entity_received_ballots|The number of received ballots for this municipality.
entity_blank_ballots|The number of blank ballots for this municipality.
entity_invalid_ballots|The number of invalid ballots for this municipality.
entity_unaccounted_ballots|The number of unaccounted ballots for this municipality.
entity_accounted_ballots|The number of accounted ballots for this municipality.
entity_blank_votes|The number of blank votes for this municipality.
entity_invalid_votes|The number of invalid votes for this municipality. Zero for elections based on proportional representation.
entity_accounted_votes|The number of accounted votes for this municipality.
list_name|The name of the list this candidate appears on. Only relevant for elections based on proportional representation.
list_id|The id of the list this candidate appears on. Only relevant for elections based on proportional representation.
list_number_of_mandates|The number of mandates this list has got. Only relevant for elections based on proportional representation.
list_votes|The number of votes this list has got. Only relevant for elections based on proportional representation.
list_connection|The ID of the list connection this list is connected to. Only relevant for elections based on proportional representation.
list_connection_parent|The ID of the parent list connection this list is connected to. Only relevant for elections based on proportional representation.
candidate_family_name|The family name of the candidate.
candidate_first_name|The first name of the candidate.
candidate_id|The ID of the candidate.
candidate_elected|True if the candidate has been elected.
candidate_votes|The number of votes this candidate got.
panachage_votes_from_list_XX|The number of votes the list got from the list with `list_id = XX`. A `list_id` with the value `999` marks the votes from the blank list.

Not yet counted municipalities are not included.

### Party results

```
URL: /election/{id}/{data-parties}
```

The raw data is available as CSV. The following fields are included:

Name|Description
---|---
name|The name of the party.
mandates|The number of mandates.
votes|The number of votes.

## Vote results

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
XLSX|`/data-xlsx`

The following fields are included in all formats:

Name|Description
---|---
title|Title of the vote.
date|The date of the vote (an ISO 8601 date string).
shortcode|Internal shortcode (defines the ordering of votes on the same day).
domain|`federation` for federal, `canton` for cantonal votes.
type|`proposal`, `counter-proposal` or `tie-breaker`.
group|The designation of the result. May be the district, the town's name divided by a slash, the city's name and the city's district divided by a slash or simply the town's name. This depends entirely on the canton.
entity_id|The id of the municipality/locale.
counted|True if the result was counted, False if the result not known yet (the voting counts are not final yet).
yeas|The number of yes votes.
nays|The number of no votes.
invalid|The number of invalid votes.
empty|The number of empty votes.
elegible_voters|The number of people elegible to vote.
