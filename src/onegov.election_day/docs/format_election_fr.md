# Spécifications de format des élections

En ce qui concerne les formats de fichiers, les fichiers XLS et XLSX sont acceptés, ils sont générés par « Wabsti élections et votes (VRSG) » ou par l'application web elle-même. Si une table est créée manuellement, le format de l'application web (OneGov) sera alors le plus facile.

## Contenu

<!-- TOC START min:1 max:4 link:true update:true -->
- [Spécifications de format des élections](#spcifications-de-format-des-lections)
  - [Contenu](#contenu)
  - [Preface](#preface)
    - [Entities](#entities)
    - [Élections tacites](#lections-tacites)
    - [Regional Elections](#regional-elections)
  - [Formats](#formats)
    - [Onegov](#onegov)
      - [Colonnes](#colonnes)
      - [Résultats du panachage](#rsultats-du-panachage)
      - [Résultats temporaires](#rsultats-temporaires)
      - [Modèle](#modle)
    - [Wabsti Majorz](#wabsti-majorz)
      - [Exportation des données de colonnes](#exportation-des-donnes-de-colonnes)
      - [Résultats des candidats de colonnes](#rsultats-des-candidats-de-colonnes)
      - [Résultats temporaires](#rsultats-temporaires-1)
      - [Modèles](#modles)
    - [Wabsti Proporz](#wabsti-proporz)
      - [Exportation des données de résultats pour les colonnes](#exportation-des-donnes-de-rsultats-pour-les-colonnes)
      - [Résultats du panachage](#rsultats-du-panachage-1)
      - [Exportation des données de statistiques pour les colonnes](#exportation-des-donnes-de-statistiques-pour-les-colonnes)
      - [Connexions de liste des colonnes](#connexions-de-liste-des-colonnes)
      - [Résultats de candidats des colonnes](#rsultats-de-candidats-des-colonnes)
      - [Résultats temporaires](#rsultats-temporaires-2)
      - [Modèles](#modles-1)
    - [WabstiCExport Majorz](#wabsticexport-majorz)
    - [WabstiCExport Proporz](#wabsticexport-proporz)
    - [Party results](#party-results)
      - [Modèles](#modles-2)

<!-- TOC END -->

## Preface

### Entities

An entity is either a municipality (cantonal instances, communal instances without quarters) or a quarter (communal instances with quarters).

### Élections tacites

Les élections tacites peuvent être mises en ligne en utilisant le format OneGov, chaque vote devant être configuré sur `0`.

### Regional Elections

When uploading results of a regional election, only entities of one district are excepted to be present.

## Formats

### Onegov

Le format, qui sera utilisé par l'application web pour l'exportation, se compose d'un seul fichier par élection. Une ligne est présente pour chaque municipalité et candidat.

#### Colonnes

Les colonnes suivantes seront évaluées et devraient exister :

Nom|Description
---|---
`election_absolute_majority`|Majorité absolue de l'élection, seulement si c'est une élection Majorz.
`election_status`|`unknown`, `interim` or `final`.
`entity_id`|Numéro BFS de la municipalité. Une valeur de `0` peut être utilisée pour les expatriés.
`entity_counted`|`True` si le résultat a été compté.
`entity_eligible_voters`|Nombre de personnes autorisées à voter dans la municipalité.
`entity_received_ballots`|Nombre de bulletins soumis dans la municipalité.
`entity_blank_ballots`|Nombre de bulletins vides dans la municipalité.
`entity_invalid_ballots`|Nombre de bulletins non valides dans la municipalité.
`entity_blank_votes`|Nombre de votes vides dans la municipalité.
`entity_invalid_votes`|Nombre de votes non valides dans la municipalité. Zéro si c'est une élection Proporz.
`list_name`|Nom de la liste de candidats. Uniquement avec les élections Proporz.
`list_id`|Identifiant de la liste de candidats. Uniquement avec les élections Proporz.
`list_number_of_mandates`|Nombre total de mandats de la liste. Uniquement avec les élections Proporz.
`list_votes`|Nombre total de votes de liste. Uniquement avec les élections Proporz.
`list_connection`|Identifiant de la connexion de liste. Uniquement avec les élections Proporz.
`list_connection_parent`|Identifiant de la connexion de liste au niveau supérieur. Uniquement avec les élections Proporz et si c'est une connexion de sous-liste.
`candidate_id`|Identifiant du candidat.
`candidate_family_name`|Nom de famille du candidat.
`candidate_first_name`|Prénom du candidat.
`candidate_elected`|Vrai, si le candidat a été élu.
`candidate_party`|Nom de le parti.
`candidate_votes`|Nombre de votes de candidats dans la municipalité.

#### Résultats du panachage

Les résultats sont susceptibles de contenir les résultats du panachage, ce qui suppose une colonne supplémentaire par liste :

Nom|Description
---|---
`panachage_votes_from_list_{XX}`|Le nombre de votes que la liste a obtenu de la liste `list_id = XX`. Une liste `list_id` avec la valeur `999` marque les votes de la liste vide.

#### Résultats temporaires

Municipalities are deemed not to have been counted yet if one of the following two conditions apply:
- `counted = false`
- the municipality is not included in the results

Si le statut est
- `interim`, le scrutin n'a pas été terminé dans sa totalité
- `final`, la totalité du scrutin est considérée comme terminée
- `unknown`, the whole election is considered completed, if all (expected) municipalities are counted

#### Modèle

- [election_onegov_majorz.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_onegov_majorz.csv)
- [election_onegov_proporz.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_onegov_proporz.csv)

### Wabsti Majorz

Le format de fichier nécessite deux diagrammes individuels : l'exportation des données et la liste des candidats élus.

#### Exportation des données de colonnes

Dans l'exportation des données, une ligne est présente pour chaque municipalité, les candidats sont disposés en colonnes. Les colonnes suivantes seront évaluées et on devrait au moins avoir celles-ci :
- `AnzMandate`
- `BFS`
- `StimmBer`
- `StimmAbgegeben`
- `StimmLeer`
- `StimmUngueltig`
- `StimmGueltig`

Ainsi que pour chaque candidat:
- `KandID_{XX}`
- `KandName_{XX}`
- `KandVorname_{XX}`
- `Stimmen_{XX}`

De plus, les votes vides et non valides ainsi que les candidats seront saisis par les noms de candidats suivants :
- `KandName_{XX} = 'Leere Zeilen` (Bulletins vides)
- `KandName_{XX} = 'Ungültige Stimmen` (Bulletins non valides)

#### Résultats des candidats de colonnes

Parce que ce format de fichier n'offre aucune information concernant les candidats élus, ceux-ci doivent être inclus dans une deuxième colonne. Chaque ligne est composée d'un candidat élu avec les colonnes suivantes :

Nom|Description
---|---
`KandID`|Identifiant du candidat (`KandID_{XX}`).

#### Résultats temporaires

Le format de fichier ne contient aucune information claire sur la situation du comptage complet de l'élection globale. Cette information sera fournie directement dans un formulaire destiné au téléchargement des données.

Le format de fichier ne contient également aucune information sur l'état du comptage complet d'une municipalité individuelle. Si des municipalités manquent complètement dans les résultats, on les considèrera comme pas encore comptées.

#### Modèles

- [election_wabsti_majorz_results.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_majorz_results.csv)
- [election_wabsti_majorz_candidates.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_majorz_candidates.csv)

### Wabsti Proporz

Le format de fichier nécessite quatre diagrammes individuels : l'exportation des données pour les résultats, l'exportation des données pour les statistiques, les connexions de liste et les candidats élus de liste.

#### Exportation des données de résultats pour les colonnes

Une ligne est présente par candidat et municipalité dans l'exportation des données. Les colonnes suivantes seront évaluées et devraient exister :
- `Einheit_BFS`
- `Kand_Nachname`
- `Kand_Vorname`
- `Liste_KandID`
- `Liste_ID`
- `Liste_Code`
- `Kand_StimmenTotal`
- `Liste_ParteistimmenTotal`

#### Résultats du panachage

Les résultats sont susceptibles de contenir les résultats du panachage, ce qui suppose une colonne supplémentaire par liste (`{List ID}.{List code}`: le nombre de votes que la liste a obtenu de la liste portant un `Liste_ID` donné). Le fait que `Liste_ID` comporte la valeur `99` (`99.WoP`) indique qu’il s’agit des votes de la liste vide.

#### Exportation des données de statistiques pour les colonnes

Le fichier avec les statistiques des municipalités individuelles devrait contenir les colonnes suivantes :
- `Einheit_BFS`
- `Einheit_Name`
- `StimBerTotal`
- `WZEingegangen`
- `WZLeer`
- `WZUngueltig`
- `StmWZVeraendertLeerAmtlLeer`

#### Connexions de liste des colonnes

Le fichier avec les connexions de liste devrait contenir les colonnes suivantes :
- `Liste`
- `LV`
- `LUV`

#### Résultats de candidats des colonnes

Étant donné que le format du fichier ne fournit pas d'informations concernant le candidat élu, celles-ci doivent être incluses dans une deuxième colonne. Chaque rangée se rapporte à un candidat élu et est composée des colonnes suivantes :

Nom|Description
---|---
`Liste_KandID`|L'identifiant du candidat.

#### Résultats temporaires

Le format de fichier ne contient aucune information claire sur la situation du comptage complet de l'élection globale. Cette information sera fournie directement dans un formulaire destiné au téléchargement des données.

Le format de fichier ne contient également aucune information sur l'état du comptage complet d'une municipalité individuelle. Si des municipalités manquent complètement dans les résultats, on les considèrera comme pas encore comptées.

#### Modèles

- [election_wabsti_proporz_results.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_proporz_results.csv)
- [election_wabsti_proporz_statistics.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_proporz_statistics.csv)
- [election_wabsti_proporz_list_connections.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_proporz_list_connections.csv)
- [election_wabsti_proporz_candidates.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_proporz_candidates.csv)


### WabstiCExport Majorz

La version `>= 2.2` est prise en charge, veuillez vous référer à la documentation fournie par le programme exportateur pour plus d'informations concernant les colonnes des différents fichiers.


### WabstiCExport Proporz

La version `>= 2.2` est prise en charge, veuillez vous référer à la documentation fournie par le programme exportateur pour plus d'informations concernant les colonnes des différents fichiers.


### Party results

Chaque élection (proporz) est susceptible de contenir les résultats de partis. Ces résultats sont indépendants des autres résultats et contiennent généralement les résultats déjà agrégés des différentes listes d'un parti.

Les colonnes suivantes seront évaluées et devraient avoir été créées :

Nom|Description
---|---
`year`|Année de l'élection.
`total_votes`|Le total des votes de l'élection.
`name`|La dénomination du parti.
`color`|La couleur du parti.
`mandates`|Le nombre de mandats.
`votes`|Le nombre de votes.


#### Modèles

- [election_party_results.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_party_results.csv)
