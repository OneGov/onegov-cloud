Elezioni & votazioni: Open Data
===============================

Condizioni d’uso
----------------

Libero utilizzo. Indicazione della fonte obbligatoria.

- Questo set di dati può essere utilizzato a fini non commerciali.
- Questo set di dati può essere utilizzato a fini commerciali.
- È obbligatoria l’indicazione della fonte (autore, titolo e link al set di dati).

Introduzione
------------

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
`type`|`election` per elezioni, `election_compound` per componente delle elezioni, `vote` per votazioni.
`title`|Un oggetto contenente i titoli tradotti.
`date`|La data (ISO 8601).
`domain`|Il dominio di influenza (federazione, cantone, ...).
`url`|Un collegamento alla visualizzazione dettagliata.
`completed`|True, if the vote or election is completed.
`progress`|Un oggetto contenente il numero dei comuni/elezioni già contati (`counted`) e il numero totale di comuni/elezioni (`total`).
`last_modified`|L'ultima volta in cui si è verificata una modifica dei dati (ISO 8601).
`turnout`|Affluenza alle urne in percentuale.

I risultati della votazione contengono le seguenti informazioni aggiuntive:

Nome|Descrizione
---|---
`answer`|La risposta del voto: `accepted` (accettato), `rejected` (respinto), `proposal` o `counter-proposal` (controproposta).
`yeas_percentage`|Percentuale voti favorevoli.
`nays_percentage`|Percentuale voti contrari.
`local` (*optional*)|Federal and cantonal votes within a communal instance may contain additionally the results of the municipality in the form of an object with `answer`, `yeas_percentage` and `nays_percentage`.

I risultati delle elezioni contengono le seguenti informazioni aggiuntive:

Nome|Descrizione
---|---
`elected`|Una lista con i candidati eletti.

I risultati del componente delle elezioni contengono le seguenti informazioni aggiuntive:

Nome|Descrizione
---|---
`elected`|Una lista con i candidati eletti.
`elections`|Una lista con link alle elezioni.

2 Risultati dell'elezione
-------------------------

### Risultati elaborati

```
URL: /election/{id}/json
```

Rimanda i dati della visualizzazione principale in forma strutturata.

### Dati grezzi

#### Risultati dei candidati

```
URL: /election/{id}/data-{format}
```

I dati grezzi dei candidati sono disponibili nei formati seguenti:

Formato|URL
---|---
JSON|`/data-json`
CSV|`/data-csv`

I seguenti campi sono contenuti in tutti i formati:

Nome|Descrizione
---|---
`election_id`|ID dell'elezione. Utilizzato nell'URL.
`election_title_{locale}`|Titoli tradotti, ad esempio `title_de_ch` per il titolo tedesco.
`election_short_title_{locale}`|Titoli abbreviati tradotti, ad esempio `title_de_ch` per il titolo abbreviato tedesco.
`election_date`|Data dell'elezione (stringa data in formato ISO 8601)
`election_domain`|federale (`federation`), cantonale (`canton`), regionale (`region`) o comunale (`municipality`)
`election_type`|sistema proporzionale (`proporz`) o sistema maggioritario (`majorz`)
`election_mandates`|Numero di mandati/seggi.
`election_absolute_majority`|La maggioranza assoluta. Rilevante solo per le elezioni basate sul sistema di maggioranza.
`election_status`|Risultati provvisori (`interim`), risultati finali (`final`) o ignoto (`unknown`).
`entity_id`|Identificativo del comune. A value `0` represents the expats.
`entity_name`|Nome del comune.
`entity_district`|Il distretto del comune.
`entity_counted`|`True`, se lo spoglio è stato completato.
`entity_eligible_voters`|Numero degli aventi diritto al voto di questo comune.
`entity_expats`|Numero di espatriati dell'unità.
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
`list_color`|Colore della lista come valore esadecimale, ad es. `#a6b784`. Solo con elezioni con sistema proporzionale.
`list_number_of_mandates`|Il numero di mandati ottenuti da questa lista. Rilevante solo per le elezioni basate sul metodo proporzionale.
`list_votes`|Numero di voti ricevuti da questa lista. Valido solo per elezioni basate sul sistema proporzionale.
`list_connection`|L'identificato del collegamento della lista a cui questa lista è collegata. Valido solo per elezioni basate sul sistema proporzionale.
`list_connection_parent`|L'identificativo del collegamento della lista padre a cui questa lista è collegata. Valido solo per elezioni basate sul sistema proporzionale.
`list_panachage_votes_from_list_{XX}`|Il numero dei voti ottenuti dalla lista da parte della lista con `list_id = XX`. Se `list_id` vale `999`, i voti provengono dalla lista vuota. Non contiene voti della propria lista.
`candidate_family_name`|Cognome del candidato.
`candidate_first_name`|Nome del candidato.
`candidate_id`|L'identificativo del candidato.
`candidate_elected`|Vero se il candidato è stato eletto.
`candidate_party`|Il nome del partito.
`candidate_party_color`|Colore del partito come valore esadecimale, ad es. `#a6b784`.
`candidate_gender`|Il genere del/la candidato/a: `female` (femminile), `male` (maschile) oppure `undetermined` (altro). Facoltativo.
`candidate_year_of_birth`|L'anno di nascita del/la candidato/a. Facoltativo.
`candidate_votes`|Numero di voti ricevuti da questo candidato.
`candidate_panachage_votes_from_list_{XX}`|Numero di voti personali dalla lista con `list_id = XX`. Se `list_id` vale `999`, i voti provengono dalla lista vuota.

I risultati del componente delle elezioni contengono le seguenti informazioni aggiuntive:

Name|Description
---|---
`compound_id`|ID del componente delle elezioni. Utilizzato nell'URL.
`compound_title_{locale}`|Titoli tradotti, ad esempio `title_de_ch` per il titolo tedesco.
`compound_short_title_{locale}`|Titoli abbreviati tradotti, ad esempio `title_de_ch` per il titolo abbreviato tedesco.
`compound_date`|Data del componente delle elezioni (stringa data in formato ISO 8601)
`compound_mandates`|Numero totale di mandati/seggi.

I comuni non ancora contati non sono inclusi.

#### Risultati dei partiti

```
URL: /election/{id}/data-parties-{format}
```

I dati grezzi dei partiti sono disponibili nei formati seguenti:

Formato|URL
---|---
JSON|`/data-parties-json`
CSV|`/data-parties-csv`

I seguenti campi sono contenuti in tutti i formati:

Nome|Descrizione
---|---
`domain`|Il livello cui si riferisce la riga.
`domain_segment`|L'unità del livello cui si riferisce la riga.
`year`|L’anno dell’elezione.
`total_votes`|Il totale dei voti dell’elezione.
`name`|Il nome del partito nella lingua definita come standard.
`name_{locale}`|Nome tradotto del partito, ad es. `name_de_ch` per il nome tedesco.
`id`|ID del partito.
`color`|Colore del partito come valore esadecimale, ad es. `#a6b784`.
`mandates`|Il numero di mandati.
`votes`|Il numero di voti.
`voters_count`|Numero di elettori. Il numero cumulativo di voti per il numero totale di mandati per elezione. Solo per i composti elettorali.
`voters_count_percentage`|Numero di elettori (percentuali). Il numero cumulativo di voti per il numero totale di mandati per elezione (percentuali). Solo per i composti elettorali.
`panachage_votes_from_{XX}`|Il numero di voti che i partito ha ottenuto dal partito con `id = XX`. Un `id`con il valore `999` segna i voti dalla lista vuota.

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

I seguenti campi sono contenuti nei formati `JSON` e `CSV`:

Nome|Descrizione
---|---
`id`|ID du vote. Utilisé dans l'URL.
`title_{locale}`|Titoli tradotti, ad esempio `title_de_ch` per il titolo tedesco.
`short_title_{locale}`|Titoli abbreviati tradotti, ad esempio `title_de_ch` per il titolo abbreviato tedesco.
`date`|Data della votazione (una stringa ISO 8601).
`shortcode`|Abbreviazione interna (definisce l'ordine di diverse votazioni in un giorno).
`domain`|`federation` per votazioni federali, `canton` per votazioni cantonali.
`status`|Risultati provvisori (`interim`), risultati finali (`final`) o ignoto (`unknown`).
`answer`|La risposta del voto: `accepted` (accettato), `rejected` (respinto), `proposal` (progetto) o `counter-proposal` (controproposta).
`type`|Tipo: `proposal` (progetto), `counter-proposal` (controprogetto) or `tie-breaker` (domanda eventuale).
`ballot_answer`|La risposta per tipo: `accepted` (accettato) o `rejected` (respinto) per `type=proposal` (progetto) e `type=counter-proposal` (controprogetto); `proposal` (progetto) o `counter-proposal` (controproposta) per `type=tie-breaker` (omanda eventuale).
`district`|Il distretto del comune.
`name`|Nome del comune.
`entity_id`|ID del comune/dell'ubicazione. Un valore `0` rappresenta gli espatriati.
`counted`|Vero, se lo spoglio è stato completato. Falso, se il risultato non è ancora noto (i valori non sono ancora corretti).
`yeas`|Numero di voti favorevoli
`nays`|Numero di voti contrari
`invalid`|Numero di voti nulli
`empty`|Numero di voti in bianco
`eligible_voters`|Numero di aventi diritto di voto
`expats`|Numero di espatriati dell'unità

4 Sitemap
---------

```
URL: /sitemap.xml
```

Restituisce una mappa del sito in formato XML (https://www.sitemaps.org/protocol.html)

```
URL: /sitemap.json
```

Restituisce la mappa del sito come JSON.