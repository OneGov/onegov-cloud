Format Specificaziun Elecziuns
==============================

Sco formats da datoteca vegnan acceptadas datotecas CSV, XLS u XLSX che vegnan generadas dal "Wabsti Elecziuns e votaziuns (VRSG)" u da l'applicaziun web sezza. Sche la tabella duai vegnir fatga a maun, è il format da l'applicaziun web il pli simpel.

Ina "vischnanca" po er esser in district, in circul electoral e.u.v.

## Cuntegn

1. [OneGov](#1-onegov)
2. [Wabsti Maiorz](#2-wabsti-maiorz)
3. [Wabsti Proporz](#3-wabsti-proporz)
4. [WabstiCExport Maiorz](#4-wabsticexport-maiorz)
5. [WabstiCExport Proporz](#5-wabsticexport-proporz)
6. [Party results](#6-party-results)

1 Onegov
--------

The format, which will be used by the web application for the export, consists of a single file per election. There is a row for each municipality and candidate.

### Colonnas

Las suandantas colonnas vegnan evaluadas e duessan esser avant maun:

Num|Descripziun
---|---
`election_absolute_majority`|Maioritad absoluta da l'elecziun, mo tar elecziuns da maiorz.
`election_status`|`unknown`, `interim` or `final`.
`election_counted_municipalites`|Dumber da las vischnancas ch'èn dumbradas ora. Sche `election_counted_municipalites = election_total_municipalites`, vala l'elecziun sco dumbrada ora cumplettamain.
`election_total_municipalites`|Dumber total da vischnancas. Sch'i na po betg vegnir dada ina infurmaziun exacta davart il status da l'elecziun (damai che Wahlt è vegnì importà da Wabsti), è questa valur `0`.
`entity_bfs_number`|Numer UST da la vischnanca. A value of `0` can be used for expats.
`entity_name`|The name of the municipality.
`entity_elegible_voters`|Dumber da persunas cun dretg da votar da la vischnanca.
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
`candidate_family_name`|Num da famiglia da la candidata u dal candidat.
`candidate_first_name`|Prenum da la candidata u dal candidat.
`candidate_elected`|True, sche la candidata u il candidat è vegnì elegì.
`candidate_party`|The name of the party.
`candidate_votes`|Dumber da vuschs da candidat en la vischnanca.

#### Panachage results

The results may contain panachage results by adding one column per list:

Num|Descripziun
---|---
`panachage_votes_from_list_{XX}`|The number of votes the list got from the list with `list_id = XX`. A `list_id` with the value `999` marks the votes from the blank list.


### Resultats temporars

Las vischnancas che n'èn anc betg dumbradas ora n'èn betg cuntegnidas en las datas.

If the status is
- `interim`, the whole election is considered not yet completed
- `final`, the whole election is considered completed
- `unknown`, the whole vote is considered completed, if `election_counted_entities` and `election_total_entities` match

### Project

- [election_onegov_majorz.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_onegov_majorz.csv)
- [election_onegov_proporz.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_onegov_proporz.csv)

2 Wabsti Maiorz
---------------

Il format da datoteca premetta duas singulas tabellas: l'export da datas e la glista da las candidatas e dals candidats elegids.

### Colonnas "Export da datas"

En l'export da datas datti ina lingia per mintga vischnanca, las candidatas ed ils candidats figureschan en colonnas. Las suandantas colonnas vegnan evaluadas e duessan esser avant maun:

Num|Descripziun
---|---
`AnzMandate`|
`BFS`|The municipality number (BFS number) at the time of the election. A value of `0` can be used for expats.
`EinheitBez`|
`StimmBer`|
`StimmAbgegeben`|
`StimmLeer`|
`StimmUngueltig`|
`StimmGueltig`|

Sco er per mintga candidata u candidat:

Num|Descripziun
---|---
`KandID_{XX}`|
`KandName_{XX}`|
`KandVorname_{XX}`|
`Stimmen_{XX}`|

Ultra da quai vegnan las vuschs vidas e nunvalaivlas er registradas sco candidatas e candidats, e quai a maun dals suandants nums da candidat:

- `KandName_{XX} = 'Leere Zeilen'` (Empty votes)
- `KandName_{XX} = 'Ungültige Stimmen'` (Invalid votes)

### Colonnas "Resultats da las candidatas e dals candidats"

Cunquai ch'il format da datoteca na furnescha naginas infurmaziuns davart las candidatas ed ils candidats elegids, ston quellas vegnir agiuntadas en ina segunda tabella. Mintga lingia cuntegna ina candidata u in candidat elegì cun las suandantas colonnas:

Num|Descripziun
---|---
`ID`|La ID da la candidata u dal candidat (`KandID_{XX}`)
`Name`|Il num da famiglia da la candidata u dal candidat
`Vorname`|Il prenum da la candidata u dal candidat

### Resultats temporars

Il format da datoteca na cuntegna naginas infurmaziuns definitivas, sche tut l'elecziun è dumbrada ora cumplettamain. Questa infurmaziun sto vegnir furnida directamain sin il formular per l'upload da las datas.

Il format da datoteca na cuntegna naginas infurmaziuns definitivas, sch'ina singula vischnanca è dumbrada ora cumplettamain. Perquai na vegn, uscheditg che l'entira elecziun n'è betg terminada, er betg mussà il progress en Wabsti. Sch'i mancan però cumplettamain vischnancas en ils resultats, valan quellas sco anc betg dumbradas ora.

### Projects

- [election_wabsti_majorz_results.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_majorz_results.csv)
- [election_wabsti_majorz_candidates.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_majorz_candidates.csv)

3 Wabsti Proporz
----------------

Il format da datoteca premetta quatter singulas tabellas: l'export da datas dals resultats, l'export da datas da las statisticas, las colliaziuns da glistas e la glista da las candidatas e dals candidats elegids.

### Colonnas "Export da datas dals resultats"

En l'export da datas datti ina lingia per candidata u candidat e per vischnanca. Las suandantas colonnas vegnan evaluadas e duessan esser avant maun:

Num|Descripziun
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

Num|Descripziun
---|---
``{List ID}.{List code}`|The number of votes the list got from the list with the given `Liste_ID`. A `Liste_ID` with the value `99` (`99.WoP`) marks the votes from the blank list.

### Colonnas "Export da datas da la statistica"

La datoteca cun las statisticas tar las singulas vischnancas duess cuntegnair las suandantas colonnas:

Num|Descripziun
---|---
`Einheit_BFS`|
`Einheit_Name`|
`StimBerTotal`|
`WZEingegangen`|
`WZLeer`|
`WZUngueltig`|
`StmWZVeraendertLeerAmtlLeer`|

### Colonnas "Colliaziuns da glistas"

La datoteca cun las colliaziuns da glistas duess cuntegnair las suandantas colonnas:

Num|Descripziun
---|---
`Liste`|
`LV`|
`LUV`|

### Colonnas "Resultats da las candidatas e dals candidats"

Cunquai ch'il format da datoteca na furnescha naginas infurmaziuns davart las candidatas ed ils candidats elegids, ston quellas vegnir agiuntadas en ina segunda tabella. Mintga lingia cuntegna ina candidata u in candidat elegì cun las suandantas colonnas:

Num|Descripziun
---|---
`ID`|La ID da la candidata u dal candidat (`Liste_KandID`).
`Name`|Il num da famiglia da la candidata u dal candidat.
`Vorname`|Il prenum da la candidata u dal candidat.

### Resultats temporars

Il format che vegn duvrà da l'applicaziun web per l'export sa cumpona d'ina singula datoteca per elecziun. Per mintga vischnanca e candidata u candidat datti ina lingia.

Il format da datoteca na cuntegna naginas infurmaziuns definitivas, sch'ina singula vischnanca è dumbrada ora cumplettamain. Perquai na vegn, uscheditg che l'entira elecziun n'è betg terminada, er betg mussà il progress en Wabsti. Sch'i mancan però cumplettamain vischnancas en ils resultats, valan quellas sco anc betg dumbradas ora.

### Projects

- [election_wabsti_proporz_results.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_proporz_results.csv)
- [election_wabsti_proporz_statistics.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_proporz_statistics.csv)
- [election_wabsti_proporz_list_connections.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_proporz_list_connections.csv)
- [election_wabsti_proporz_candidates.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_proporz_candidates.csv)


4 WabstiCExport Maiorz
----------------------

Version `2.2` is supported, please refer to the documentation provided by the exporter program for more information about the columns of the different files.


5 WabstiCExport Proporz
-----------------------

Version `2.2` is supported, please refer to the documentation provided by the exporter program for more information about the columns of the different files.


6 Party results
---------------

Each (proporz) election may contain party results. These results are independent of the other results and typically contain the already aggregated results of the different lists of a party.

The following columns will be evaluated and should exist:

Num|Descripziun
---|---
`year`|The year of the election.
`total_votes`|The total votes of the election.
`name`|The name of the party.
`color`|The color of the party.
`mandates`|The number of mandates.
`votes`|The number of votes.

### Template

- [election_party_results.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_party_results.csv)
