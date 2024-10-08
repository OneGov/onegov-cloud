# Spécifications de format des élections

En ce qui concerne les formats de fichiers, les fichiers XLS et XLSX sont acceptés, ils sont générés par « Wabsti élections et votes (VRSG) » ou par l'application web elle-même. Si une table est créée manuellement, le format de l'application web (OneGov) sera alors le plus facile.

## Contenu

<!-- TOC updateonsave:false -->

- [Spécifications de format des élections](#sp%C3%A9cifications-de-format-des-%C3%A9lections)
    - [Contenu](#contenu)
    - [Avant-propos](#avant-propos)
        - [Entités](#entit%C3%A9s)
        - [Élections tacites](#%C3%A9lections-tacites)
        - [Élections régionales](#%C3%A9lections-r%C3%A9gionales)
    - [Formats](#formats)
        - [Onegov](#onegov)
            - [Colonnes](#colonnes)
            - [Résultats du panachage de listes](#r%C3%A9sultats-du-panachage-de-listes)
            - [Résultats du panachage de candidats](#r%C3%A9sultats-du-panachage-de-candidats)
            - [Résultats temporaires](#r%C3%A9sultats-temporaires)
            - [Composantes des élections](#composantes-des-%C3%A9lections)
            - [Modèle](#mod%C3%A8le)
        - [WabstiCExport Majorz](#wabsticexport-majorz)
        - [WabstiCExport Proporz](#wabsticexport-proporz)
        - [Résultats du parti](#r%C3%A9sultats-du-parti)
            - [Domaine d'influence](#domaine-dinfluence)
            - [Résultats du panachage](#r%C3%A9sultats-du-panachage)
            - [Modèles](#mod%C3%A8les)
        - [Création automatique des composantes des élections](#cr%C3%A9ation-automatique-des-composantes-des-%C3%A9lections)

<!-- /TOC -->

## Avant-propos

### Entités

Un entité est soit une municipalité (instances cantonales, instances communales sans quartiers), ou un quartier (instances communales avec quartiers).

### Élections tacites

Les élections tacites peuvent être mises en ligne en utilisant le format OneGov, chaque vote devant être configuré sur `0`.

### Élections régionales

Lors du téléchargement des résultats d'une élection régionale, seules les entités d'une circonscription sont exemptées d'être présentes, si l'option correspondante est définie sur l'élection.

## Formats

### Onegov

Le format, qui sera utilisé par l'application web pour l'exportation, se compose d'un seul fichier par élection. Une ligne est présente pour chaque municipalité et candidat.

#### Colonnes

Les colonnes suivantes seront évaluées et devraient exister :

Nom|Description
---|---
`election_absolute_majority`|Majorité absolue de l'élection, seulement si c'est une élection Majorz.
`election_status`|Statut de l'élection. `interim` (résultats intermédiaires), `final` (résultats finaux) or `unknown` (inconnu).
`entity_id`|Numéro BFS de la municipalité. Une valeur de `0` peut être utilisée pour les expatriés.
`entity_counted`|`True` si le résultat a été compté.
`entity_eligible_voters`|Nombre de personnes autorisées à voter dans la municipalité.
`entity_expats`|Nombre d'expatriés de l'unité. Facultatif.
`entity_received_ballots`|Nombre de bulletins soumis dans la municipalité.
`entity_blank_ballots`|Nombre de bulletins vides dans la municipalité.
`entity_invalid_ballots`|Nombre de bulletins non valides dans la municipalité.
`entity_blank_votes`|Nombre de votes vides dans la municipalité.
`entity_invalid_votes`|Nombre de votes non valides dans la municipalité. Zéro si c'est une élection Proporz.
`list_name`|Nom de la liste de candidats. Uniquement avec les élections Proporz.
`list_id`|Identifiant de la liste de candidats. Uniquement avec les élections Proporz. Peut-être numeric ou alpha-numeric.
`list_color`|La couleur de la liste en valeur hexadécimale, par exemple `#a6b784`.
`list_number_of_mandates`|Nombre total de mandats de la liste. Uniquement avec les élections Proporz.
`list_votes`Nombre de votes de liste par municipalité. Uniquement avec les élections Proporz.
`list_connection`|Identifiant de la connexion de liste ou sous-list (en cas list_connection_parent est présent). Uniquement avec les élections Proporz.
`list_connection_parent`|Identifiant de la connexion de liste au niveau supérieur. Uniquement avec les élections Proporz et si sous-liste existe.
`candidate_id`|Identifiant du candidat.
`candidate_family_name`|Nom de famille du candidat.
`candidate_first_name`|Prénom du candidat.
`candidate_elected`|Vrai, si le candidat a été élu.
`candidate_party`|Nom de le parti.
`candidate_party_color`|La couleur du parti en valeur hexadécimale, par exemple `#a6b784`.
`candidate_gender`|Le sexe du candidat : `female` (féminin), `male` (masculin) ou `undetermined` (indéterminé). Facultatif.
`candidate_year_of_birth`|L'année de naissance du candidat. Facultatif.
`candidate_votes`|Nombre de votes de candidats dans la municipalité.

#### Résultats du panachage de listes

Les résultats sont susceptibles de contenir les résultats du panachage de listes, ce qui suppose une colonne supplémentaire par liste :

Nom|Description
---|---
`list_panachage_votes_from_list_{XX}` / `panachage_votes_from_list_{XX}`|Le nombre de votes que la liste a obtenu de la liste `list_id = XX`. Une liste `list_id` avec la valeur `999` marque les votes de la liste vide. Les votes de la liste propre sont ignorés.

#### Résultats du panachage de candidats

Les résultats sont susceptibles de contenir les résultats du panachage des candidats, ce qui suppose une colonne supplémentaire par liste :

Nom|Description
---|---
`candidate_panachage_votes_from_list_{XX}`|Le nombre de votes que ce candidat a obtenu de la liste `list_id = XX`. Une liste `list_id` avec la valeur `999` marque les votes de la liste vide.


#### Résultats temporaires

Les municipalités sont considérées comme n'étant pas encore décomptées si l'une des deux conditions suivantes s'applique :
- `counted = false`
- la municipalité n'est pas comprise dans les résultats

Si le statut est
- `interim`, le scrutin n'a pas été terminé dans sa totalité
- `final`, la totalité du scrutin est considérée comme terminée
- `unknown`, la totalité du scrutin est considérée comme terminée si toutes les municipalités (prévues) sont décomptées

#### Composantes des élections

Les résultats des composantes des élections peuvent être téléchargés de manière groupée en fournissant un seul fichier avec toutes les lignes des résultats de chaque élection.

#### Modèle

- [election_onegov_majorz.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/election_onegov_majorz.csv)
- [election_onegov_proporz.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/election_onegov_proporz.csv)


### WabstiCExport Majorz

La version `>= 2.2` est prise en charge, veuillez vous référer à la documentation fournie par le programme exportateur pour plus d'informations concernant les colonnes des différents fichiers.


### WabstiCExport Proporz

La version `>= 2.2` est prise en charge, veuillez vous référer à la documentation fournie par le programme exportateur pour plus d'informations concernant les colonnes des différents fichiers.


### Résultats du parti

Chaque élection (proporz) et chaque composition électoral est susceptible de contenir les résultats de partis. Ces résultats sont indépendants des autres résultats et contiennent généralement les résultats déjà agrégés des différentes listes d'un parti.

Les colonnes suivantes seront évaluées et devraient avoir été créées :

Nom|Description
---|---
`domain`|Le domaine d'influence auquel la ligne s'applique. Facultatif.
`domain_segment`|L'unité du domaine d'influence à laquelle s'applique la ligne. Facultatif.
`year`|Année de l'élection.
`total_votes`|Le total des votes de l'élection.
`name`|Le dénomination du parti dans la langue par défaut. Optionnel*.
`name_{locale}`|Nom traduit du parti, par exemple `name_de_ch` pour le nom allemand. Optionnel. Assurez-vous de fournir le nom de la partie dans la langue par défaut soit avec la colonne `name` ou `name_{default_locale}`.
`id`|Identifiant du parti (n'importe quel numéro).
`color`|La couleur du parti en valeur hexadécimale, par exemple `#a6b784`.
`mandates`|Le nombre de mandats.
`votes`|Le nombre de votes.
`voters_count`|Nombre de votants. Le nombre cumulé de voix par rapport au nombre total de mandats par élection. Uniquement pour les composantes des élections.
`voters_count_percentage`|Nombre de votants (pourcentages). Le nombre cumulé de voix par rapport au nombre total de mandats par élection (pourcentages). Uniquement pour les composantes des élections.

#### Domaine d'influence

`domain` et `domain_segment` permettent de fournir les résultats des partis pour un domaine d'influence différent de celui de l'élection ou du composé. `domain` correspond à un sous-domaine d'influence de l'élection ou du composé, par exemple pour les élections législatives cantonales `superregion`, `region`, `district` ou `municipality` selon le canton. `domain_segment` correspond à une unité dans ce sous-domaine d'influence, par exemple `Region 1`, `Bergün`, `Toggenburg` ou `Zug`. Normalement, `domain` et `domain_segment` peuvent être laissés vides ou omis ; dans ce cas, `domain` est implicitement défini comme le `domain` de l'élection ou de l'association. Actuellement, seul le `domain` de l'élection ou de l'association est supporté, ainsi que `domain = 'superregion'` pour les associations d'élections.

#### Résultats du panachage

Les résultats peuvent inclure des résultats avec panachage en ajoutant une colonne par parti :

Nom|Description
---|---
`panachage_votes_from_{XX}`|Le nombre de votes que le parti a obtenu de la part du parti avec un `id = XX`. Un `id` avec la valeur `999` marque les votes à partir de la liste vide.

Les résultats avec panachage sont uniquement ajoutés si :
- `year` correspond à l'année de l'élection
- `id (XX)` ne correspond pas à l'« identifiant » de la ligne

#### Modèles

- [election_party_results.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/election_party_results.csv)
