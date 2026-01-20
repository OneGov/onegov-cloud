# Format Specification Votes

Sco formats da datoteca vegnan acceptadas datotecas che vegnan generadas a maun, dals programs d'elecziun "Wabsti Elecziuns e votaziuns (VRSG)", u da l'applicaziun web sezza.

Ina "vischnanca" po er esser in district, in circul electoral e.u.v.

## Cuntegn

<!-- TOC updateonsave:false -->

- [Format Specification Votes](#format-specification-votes)
    - [Cuntegn](#cuntegn)
    - [Remartgas preliminaras](#remartgas-preliminaras)
        - [Unitads](#unitads)
    - [Formats](#formats)
        - [OneGov](#onegov)
        - [Colonnas](#colonnas)
            - [Resultats temporars](#resultats-temporars)
            - [Project](#project)
        - [WabstiCExport](#wabsticexport)
        - [eCH-0252](#ech-0252)

<!-- /TOC -->


## Remartgas preliminaras

### Unitads

In'unitad correspunda ad ina vischnanca (instanzas chantunalas, instanzas communalas senza quartiers) u ad in quartier (instanzas communalas cun quartiers).

## Formats


### OneGov

Il format che vegn duvrà da l'applicaziun web per l'export sa cumpona d'ina singula datoteca per votaziun. Per mintga vischnanca e per mintga tip da votaziun (proposta, cuntraproposta, dumonda decisiva) datti ina lingia.

### Colonnas

Las suandantas colonnas vegnan evaluadas e ston almain esser avant maun:

Num|Descripziun
---|---
`status`|Resultats intermediars (`interim`), resultats finals (`final`) u stadi dals resultats nunenconuschent (`unknown`).
`type`|`proposal` (proposta), `counter-proposal` (cuntraproposta) or `tie-breaker` (dumonda decisiva).
`entity_id`|La ID da la vischnanca/dal lieu. A value `0` represents the expats.
`counted`|Gist, sch'il resultat è vegnì eruì. Fauss, sch'il resultat n'è anc betg enconuschent (las valurs n'èn anc betg correctas).
`yeas`|Il dumber da las vuschs affirmativas.
`nays`|Il dumber da las vuschs negativas.
`invalid`|Il dumber da las vuschs nunvalaivlas.
`empty`|Il dumber da las vuschs vidas.
`eligible_voters`|Il dumber da las persunas cun dretg da votar.
`expats`|Dumber da las persunas da l'unitad che vivan a l'exteriur. Opziunal.


#### Resultats temporars

Vischnancas valan sco anc betg dumbradas ora, sch'ina da las duas suandantas cundiziuns constat:
- `counted = false`
- la vischnanca n'è betg cuntegnida en ils resultats

Sch'il status
- è `interim`, vala la votaziun sco anc betg terminada
- è `final`, vala la votaziun sco terminada
- è `unknown` ist, vala la votaziun sco terminada, sche tut las vischnancas (spetgadas) èn dumbradas ora

#### Project

- [vote_onegov.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/vote_onegov.csv)


### WabstiCExport

Sustegnida vegn la versiun `>= 2.2`. Las differentas colonnas da las differentas datotecas èn definidas en la documentaziun dal program Exporter.

### eCH-0252

Vedi [eCH-0252](https://www.ech.ch/de/ech/ech-0252).
