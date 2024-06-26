Elecziuns & votaziuns: Open Data
================================

Cundiziun d'utilisaziun
-----------------------

Libra utilisaziun. La funtauna sto vegnir inditgada.

- Vus dastgais duvrar questa unitad da datas per intents betg commerzials.
- Vus dastgais duvrar questa unitad da datas per intents commerzials.
- La funtauna sto vegnir inditgada (autura u autur, titel e link a l'unitad da datas).

Introducziun
------------

Per mintga pagina impurtanta datti in'alternativa JSON correspundenta.

Tuts Responses cuntegnan il `Last-Modified` HTTP Header che infurmescha, cura ch'igl è vegnida fatga l'ultima midada (p.ex. cura ch'igl èn vegnids chargiads si l'ultima giada resultats d'ina elecziun u d'ina votaziun).

Ina "vischnanca" po er esser in district, in circul electoral e.u.v.

Cuntegn
-------

1. [Survista dals resultats](#1-survista-dals-resultats)
2. [Resultats da las elecziuns](#2-resultats-da-las-elecziuns)
3. [Resultats da la votaziun](#3-resultats-da-la-votaziun)

1 Survista dals resultats
-------------------------

```
URL (latest): /json
URL (archive by year): /archive/{year}/json
URL (archive by date): /archive/{year}-{month}-{day}/json
URL (election): /election/{id}/summary
URL (vote): /vote/{id}/summary
```

Ils resultats che vegnan preschentads sin la pagina iniziala e sin las paginas d'archiv èn disponibels en il format JSON. Las datas cuntegnan ultra d'intginas infurmaziuns globalas per mintga elecziun / votaziun las suandantas infurmaziuns:

Num|Descripziun
---|---
`type`|`election` per elecziuns, `election_compound` per colliaziuns cun l'elecziun, f`vote` per votaziuns.
`title`|In object cun ils titels translatads.
`date`|La data (ISO 8601).
`domain`|Champ d'influenza (confederaziun, chantun, ...).
`url`|In link a la vista detagliada.
`completed`|True, if the vote or election is completed.
`progress`|In object che cuntegna il dumber da las vischnancas/elecziuns dumbradas ora (`counted`) ed il dumber total da vischnancas/elecziuns (`total`).
`last_modified`|Ultima midadas (ISO 8601).
`turnout`|Participaziun a la elecziun/votaziun en pertschient.

Ils resultats da la votaziun cuntegnan las suandantas infurmaziuns supplementaras:

Num|Descripziun
---|---
`answer`|Il resultat da la votaziun: acceptà (`accepted`), refusà (`rejected`), iniziativa (`proposal`) u cuntraproposta (`counter-proposal`).
`yeas_percentage`|Vuschs affirmativas en pertschients.
`nays_percentage`|Vuschs negativas en pertschients.
`local` (*optional*)|Federal and cantonal votes within a communal instance may contain additionally the results of the municipality in the form of an object with `answer`, `yeas_percentage` and `nays_percentage`.

Ils resultats da las elecziuns cuntegnan las suandantas indicaziuns supplementaras:

Name|Description
---|---
`elected`|Ina glista cun las candidatas ed ils candidats elegids.

Ils resultats da las colliaziuns cun l'elecziun cuntegnan las suandantas indicaziuns supplementaras:

Name|Description
---|---
`elected`|Ina glista cun las candidatas ed ils candidats elegids.
`elections`|Ina glista cun links per las elecziuns.

2 Resultats da las elecziuns
----------------------------

### Resultats elavurads

```
URL: /election/{id}/json
```

I vegnan restituidas las medemas datas sco en la vista normala, mo en ina furma structurada.

### Datas nunelavuradas

#### Resultats da las candidatas e dals candidats

```
URL: /election/{id}/data-{format}
```

Las datas nunelavuradas da las candidatas e dals candidats èn disponiblas en ils suandants formats:

Format|URL
---|---
JSON|`/data-json`
CSV|`/data-csv`

Ils suandants champs èn disponibels en tut ils formats:

Num|Descripziun
---|---
`election_id`|ID dell'elezione. Utilizzato nell'URL.
`election_title_{locale}`|Titel translatà, p.ex. `title_de_ch` per il titel tudestg.
`election_short_title_{locale}`|Titel curt translatà, p.ex. `title_de_ch` per il titel tudestg.
`election_date`|La data da l'elecziun (sco segns ISO 8601)
`election_domain`|sin plaun naziunal (`federation`), regiunal (`region`), chantunal (`canton`) u communal (`municipality`)
`election_type`|elecziun da proporz (`proporz`) u elecziun da maiorz (`majorz`)
`election_mandates`|Il dumber dals mandats/sezs.
`election_absolute_majority`|La maioritad absoluta. Mo tar elecziuns da maiorz.
`election_status`|Zwischenergebnisse (`interim`), Endergebnisse (`final`) oder unbekannt (`unknown`).
`entity_id`|La ID da la vischnanca/dal lieu. A value `0` represents the expats.
`entity_name`|Il num da la vischnanca/dal lieu.
`entity_district`|Circul electoral/district/regiun da la vischnanca.
`entity_counted`|`True`, sch'il resultat è vegnì eruì.
`entity_eligible_voters`|Il dumber da las votantas e dals votants da la vischnanca/dal lieu.
`entity_expats`|Dumber da las persunas da l'unitad che vivan a l'exteriur.
`entity_received_ballots`|Il dumber dals cedels electorals consegnads da la vischnanca/dal lieu.
`entity_blank_ballots`|Il dumber dals cedels electorals vids da la vischnanca/dal lieu.
`entity_invalid_ballots`|Il dumber dals cedels electorals nunvalaivels da la vischnanca/dal lieu.
`entity_unaccounted_ballots`|Il dumber dals cedels electorals nunvalaivels u vids da la vischnanca/dal lieu.
`entity_accounted_ballots`|Il dumber dals cedels electorals valaivels da la vischnanca/dal lieu.
`entity_blank_votes`|Il dumber da las vuschs vidas da la vischnanca/dal lieu.
`entity_invalid_votes`|Il dumber da las vuschs nunvalaivlas da la vischnanca/dal lieu. Nagins en cas d'ina elecziun da proporz.
`entity_accounted_votes`|Il dumber da las vuschs valaivlas da la vischnanca/dal lieu.
`list_name`|Il num da la glista da la persuna che candidescha. Mo en cas d'elecziuns da proporz.
`list_id`|La ID da la glista, per la quala la candidata u il candidat candidescha. Mo tar elecziuns da proporz.
`list_color`|La colur da la glista sco valur hexadecimala, p.ex. `#a6b784`. Mo tar elecziuns da proporz.
`list_number_of_mandates`|Il dumber da mandats da la glista. Mo tar elecziuns da proporz.
`list_votes`|Il dumber da las vuschs da las glistas. Mo tar elecziuns da proporz.
`list_connection`|La ID da la colliaziun da glistas. Mo tar elecziuns da proporz.
`list_connection_parent`|La ID da la colliaziun da glistas surordinada. Mo en cas d'elecziuns da proporz e sch'i sa tracta d'ina sutcolliaziun da glistas.
`list_panachage_votes_from_list_XX`|Il dumber da vuschs da la glista cun `list_id = XX`. La `list_id` cun la valur `999` stat per la glista vida. Na cuntegna naginas vuschs da l'atgna glista.
`candidate_family_name`|Il num da famiglia da la persuna che candidescha.
`candidate_first_name`|Il prenum da la persuna che candidescha.
`candidate_id`|La ID da la candidata u dal candidat.
`candidate_elected`|True, sche la candidata u il candidat è vegnì elegì.
`candidate_party`|Il num da la partida.
`candidate_party_color`|La colur da la partida sco valur hexadecimala, p.ex. `#a6b784`.
`candidate_gender`|La schlattaina da la candidata u dal candidat: `female` (feminin), `male` (masculin) u `undetermined` (nundeterminà). Opziunal.
`candidate_year_of_birth`|L'annada da la candidata u dal candidat. Opziunal.
`candidate_votes`|Il dumber da las vuschs da candidat(a) da la vischnanca/dal lieu.
`candidate_panachage_votes_from_list_XX`|Il dumber da vuschs da candidatas e candidats da la glista cun `list_id = XX`. La `list_id` cun la valur `999` stat per la glista vida.

Ils resultats da las colliaziuns cun l'elecziun cuntegnan las suandantas indicaziuns supplementaras:

Name|Description
---|---
`compound_id`|ID da la colliaziun cun l'elecziun. Utilizzato nell'URL.
`compound_title_{locale}`|Titel translatà, p.ex. `title_de_ch` per il titel tudestg.
`compound_short_title_{locale}`|Titel curt translatà, p.ex. `title_de_ch` per il titel tudestg.
`compound_date`|La data da la colliaziun cun l'elecziun (sco segns ISO 8601).
`compound_mandates`|Il dumber total dals mandats/sezs.

Las vischnancas che n'èn anc betg dumbradas ora n'èn betg cuntegnidas.

#### Resultats da las partidas

```
URL: /election/{id}/data-parties-{format}
```

Las datas nunelavuradas da las partidas èn disponiblas en ils suandants formats:

Format|URL
---|---
JSON|`/data-parties-json`
CSV|`/data-parties-csv`

Ils suandants champs èn disponibels en tut ils formats:

Num|Descripziun
---|---
`domain`|Il plaun, per il qual la lingia vala.
`domain_segment`|L'unitad dal plaun, per la quala la lingia vala.
`year`|L'onn da l'elecziun.
`total_votes`|Il dumber total da las vuschs da l'elecziun.
`name`|Il num da la partida en la lingua da standard.
`name_{locale}`|Translaziun dal num da la partida, p.ex. `name_de_ch` per il num tudestg.
`color`|La colur da la partida sco valur hexadecimala, p.ex. `#a6b784`.
`mandates`|Il dumber da mandats da la partida.
`votes`|Il dumber da vuschs da la partida.
`voters_count`|Wählerzahlen. Die kumulierte Anzahl Stimmen pro Gesamtanzahl Mandate pro Wahl. Nur für verbundene Wahlen.
`voters_count_percentage`|Wählerzahlen (prozentual). Die kumulierte Anzahl Stimmen pro Gesamtanzahl Mandate pro Wahl. Nur für verbundene Wahlen.
`panachage_votes_from_{XX}`|Il dumber da vuschs da la glista cun `list_id = XX`. La `list_id` cun la valur `999` stat per la glista vida.

3 Resultats da la votaziun
--------------------------

### Resultats elavurads

```
URL: /vote/{id}/json
```

I vegnan restituidas las medemas datas sco en la vista normala, mo en ina furma structurada.

### Datas nunelavuradas

```
URL: `/vote/{id}/{data-format}`
```

Las datas nunelavuradas che vegnan duvradas per mussar ils resultats stattan a disposiziun en ils suandants formats:

Format|URL
---|---
JSON|`/data-json`
CSV|`/data-csv`

Ils suandants champs èn disponibels en ils formats `JSON` e `CSV`:

Num|Descripziun
---|---
`id`|ID da la votaziun. Ussà en l'URL.
`title_{locale}`|Titel translatà, p.ex. `title_de_ch` per il titel tudestg.
`short_title_{locale}`|Titel curt translatà, p.ex. `title_de_ch` per il titel tudestg.
`date`|La data da la votaziun (sco segns ISO 8601).
`shortcode`|Scursanida interna (definescha la successiun da pliras votaziuns che han lieu il medem di).
`domain`|`federation` per votaziuns naziunalas, `canton` per votaziuns chantunalas.
`status`|Resultats intermediars (`interim`), resultats finals (`final`) u stadi dals resultats nunenconuschent (`unknown`).
`answer`|Il resultat da la votaziun: `accepted` (acceptà), `rejected` (refusà), `proposal` (proposta) u `counter-proposal` (cuntraproposta).
`type`|Tip: `proposal` (proposta), `counter-proposal` (cuntraproposta) u `tie-breaker` (dumonda decisiva).
`ballot_answer`|Il resultat tenor il tip: `accepted` (accepta) u `rejected` (refusada) per `type=proposal` (proposta) e `type=counter-proposal`(cuntraproposta); `proposal` (proposta) u `counter-proposal` (cuntraproposta) per `type=tie-breaker` (dumonda decisiva).
`district`|Circul electoral/district/regiun da la vischnanca.
`name`|Il num da la vischnanca/dal lieu.
`entity_id`|La ID da la vischnanca/dal lieu. A value `0` represents the expats.
`counted`|Gist, sch'il resultat è vegnì eruì. Fauss, sch'il resultat n'è anc betg enconuschent (las valurs n'èn anc betg correctas).
`yeas`|Il dumber da las vuschs affirmativas
`nays`|Il dumber da las vuschs negativas
`invalid`|Il dumber da las vuschs nunvalaivlas
`empty`|Il dumber da las vuschs vidas
`eligible_voters`|Il dumber da las persunas cun dretg da votar
`expats`|Dumber da las persunas da l'unitad che vivan a l'exteriur.

4 Sitemap
---------

```
URL: /sitemap.xml
```

Returnar enavos il sez en il format da XML. (https://www.sitemaps.org/protocol.html).

```
URL: /sitemap.json
```

Returnar enavos il sez en il format da JSON.
