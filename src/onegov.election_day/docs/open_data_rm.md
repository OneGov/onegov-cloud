# Elecziuns & votaziuns: Open Data

## Contents

1. [Summarized results](#summary)
2. [Election results](#election)
3. [Vote results](#vote)

## Summarized results

**URL (latest)**: `/json`

**URL (archive by year)**: `/archive/{year}/json`

**URL (archive by date)**: `/archive/{year}-{month}-{day}/json`

**URL (election)**: `/election/{id}/summary`

**URL (vote)**: `/vote/{id}/summary`

The summarized results displayed at the home page (only the results of latest votes and elections) and the archive (browsable by year or date) is also available as JSON. The data contains some global informations and for every election and vote the following commong information:

- **type**: `election` for elections, `vote` for votes.

- **title**: An object containing the translated titles.

- **date**: The date (ISO 8601).

- **domain**: The domain of influence (federation, canton, ...).

- **url**: A link to the detailed view.

- **progess**: An object containing the number already counted municipalities (`counted`) and the total number of municipalities (`total`).

Vote results contain the following additional information:

- **answer**: The answer of the vote: `accepted`, `rejected`, `proposal` or `counter-proposal`.

- **yeas_percentage**: Yeas percentage.

- **nays_percentage**: Nays percentage.

## Election results

**URL**: `/election/{id}/{data-format}`

Las datas nunelavuradas che vegnan duvradas per mussar ils resultats stattan a disposiziun en ils suandants formats:

- **JSON**: (`/data-json`)

- **CSV**: (`/data-csv`)

- **XLSX**: (`/data-xlsx`)

Ils suandants champs èn disponibels en tut ils formats:

- **election_title**: Titel da l'elecziun

- **election_date**: La data da l'elecziun (sco segns ISO 8601)

- **election_type**: "proporz" en cas d'ina elecziun da proporz, "majorz" en cas d'ina elecziun da maiorz

- **election_mandates**: Il dumber dals sezs.

- **election_absolute_majority**: The absolute majority. Only relevant for elections based on majority system.

- **election_counted_municipalities**: The number of already counted municipalities.

- **election_total_municipalities**: The total number of municipalities.

- **municipality_name**: Il num da la vischnanca/dal lieu

- **municipality_bfs_number**: La ID da la vischnanca/dal lieu. Pli enconuschent sco "numer UST".

- **municipality_elegible_voters**: Il dumber da las votantas e dals votants da la vischnanca/dal lieu.

- **municipality_received_ballots**: Il dumber dals cedels electorals consegnads da la vischnanca/dal lieu.

- **municipality_blank_ballots**: Il dumber dals cedels electorals vids da la vischnanca/dal lieu.

- **municipality_invalid_ballots**: Il dumber dals cedels electorals nunvalaivels da la vischnanca/dal lieu.

- **municipality_unaccounted_ballots**: Il dumber dals cedels electorals nunvalaivels u vids da la vischnanca/dal lieu.

- **municipality_accounted_ballots**: Il dumber dals cedels electorals valaivels da la vischnanca/dal lieu.

- **municipality_blank_votes**: Il dumber da las vuschs vidas da la vischnanca/dal lieu.

- **municipality_invalid_votes**: Il dumber da las vuschs nunvalaivlas da la vischnanca/dal lieu. Nagins en cas d'ina elecziun da proporz.

- **municipality_accounted_votes**: Il dumber da las vuschs valaivlas da la vischnanca/dal lieu.

- **list_name**: Il num da la glista da la persuna che candidescha. Mo en cas d'elecziuns da proporz.

- **list_id**: The id of the list this candidate appears on. Only relevant for elections based on proportional representation.

- **list_number_of_mandates**: The number of mandates this list has got. Only relevant for elections based on proportional representation.

- **list_votes**: Il dumber da las vuschs da las glistas. Mo tar elecziuns da proporz.

- **list_connection**: La ID da la colliaziun da glistas. Mo tar elecziuns da proporz.

- **list_connection_parent**: La ID da la colliaziun da glistas surordinada. Mo en cas d'elecziuns da proporz e sch'i sa tracta d'ina sutcolliaziun da glistas.

- **candidate_family_name**: Il num da famiglia da la persuna che candidescha.

- **candidate_first_name**: Il prenum da la persuna che candidescha.

- **candidate_id**: The ID of the candidate.

- **candidate_elected**: True if the candidate has been elected.

- **candidate_votes**: Il dumber da las vuschs da candidat(a) da la vischnanca/dal lieu.

## Vote results

**URL**: `/vote/{id}/{data-format}`

Las datas nunelavuradas che vegnan duvradas per mussar ils resultats stattan a disposiziun en ils suandants formats:

- **JSON**: (`/data-json`)

- **CSV**: (`/data-csv`)

- **XLSX**: (`/data-xlsx`)

Ils suandants champs èn disponibels en tut ils formats:

- **title**: Titel da la votaziun.

- **date**: La data da la votaziun (sco segns ISO 8601).

- **shortcode**: Scursanida interna (definescha la successiun da pliras votaziuns che han lieu il medem di).

- **domain**: "federation" per votaziuns naziunalas, "canton" per votaziuns chantunalas

- **type**: "proposal" (proposta), "counter-proposal" (cuntraproposta) or "tie-breaker" (dumonda decisiva).

- **group**: La derivanza dal resultat. Quai po esser il district e la vischnanca, separads cun in stritg diagonal, il num da la citad ed il num dal circul, er separads cun in stritg diagonal, u simplamain il num da la vischnanca. Quai dependa dal chantun respectiv.

- **municipality_id**: La ID da la vischnanca/dal lieu. Pli enconuschent sco "numer UST".

- **counted**: Gist, sch'il resultat è vegnì eruì. Fauss, sch'il resultat n'è anc betg enconuschent (las valurs n'èn anc betg correctas).

- **yeas**: Il dumber da las vuschs affirmativas

- **nays**: Il dumber da las vuschs negativas

- **invalid**: Il dumber da las vuschs nunvalaivlas

- **empty**: Il dumber da las vuschs vidas

- **elegible_voters**: Il dumber da las persunas cun dretg da votar
