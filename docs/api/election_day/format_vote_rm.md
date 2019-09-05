# Format Specification Votes

Sco formats da datoteca vegnan acceptadas datotecas che vegnan generadas a maun, dals programs d'elecziun "Wabsti Elecziuns e votaziuns (VRSG)", u da l'applicaziun web sezza.

Ina "vischnanca" po er esser in district, in circul electoral e.u.v.

## Cuntegn

<!-- TOC START min:1 max:4 link:true update:true -->
- [Format Specification Votes](#format-specification-votes)
  - [Cuntegn](#cuntegn)
  - [Remartgas preliminaras](#remartgas-preliminaras)
    - [Unitads](#unitads)
  - [Formats](#formats)
    - [Format da standard](#format-da-standard)
      - [Colonnas](#colonnas)
      - [Resultats temporars](#resultats-temporars)
      - [Project](#project)
    - [OneGov](#onegov)
    - [Colonnas](#colonnas-1)
      - [Resultats temporars](#resultats-temporars-1)
      - [Project](#project-1)
    - [Wabsti](#wabsti)
      - [Colonnas](#colonnas-2)
      - [Resultats temporars](#resultats-temporars-2)
      - [Project](#project-2)
    - [WabstiCExport](#wabsticexport)

<!-- TOC END -->


## Remartgas preliminaras

### Unitads

In'unitad correspunda ad ina vischnanca (instanzas chantunalas, instanzas communalas senza quartiers) u ad in quartier (instanzas communalas cun quartiers).

## Formats

### Format da standard

Per project da votaziun exista per regla ina datoteca CSV/Excel. Sche la votaziun cuntegna però ina cuntraproposta ed ina dumonda decisiva, ston vegnir furnidas trais datotecas: ina datoteca cun ils resultats da la votaziun, ina datoteca cun ils resultats da la cuntraproposta ed ina datoteca cun ils resultats da la dumonda decisiva.

#### Colonnas

Mintga lingia cuntegna il resultat d'ina singula vischnanca, sch'ils cedels da votar èn vegnids dumbrads cumplettamain. Las suandantas colonnas vegnan spetgadas en la successiun menziunada qua:

Num|Descripziun
---|---
`ID`|Il numer UST da la vischnanca il mument da la votaziun. La valur `0` po vegnir duvrada per persunas che vivan a l'exteriur.
`Ja Stimmen`|Il dumber da las vuschs affirmativas da la votaziun. Sch'il text `unbekannt` vegn endatà, vegn la lingia ignorada (cedels da votar anc betg dumbrads).
`Nein Stimmen`|Il dumber da las vuschs negativas da la votaziun. Sch'il text `unbekannt` vegn endatà, vegn la lingia ignorada (cedels da votar anc betg dumbrads).
`Stimmberechtigte`|Il dumber da las persunas cun dretg da votar. Sch'il text `unbekannt` vegn endatà, vegn la lingia ignorada (cedels da votar anc betg dumbrads).
`Leere Stimmzettel`|Il dumber dals cedels da votar ch'èn vegnids dads giu vids. Sch'il text `unbekannt` vegn endatà, vegn la lingia ignorada (cedels da votar anc betg dumbrads).
`Ungültige Stimmzettel`|Il dumber dals cedels da votar nunvalaivels. Sch'il text `unbekannt` vegn endatà, vegn la lingia ignorada (cedels da votar anc betg dumbrads).

#### Resultats temporars

Sche la vischnanca n'è betg cuntegnida en ils resultats, vala ella sco anc betg dumbrada ora.

#### Project

- [vote_standard.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/vote_standard.csv)

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


#### Resultats temporars

Vischnancas valan sco anc betg dumbradas ora, sch'ina da las duas suandantas cundiziuns constat:
- `counted = false`
- la vischnanca n'è betg cuntegnida en ils resultats

Sch'il status
- è `interim`, vala la votaziun sco anc betg terminada
- è `final`, vala la votaziun sco terminada
- è `unknown` ist, vala la votaziun sco terminada, sche tut las vischnancas (spetgadas) èn dumbradas ora

#### Project

- [vote_onegov.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/vote_onegov.csv)


### Wabsti

The format of the "Wabsti Elections and Referenda (VRSG)" election program consists of a single file which contains all the data for many referenda. There is a line for every referendum and municipality.

#### Colonnas

Las suandantas colonnas vegnan evaluadas e ston almain esser avant maun:
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

#### Resultats temporars

Vischnancas valan sco anc betg dumbradas ora, sch'ina da las duas suandantas cundiziuns constat:
- `StimmBet = 0`
- la vischnanca n'è betg cuntegnida en ils resultats

#### Project

- [vote_wabsti.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/vote_wabsti.csv)


### WabstiCExport

Sustegnida vegn la versiun `>= 2.2`. Las differentas colonnas da las differentas datotecas èn definidas en la documentaziun dal program Exporter.
