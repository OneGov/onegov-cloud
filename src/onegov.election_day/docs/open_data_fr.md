# Elections et votes : Données ouvertes

## Introduction

There are JSON alternatives for all important views.

All responses contain the `Last-Modified` HTTP Header with the last time, the data has change (i.e. the last time, results of an election or vote have been uploaded).

## Contents

1. [Summarized results](#summarized-results)
2. [Election results](#election-results)
3. [Vote results](#vote-results)

## Summarized results

**URL (latest)**: `/json`

**URL (archive by year)**: `/archive/{year}/json`

**URL (archive by date)**: `/archive/{year}-{month}-{day}/json`

The summarized results displayed at the home page (only the results of latest votes and elections) and the archive (browsable by year or date) is also available as JSON. The data contains some global informations and for every election and vote the following commong information:

- **type**: `election` for elections, `vote` for votes.

- **title**: An object containing the translated titles.

- **date**: The date (ISO 8601).

- **domain**: The domain of influence (federation, canton, ...).

- **url**: A link to the detailed view.

- **data_url**: A link to the detailed JSON data, see below.

- **progess**: An object containing the number already counted municipalities (`counted`) and the total number of municipalities (`total`).

Vote results contain the following additional information:

- **answer**: The answer of the vote: `accepted`, `rejected`, `proposal` or `counter-proposal`.

- **yeas_percentage**: Yeas percentage.

- **nays_percentage**: Nays percentage.

## Election results

**URL**: `/election/{id}/{format}`

Les données brutes utilisées pour afficher les résultats de votes sont disponibles dans les formats suivants:

- **JSON**: (`/json`)

- **CSV**: (`/csv`)

- **XLSX**: (`/xlsx`)

Les champs suivants sont inclus dans tous les formats:

- **election_title**: Titre de l'élection.

- **election_date**: La date de l'élection (an ISO 8601 date string).

- **election_type**: "proporz" pour proportionnelle, "majorz" pour le système majoritaire.

- **election_mandates**: Nombre de mandats.

- **election_absolute_majority**: The absolute majority. Only relevant for elections based on majority system.

- **election_counted_municipalities**: The number of already counted municipalities.

- **election_total_municipalities**: The total number of municipalities.

- **municipality_name**: Le nom de la municipalité.

- **municipality_bfs_number**: L'identifiant de la municipalité / locale ("BFS Nummer").

- **municipality_elegible_voters**: Le nombre de personnes éligible à voter pour cette municipalité.

- **municipality_received_ballots**: Le nombre de bulletins de vote reçus pour cette municipalité.

- **municipality_blank_ballots**: Le nombre de bulletins blancs pour cette municipalité.

- **municipality_invalid_ballots**: Le nombre de bulletins nuls pour cette municipalité.

- **municipality_unaccounted_ballots**: Le nombre de bulletins de vote non comptabilisés pour cette municipalité.

- **municipality_accounted_ballots**: Le nombre de bulletins de votes comptabilisés pour cette municipalité.

- **municipality_blank_votes**: Le nombre de votes en blanc pour cette municipalité.

- **municipality_invalid_votes**: Le nombre de votes valides pour cette municipalité. Zéro pour les élections sur la base de la représentation proportionnelle.

- **municipality_accounted_votes**: Le nombre de votes comptabilisés pour cette municipalité.

- **list_name**: Le nom de la liste sur laquelle ce candidat apparaît. Uniquement valable pour les élections sur la base de la représentation proportionnelle.

- **list_id**: The id of the list this candidate appears on. Only relevant for elections based on proportional representation.

- **list_number_of_mandates**: The number of mandates this list has got. Only relevant for elections based on proportional representation.

- **list_votes**: Le nombre de votes que cette liste a obtenu. Uniquement valable pour les élections sur la base de la représentation proportionnelle.

- **list_connection**: L'Identifiant de la connexion de la liste à laquelle cette liste est connectée. Uniquement valable pour les élections sur la base de la représentation proportionnelle.

- **list_connection_parent**: L'Identifiant de la connexion de liste parent à laquelle cette liste est connectée. Uniquement valable pour les élections sur la base de la représentation proportionnelle.

- **candidate_family_name**: Le nom de famille du candidat.

- **candidate_first_name**: Le prénom du candidat.

- **candidate_id**: The ID of the candidate.

- **candidate_elected**: Vrai si le candidat a été élu.

- **candidate_votes**: Le nombre de voix que ce candidat a obtenu.

## Vote results

**URL**: `/vote/{id}/{format}`

Les données brutes utilisées pour afficher les résultats de votes sont disponibles dans les formats suivants:

- **JSON**: (`/json`)

- **CSV**: (`/csv`)

- **XLSX**: (`/xlsx`)

Les champs suivants sont inclus dans tous les formats:

- **title**: Nom du vote:

- **date**: La date du vote (une chaîne de date ISO 8601).

- **shortcode**: Shortcode interne (définit l'ordre des votes ayant lieu le même jour).

- **domain**: "fédération" pour fédéral, "canton" for les votes cantonaux.

- **type**: "proposition" (Vorschlag), "contre-proposition" (Gegenvorschlag) or "jeu décisif" (Stichfrage).

- **group**: La désignation du résultat. Peut être le district, le nom de la ville divisé par un slash, le nom de la ville et le district de la ville divisés par un slash ou simplement le nom de la ville. Cela dépend entièrement du canton.

- **municipality_id**: La référence de la municipalité/localité. Mieux connu sous le nom de "BFS Nummer"

- **counted**: Vrai si le résultat a été compté, faux si le résultat n'est pas encore connu (le compte des votes n'est pas encore fini).

- **yeas**: Nombre de votes oui

- **nays**: Nombre de votes non

- **invalid**: Nombre de votes invalides.

- **empty**: Nombre de votes blancs

- **elegible_voters**: Nombre de personne aptes à voter.
