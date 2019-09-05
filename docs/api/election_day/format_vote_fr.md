# Spécifications de format des votes

Les formats de fichier acceptés sont les fichiers générés à la main par le programme électoral « Élections et référendums de Wabsti (VRSG) », ou par l'application web elle-même.

«Municipalité» fait référence à un district, une circonscription électorale, etc.

## Contenu

<!-- TOC START min:1 max:4 link:true asterisk:false update:true -->
- [Spécifications de format des votes](#spécifications-de-format-des-votes)
    - [Contenu](#contenu)
    - [Avant-propos](#avant-propos)
        - [Entités](#entités)
    - [Formats](#formats)
        - [Format standard](#format-standard)
            - [Colonnes](#colonnes)
            - [Résultats temporaires](#résultats-temporaires)
            - [Modèle](#modèle)
        - [OneGov](#onegov)
            - [Colonnes](#colonnes-1)
            - [Résultats temporaires](#résultats-temporaires-1)
            - [Modèle](#modèle-1)
        - [Wabsti](#wabsti)
            - [Colonnes](#colonnes-2)
            - [Résultats temporaires](#résultats-temporaires-2)
            - [Modèle](#modèle-2)
        - [WabstiCExport](#wabsticexport)
<!-- TOC END -->


## Avant-propos

### Entités

Un entité est soit une municipalité (instances cantonales, instances communales sans quartiers), ou un quartier (instances communales avec quartiers).

## Formats

### Format standard

Il y a généralement un fichier CSV/Excel par proposition de référendum. Cependant, si le référendum comprend une contre-proposition et un départage, trois fichiers doivent alors être fournis : un fichier avec les résultats du référendum, un fichier avec les résultats de la contre-proposition, et un fichier avec les résultats du départage.

#### Colonnes

Chaque ligne contient les résultats d'une municipalité unique, à condition qu'ils aient été décomptés intégralement. Les colonnes suivantes sont prévues dans l'ordre répertorié ici :

Nom|Description
---|---
`ID`|Le nombre de municipalités (nombre de BFS) au moment du vote. Une valeur de `0` peut être utilisée pour les expatriés.
`Ja Stimmen`|Le nombre de votes « oui ». Si le mot `unknown`/`unbekannt` est saisi, la ligne sera ignorée (pas encore décompté).
`Nein Stimmen`|Le nombre de votes « non ». Si le mot `unknown`/`unbekannt` est saisi, la ligne sera ignorée (pas encore décompté).
`Stimmberechtigte`|Le nombre de personnes habilitées à voter. Si le mot `unknown`/`unbekannt` est saisi, la ligne sera ignorée (pas encore décompté).
`Leere Stimmzettel`|Le nombre de bulletins de vote blancs. Si le mot `unknown`/`unbekannt` est saisi, la ligne sera ignorée (pas encore décompté).
`Ungültige Stimmzettel`|Le nombre de bulletins de vote nuls. Si le mot `unknown`/`unbekannt` est saisi, la ligne sera ignorée (pas encore décompté).

#### Résultats temporaires

Les municipalités sont considérées comme n'étant pas encore décomptées si la municipalité n'est pas comprise dans les résultats.

#### Modèle

- [vote_standard.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/vote_standard.csv)


### OneGov

Le format utilisé par l'application web pour l'exportation consiste en un fichier unique par vote. Il y a une ligne pour chaque municipalité et type de référendum (proposition, contre-proposition, départage).

#### Colonnes

Les colonnes suivantes seront évaluées et devraient exister :

Nom|Description
---|---
`status`|`interim` (résultats intermédiaires), `final` (résultats finaux) or `unknown` (inconnu).
`type`|`proposal` (proposition), `counter-proposal` (contre-proposition) ou `tie-breaker` (jeu décisif).
`entity_id`|La référence de la municipalité/localité. Une valeur `0` représente les expatriés.
`counted`|Vrai si le résultat a été compté, faux si le résultat n'est pas encore connu (le compte des votes n'est pas encore fini).
`yeas`|Nombre de votes oui
`nays`|Nombre de votes non
`invalid`|Nombre de votes invalides.
`empty`|Nombre de votes blancs
`eligible_voters`|Nombre de personne aptes à voter.


#### Résultats temporaires

Les municipalités sont considérées comme n'étant pas encore décomptées si l'une des deux conditions suivantes s'applique :
- `counted = false`
- la municipalité n'est pas comprise dans les résultats

Si le statut est
- `interim`, le scrutin n'a pas été terminé dans sa totalité
- `final`, la totalité du scrutin est considérée comme terminée
- `unknown`, la totalité du scrutin est considérée comme terminée si toutes les municipalités (prévues) sont décomptées

#### Modèle

- [vote_onegov.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/vote_onegov.csv)


### Wabsti

Le format du programme électoral « Élections et référendums de Wabsti (VRSG) » consiste en un fichier unique contenant toutes les données pour de nombreux référendums. Il y a une ligne pour chaque référendum et municipalité.

#### Colonnes

Les colonnes suivantes seront évaluées et devraient exister :
- `Vorlage-Nr.`
- `Name`
- `BfS-Nr.`
- `Stimmberechtigte`
- `leere SZ`
- `ungültige SZ`
- `Ja`
- `Nein`
- `GegenvJa`
- `GegenvNein`
- `StichfrJa`
- `StichfrNein`
- `StimmBet`

#### Résultats temporaires

Les municipalités sont considérées comme n'étant pas encore décomptées si l'une des deux conditions suivantes s'applique :

- `StimmBet = 0`
- la municipalité n'est pas comprise dans les résultats

#### Modèle

- [vote_wabsti.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/vote_wabsti.csv)


### WabstiCExport

La version `>= 2.2` est prise en charge, veuillez vous référer à la documentation fournie par le programme exportateur pour plus d'informations concernant les colonnes des différents fichiers.
