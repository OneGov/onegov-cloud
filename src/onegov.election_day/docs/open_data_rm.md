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
`type`|`election` per elecziuns, `vote` per votaziuns.
`title`|In object cun ils titels translatads.
`date`|La data (ISO 8601).
`domain`|Champ d'influenza (confederaziun, chantun, ...).
`url`|In link a la vista detagliada.
`completed`|True, if the vote or election is completed.
`progress`|In object che cuntegna il dumber da las vischnancas dumbradas ora (`counted`) ed il dumber total da vischnancas (`total`).

Ils resultats da la votaziun cuntegnan las suandantas infurmaziuns supplementaras:

Num|Descripziun
---|---
`answer`|Il resultat da la votaziun: acceptà (`accepted`), refusà (`rejected`), iniziativa (`proposal`) u cuntraproposta (`counter-proposal`).
`yeas_percentage`|Vuschs affirmativas en pertschients.
`nays_percentage`|Vuschs negativas en pertschients.
`local` (*optional*)|Federal and cantonal votes within a communal instance may contain additionally the results of the municipality in the form of an object with `answer`, `yeas_percentage` and `nays_percentage`.


2 Resultats da las elecziuns
----------------------------

### Resultats elavurads

```
URL: /election/{id}/json
```

I vegnan restituidas las medemas datas sco en la vista normala, mo en ina furma structurada.

### Datas nunelavuradas

```
URL: `/election/{id}/{data-format}`
```

Las datas nunelavuradas che vegnan duvradas per mussar ils resultats stattan a disposiziun en ils suandants formats:

Format|URL
---|---
JSON|`/data-json`
CSV|`/data-csv`

Ils suandants champs èn disponibels en tut ils formats:

Num|Descripziun
---|---
`election_title_{locale}`|Titel translatà, p.ex. `title_de_ch` per il titel tudestg.
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
`list_number_of_mandates`|Il dumber da mandats da la glista. Mo tar elecziuns da proporz.
`list_votes`|Il dumber da las vuschs da las glistas. Mo tar elecziuns da proporz.
`list_connection`|La ID da la colliaziun da glistas. Mo tar elecziuns da proporz.
`list_connection_parent`|La ID da la colliaziun da glistas surordinada. Mo en cas d'elecziuns da proporz e sch'i sa tracta d'ina sutcolliaziun da glistas.
`candidate_family_name`|Il num da famiglia da la persuna che candidescha.
`candidate_first_name`|Il prenum da la persuna che candidescha.
`candidate_id`|La ID da la candidata u dal candidat.
`candidate_elected`|True, sche la candidata u il candidat è vegnì elegì.
`candidate_votes`|Il dumber da las vuschs da candidat(a) da la vischnanca/dal lieu.
`panachage_votes_from_list_XX`|Il dumber da vuschs da la glista cun `list_id = XX`. La `list_id` cun la valur `999` stat per la glista vida.

Las vischnancas che n'èn anc betg dumbradas ora n'èn betg cuntegnidas.

### Party results

```
URL: /election/{id}/{data-parties}
```

Las datas nunelavuradas èn disponiblas sco CSV. Ils suandants champs èn cuntegnids:

Num|Descripziun
---|---
`year`|L'onn da l'elecziun.
`total_votes`|Il dumber total da las vuschs da l'elecziun.
`name`|Il num da la partida.
`color`|La colur da la partida.
`mandates`|Il dumber da mandats da la partida.
`votes`|Il dumber da vuschs da la partida.
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

Ils suandants champs èn disponibels en tut ils formats:

Num|Descripziun
---|---
`title_{locale}`|Titel translatà, p.ex. `title_de_ch` per il titel tudestg.
`date`|La data da la votaziun (sco segns ISO 8601).
`shortcode`|Scursanida interna (definescha la successiun da pliras votaziuns che han lieu il medem di).
`domain`|`federation` per votaziuns naziunalas, `canton` per votaziuns chantunalas.
`status`|Resultats intermediars (`interim`), resultats finals (`final`) u stadi dals resultats nunenconuschent (`unknown`).
`type`|`proposal` (proposta), `counter-proposal` (cuntraproposta) or "tie-breaker" (dumonda decisiva).
`entity_id`|La ID da la vischnanca/dal lieu. A value `0` represents the expats.
`entity_name`|Il num da la vischnanca/dal lieu.
`entity_district`|Circul electoral/district/regiun da la vischnanca.
`counted`|Gist, sch'il resultat è vegnì eruì. Fauss, sch'il resultat n'è anc betg enconuschent (las valurs n'èn anc betg correctas).
`yeas`|Il dumber da las vuschs affirmativas
`nays`|Il dumber da las vuschs negativas
`invalid`|Il dumber da las vuschs nunvalaivlas
`empty`|Il dumber da las vuschs vidas
`eligible_voters`|Il dumber da las persunas cun dretg da votar
