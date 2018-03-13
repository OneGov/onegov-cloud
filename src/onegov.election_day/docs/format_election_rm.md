# Format Specificaziun Elecziuns

Sco formats da datoteca vegnan acceptadas datotecas CSV, XLS u XLSX che vegnan generadas dal "Wabsti Elecziuns e votaziuns (VRSG)" u da l'applicaziun web sezza. Sche la tabella duai vegnir fatga a maun, è il format da l'applicaziun web (OneGov) il pli simpel.

## Cuntegn

<!-- TOC START min:1 max:4 link:true update:true -->
- [Format Specificaziun Elecziuns](#format-specificaziun-elecziuns)
  - [Cuntegn](#cuntegn)
  - [Vorbemerkungen](#vorbemerkungen)
    - [Einheiten](#einheiten)
    - [Elecziun taciturnas](#elecziun-taciturnas)
    - [Regionale Wahlen](#regionale-wahlen)
  - [Formate](#formate)
    - [Onegov](#onegov)
      - [Colonnas](#colonnas)
      - [Panachage results](#panachage-results)
      - [Resultats temporars](#resultats-temporars)
      - [Project](#project)
    - [Wabsti Maiorz](#wabsti-maiorz)
      - [Colonnas "Export da datas"](#colonnas-export-da-datas)
      - [Colonnas "Resultats da las candidatas e dals candidats"](#colonnas-resultats-da-las-candidatas-e-dals-candidats)
      - [Resultats temporars](#resultats-temporars-1)
      - [Projects](#projects)
    - [Wabsti Proporz](#wabsti-proporz)
      - [Colonnas "Export da datas dals resultats"](#colonnas-export-da-datas-dals-resultats)
      - [Panachage results](#panachage-results-1)
      - [Colonnas "Export da datas da la statistica"](#colonnas-export-da-datas-da-la-statistica)
      - [Colonnas "Colliaziuns da glistas"](#colonnas-colliaziuns-da-glistas)
      - [Colonnas "Resultats da las candidatas e dals candidats"](#colonnas-resultats-da-las-candidatas-e-dals-candidats-1)
      - [Resultats temporars](#resultats-temporars-2)
      - [Projects](#projects-1)
    - [WabstiCExport Maiorz](#wabsticexport-maiorz)
    - [WabstiCExport Proporz](#wabsticexport-proporz)
    - [Party results](#party-results)
      - [Template](#template)

<!-- TOC END -->

## Vorbemerkungen

### Einheiten

Eine Einheit entspricht einer Gemeinde (kantonale Instanzen, kommunale Instanzen ohne Stadtteilen) oder einem Stadtteil (kommunale Instanzen mit Stadtteilen).

### Elecziun taciturnas

Per elecziuns taciturnas po vegnir duvrà il format OneGov. En quest cas vegnan tut las vuschs messas a `0`.

### Regionale Wahlen

Bei regionalen Wahlen werden nur Wahlresultate der Einheiten eines Wahlkreises erwartet.

## Formate

### Onegov

Il format che vegn duvrà da l'applicaziun web per l'export sa cumpona d'ina singula datoteca per elecziun. Per mintga vischnanca e candidata u candidat datti ina lingia.

#### Colonnas

Las suandantas colonnas vegnan evaluadas e duessan esser avant maun:

Num|Descripziun
---|---
`election_absolute_majority`|Maioritad absoluta da l'elecziun, mo tar elecziuns da maiorz.
`election_status`|`unknown`, `interim` or `final`.
`entity_id`|Numer UST da la vischnanca. La valur `0` po vegnir duvrada per persunas che vivan a l'exteriur.
`entity_counted`|`True`, sch'il resultat è vegnì eruì.
`entity_eligible_voters`|Dumber da persunas cun dretg da votar da la vischnanca.
`entity_received_ballots`|Dumber da cedels da votar consegnads da la vischnanca.
`entity_blank_ballots`|Dumber da cedels da votar vids da la vischnanca.
`entity_invalid_ballots`|Dumber da cedels da votar nunvalaivels da la vischnanca.
`entity_blank_votes`|Dumber da vuschs vidas da la vischnanca.
`entity_invalid_votes`|Dumber da vuschs nunvalaivlas da la vischnanca. Nulla en cas d'ina elecziun da proporz.
`list_name`|Num da la glista da la candidata u dal candidat. Mo tar elecziuns da proporz.
`list_id`|ID da la glista da la candidata u dal candidat. Mo tar elecziuns da proporz.
`list_number_of_mandates`|Dumber total da mandats da la glista. Mo tar elecziuns da proporz.
`list_votes`|Dumber total da vuschs da la glista. Mo tar elecziuns da proporz.
`list_connection`|ID da la colliaziun da glistas. Mo tar elecziuns da proporz.
`list_connection_parent`|ID da la colliaziun da glistas surordinada. Mo tar elecziuns da proporz e sch'i sa tracta d'ina sutcolliaziun da glistas.
`candidate_id`|La ID da la candidata u dal candidat.
`candidate_family_name`|Num da famiglia da la candidata u dal candidat.
`candidate_first_name`|Prenum da la candidata u dal candidat.
`candidate_elected`|True, sche la candidata u il candidat è vegnì elegì.
`candidate_party`|Il num da la partida.
`candidate_votes`|Dumber da vuschs da candidat en la vischnanca.

#### Panachage results

Ils resultats pon cuntegnair datas panaschadas, tras quai ch'i vegn agiuntada ina colonna per glista:

Num|Descripziun
---|---
`panachage_votes_from_list_{XX}`|The number of votes the list got from the list with `list_id = XX`. A `list_id` with the value `999` marks the votes from the blank list.


#### Resultats temporars

Municipalities are deemed not to have been counted yet if one of the following two conditions apply:
- `counted = false`
- the municipality is not included in the results

Sch'il status è
- `interim`, vala la votaziun sco betg anc terminada
- `final`, vala la votaziun sco terminada
- `unknown`, the whole election is considered completed, if all (expected) municipalities are counted

#### Project

- [election_onegov_majorz.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_onegov_majorz.csv)
- [election_onegov_proporz.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_onegov_proporz.csv)

### Wabsti Maiorz

Il format da datoteca premetta duas singulas tabellas: l'export da datas e la glista da las candidatas e dals candidats elegids.

#### Colonnas "Export da datas"

En l'export da datas datti ina lingia per mintga vischnanca, las candidatas ed ils candidats figureschan en colonnas. Las suandantas colonnas vegnan evaluadas e duessan esser avant maun:
- `AnzMandate`
- `BFS`
- `StimmBer`
- `StimmAbgegeben`
- `StimmLeer`
- `StimmUngueltig`
- `StimmGueltig`

Sco er per mintga candidata u candidat:
- `KandID_{XX}`
- `KandName_{XX}`
- `KandVorname_{XX}`
- `Stimmen_{XX}`

Ultra da quai vegnan las vuschs vidas e nunvalaivlas er registradas sco candidatas e candidats, e quai a maun dals suandants nums da candidat:
- `KandName_{XX} = 'Leere Zeilen'` (Vuschs vidas)
- `KandName_{XX} = 'Ungültige Stimmen'` (Vuschs nunvalaivlas)

#### Colonnas "Resultats da las candidatas e dals candidats"

Cunquai ch'il format da datoteca na furnescha naginas infurmaziuns davart las candidatas ed ils candidats elegids, ston quellas vegnir agiuntadas en ina segunda tabella. Mintga lingia cuntegna ina candidata u in candidat elegì cun las suandantas colonnas:

Num|Descripziun
---|---
`KandID`|La ID da la candidata u dal candidat (`KandID_{XX}`).

#### Resultats temporars

Il format da datoteca na cuntegna naginas infurmaziuns definitivas, sche tut l'elecziun è dumbrada ora cumplettamain. Questa infurmaziun sto vegnir furnida directamain sin il formular per l'upload da las datas.

Il format da datoteca na cuntegna naginas infurmaziuns definitivas, sch'ina singula vischnanca è dumbrada ora cumplettamain. Sch'i mancan però cumplettamain vischnancas en ils resultats, valan quellas sco anc betg dumbradas ora.

#### Projects

- [election_wabsti_majorz_results.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_majorz_results.csv)
- [election_wabsti_majorz_candidates.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_majorz_candidates.csv)

### Wabsti Proporz

Il format da datoteca premetta quatter singulas tabellas: l'export da datas dals resultats, l'export da datas da las statisticas, las colliaziuns da glistas e la glista da las candidatas e dals candidats elegids.

#### Colonnas "Export da datas dals resultats"

En l'export da datas datti ina lingia per candidata u candidat e per vischnanca. Las suandantas colonnas vegnan evaluadas e duessan esser avant maun:
- `Einheit_BFS`
- `Kand_Nachname`
- `Kand_Vorname`
- `Liste_KandID`
- `Liste_ID`
- `Liste_Code`
- `Kand_StimmenTotal`
- `Liste_ParteistimmenTotal`

#### Panachage results

Ils resultats pon cuntegnair datas panaschadas, tras quai ch'i vegn agiuntada ina colonna per glista (`{List ID}.{List code}`: il dumber da vuschs da la glista cun `Liste_ID`). La `Liste_ID` cun la valur `99` (`99.WoP`) stat per la glista vida.

#### Colonnas "Export da datas da la statistica"

La datoteca cun las statisticas tar las singulas vischnancas duess cuntegnair las suandantas colonnas:
- `Einheit_BFS`
- `Einheit_Name`
- `StimBerTotal`
- `WZEingegangen`
- `WZLeer`
- `WZUngueltig`
- `StmWZVeraendertLeerAmtlLeer`

#### Colonnas "Colliaziuns da glistas"

La datoteca cun las colliaziuns da glistas duess cuntegnair las suandantas colonnas:
- `Liste`
- `LV`
- `LUV`

#### Colonnas "Resultats da las candidatas e dals candidats"

Cunquai ch'il format da datoteca na furnescha naginas infurmaziuns davart las candidatas ed ils candidats elegids, ston quellas vegnir agiuntadas en ina segunda tabella. Mintga lingia cuntegna ina candidata u in candidat elegì cun las suandantas colonnas:

Num|Descripziun
---|---
`Liste_KandID`|La ID da la candidata u dal candidat.

#### Resultats temporars

Il format che vegn duvrà da l'applicaziun web per l'export sa cumpona d'ina singula datoteca per elecziun. Per mintga vischnanca e candidata u candidat datti ina lingia.

Il format da datoteca na cuntegna naginas infurmaziuns definitivas, sch'ina singula vischnanca è dumbrada ora cumplettamain. Sch'i mancan però cumplettamain vischnancas en ils resultats, valan quellas sco anc betg dumbradas ora.

#### Projects

- [election_wabsti_proporz_results.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_proporz_results.csv)
- [election_wabsti_proporz_statistics.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_proporz_statistics.csv)
- [election_wabsti_proporz_list_connections.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_proporz_list_connections.csv)
- [election_wabsti_proporz_candidates.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_proporz_candidates.csv)


### WabstiCExport Maiorz

Sustegnida vegn la versiun '>= 2.2'. Las differentas colonnas da las differentas datotecas èn definidas en la documentaziun dal program d'export.


### WabstiCExport Proporz

Sustegnida vegn la versiun '>= 2.2'. Las differentas colonnas da las differentas datotecas èn definidas en la documentaziun dal program d'export.


### Party results

Mintga elecziun da proporz po cuntegnair resultats da partidas. Quels èn independents dals auters resultats e cuntegnan tipicamain ils resultats cumulads da las differentas glistas d'ina singula partida.

Las suandantas colonnas vegnan evaluadas e duessan esser avant maun:

Num|Descripziun
---|---
`year`|L'onn da l'elecziun.
`total_votes`|Il dumber total da vuschs da l'elecziun.
`name`|Il num da la partida.
`color`|La colur da la partida.
`mandates`|Il dumber da sezs da la partida.
`votes`|Il dumber da vuschs da la partida.

#### Template

- [election_party_results.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_party_results.csv)
