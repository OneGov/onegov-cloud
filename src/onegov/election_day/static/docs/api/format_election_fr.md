# Spécifications de format des élections

En ce qui concerne les formats de fichiers, les fichiers XLS et XLSX sont acceptés, ils sont générés par « Wabsti élections et votes (VRSG) » ou par l'application web elle-même. Si une table est créée manuellement, le format de l'application web (OneGov) sera alors le plus facile.

## Contenu

<!-- https://atom.io/packages/atom-mdtoc -->
<!-- MDTOC maxdepth:6 firsth1:2 numbering:1 flatten:0 bullets:1 updateOnSave:1 -->

- 1. [Contenu](#Contenu)
- 2. [Avant-propos](#Avant-propos)
   - 2.1. [Entités](#Entites)
   - 2.2. [Élections tacites](#Elections-tacites)
   - 2.3. [Élections régionales](#Elections-regionales)
- 3. [Formats](#Formats)
   - 3.1. [Onegov](#Onegov)
      - 3.1.1. [Colonnes](#Colonnes)
      - 3.1.2. [Résultats du panachage](#Resultats-du-panachage)
      - 3.1.3. [Résultats temporaires](#Resultats-temporaires)
      - 3.1.4. [Composantes des élections](#Composantes-des-elections)
      - 3.1.5. [Modèle](#Modele)
   - 3.2. [Wabsti Majorz](#Wabsti-Majorz)
      - 3.2.1. [Exportation des données de colonnes](#Exportation-des-donnees-de-colonnes)
      - 3.2.2. [Résultats des candidats de colonnes](#Resultats-des-candidats-de-colonnes)
      - 3.2.3. [Résultats temporaires](#Resultats-temporaires-1)
      - 3.2.4. [Modèles](#Modeles)
   - 3.3. [Wabsti Proporz](#Wabsti-Proporz)
      - 3.3.1. [Exportation des données de résultats pour les colonnes](#Exportation-des-donnees-de-resultats-pour-les-colonnes)
      - 3.3.2. [Résultats du panachage](#Resultats-du-panachage-1)
      - 3.3.3. [Exportation des données de statistiques pour les colonnes](#Exportation-des-donnees-de-statistiques-pour-les-colonnes)
      - 3.3.4. [Connexions de liste des colonnes](#Connexions-de-liste-des-colonnes)
      - 3.3.5. [Résultats de candidats des colonnes](#Resultats-de-candidats-des-colonnes)
      - 3.3.6. [Résultats temporaires](#Resultats-temporaires-2)
      - 3.3.7. [Modèles](#Modeles-1)
   - 3.4. [WabstiCExport Majorz](#WabstiCExport-Majorz)
   - 3.5. [WabstiCExport Proporz](#WabstiCExport-Proporz)
   - 3.6. [Résultats du parti](#Resultats-du-parti)
      - 3.6.1. [Résultats du panachage](#Resultats-du-panachage-2)
      - 3.6.2. [Modèles](#Modeles-2)
   - 3.7. [Création automatique des composantes des élections](#Creation-automatique-des-composantes-des-elections)

<!-- /MDTOC -->

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
`list_color`|La couleur de la liste en valeur hexadécimale, par exemple `#a6b784'.
`list_number_of_mandates`|Nombre total de mandats de la liste. Uniquement avec les élections Proporz.
`list_votes`Nombre de votes de liste par municipalité. Uniquement avec les élections Proporz.
`list_connection`|Identifiant de la connexion de liste ou sous-list (en cas list_connection_parent est présent). Uniquement avec les élections Proporz.
`list_connection_parent`|Identifiant de la connexion de liste au niveau supérieur. Uniquement avec les élections Proporz et si sous-liste existe.
`candidate_id`|Identifiant du candidat.
`candidate_family_name`|Nom de famille du candidat.
`candidate_first_name`|Prénom du candidat.
`candidate_elected`|Vrai, si le candidat a été élu.
`candidate_party`|Nom de le parti.
`candidate_party_color`|La couleur du parti en valeur hexadécimale, par exemple `#a6b784'.
`candidate_gender`|Le sexe du candidat : `female` (féminin), `male` (masculin) ou `undetermined` (indéterminé). Facultatif.
`candidate_year_of_birth`|L'année de naissance du candidat. Facultatif.
`candidate_votes`|Nombre de votes de candidats dans la municipalité.

#### Résultats du panachage

Les résultats sont susceptibles de contenir les résultats du panachage, ce qui suppose une colonne supplémentaire par liste :

Nom|Description
---|---
`list_panachage_votes_from_list_{XX}`|Le nombre de votes que la liste a obtenu de la liste `list_id = XX`. Une liste `list_id` avec la valeur `999` marque les votes de la liste vide.

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

- [election_wabsti_majorz_results.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/election_wabsti_majorz_results.csv)
- [election_wabsti_majorz_candidates.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/election_wabsti_majorz_candidates.csv)

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

- [election_wabsti_proporz_results.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/election_wabsti_proporz_results.csv)
- [election_wabsti_proporz_statistics.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/election_wabsti_proporz_statistics.csv)
- [election_wabsti_proporz_list_connections.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/election_wabsti_proporz_list_connections.csv)
- [election_wabsti_proporz_candidates.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/election_wabsti_proporz_candidates.csv)


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
`color`|La couleur du parti en valeur hexadécimale, par exemple `#a6b784'.
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

### Création automatique des composantes des élections

Avec WabstiC Export version 2.4.3, les composantes des élections peuvent être créées en utilisant le fichier 'WP_Wahl.csv'.
Le token est créé sous **Source de données Wabsti**.

    curl https://[base_url]/create-wabsti-proporz \
      --user :[token] \
      --header "Accept-Language: de_CH" \
      --form "wp_wahl=@WP_Wahl.csv"

La demande précedant effectue ensuite les étapes suivantes:

1. Tous les élections présent dans le fichier `WP_Wahl.csv`.
2. la composante des élections
3. Une cartopgraphie pour chaque election afin de mettre a jour les résultats.
