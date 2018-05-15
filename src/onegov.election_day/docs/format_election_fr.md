# Spécifications de format des élections

En ce qui concerne les formats de fichiers, les fichiers XLS et XLSX sont acceptés, ils sont générés par « Wabsti élections et votes (VRSG) » ou par l'application web elle-même. Si une table est créée manuellement, le format de l'application web (OneGov) sera alors le plus facile.

## Contenu

<!-- TOC START min:1 max:4 link:true update:true -->
- [Spécifications de format des élections](#spcifications-de-format-des-lections)
  - [Contenu](#contenu)
  - [Avant-propos](#avant-propos)
    - [Entités](#entits)
    - [Élections tacites](#lections-tacites)
    - [Élections régionales](#lections-rgionales)
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
    - [Résultats du parti](#rsultats-du-parti)
      - [Modèles](#modles-2)

<!-- TOC END -->

## Avant-propos

### Entités

Un entité est soit une municipalité (instances cantonales, instances communales sans quartiers), ou un quartier (instances communales avec quartiers).

### Élections tacites

Les élections tacites peuvent être mises en ligne en utilisant le format OneGov, chaque vote devant être configuré sur `0`.

### Élections régionales

Lors du téléchargement des résultats d'une élection régionale, seules les entités d'une circonscription sont exemptées d'être présentes.

## Formats

### Onegov

Le format, qui sera utilisé par l'application web pour l'exportation, se compose d'un seul fichier par élection. Une ligne est présente pour chaque municipalité et candidat.

#### Colonnes

Les colonnes suivantes seront évaluées et devraient exister :

Nom|Description
---|---
`election_absolute_majority`|Majorité absolue de l'élection, seulement si c'est une élection Majorz.
`election_status`|`interim` (résultats intermédiaires), `final` (résultats finaux) or `unknown` (inconnu).
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

Les municipalités sont considérées comme n'étant pas encore décomptées si l'une des deux conditions suivantes s'applique :
- `counted = false`
- la municipalité n'est pas comprise dans les résultats

Si le statut est
- `interim`, le scrutin n'a pas été terminé dans sa totalité
- `final`, la totalité du scrutin est considérée comme terminée
- `unknown`, la totalité du scrutin est considérée comme terminée si toutes les municipalités (prévues) sont décomptées

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

Comme le format de fichier peut ne pas fournir d'informations sur les candidats élus, ces informations peuvent être fournies dans un deuxième tableau. Chaque ligne est composée d'un candidat élu avec les colonnes suivantes :

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


### Résultats du parti

Chaque élection (proporz) est susceptible de contenir les résultats de partis. Ces résultats sont indépendants des autres résultats et contiennent généralement les résultats déjà agrégés des différentes listes d'un parti.

Les colonnes suivantes seront évaluées et devraient avoir été créées :

Nom|Description
---|---
`year`|Année de l'élection.
`total_votes`|Le total des votes de l'élection.
`name`|La dénomination du parti.
`id`|Identifiant du parti (n'importe quel numéro).
`color`|La couleur du parti.
`mandates`|Le nombre de mandats.
`votes`|Le nombre de votes.

Les résultats peuvent inclure des résultats avec panachage en ajoutant une colonne par parti :

Nom|Description
---|---
`panachage_votes_from_{XX}`|Le nombre de votes que le parti a obtenu de la part du parti avec un `id = XX`. Un `id` avec la valeur `999` marque les votes à partir de la liste vide.

Les résultats avec panachage sont uniquement ajoutés si :
- `year` correspond à l'année de l'élection
- `id (XX)` ne correspond pas à l'« identifiant » de la ligne

#### Modèles

- [election_party_results.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_party_results.csv)
