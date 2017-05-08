Elezioni & votazioni: Dati aperti
=================================

## Introduzione

Ci sono alternative al formato JSON per tutte le visualizzazioni più importanti. Tutte le risposte contengono l'intestazione HTTP `Last-Modified` (Ultima modifica) con l'ultima volta in cui si è verificata una modifica dei dati (ad es. l'ultima volta in cui i risultati di un'elezione o i voti sono stati caricati).

"Comune" si riferisce ad un distretto, una circoscrizione elettorale, etc.

Contenuti
---------

1. [Riepilogo dei risultati](#1-riepilogo-dei-risultati)
2. [Risultati dell'elezione](#2-risultati-dellelezione)
3. [Risultati della votazione](#3-risultati-della-votazione)

1 Riepilogo dei risultati
-------------------------

```
URL (ultimo): /json
URL (archivio per anno): /archive/{anno}/json
URL (archivio per data): /archive/{anno}-{mese}-{giorno}/json
URL (elezione): /election/{id}/summary
URL (votazione): /vote/{id}/summary
```

Il riepilogo dei risultati visualizzato sulla pagina iniziale (solo i risultati delle ultime votazioni ed elezioni) e l'archivio (navigabile per anno o data) sono disponibili anche nel formato JSON. I dati contengono alcune informazioni globali e, per ogni elezione e votazione, le seguenti informazioni comuni:

Nome|Descrizione
---|---
`type`|`election` per elezioni, `vote` per votazioni.
`title`|Un oggetto contenente i titoli tradotti.
`date`|La data (ISO 8601).
`domain`|Il dominio di influenza (federazione, cantone, ...).
`url`|Un collegamento alla visualizzazione dettagliata.
`completed`|True, if the vote or election is completed.
`progess`|Un oggetto contenente il numero dei comuni già contati (`counted`) e il numero totale di comuni (`total`).

I risultati della votazione contengono le seguenti informazioni aggiuntive:

Nome|Descrizione
---|---
`answer`|La risposta del voto: `accepted` (accettato), `rejected` (respinto), `proposal` o `counter-proposal` (controproposta).
`yeas_percentage`|Percentuale voti favorevoli.
`nays_percentage`|Percentuale voti contrari.
`local` (*optional*)|Federal and cantonal votes within a communal instance may contain additionally the results of the municipality in the form of an object with `answer`, `yeas_percentage` and `nays_percentage`.


2 Risultati dell'elezione
-------------------------

### Risultati elaborati

```
URL: /election/{id}/json
```

Rimanda i dati della visualizzazione principale in forma strutturata.

### Dati grezzi

```
URL: /election/{id}/{data-format}
```

I dati grezzi utilizzati per indicare i risultati sono disponibili nei formati seguenti:

Formato|URL
---|---
JSON|`/data-json`
CSV|`/data-csv`
XLSX|`/data-xlsx`

I seguenti campi sono contenuti in tutti i formati:

Nome|Descrizione
---|---
`election_title`|Titolo dell'elezione.
`election_date`|Data dell'elezione (stringa data in formato ISO 8601)
`election_type`|`proporz` per il sistema proporzionale, `majorz` per il sistema maggioritario.
`election_mandates`|Numero di mandati.
`election_absolute_majority`|La maggioranza assoluta. Rilevante solo per le elezioni basate sul sistema di maggioranza.
`election_status`|Interim results (`interim`), final results (`final`) or unknown (`unknown`).
`election_counted_entities`|Il numero di comuni già contati.
`election_total_entities`|Il numero totale dei comuni.
`entity_name`|Nome del comune.
`entity_id`|Identificativo del comune. A value `0` represents the expats.
`entity_elegible_voters`|Numero degli aventi diritto al voto di questo comune.
`entity_received_ballots`|Numero di schede ricevute per questo comune.
`entity_blank_ballots`|Numero di schede bianche per questo comune.
`entity_invalid_ballots`|Numero di schede nulle per questo comune.
`entity_unaccounted_ballots`|Numero di schede non valide per questo comune.
`entity_accounted_ballots`|Numero di schede valide per questo comune.
`entity_blank_votes`|Numero di voti nulli in questo comune.
`entity_invalid_votes`|Numero di voti non validi in questo comune. Zero per elezioni basate sul sistema proporzionale.
`entity_accounted_votes`|Numero di voti validi in questo comune.
`list_name`|Nome della lista alla quale appartiene questo candidato. Valido solo per elezioni basate sul sistema proporzionale.
`list_id`|L'identificativo della lista su cui questo candidato compare. Rilevante solo per le elezioni basate sul metodo proporzionale.
`list_number_of_mandates`|Il numero di mandati ottenuti da questa lista. Rilevante solo per le elezioni basate sul metodo proporzionale.
`list_votes`|Numero di voti ricevuti da questa lista. Valido solo per elezioni basate sul sistema proporzionale.
`list_connection`|L'identificato del collegamento della lista a cui questa lista è collegata. Valido solo per elezioni basate sul sistema proporzionale.
`list_connection_parent`|L'identificativo del collegamento della lista padre a cui questa lista è collegata. Valido solo per elezioni basate sul sistema proporzionale.
`candidate_family_name`|Cognome del candidato.
`candidate_first_name`|Nome del candidato.
`candidate_id`|L'identificativo del candidato.
`candidate_elected`|Vero se il candidato è stato eletto.
`candidate_votes`|Numero di voti ricevuti da questo candidato.
`panachage_votes_from_list_XX`|The number of votes the list got from the list with `list_id = XX`. A `list_id` with the value `999` marks the votes from the blank list.

I comuni non ancora contati non sono inclusi.

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
`color`|The color of the party.
`mandates`|The number of mandates.
`votes`|The number of votes.

3 Risultati della votazione
---------------------------

### Risultati elaborati

```
URL: /vote/{id}/json
```

Rimanda i dati della visualizzazione principale in forma strutturata.

### Dati grezzi

```
URL: /vote/{id}/{data-format}
```

I dati grezzi utilizzati per indicare i risultati sono disponibili nei formati seguenti:

Formato|URL
---|---
JSON|`/data-json`
CSV|`/data-csv`
XLSX|`/data-xlsx`

I seguenti campi sono contenuti in tutti i formati:

Nome|Descrizione
---|---
`title`|Titolo della votazione.
`date`|Data della votazione (una stringa ISO 8601).
`shortcode`|Abbreviazione interna (definisce l'ordine di diverse votazioni in un giorno).
`domain`|`federation` per votazioni federali, `canton` per votazioni cantonali.
`status`|Interim results (`interim`), final results (`final`) or unknown (`unknown`).
`type`|`proposal` (progetto), `counter-proposal` (controprogetto) or `tie-breaker` (domanda eventuale).
`group`|Da dove viene il risultato. Si può trattare del distretto e del comune, separati da una barra, del nome della città e del nome del circolo, anch'essi separati da una barra, o del semplice nome di un comune. Tutto ciò dipende dal rispettivo Cantone.
`entity_id`|ID del comune/dell'ubicazione. A value `0` represents the expats.
`counted`|Vero, se lo spoglio è stato completato. Falso, se il risultato non è ancora noto (i valori non sono ancora corretti).
`yeas`|Numero di voti favorevoli
`nays`|Numero di voti contrari
`invalid`|Numero di voti nulli
`empty`|Numero di voti in bianco
`elegible_voters`|Numero di aventi diritto di voto
