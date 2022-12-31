# Format Specificaziun Elecziuns

Sco formats da datoteca vegnan acceptadas datotecas CSV, XLS u XLSX che vegnan generadas dal "Wabsti Elecziuns e votaziuns (VRSG)" u da l'applicaziun web sezza. Sche la tabella duai vegnir fatga a maun, è il format da l'applicaziun web (OneGov) il pli simpel.

## Cuntegn

<!-- https://atom.io/packages/atom-mdtoc -->
<!-- MDTOC maxdepth:6 firsth1:2 numbering:1 flatten:0 bullets:1 updateOnSave:1 -->

- 1. [Cuntegn](#Cuntegn)
- 2. [Remartgas preliminaras](#Remartgas-preliminaras)
   - 2.1. [Unitads](#Unitads)
   - 2.2. [Elecziun taciturnas](#Elecziun-taciturnas)
   - 2.3. [Elecziuns regiunalas](#Elecziuns-regiunalas)
- 3. [Formats](#Formats)
   - 3.1. [Onegov](#Onegov)
      - 3.1.1. [Colonnas](#Colonnas)
      - 3.1.2. [Resultats pon cuntegnair datas panaschadas](#Resultats-pon-cuntegnair-datas-panaschadas)
      - 3.1.3. [Resultats temporars](#Resultats-temporars)
      - 3.1.4. [Elecziuns colliadas](#Elecziuns-colliadas)
      - 3.1.5. [Project](#Project)
   - 3.2. [Wabsti Maiorz](#Wabsti-Maiorz)
      - 3.2.1. [Colonnas "Export da datas"](#Colonnas-Export-da-datas)
      - 3.2.2. [Colonnas "Resultats da las candidatas e dals candidats"](#Colonnas-Resultats-da-las-candidatas-e-dals-candidats)
      - 3.2.3. [Resultats temporars](#Resultats-temporars-1)
      - 3.2.4. [Projects](#Projects)
   - 3.3. [Wabsti Proporz](#Wabsti-Proporz)
      - 3.3.1. [Colonnas "Export da datas dals resultats"](#Colonnas-Export-da-datas-dals-resultats)
      - 3.3.2. [Resultats pon cuntegnair datas panaschadas](#Resultats-pon-cuntegnair-datas-panaschadas-1)
      - 3.3.3. [Colonnas "Export da datas da la statistica"](#Colonnas-Export-da-datas-da-la-statistica)
      - 3.3.4. [Colonnas "Colliaziuns da glistas"](#Colonnas-Colliaziuns-da-glistas)
      - 3.3.5. [Colonnas "Resultats da las candidatas e dals candidats"](#Colonnas-Resultats-da-las-candidatas-e-dals-candidats-1)
      - 3.3.6. [Resultats temporars](#Resultats-temporars-2)
      - 3.3.7. [Projects](#Projects-1)
   - 3.4. [WabstiCExport Maiorz](#WabstiCExport-Maiorz)
   - 3.5. [WabstiCExport Proporz](#WabstiCExport-Proporz)
   - 3.6. [Resultats da la(s) partida(s)](#Resultats-da-las-partidas)
      - 3.6.1. [Einflussbereich](#Einflussbereich)
      - 3.6.2. [Resultats pon cuntegnair datas panaschadas](#Resultats-pon-cuntegnair-datas-panaschadas-2)
      - 3.6.3. [Projects](#Projects-2)

<!-- /MDTOC -->

## Remartgas preliminaras

### Unitads

In'unitad correspunda ad ina vischnanca (instanzas chantunalas, instanzas communalas senza quartiers) u ad in quartier (instanzas communalas cun quartiers).

### Elecziun taciturnas

Per elecziuns taciturnas po vegnir duvrà il format OneGov. En quest cas vegnan tut las vuschs messas a `0`.

### Elecziuns regiunalas

En cas d'elecziuns regiunalas vegnan spetgads mo ils resultats da l'elecziun da las unitads d'in circul electoral, if the corresponding option is set on the election.

## Formats

### Onegov

Il format che vegn duvrà da l'applicaziun web per l'export sa cumpona d'ina singula datoteca per elecziun. Per mintga vischnanca e candidata u candidat datti ina lingia.

#### Colonnas

Las suandantas colonnas vegnan evaluadas e duessan esser avant maun:

Num|Descripziun
---|---
`election_absolute_majority`|Maioritad absoluta da l'elecziun, mo tar elecziuns da maiorz.
`election_status`|Resultats intermediars (`interim`), resultats finals (`final`) u stadi dals resultats nunenconuschent (`unknown`).
`entity_id`|Numer UST da la vischnanca. La valur `0` po vegnir duvrada per persunas che vivan a l'exteriur.
`entity_counted`|`True`, sch'il resultat è vegnì eruì.
`entity_eligible_voters`|Dumber da persunas cun dretg da votar da la vischnanca.
`entity_expats`|Dumber da las persunas da l'unitad che vivan a l'exteriur. Opziunal.
`entity_received_ballots`|Dumber da cedels da votar consegnads da la vischnanca.
`entity_blank_ballots`|Dumber da cedels da votar vids da la vischnanca.
`entity_invalid_ballots`|Dumber da cedels da votar nunvalaivels da la vischnanca.
`entity_blank_votes`|Dumber da vuschs vidas da la vischnanca.
`entity_invalid_votes`|Dumber da vuschs nunvalaivlas da la vischnanca. Nulla en cas d'ina elecziun da proporz.
`list_name`|Num da la glista da la candidata u dal candidat. Mo tar elecziuns da proporz.
`list_id`|ID da la glista da la candidata u dal candidat. Mo tar elecziuns da proporz.
`list_color`|Die Farbe der Liste als Hexadezimalwert, z.B. `#a6b784'. Nur bei Proporzwahlen.
`list_number_of_mandates`|Dumber total da mandats da la glista. Mo tar elecziuns da proporz.
`list_votes`|Dumber a vuschs da la glista. Mo tar elecziuns da proporz.
`list_connection`|ID da la colliaziun da glistas. Mo tar elecziuns da proporz.
`list_connection_parent`|ID da la colliaziun da glistas surordinada. Mo tar elecziuns da proporz e sch'i sa tracta d'ina sutcolliaziun da glistas.
`candidate_id`|La ID da la candidata u dal candidat.
`candidate_family_name`|Num da famiglia da la candidata u dal candidat.
`candidate_first_name`|Prenum da la candidata u dal candidat.
`candidate_elected`|True, sche la candidata u il candidat è vegnì elegì.
`candidate_party`|Il num da la partida.
`candidate_party_color`|Die Farbe der Partei als Hexadezimalwert, z.B. `#a6b784'.
`candidate_gender`|La schlattaina da la candidata u dal candidat: `female` (feminin), `male` (masculin) u `undetermined` (nundeterminà). Opziunal.
`candidate_year_of_birth`|L'annada da la candidata u dal candidat. Opziunal.
`candidate_votes`|Dumber da vuschs da candidat en la vischnanca.

#### Resultats pon cuntegnair datas panaschadas

Ils resultats pon cuntegnair datas panaschadas, tras quai ch'i vegn agiuntada ina colonna per glista:

Num|Descripziun
---|---
`list_panachage_votes_from_list_{XX}`|Il dumber da vuschs da la glista cun `list_id = XX`. La `list_id` cun la valur `999` stat per la glista vida.

#### Resultats temporars

Unitads valan sco anc betg quintadas ora, sch'ina da las duas suandantas cundiziuns constat:
- `counted = false`
- l'unitad n'è betg cuntegnida en ils resultats

Sch'il status è
- `interim`, vala la votaziun sco betg anc terminada
- `final`, vala la votaziun sco terminada
- `unknown`, l'elecziun vala sco terminada, sche tut las unitads (spetgadas) èn dumbradas

#### Elecziuns colliadas

Ils resultats d'elecziuns colliadas pon vegnir chargiads si en ina, sch'i vegn furnida in'unica datoteca cun tut las lingias dals resultats da las singulas elecziuns.

#### Project

- [election_onegov_majorz.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/election_onegov_majorz.csv)
- [election_onegov_proporz.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/election_onegov_proporz.csv)

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

Cunquai ch'il format da la datoteca na furnescha betg adina infurmaziuns davart las candidatas ed ils candidats elegids, pon quellas vegnir furnidas en ina segunda tabella. Mintga lingia cuntegna ina candidata u in candidat elegì cun las suandantas colonnas:

Num|Descripziun
---|---
`KandID`|La ID da la candidata u dal candidat (`KandID_{XX}`).

#### Resultats temporars

Il format da datoteca na cuntegna naginas infurmaziuns definitivas, sche tut l'elecziun è dumbrada ora cumplettamain. Questa infurmaziun sto vegnir furnida directamain sin il formular per l'upload da las datas.

Il format da datoteca na cuntegna naginas infurmaziuns definitivas, sch'ina singula vischnanca è dumbrada ora cumplettamain. Sch'i mancan però cumplettamain vischnancas en ils resultats, valan quellas sco anc betg dumbradas ora.

#### Projects

- [election_wabsti_majorz_results.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/election_wabsti_majorz_results.csv)
- [election_wabsti_majorz_candidates.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/election_wabsti_majorz_candidates.csv)

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

#### Resultats pon cuntegnair datas panaschadas

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

- [election_wabsti_proporz_results.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/election_wabsti_proporz_results.csv)
- [election_wabsti_proporz_statistics.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/election_wabsti_proporz_statistics.csv)
- [election_wabsti_proporz_list_connections.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/election_wabsti_proporz_list_connections.csv)
- [election_wabsti_proporz_candidates.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/election_wabsti_proporz_candidates.csv)


### WabstiCExport Maiorz

Sustegnida vegn la versiun '>= 2.2'. Las differentas colonnas da las differentas datotecas èn definidas en la documentaziun dal program d'export.


### WabstiCExport Proporz

Sustegnida vegn la versiun '>= 2.2'. Las differentas colonnas da las differentas datotecas èn definidas en la documentaziun dal program d'export.


### Resultats da la(s) partida(s)

Mintga elecziun da proporz po cuntegnair resultats da partidas. Quels èn independents dals auters resultats e cuntegnan tipicamain ils resultats cumulads da las differentas glistas d'ina singula partida.

Las suandantas colonnas vegnan evaluadas e duessan esser avant maun:

Num|Descripziun
---|---
`domain`|Der Einflussbereich, für den die Zeile gilt. Optional.
`domain_segment`|Die Einheit des Einflussbereichs, für die die Zeile gilt. Optional.
`year`|L'onn da l'elecziun.
`total_votes`|Il dumber total da vuschs da l'elecziun.
`name`|Il num da la partida en la lingua da standard. Opziunal*.
`name_{locale}`|Translaziun dal num da la partida, p.ex. `name_de_CH` per il num tudestg. Opziunal. Guardai che Vus inditgeschias il num da la partida en la lingua da standard ubain en la colonna name ubain en la colonna name_{default_locale}.
`id`|ID da la partida (cifra casuala).
`color`|Die Farbe der Partei als Hexadezimalwert, z.B. `#a6b784'.
`mandates`|Il dumber da sezs da la partida.
`votes`|Il dumber da vuschs da la partida.
`voters_count`|Wählerzahlen. Die kumulierte Anzahl Stimmen pro Gesamtanzahl Mandate pro Wahl. Nur für verbundene Wahlen.
`voters_count_percentage`|Wählerzahlen (prozentual). Die kumulierte Anzahl Stimmen pro Gesamtanzahl Mandate pro Wahl (prozentual). Nur für verbundene Wahlen.

#### Einflussbereich

`domain` und `domain_segment` ermöglichen, Parteiresultate für einen anderen Einflussbereich als den der Wahl oder des Verbundes zu erfassen. `domain` entspricht dabei einem untergeordneten Einflussbereichs der Wahl oder des Verbundes, z.B. bei kantonalen Parlamentswahlen je nach Kanton `superregion`, `region`, `district` oder `municipality`. `domain_segment` entspricht einer Einheit in diesem untergeordneten Einflussbereich, z.B. `Region 1`, `Bergün`, `Toggenburg` oder `Zug`. Im Normalfall können sowohl `domain` als auch `domain_segment` leer oder weggelassen werden, `domain` wird in diesem Fall implizit auf den `domain` der Wahl oder des Verbundes gesetzt. Aktuell wird nur der `domain` der Wahl oder des Verbundes sowie `domain = 'superregion'` bei verbundenen Wahlen unterstützt.

#### Resultats pon cuntegnair datas panaschadas

Ils resultats pon cuntegnair datas panaschadas, tras quai ch'i vegn agiuntada ina colonna per partida:

Num|Descripziun
---|---
`panachage_votes_from_{XX}`|Il dumber da vuschs da la partida cun `id = XX`. La `id` cun la valur `999` stat per las vuschs da la glista vida.

Datas panaschadas vegnan agiuntadas mo, sche:
- `year` correspunda a l'onn da l'elecziun
- `id (XX)` na correspounda betg a `id` da la colonna

#### Projects

- [election_party_results.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/election_party_results.csv)
