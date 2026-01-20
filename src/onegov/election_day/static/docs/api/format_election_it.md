# Specifica Formato Elezioni

Sono accettati come formati di file CSV, XLS o XLSX generati dai "Wabsti elezioni e voti (VRSG)" oppure dall'applicazione web stessa. Se una tabella deve essere creata a mano allora il formato dell'applicazione web (OneGov) è il più semplice.

## Contenuto

<!-- TOC updateonsave:false -->

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
            - [Dati relativi ai voti ottenuti dai candidati tramite panachage](#dati-relativi-ai-voti-ottenuti-dai-candidati-tramite-panachage)
            - [Risultati temporanei](#risultati-temporanei)
            - [Componenti delle elezioni](#componenti-delle-elezioni)
            - [Modello](#modello)
        - [WabstiCExport Sistema Maggioritario](#wabsticexport-sistema-maggioritario)
        - [WabstiCExport Sistema Proporzionale](#wabsticexport-sistema-proporzionale)
        - [Risultati dei partiti](#risultati-dei-partiti)
            - [Circondario](#circondario)
            - [Risultati panachage](#risultati-panachage)
            - [Modelli](#modelli)

<!-- /TOC -->

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
