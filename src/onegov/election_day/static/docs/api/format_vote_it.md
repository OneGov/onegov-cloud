# Specifica Formato Voti

I formati di file accettabili sono file generati manualmente, dal software elettorale "Wabsti Elections and Referenda (VRSG)" o dall'applicazione web stessa.

"Comune" si riferisce ad un distretto, una circoscrizione elettorale, etc.

## Contenuto

<!-- https://atom.io/packages/atom-mdtoc -->
<!-- MDTOC maxdepth:6 firsth1:2 numbering:1 flatten:0 bullets:1 updateOnSave:1 -->

- 1. [Contenuto](#contenuto)
- 2. [Prefazione](#prefazione)
   - 2.1. [Enti](#enti)
- 3. [Formati](#formati)
   - 3.1. [Formato standard](#formato-standard)
      - 3.1.1. [Colonne](#colonne)
      - 3.1.2. [Risultati temporanei](#risultati-temporanei)
      - 3.1.3. [Modello](#modello)
   - 3.2. [OneGov](#onegov)
      - 3.2.1. [Colonne](#colonne)
      - 3.2.2. [Risultati temporanei](#risultati-temporanei)
      - 3.2.3. [Modello](#modello)
   - 3.3. [Wabsti](#wabsti)
      - 3.3.1. [Colonne](#colonne)
      - 3.3.2. [Risultati temporanei](#risultati-temporanei)
      - 3.3.3. [Modello](#modello)
   - 3.4. [WabstiCExport](#wabsticexport)
   - 3.5. [eCH-0252](#ech-0252)

<!-- /MDTOC -->
## Prefazione

### Enti

Un ente può essere un comune (esempi cantonali, esempi comunali senza quartieri) o un quartiere (esempi comunali con quartieri)

## Formati

### Formato standard

Generalmente esiste un file CSV/Excel per ogni proposta referendaria. Tuttavia, qualora il referendum includesse una controproposta e uno spareggio, è necessario consegnare tre file: un file con i risultati del referendum, un file con i risultati della controproposta e un file con i risultati dello spareggio.

#### Colonne

Ogni riga contiene il risultato di un singolo comune, purché questo sia stato conteggiato per intero. Le seguenti colonne sono previste nell'ordine elencato qui:

Nome|Descrizione
---|---
`ID`|Il numero del comune (numero BFS) al momento del voto. Un valore di `0` può essere usato per gli espatriati.
`Ja Stimmen`|Il numero di voti "si". Se viene inserita la parola `unknown`/`unbekannt`, la riga verrà ignorata (non ancora conteggiata).
`Nein Stimmen`|Il numero di voti "no". Se viene inserita la parola `unknown`/`unbekannt`, la riga verrà ignorata (non ancora conteggiata).
`Stimmberechtigte`|Il numero di persone idonee a votare. Se viene inserita la parola `unknown`/`unbekannt`, la riga verrà ignorata (non ancora conteggiata).
`Leere Stimmzettel`|Il numero delle schede bianche. Se viene inserita la parola `unknown`/`unbekannt`, la riga verrà ignorata (non ancora conteggiata).
`Ungültige Stimmzettel`|Il numero delle schede nulle. Se viene inserita la parola `unknown`/`unbekannt`, la riga verrà ignorata (non ancora conteggiata).

#### Risultati temporanei

Si ritiene che i comuni non siano stati conteggiati se il comune non è incluso nei risultati.

#### Modello

- [vote_standard.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/vote_standard.csv)

### OneGov

Il formato utilizzato dall'applicazione Web per l'esportazione consiste in un singolo file per voto. C'è una riga per ogni comune e tipo di referendum (proposta, controproposta, spareggio).

#### Colonne

Saranno prese in considerazione le seguenti colonne e devono essere presenti:

Nome|Descrizione
---|---
`status`|`interim` (risultati provvisori), `final` (risultati finali) o `unknown` (ignoto).
`type`|`proposal` (progetto), `counter-proposal` (controprogetto) or `tie-breaker` (domanda eventuale).
`entity_id`|ID del comune/dell'ubicazione. Un valore `0` rappresenta gli espatriati.
`counted`|Vero, se lo spoglio è stato completato. Falso, se il risultato non è ancora noto (i valori non sono ancora corretti).
`yeas`|Numero di voti favorevoli
`nays`|Numero di voti contrari
`invalid`|Numero di voti nulli
`empty`|Numero di voti in bianco
`eligible_voters`|Numero di aventi diritto di voto
`expats`|Numero di espatriati dell'unità. Facoltativo.


#### Risultati temporanei

Si ritiene che i comuni non siano stati conteggiati se si verifica una delle due seguenti condizioni:
- `counted = false`
- il comune non è incluso nei risultati

Se lo stato è
- `interim`, l'intera votazione non è ancora stata completata
- `final`, l'intera votazione è stata completata
- `unknown`, l'intera votazione è stata completata, se vengono contati tutti i comuni (previsti)

#### Modello

- [vote_onegov.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/vote_onegov.csv)

### Wabsti

Il formato del programma elettorale "Elezioni e referendum Wabsti (VRSG)" consiste in un singolo file che contiene tutti i dati per molti referendum. C'è una riga per ogni referendum e comune.

#### Colonne

Saranno prese in considerazione le seguenti colonne e devono essere presenti:
- `Vorlage-Nr.`
- `Name`
- `BfS-Nr.`
- `Stimmberechtigte`
- `leere SZ`
- `ungültige SZ`
- `Ja`
- `Nein`
- `GegenvJa`
- `GegenvNein`
- `StichfrJa`
- `StichfrNein`
- `StimmBet`

#### Risultati temporanei

Si ritiene che i comuni non siano stati conteggiati se si verifica una delle due seguenti condizioni:
- `StimmBet = 0`
- il comune non è incluso nei risultati

#### Modello

- [vote_wabsti.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/vote_wabsti.csv)


### WabstiCExport

La versione `>= 2.2` è supportata. Consulta la documentazione del programma di esportazione per ulteriori informazioni riguardo le colonne dei vari file.


### eCH-0252

Vedi [eCH-0252](https://www.ech.ch/de/ech/ech-0252).
