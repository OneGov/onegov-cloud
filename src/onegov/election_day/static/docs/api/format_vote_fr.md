# Spécifications de format des votes

Les formats de fichier acceptés sont les fichiers générés à la main par le programme électoral « Élections et référendums de Wabsti (VRSG) », ou par l'application web elle-même.

«Municipalité» fait référence à un district, une circonscription électorale, etc.

## Contenu

<!-- TOC updateonsave:false -->

- [Spécifications de format des votes](#sp%C3%A9cifications-de-format-des-votes)
    - [Contenu](#contenu)
    - [Avant-propos](#avant-propos)
        - [Entités](#entit%C3%A9s)
    - [Formats](#formats)
        - [OneGov](#onegov)
            - [Colonnes](#colonnes)
            - [Résultats temporaires](#r%C3%A9sultats-temporaires)
            - [Modèle](#mod%C3%A8le)
        - [WabstiCExport](#wabsticexport)
        - [eCH-0252](#ech-0252)

<!-- /TOC -->

## Avant-propos

### Entités

Un entité est soit une municipalité (instances cantonales, instances communales sans quartiers), ou un quartier (instances communales avec quartiers).

## Formats


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
`expats`|Nombre d'expatriés. Facultatif.


#### Résultats temporaires

Les municipalités sont considérées comme n'étant pas encore décomptées si l'une des deux conditions suivantes s'applique :
- `counted = false`
- la municipalité n'est pas comprise dans les résultats

Si le statut est
- `interim`, le scrutin n'a pas été terminé dans sa totalité
- `final`, la totalité du scrutin est considérée comme terminée
- `unknown`, la totalité du scrutin est considérée comme terminée si toutes les municipalités (prévues) sont décomptées

#### Modèle

- [vote_onegov.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/vote_onegov.csv)



### WabstiCExport

La version `>= 2.2` est prise en charge, veuillez vous référer à la documentation fournie par le programme exportateur pour plus d'informations concernant les colonnes des différents fichiers.


### eCH-0252

Voir [eCH-0252](https://www.ech.ch/de/ech/ech-0252).
