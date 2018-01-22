Spécifications de format des élections
======================================

En ce qui concerne les formats de fichiers, les fichiers XLS et XLSX sont acceptés, ils sont générés par « Wabsti élections et votes (VRSG) » ou par l'application web elle-même. Si une table est créée manuellement, le format de l'application web sera alors le plus facile.

## Contenu

1. [OneGov](#1-onegov)
2. [Wabsti Majorz](#2-wabsti-majorz)
3. [Wabsti Proporz](#3-wabsti-proporz)
4. [WabstiCExport Majorz](#4-wabsticexport-majorz)
5. [WabstiCExport Proporz](#5-wabsticexport-proporz)
6. [Party results](#6-party-results)
7. [Élection tacite](#7-election-tacite)


1 Onegov
--------

Le format, qui sera utilisé par l'application web pour l'exportation, se compose d'un seul fichier par élection. Une ligne est présente pour chaque municipalité et candidat.

### Colonnes

Les colonnes suivantes seront évaluées et devraient exister :

Nom|Description
---|---
`election_absolute_majority`|Majorité absolue de l'élection, seulement si c'est une élection Majorz.
`election_status`|`unknown`, `interim` or `final`.
`election_counted_entities`|Nombre de municipalités comptées. Si `election_counted_entities = election_total_entities`, on considère alors que l'élection est entièrement comptée.
`election_total_entities`|Nombre total de municipalités. Si aucune information précise à propos de la situation de l'élection n'est possible (parce que l'élection a été importée par Wabsti), alors cette valeur est `0`.
`entity_id`|Numéro BFS de la municipalité. Une valeur de `0` peut être utilisée pour les expatriés.
`entity_elegible_voters`|Nombre de personnes autorisées à voter dans la municipalité.
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

### Résultats temporaires

Les municipalités pas encore entièrement comptées ne sont pas incluses dans les fichiers.

Si le statut est
- `interim`, le scrutin n'a pas été terminé dans sa totalité
- `final`, la totalité du scrutin est considérée comme terminée
- `unknown`, la totalité du scrutin est considérée comme terminée si les valeurs `election_counted_entities` et `election_total_entities` se correspondent

### Modèle

- [election_onegov_majorz.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_onegov_majorz.csv)
- [election_onegov_proporz.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_onegov_proporz.csv)

4 Wabsti Majorz
---------------

Le format de fichier nécessite deux diagrammes individuels : l'exportation des données et la liste des candidats élus.

### Exportation des données de colonnes

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

### Résultats des candidats de colonnes

Parce que ce format de fichier n'offre aucune information concernant les candidats élus, ceux-ci doivent être inclus dans une deuxième colonne. Chaque ligne est composée d'un candidat élu avec les colonnes suivantes :

Nom|Description
---|---
`ID`|Identifiant du candidat (`KandID_{XX}`).
`Name`|Le nom de famille du candidat.
`Vorname`|Le prénom du candidat.

### Résultats temporaires

Le format de fichier ne contient aucune information claire sur la situation du comptage complet de l'élection globale. Cette information sera fournie directement dans un formulaire destiné au téléchargement des données.

Le format de fichier ne contient également aucune information sur l'état du comptage complet d'une municipalité individuelle. Ainsi, tant que l'élection entière n'est pas terminée, aucune notification de progrès ne sera affichée pour Wabsti. Si des municipalités manquent complètement dans les résultats, on les considèrera comme pas encore comptées.

### Modèles

- [election_wabsti_majorz_results.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_majorz_results.csv)
- [election_wabsti_majorz_candidates.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_majorz_candidates.csv)

3 Wabsti Proporz
----------------

Le format de fichier nécessite quatre diagrammes individuels : l'exportation des données pour les résultats, l'exportation des données pour les statistiques, les connexions de liste et les candidats élus de liste.

### Exportation des données de résultats pour les colonnes

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

### Exportation des données de statistiques pour les colonnes

Le fichier avec les statistiques des municipalités individuelles devrait contenir les colonnes suivantes :
- `Einheit_BFS`
- `Einheit_Name`
- `StimBerTotal`
- `WZEingegangen`
- `WZLeer`
- `WZUngueltig`
- `StmWZVeraendertLeerAmtlLeer`

### Connexions de liste des colonnes

Le fichier avec les connexions de liste devrait contenir les colonnes suivantes :
- `Liste`
- `LV`
- `LUV`

### Résultats de candidats des colonnes

Étant donné que le format du fichier ne fournit pas d'informations concernant le candidat élu, celles-ci doivent être incluses dans une deuxième colonne. Chaque rangée se rapporte à un candidat élu et est composée des colonnes suivantes :

Nom|Description
---|---
`ID`|L'identifiant du candidat (`Liste_KandID`).
`Name`|Le nom de famille du candidat.
`Vorname`|Le prénom du candidat.

### Résultats temporaires

Le format de fichier ne contient aucune information claire sur la situation du comptage complet de l'élection globale. Cette information sera fournie directement dans un formulaire destiné au téléchargement des données.

Le format de fichier ne contient également aucune information sur l'état du comptage complet d'une municipalité individuelle. Ainsi, tant que l'élection entière n'est pas terminée, aucune notification de progrès ne sera affichée pour Wabsti. Si des municipalités manquent complètement dans les résultats, on les considèrera comme pas encore comptées.

### Modèles

- [election_wabsti_proporz_results.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_proporz_results.csv)
- [election_wabsti_proporz_statistics.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_proporz_statistics.csv)
- [election_wabsti_proporz_list_connections.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_proporz_list_connections.csv)
- [election_wabsti_proporz_candidates.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_proporz_candidates.csv)


4 WabstiCExport Majorz
----------------------

La version `2.2` est prise en charge, veuillez vous référer à la documentation fournie par le programme exportateur pour plus d'informations concernant les colonnes des différents fichiers.


5 WabstiCExport Proporz
-----------------------

La version `2.2` est prise en charge, veuillez vous référer à la documentation fournie par le programme exportateur pour plus d'informations concernant les colonnes des différents fichiers.


6 Party results
---------------

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


### Modèles

- [election_party_results.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_party_results.csv)


7 Élection tacite
-----------------

Les élections tacites peuvent être mises en ligne en utilisant le format interne, chaque vote devant être configuré sur `0`.
