(1) Specifica Formato Elezioni
==============================

Sono accettati come formati di file CSV, XLS o XLSX generati dai programmi elettorali "elezioni (SESAM)" e "Wabsti elezioni e voti (VRSG)" oppure dall'applicazione web stessa. Se una tabella deve essere creata a mano allora il formato dell'applicazione web è il più semplice.

## Contenuto

1.1. [OneGov](#onegov)
1.2. [SESAM Sistema Maggioritario](#sesam-sistema-maggioritario)
1.3. [SESAM Sistema Proporzionale](#sesam-sistema-proporzionale)
1.4. [Wabsti Sistema Maggioritario](#wabsti-sistema-maggioritario)
1.5. [Wabsti Sistema Proporzionale](#wabsti-sistema-proporzionale)
1.6. [WabstiCExport Sistema Maggioritario](#wabsticexport-sistema-maggioritario)
1.7. [WabstiCExport Sistema Proporzionale](#wabsticexport-sistema-proporzionale)
1.8. [Party results](#party-results)


1.1 - Onegov
------------

Il formato che sarà utilizzato dall'applicazione web per l'esportazione è costituito da un unico file per ogni elezione. È presente una riga per ogni comune e candidato.

### Colonne

Saranno prese in considerazione le seguenti colonne e devono essere presenti:

Nome|Descrizione
---|---
`election_absolute_majority`|Maggioranza assoluta delle elezioni, solo se elezione con sistema maggioritario.
`election_status`|`unknown`, `interim` or `final`.
`election_counted_entities`|Numero di comuni scrutinati. Se `election_counted_entities = election_total_entities`, allora l'elezione è considerata completamente scrutinata.
`election_total_entities`|Numero totale dei comuni. Se non sono disponibili notizie certe sullo stato dell'elezione (perché l'elezione è stata importata da Wabsti) allora questo valore è `0`.
`entity_id`|Numero BFS del comune. A value of `0` can be used for expats.
`entity_name`|The name of the municipality.
`entity_elegible_voters`|Numero di aventi diritto al voto nel Comune.
`entity_received_ballots`|Numero di schede presentate nel Comune.
`entity_blank_ballots`|Numero di schede bianche nel Comune.
`entity_invalid_ballots`|Numero di schede nulle nel Comune.
`entity_blank_votes`|Numero voti bianchi nel Comune.
`entity_invalid_votes`|Numero di voti nulli nel Comune. Zero nel caso di elezione con sistema proporzionale.
`list_name`|Nome della lista di candidati. Solo con elezioni con sistema proporzionale.
`list_id`|ID della lista del candidato. Solo con elezioni con sistema proporzionale.
`list_number_of_mandates`|Numero totale di mandati della lista. Solo con elezioni con sistema proporzionale.
`list_votes`|Numero totale di voti di lista. Solo con elezioni con sistema proporzionale.
`list_connection`|ID dell'apparentamento della lista. Solo con elezioni con sistema proporzionale.
`list_connection_parent`|ID dell'apparentamento della lista di livello superiore. Solo con elezioni con sistema proporzionale e se è un apparentamento con una sottolista.
`candidate_family_name`|Cognome del candidato.
`candidate_first_name`|Nome del candidato.
`candidate_elected`|Vero, se il candidato è stato eletto.
`candidate_votes`|Numero di voti per il candidato nel Comune.

#### Panachage results

The results may contain panachage results by adding one column per list:

Nome|Descrizione
---|---
`panachage_votes_from_list_{XX}`|The number of votes the list got from the list with `list_id = XX`. A `list_id` with the value `999` marks the votes from the blank list.

### Risultati temporanei

I comuni non ancora completamente scrutinati non sono inclusi nei file.

If the status is
- `interim`, the whole election is considered not yet completed
- `final`, the whole election is considered completed
- `unknown`, the whole vote is considered completed, if `election_counted_entities` and `election_total_entities` match

### Modello

- [election_onegov_majorz.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_onegov_majorz.csv)
- [election_onegov_proporz.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_onegov_proporz.csv)

1.2 - SESAM Sistema Maggioritario
---------------------------------

Il formato di esportazione SESAM contiene direttamente tutti i dati richiesti. È presente una linea per candidato e comune.

### Colonne

Saranno prese in considerazione le seguenti colonne e almeno queste devono essere presenti:

Nome|Descrizione
---|---
`Anzahl Sitze`|Numero eletti
`Wahlkreis-Nr`|Numero del distretto elettorale
`Wahlkreisbezeichnung`|Electoral district name
`Anzahl Gemeinden`|Numero di comuni
`Stimmberechtigte`|Numero di aventi diritto al voto
`Wahlzettel`|Schede elettorali
`Ungültige Wahlzettel`|Schede non valide
`Leere Wahlzettel`|Schede bianche
`Leere Stimmen`|Voti nulli
`Ungueltige Stimmen`|Voti non validi
`Kandidaten-Nr`|Numero del candidato
`Gewaehlt`|Eletto
`Name`|Cognome
`Vorname`|Nome
`Stimmen`|Voti

### Risultati temporanei

L'elezione è considerata non scrutinata se la quantità di comuni scrutinati in "Numero di comuni" non corrisponde al numero totale dei comuni. I comuni il cui scrutinio non è completo non sono inclusi nei dati.

### Modello

- [election_sesam_majorz.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_sesam_majorz.csv)

1.3 - SESAM Sistema Proporzionale
---------------------------------

Il formato di esportazione SESAM contiene direttamente tutti i dati richiesti. È presente una linea per candidato e comune.

### Colonne

Saranno prese in considerazione le seguenti colonne e almeno queste devono essere presenti:

Nome|Descrizione
---|---
`Anzahl Sitze`|Numero eletti
`Wahlkreis-Nr`|Numero del distretto elettorale
`Wahlkreisbezeichnung`|Electoral district name
`Stimmberechtigte`|Numero di aventi diritto al voto
`Wahlzettel`|Schede elettorali
`Ungültige Wahlzettel`|Schede non valide
`Leere Wahlzettel`|Schede bianche
`Leere Stimmen`|Voti nulli
`Listen-Nr`|Numero elenco
`Parteibezeichnung`|Descrizione partito
`HLV-Nr`|
`ULV-Nr`|
`Anzahl Sitze Liste`|Elenco numero eletti
`Kandidatenstimmen unveränderte Wahlzettel`|Voti per il candidato a scrutinio invariato, parte del voto di lista
`Zusatzstimmen unveränderte Wahlzettel`|Ulteriori voti a scrutinio invariato, parte del voto di lista
`Kandidatenstimmen veränderte Wahlzettel`|Voti per il candidato a scrutinio modificato, parte del voto di lista
`Zusatzstimmen veränderte Wahlzettel`|Ulteriori voti a scrutinio modificato, parte del voto di lista
`Kandidaten-Nr`|Numero del candidato
`Gewählt`|Eletto
`Name`|Cognome
`Vorname`|Nome
`Stimmen Total aus Wahlzettel`|Totale voto da scrutinio
`Anzahl Gemeinden`|Numero di comuni

#### Panachage results

The results may contain panachage results by adding one column per list:

Nome|Descrizione
---|---
`{List number} {List name}`|The number of votes the list got from the list with the given `Listen-Nr`. A `Listen-Nr` with the value `00` (`00 OHNE`) marks the votes from the blank list.

### Risultati temporanei

L'elezione è considerata non scrutinata se la quantità di comuni scrutinati in "Numero di comuni" non corrisponde al numero totale dei comuni. I comuni il cui scrutinio non è completo non sono inclusi nei dati.

### Modello

- [election_sesam_proporz.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_sesam_proporz.csv)

1.4 - Wabsti Sistema Maggioritario
----------------------------------

Il formato del file ha bisogno di due tabelle separate: l'esportazione dei dati e l'elenco dei candidati eletti.

### Esportazione delle colonne dati

Nell'esportazione dei dati, è presente una riga per ogni comune, i candidati sono disposti in colonne. Saranno prese in considerazione le seguenti colonne e devono essere presenti:

Nome|Descrizione
---|---
`AnzMandate`|
`BFS`|The municipality number (BFS number) at the time of the election. A value of `0` can be used for expats.
`EinheitBez`|
`StimmBer`|
`StimmAbgegeben`|
`StimmLeer`|
`StimmUngueltig`|
`StimmGueltig`|

Così come per ogni candidato

Nome|Descrizione
---|---
`KandID_{XX}`|ID del candidato
`KandName_{XX}`|Cognome del candidato
`KandVorname_{XX}`|
`Stimmen_{XX}`|

Inoltre i voti, così come i candidati, nulli e non validi saranno attribuiti ai seguenti nomi di candidati:

- `KandName_{XX} = 'Leere Zeilen'`
- `KandName_{XX} = 'Ungültige Stimmen'`

### Colonne risultati candidati

Poiché il formato di file non fornisce alcuna informazione sul candidato eletto, questi devono essere inclusi in una seconda colonna. Ogni riga è composta da un candidato eletto con le seguenti colonne:

Nome|Descrizione
---|---
`ID`|ID del candidato (`KandID_{XX}`).
`Name`|Cognome del candidato.
`Vorname`|Nome del candidato

### Risultati temporanei

Il formato del file non contiene alcuna informazione chiara sul fatto che l'elezione complessiva sia stata completamente scrutinata. Questa informazione deve essere fornita direttamente sul modulo per il caricamento dei dati.

Il formato del file, inoltre, non contiene alcuna informazione sul fatto che un comune specifico sia stato completamente scrutinato. Pertanto finché l'intera elezione non è scrutinata non sarà notificato alcun avanzamento per Wabsti. Se i comuni mancano del tutto di risultati, essi sono considerati non ancora scrutinati.

### Modelli

- [election_wabsti_majorz_results.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_majorz_results.csv)
- [election_wabsti_majorz_candidates.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_majorz_candidates.csv)

1.5 - Wabsti Sistema Proporzionale
----------------------------------

Il formato di file ha bisogno di quattro tabelle separate: l'esportazione dei dati dei risultati, l'esportazione dei dati di statistica, gli apparentamenti delle liste e i candidati di lista eletti.

### Colonne esportazione dei dati dei risultati

È presente una linea per candidato e comune nell'esportazione dei dati. Saranno prese in considerazione le seguenti colonne e devono essere presenti:

Nome|Descrizione
---|---
`Einheit_BFS`|The municipality number (BFS number) at the time of the election. A value of `0` can be used for expats.
`Einheit_Name`|
`Kand_Nachname`|
`Kand_Vorname`|
`Liste_KandID`|
`Liste_ID`|
`Liste_Code`|
`Kand_StimmenTotal`|
`Liste_ParteistimmenTotal`|

#### Panachage results

The results may contain panachage results by adding one column per list:

Nome|Descrizione
---|---
`{List ID}.{List code}`|The number of votes the list got from the list with the given `Liste_ID`. A `Liste_ID` with the value `99` (`99.WoP`) marks the votes from the blank list.

### Colonne esportazione di dati di statistica

Il file con le statistiche dei singoli comuni devono contenere le seguenti colonne:

Nome|Descrizione
---|---
`Einheit_BFS`|
`Einheit_Name`|
`StimBerTotal`|
`WZEingegangen`|
`WZLeer`|
`WZUngueltig`|
`StmWZVeraendertLeerAmtlLeer`|

### Colonne apparentamenti delle liste

Il file con gli apparentamenti delle liste dovrebbe contenere le seguenti colonne:

Nome|Descrizione
---|---
`Liste`|
`LV`|
`LUV`|

### Colonne risultati candidati

Poiché il formato di file non fornisce alcuna informazione sul candidato eletto, questi devono essere inclusi in una seconda colonna. Ogni riga è composta da un candidato eletto con le seguenti colonne:

Nome|Descrizione
---|---
`ID`|ID del candidato (`Liste_KandID`).
`Name`|Cognome del candidato.
`Vorname`|Nome del candidato.

### Risultati temporanei

Il formato del file non contiene alcuna informazione chiara sul fatto che l'elezione complessiva sia stata completamente scrutinata. Questa informazione deve essere fornita direttamente sul modulo per il caricamento dei dati.

Il formato del file, inoltre, non contiene alcuna informazione sul fatto che un comune specifico sia stato completamente scrutinato. Pertanto finché l'intera elezione non è scrutinata non sarà notificato alcun avanzamento per Wabsti. Se i comuni mancano del tutto di risultati, essi sono considerati non ancora scrutinati.

### Modelli

- [election_wabsti_proporz_results.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_proporz_results.csv)
- [election_wabsti_proporz_statistics.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_proporz_statistics.csv)
- [election_wabsti_proporz_list_connections.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_proporz_list_connections.csv)
- [election_wabsti_proporz_candidates.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_proporz_candidates.csv)


1.6 - WabstiCExport Sistema Maggioritario
-----------------------------------------

Version `2.2` is supported, please refer to the documentation provided by the exporter program for more information about the columns of the different files.


1.7 - WabstiCExport Sistema Proporzionale
-----------------------------------------

Version `2.2` is supported, please refer to the documentation provided by the exporter program for more information about the columns of the different files.


1.8 - Party results
-------------------

Each (proporz) election may contain party results. These results are independent of the other results and typically contain the already aggregated results of the different lists of a party.

The following columns will be evaluated and should exist:

Nome|Descrizione
---|---
`year`|The year of the election.
`total_votes`|The total votes of the election.
`name`|The name of the party.
`color`|The color of the party.
`mandates`|The number of mandates.
`votes`|The number of votes.

### Template

- [election_party_results.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_party_results.csv)
