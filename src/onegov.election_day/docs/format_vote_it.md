# Specifica Formato Voti

I formati di file accettabili sono file generati manualmente, dal software elettorale "Wabsti Elections and Referenda (VRSG)" o dall'applicazione web stessa.

"Comune" si riferisce ad un distretto, una circoscrizione elettorale, etc.

## Contenuto

<!-- TOC START min:1 max:4 link:true asterisk:false update:true -->
- [Specifica Formato Voti](#specifica-formato-voti)
    - [Contenuto](#contenuto)
    - [Prefazione](#prefazione)
        - [Enti](#enti)
    - [Formati](#formati)
        - [Formato standard](#formato-standard)
            - [Colonne](#colonne)
            - [Risultati temporanei](#risultati-temporanei)
            - [Modello](#modello)
        - [OneGov](#onegov)
            - [Colonne](#colonne-1)
            - [Risultati temporanei](#risultati-temporanei-1)
            - [Modello](#modello-1)
        - [Wabsti](#wabsti)
            - [Colonne](#colonne-2)
            - [Risultati temporanei](#risultati-temporanei-2)
            - [Modello](#modello-2)
        - [WabstiCExport](#wabsticexport)
<!-- TOC END -->

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

- [vote_standard.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/vote_standard.csv)

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


#### Risultati temporanei

Si ritiene che i comuni non siano stati conteggiati se si verifica una delle due seguenti condizioni:
- `counted = false`
- il comune non è incluso nei risultati

Se lo stato è
- `interim`, l'intera votazione non è ancora stata completata
- `final`, l'intera votazione è stata completata
- `unknown`, l'intera votazione è stata completata, se vengono contati tutti i comuni (previsti)

#### Modello

- [vote_onegov.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/vote_onegov.csv)

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

- [vote_wabsti.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/vote_wabsti.csv)


### WabstiCExport

La versione `>= 2.2` è supportata. Consulta la documentazione del programma di esportazione per ulteriori informazioni riguardo le colonne dei vari file.
