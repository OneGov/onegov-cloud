Elezioni & votazioni: Open Data

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

I dati grezzi utilizzati per indicare i risultati sono disponibili nei formati seguenti:

- **JSON**: (`/json`)

- **CSV**: (`/csv`)

- **XLSX**: (`/xlsx`)

I seguenti campi sono contenuti in tutti i formati:

- **election_title**: Titolo dell'elezione.

- **election_date**: Data dell'elezione (stringa data in formato ISO 8601)

- **election_type**: "proporz" per il sistema proporzionale, "majorz" per il sistema maggioritario.

- **election_mandates**: Numero di mandati.

- **election_absolute_majority**: The absolute majority. Only relevant for elections based on majority system.

- **election_counted_municipalities**: The number of already counted municipalities.

- **election_total_municipalities**: The total number of municipalities.

- **municipality_name**: Nome del comune.

- **municipality_bfs_number**: Identificativo del comune/località ("BFS Nummer").

- **municipality_elegible_voters**: Numero degli aventi diritto al voto di questo comune.

- **municipality_received_ballots**: Numero di schede ricevute per questo comune.

- **municipality_blank_ballots**: Numero di schede bianche per questo comune.

- **municipality_invalid_ballots**: Numero di schede nulle per questo comune.

- **municipality_unaccounted_ballots**: Numero di schede non valide per questo comune.

- **municipality_accounted_ballots**: Numero di schede valide per questo comune.

- **municipality_blank_votes**: Numero di voti nulli in questo comune.

- **municipality_invalid_votes**: Numero di voti non validi in questo comune. Zero per elezioni basate sul sistema proporzionale.

- **municipality_accounted_votes**: Numero di voti validi in questo comune.

- **list_name**: Nome della lista alla quale appartiene questo candidato. Valido solo per elezioni basate sul sistema proporzionale.

- **list_id**: The id of the list this candidate appears on. Only relevant for elections based on proportional representation.

- **list_number_of_mandates**: The number of mandates this list has got. Only relevant for elections based on proportional representation.

- **list_votes**: Numero di voti ricevuti da questa lista. Valido solo per elezioni basate sul sistema proporzionale.

- **list_connection**: L'identificato del collegamento della lista a cui questa lista è collegata. Valido solo per elezioni basate sul sistema proporzionale.

- **list_connection_parent**: L'identificativo del collegamento della lista padre a cui questa lista è collegata. Valido solo per elezioni basate sul sistema proporzionale.

- **candidate_family_name**: Cognome del candidato.

- **candidate_first_name**: Nome del candidato.

- **candidate_id**: The ID of the candidate.

- **candidate_elected**: Vero se il candidato è stato eletto.

- **candidate_votes**: Numero di voti ricevuti da questo candidato.

## Vote results

**URL**: `/vote/{id}/{format}`

I dati grezzi utilizzati per indicare i risultati sono disponibili nei formati seguenti:

- **JSON**: (`/json`)

- **CSV**: (`/csv`)

- **XLSX**: (`/xlsx`)

I seguenti campi sono contenuti in tutti i formati:

- **title**: Titolo della votazione.

- **date**: Data della votazione (una stringa ISO 8601).

- **shortcode**: Abbreviazione interna (definisce l'ordine di diverse votazioni in un giorno).

- **domain**: "federation" per votazioni federali, "canton" per votazioni cantonali

- **type**: "proposal" (progetto), "counter-proposal" (controprogetto) or "tie-breaker" (domanda eventuale).

- **group**: Da dove viene il risultato. Si può trattare del distretto e del comune, separati da una barra, del nome della città e del nome del circolo, anch'essi separati da una barra, o del semplice nome di un comune. Tutto ciò dipende dal rispettivo Cantone.

- **municipality_id**: ID del comune/dell'ubicazione. Meglio noto come "numero UST".

- **counted**: Vero, se lo spoglio è stato completato. Falso, se il risultato non è ancora noto (i valori non sono ancora corretti).

- **yeas**: Numero di voti favorevoli

- **nays**: Numero di voti contrari

- **invalid**: Numero di voti nulli

- **empty**: Numero di voti in bianco

- **elegible_voters**: Numero di aventi diritto di voto
