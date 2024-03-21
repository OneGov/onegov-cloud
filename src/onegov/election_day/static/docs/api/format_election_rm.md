# Format Specificaziun Elecziuns

Sco formats da datoteca vegnan acceptadas datotecas CSV, XLS u XLSX che vegnan generadas dal "Wabsti Elecziuns e votaziuns (VRSG)" u da l'applicaziun web sezza. Sche la tabella duai vegnir fatga a maun, è il format da l'applicaziun web (OneGov) il pli simpel.

## Cuntegn

<!-- TOC updateonsave:false -->

- [Format Specificaziun Elecziuns](#format-specificaziun-elecziuns)
    - [Cuntegn](#cuntegn)
    - [Remartgas preliminaras](#remartgas-preliminaras)
        - [Unitads](#unitads)
        - [Elecziun taciturnas](#elecziun-taciturnas)
        - [Elecziuns regiunalas](#elecziuns-regiunalas)
    - [Formats](#formats)
        - [Onegov](#onegov)
            - [Colonnas](#colonnas)
            - [Resultats pon cuntegnair datas panaschadas da glistas](#resultats-pon-cuntegnair-datas-panaschadas-da-glistas)
            - [Datas da candidatas e candidats panaschads](#datas-da-candidatas-e-candidats-panaschads)
            - [Resultats temporars](#resultats-temporars)
            - [Elecziuns colliadas](#elecziuns-colliadas)
            - [Project](#project)
        - [WabstiCExport Maiorz](#wabsticexport-maiorz)
        - [WabstiCExport Proporz](#wabsticexport-proporz)
        - [Resultats da las partidas](#resultats-da-las-partidas)
            - [Champ d'influenza](#champ-dinfluenza)
            - [Resultats pon cuntegnair datas panaschadas](#resultats-pon-cuntegnair-datas-panaschadas)
            - [Projects](#projects)

<!-- /TOC -->

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
`list_color`|La colur da la glista sco valur hexadecimala, p.ex. `#a6b784`. Mo tar elecziuns da proporz.
`list_number_of_mandates`|Dumber total da mandats da la glista. Mo tar elecziuns da proporz.
`list_votes`|Dumber a vuschs da la glista. Mo tar elecziuns da proporz.
`list_connection`|ID da la colliaziun da glistas. Mo tar elecziuns da proporz.
`list_connection_parent`|ID da la colliaziun da glistas surordinada. Mo tar elecziuns da proporz e sch'i sa tracta d'ina sutcolliaziun da glistas.
`candidate_id`|La ID da la candidata u dal candidat.
`candidate_family_name`|Num da famiglia da la candidata u dal candidat.
`candidate_first_name`|Prenum da la candidata u dal candidat.
`candidate_elected`|True, sche la candidata u il candidat è vegnì elegì.
`candidate_party`|Il num da la partida.
`candidate_party_color`|La colur da la partida sco valur hexadecimala, p.ex. `#a6b784`.
`candidate_gender`|La schlattaina da la candidata u dal candidat: `female` (feminin), `male` (masculin) u `undetermined` (nundeterminà). Opziunal.
`candidate_year_of_birth`|L'annada da la candidata u dal candidat. Opziunal.
`candidate_votes`|Dumber da vuschs da candidat en la vischnanca.

#### Resultats pon cuntegnair datas panaschadas da glistas

Ils resultats pon cuntegnair datas panaschadas da glistas, tras quai ch'i vegn agiuntada ina colonna per glista:

Num|Descripziun
---|---
`list_panachage_votes_from_list_{XX}` / `panachage_votes_from_list_{XX}`|Il dumber da vuschs da la glista cun `list_id = XX`. La `list_id` cun la valur `999` stat per la glista vida. Las vuschs da l'atgna glista vegnan ignoradas.

#### Datas da candidatas e candidats panaschads

Ils resultats pon cuntegnair datas da candidatas e candidats panaschads, tras quai ch'i vegn agiuntada ina colonna per glista:

Num|Descripziun
---|---
`candidate_panachage_votes_from_list_{XX}`|Il dumber da vuschs da candidatas e candidats da la glista cun `list_id = XX`. La `list_id` cun la valur `999` stat per la glista vida.

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


### WabstiCExport Maiorz

Sustegnida vegn la versiun '>= 2.2'. Las differentas colonnas da las differentas datotecas èn definidas en la documentaziun dal program d'export.


### WabstiCExport Proporz

Sustegnida vegn la versiun '>= 2.2'. Las differentas colonnas da las differentas datotecas èn definidas en la documentaziun dal program d'export.


### Resultats da la(s) partida(s)

Mintga elecziun da proporz po cuntegnair resultats da partidas. Quels èn independents dals auters resultats e cuntegnan tipicamain ils resultats cumulads da las differentas glistas d'ina singula partida.

Las suandantas colonnas vegnan evaluadas e duessan esser avant maun:

Num|Descripziun
---|---
`domain`|Il plaun, per il qual la lingia vala. Opziunal.
`domain_segment`|L'unitad dal plaun, per la quala la lingia vala. Opziunal.
`year`|L'onn da l'elecziun.
`total_votes`|Il dumber total da vuschs da l'elecziun.
`name`|Il num da la partida en la lingua da standard. Opziunal*.
`name_{locale}`|Translaziun dal num da la partida, p.ex. `name_de_CH` per il num tudestg. Opziunal. Guardai che Vus inditgeschias il num da la partida en la lingua da standard ubain en la colonna name ubain en la colonna name_{default_locale}.
`id`|ID da la partida (cifra casuala).
`color`|La colur da la partida sco valur hexadecimala, p.ex. `#a6b784`.
`mandates`|Il dumber da sezs da la partida.
`votes`|Il dumber da vuschs da la partida.
`voters_count`|Wählerzahlen. Die kumulierte Anzahl Stimmen pro Gesamtanzahl Mandate pro Wahl. Nur für verbundene Wahlen.
`voters_count_percentage`|Wählerzahlen (prozentual). Die kumulierte Anzahl Stimmen pro Gesamtanzahl Mandate pro Wahl (prozentual). Nur für verbundene Wahlen.

#### Champ d'influenza

`domain` e `domain_segment` permettan d'endatar ils resultats da la partida per in auter champ d'influenza che quel da l'elecziun u da la colliaziun. `domain` correspunda ad in champ d'influenza subordinà da l'elecziun u da la colliaziun, p.ex. en las elecziuns da parlaments chantunals tut tenor chantun `superregion`, `region`, `district` u `municipality`. `domain_segment` correspunda ad in'unitad en quest champ d'influenza subordinà, p.ex. `Regiun 1`, `Bravuogn`, `Toggenburg` u `Zug`. Normalmain po tant il champ `domain` sco er il champ `domain_segment` vegnir laschà vid u vegnir laschà davent. Il champ `domain` survegn lura implicitamain il `domain` da l'elecziun u da la colliaziun. Actualmain vegnan sustegnids mo il `domain` da l'elecziun u da la colliaziun sco er il `domain = superregion` en elecziuns colliadas.

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
