# Specifica Formato Voti

I formati di file accettabili sono file generati manualmente, dal software elettorale "Wabsti Elections and Referenda (VRSG)" o dall'applicazione web stessa.

"Comune" si riferisce ad un distretto, una circoscrizione elettorale, etc.

## Contenuto

<!-- TOC updateonsave:false -->

- [Specifica Formato Voti](#specifica-formato-voti)
    - [Contenuto](#contenuto)
    - [Prefazione](#prefazione)
        - [Enti](#enti)
    - [Formati](#formati)
        - [OneGov](#onegov)
            - [Colonne](#colonne)
            - [Risultati temporanei](#risultati-temporanei)
            - [Modello](#modello)
        - [WabstiCExport](#wabsticexport)
        - [eCH-0252](#ech-0252)

<!-- /TOC -->

## Prefazione

### Enti

Un ente può essere un comune (esempi cantonali, esempi comunali senza quartieri) o un quartiere (esempi comunali con quartieri)

## Formati


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


### WabstiCExport

La versione `>= 2.2` è supportata. Consulta la documentazione del programma di esportazione per ulteriori informazioni riguardo le colonne dei vari file.


### eCH-0252

Vedi [eCH-0252](https://www.ech.ch/de/ech/ech-0252).
