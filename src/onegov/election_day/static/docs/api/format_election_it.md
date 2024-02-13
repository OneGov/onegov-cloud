# Specifica Formato Elezioni

Sono accettati come formati di file CSV, XLS o XLSX generati dai "Wabsti elezioni e voti (VRSG)" oppure dall'applicazione web stessa. Se una tabella deve essere creata a mano allora il formato dell'applicazione web (OneGov) è il più semplice.

## Contenuto

<!-- https://atom.io/packages/atom-mdtoc -->
<!-- MDTOC maxdepth:6 firsth1:1 numbering:0 flatten:0 bullets:1 updateOnSave:1 -->

- [Specifica Formato Elezioni](#specifica-formato-elezioni)
   - [Contenuto](#contenuto)
   - [Prefazione](#prefazione)
      - [Enti](#enti)
      - [Elezioni tacite](#elezioni-tacite)
      - [Elezioni regionali](#elezioni-regionali)
   - [Formati](#formati)
      - [Onegov](#onegov)
         - [Colonne](#colonne)
         - [Risultati panachage della lista](#risultati-panachage-della-lista)
         - [Risultati temporanei](#risultati-temporanei)
         - [Componenti delle elezioni](#componenti-delle-elezioni)
         - [Modello](#modello)
      - [Wabsti Sistema Maggioritario](#wabsti-sistema-maggioritario)
         - [Esportazione delle colonne dati](#esportazione-delle-colonne-dati)
         - [Colonne risultati candidati](#colonne-risultati-candidati)
         - [Risultati temporanei](#risultati-temporanei)
         - [Modelli](#modelli)
      - [Wabsti Sistema Proporzionale](#wabsti-sistema-proporzionale)
         - [Colonne esportazione dei dati dei risultati](#colonne-esportazione-dei-dati-dei-risultati)
         - [Risultati panachage](#risultati-panachage)
         - [Colonne esportazione di dati di statistica](#colonne-esportazione-di-dati-di-statistica)
         - [Colonne apparentamenti delle liste](#colonne-apparentamenti-delle-liste)
         - [Colonne risultati candidati](#colonne-risultati-candidati)
         - [Risultati temporanei](#risultati-temporanei)
         - [Modelli](#modelli)
      - [WabstiCExport Sistema Maggioritario](#wabsticexport-sistema-maggioritario)
      - [WabstiCExport Sistema Proporzionale](#wabsticexport-sistema-proporzionale)
      - [Risultati dei partiti](#risultati-dei-partiti)
         - [Circondario](#circondario)
         - [Risultati panachage](#risultati-panachage)
         - [Modelli](#modelli)

<!-- /MDTOC -->

## Prefazione

### Enti

Un ente può essere un comune (esempi cantonali, esempi comunali senza quartieri) o un quartiere (esempi comunali con quartieri)

### Elezioni tacite

Si possono caricare delle elezioni tacite usando il formato OneGov con ogni voto impostato a `0`.

### Elezioni regionali

Quando si caricano i risultati di un'elezione regionale, solo gli enti di un distretto devono essere presenti, se l'opzione corrispondente è impostata sull'elezione.

## Formati

### Onegov

Il formato che sarà utilizzato dall'applicazione web per l'esportazione è costituito da un unico file per ogni elezione. È presente una riga per ogni comune e candidato.

#### Colonne

Saranno prese in considerazione le seguenti colonne e devono essere presenti:

Nome|Descrizione
---|---
`election_absolute_majority`|Maggioranza assoluta delle elezioni, solo se elezione con sistema maggioritario.
`election_status`|Stato delle elezioni. `interim` (risultati provvisori), `final` (risultati finali) o `unknown` (ignoto).
`entity_id`|Numero BFS del comune. Si può usare il valore `0` per gli espatriati
`entity_counted`|`True`, se lo spoglio è stato completato.
`entity_eligible_voters`|Numero di aventi diritto al voto nel Comune.
`entity_expats`|Numero di espatriati dell'unità. Facoltativo.
`entity_received_ballots`|Numero di schede presentate nel Comune.
`entity_blank_ballots`|Numero di schede bianche nel Comune.
`entity_invalid_ballots`|Numero di schede nulle nel Comune.
`entity_blank_votes`|Numero voti bianchi nel Comune.
`entity_invalid_votes`|Numero di voti nulli nel Comune. Zero nel caso di elezione con sistema proporzionale.
`list_name`|Nome della lista di candidati. Solo con elezioni con sistema proporzionale.
`list_id`|ID della lista del candidato. Solo con elezioni con sistema proporzionale. Può essere numerico o alfanumerico.
`list_color`|Colore della lista come valore esadecimale, ad es. `#a6b784`.  Solo con elezioni con sistema proporzionale.
`list_number_of_mandates`|Numero totale di mandati della lista. Solo con elezioni con sistema proporzionale.
`list_votes`|Numero di voti di lista per comune. Solo con elezioni con sistema proporzionale.
`list_connection`|ID dell'apparentamento della lista. Solo con elezioni con sistema proporzionale.
`list_connection_parent`|ID dell'apparentamento della lista di livello superiore. Solo con elezioni con sistema proporzionale e se è un apparentamento con una sottolista.
`candidate_id`|ID del candidato.
`candidate_family_name`|Cognome del candidato.
`candidate_first_name`|Nome del candidato.
`candidate_elected`|Vero, se il candidato è stato eletto.
`candidate_party`|Il nome del partito.
`candidate_party_color`|Colore del partito come valore esadecimale, ad es. `#a6b784`.
`candidate_gender`|Il genere del/la candidato/a: `female` (femminile), `male` (maschile) oppure `undetermined` (altro). Facoltativo.
`candidate_year_of_birth`|L'anno di nascita del/la candidato/a. Facoltativo.
`candidate_votes`|Numero di voti per il candidato nel Comune.

#### Risultati panachage della lista

I risultati possono contenere dei risultati di panachage della lista aggiungendo una colonna per lista:

Nome|Descrizione
---|---
`list_panachage_votes_from_list_{XX}` / `panachage_votes_from_list_{XX}`|Il numero dei voti ottenuti dalla lista da parte della lista con `list_id = XX`. Se `list_id` vale `999`, i voti provengono dalla lista vuota. I voti provenienti dalla propria lista vengono ignorati.


#### Dati relativi ai voti ottenuti dai candidati tramite panachage

I risultati possono contenere dati relativi ai voti ottenuti dai candidati tramite panachage aggiungendo una colonna per lista:

Nome|Descrizione
---|---
`candidate_panachage_votes_from_list_{XX}`|Numero di voti personali dalla lista con `list_id = XX`. Se `list_id` vale `999`, i voti provengono dalla lista vuota.

#### Risultati temporanei

Si ritiene che i comuni non siano stati conteggiati se si verifica una delle due seguenti condizioni:
- `counted = false`
- il comune non è incluso nei risultati

Se lo stato è
- `interim`, l’intera elezione non è ancora stata completata
- `final`, l’intera elezione è stata completata
- `unknown`, l'intera elezione viene considerata completata, se vengono contati tutti i comuni (previsti)

#### Componenti delle elezioni

I risultati di elezioni legate tra loro possono essere caricati tutti insieme mediante un unico file contenente tutte le righe dei risultati delle singole elezioni.

#### Modello

- [election_onegov_majorz.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/election_onegov_majorz.csv)
- [election_onegov_proporz.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/election_onegov_proporz.csv)

### Wabsti Sistema Maggioritario

Il formato del file ha bisogno di due tabelle separate: l'esportazione dei dati e l'elenco dei candidati eletti.

#### Esportazione delle colonne dati

Nell'esportazione dei dati, è presente una riga per ogni comune, i candidati sono disposti in colonne. Saranno prese in considerazione le seguenti colonne e devono essere presenti:
- `AnzMandate`
- `BFS`
- `StimmBer`
- `StimmAbgegeben`
- `StimmLeer`
- `StimmUngueltig`
- `StimmGueltig`

Così come per ogni candidato
- `KandID_{XX}`
- `KandName_{XX}`
- `KandVorname_{XX}`
- `Stimmen_{XX}`

Inoltre i voti, così come i candidati, nulli e non validi saranno attribuiti ai seguenti nomi di candidati:
- `KandName_{XX} = 'Leere Zeilen'`
- `KandName_{XX} = 'Ungültige Stimmen'`

#### Colonne risultati candidati

Poiché il formato del file potrebbe non fornire alcuna informazione sui candidati eletti, queste informazioni possono essere fornite in una seconda tabella. Ogni riga è composta da un candidato eletto con le seguenti colonne:

Nome|Descrizione
---|---
`KandID`|ID del candidato (`KandID_{XX}`).

#### Risultati temporanei

Il formato del file non contiene alcuna informazione chiara sul fatto che l'elezione complessiva sia stata completamente scrutinata. Questa informazione deve essere fornita direttamente sul modulo per il caricamento dei dati.

Il formato del file, inoltre, non contiene alcuna informazione sul fatto che un comune specifico sia stato completamente scrutinato. Se i comuni mancano del tutto di risultati, essi sono considerati non ancora scrutinati.

#### Modelli

- [election_wabsti_majorz_results.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/election_wabsti_majorz_results.csv)
- [election_wabsti_majorz_candidates.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/election_wabsti_majorz_candidates.csv)

### Wabsti Sistema Proporzionale

Il formato di file ha bisogno di quattro tabelle separate: l'esportazione dei dati dei risultati, l'esportazione dei dati di statistica, gli apparentamenti delle liste e i candidati di lista eletti.

#### Colonne esportazione dei dati dei risultati

È presente una linea per candidato e comune nell'esportazione dei dati. Saranno prese in considerazione le seguenti colonne e devono essere presenti:
- `Einheit_BFS`
- `Kand_Nachname`
- `Kand_Vorname`
- `Liste_KandID`
- `Liste_ID`
- `Liste_Code`
- `Kand_StimmenTotal`
- `Liste_ParteistimmenTotal`

#### Risultati panachage

I risultati possono contenere dei risultati di panachage aggiungendo una colonna per lista (`{List ID}.{List code}`: il numero dei voti ottenuti dalla lista proveniente dalla lista con il `Liste_ID` specificato). Se `Liste_ID` vale `99` (`99.WoP`), i voti provengono dalla lista vuota.

#### Colonne esportazione di dati di statistica

Il file con le statistiche dei singoli comuni devono contenere le seguenti colonne:
- `Einheit_BFS`
- `Einheit_Name`
- `StimBerTotal`
- `WZEingegangen`
- `WZLeer`
- `WZUngueltig`
- `StmWZVeraendertLeerAmtlLeer`

#### Colonne apparentamenti delle liste

Il file con gli apparentamenti delle liste dovrebbe contenere le seguenti colonne:
- `Liste`
- `LV`
- `LUV`

#### Colonne risultati candidati

Poiché il formato di file non fornisce alcuna informazione sul candidato eletto, questi devono essere inclusi in una seconda colonna. Ogni riga è composta da un candidato eletto con le seguenti colonne:

Nome|Descrizione
---|---
`Liste_KandID`|ID del candidato.

#### Risultati temporanei

Il formato del file non contiene alcuna informazione chiara sul fatto che l'elezione complessiva sia stata completamente scrutinata. Questa informazione deve essere fornita direttamente sul modulo per il caricamento dei dati.

Il formato del file, inoltre, non contiene alcuna informazione sul fatto che un comune specifico sia stato completamente scrutinato. Se i comuni mancano del tutto di risultati, essi sono considerati non ancora scrutinati.

#### Modelli

- [election_wabsti_proporz_results.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/election_wabsti_proporz_results.csv)
- [election_wabsti_proporz_statistics.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/election_wabsti_proporz_statistics.csv)
- [election_wabsti_proporz_list_connections.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/election_wabsti_proporz_list_connections.csv)
- [election_wabsti_proporz_candidates.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/election_wabsti_proporz_candidates.csv)


### WabstiCExport Sistema Maggioritario

La versione `>= 2.2` è supportata. Consulta la documentazione del programma di esportazione per ulteriori informazioni riguardo le colonne dei vari file.


### WabstiCExport Sistema Proporzionale

La versione `>= 2.2` è supportata. Consulta la documentazione del programma di esportazione per ulteriori informazioni riguardo le colonne dei vari file.


### Risultati dei partiti

Ciascuna elezione ("proporz") e ogni composto elettorale può contenere i risultati di partito. Questi risultati sono indipendenti dagli altri risultati e di solito contengono i valori già aggregati delle varie liste di un partito.

Le seguenti colonne verranno valutate e devono esistere:

Nome|Descrizione
---|---
`domain`|Il livello cui si riferisce la riga. Facoltativo.
`domain_segment`|L'unità del livello cui si riferisce la riga. Facoltativo.
`year`|L’anno dell’elezione.
`total_votes`|Il totale dei voti dell’elezione.
`name`|Il nome del partito nella lingua definita come standard. Quale opzione*.
`name_{locale}`|Nome tradotto del partito, ad es. `name_de_ch` per il nome tedesco. Quale opzione. Si assicuri di aver indicato nella colonna name oppure nella colonna name_{default_locale} il nome del partito nella lingua definita come standard.
`name`|Il nome del partito.
`id`|ID del partito (qualsiasi numero).
`color`|Colore del partito come valore esadecimale, ad es. `#a6b784`.
`mandates`|Il numero di mandati.
`votes`|Il numero di voti.
`voters_count`|Numero di elettori. Il numero cumulativo di voti per il numero totale di mandati per elezione. Solo per i composti elettorali.
`voters_count_percentage`|Numero di elettori (percentuali). Il numero cumulativo di voti per il numero totale di mandati per elezione (percentuali). Solo per i composti elettorali.

#### Circondario

`domain` e `domain_segment` consentono di registrare i risultati di partito per un altro circondario rispetto a quello dell'elezione o della combinazione di elezioni. In questo contesto `domain` corrisponde a un circondario subordinato dell'elezione o della combinazione di elezioni, ad es. nel caso di elezioni parlamentari cantonali, a seconda del Cantone `superregion`, `region`, `district` oppure `municipality`. `domain_segment` corrisponde a un'unità in questo circondario subordinato, ad es. `Region 1`, `Bergün`, `Toggenburg` oppure `Zug`. Di norma sia `domain` sia `domain_segment` possono essere lasciati in bianco od omessi; in questo caso `domain` viene impostato automaticamente su `domain` dell'elezione o della combinazione di elezioni. Attualmente vengono supportati solo `domain` dell'elezione o della combinazione di elezioni nonché `domain = 'superregion'` in caso di elezioni legate tra loro.

#### Risultati panachage

I risultati potrebbero contenere risultati misti aggiungendo una colonna per partito:

Name|Description
---|---
`panachage_votes_from_{XX}`|Il numero di voti che i partito ha ottenuto dal partito con `id = XX`. Un `id`con il valore `999` segna i voti dalla lista vuota.

Risultati misti sono aggiunti solo se:
- `year` corrisponde all'anno dell'elezione
- `id (XX)` non corrisponde il `id`della fila

#### Modelli

- [election_party_results.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/election_party_results.csv)
