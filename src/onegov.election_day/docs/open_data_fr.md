Elections et votes : Données ouvertes
=====================================

## Introduction

Il y a des alternatives JSON pour toutes les vues importantes. Toutes les réponses contiennent l’en-tête HTTP `Last-Modified` (Modifié pour la dernière fois) avec la dernière fois que les données ont changé (c’est-à-dire la dernière fois que les résultats d'une élection ou d’une votation ont été téléchargés).

«Municipalité» fait référence à un district, une circonscription électorale, etc.

Contenu
-------

1. [Résultats synthétisés](#1-résultats-synthétisés)
2. [Résultats des élections](#2-résultats-des-élections)
3. [Les résultats de la votation](#3-les-résultats-de-la-votation)

1 Résultats synthétisés
-----------------------

```
URL (dernier): /json
URL (archives par année): /archive/{année}/json
URL (archives par date): /archive/{année}-{mois}-{jour}/json
URL (élection): /election/{id}/summary
URL (votation): /vote/{id}/summary
```

Les résultats synthétisés affichés sur la page d'accueil (seuls les résultats des dernières votations et élections) et dans les archives (il est possible de rechercher par année ou par date) sont également disponibles en JSON. Les données contiennent des informations globales et pour chaque élection et votation les informations communes suivantes :

Nom|Description
---|---
`type`|`election` pour les élections, `vote` pour les votations.
`title`|Un objet contenant les titres traduits.
`date`|La date (ISO 8601).
`domain`|Le domaine d'influence (fédération, canton, ...).
`url`|Un lien vers la vue détaillée.
`completed`|True, if the vote or election is completed.
`progess`|Un objet contenant le nombre de municipalités déjà comptées (`counted`) et le nombre total de municipalités (`total`).

Les résultats de la votation contiennent les informations supplémentaires suivantes :

Nom|Description
---|---
`answer`|La réponse de la votation : `accepted` (acceptée), `rejected` (rejetée), `proposal` (proposition) ou `counter-proposal` (contre-proposition).
`yeas_percentage`|Pourcentage de oui.
`nays_percentage`|Pourcentage de non.
`local` (*optional*)|Federal and cantonal votes within a communal instance may contain additionally the results of the municipality in the form of an object with `answer`, `yeas_percentage` and `nays_percentage`.


2 Résultats des élections
-------------------------

### Résultats transformés

```
URL: /election/{id}/json
```

Retourne les données de la vue principale sous une forme structurée.

### Données brutes

```
URL: /election/{id}/{data-format}
```

Les données brutes utilisées pour afficher les résultats de élections sont disponibles dans les formats suivants:

Format|URL
---|---
JSON|`/data-json`
CSV|`/data-csv`
XLSX|`/data-xlsx`

Les champs suivants sont inclus dans tous les formats:

Nom|Description
---|---
`election_title`|Titre de l'élection.
`election_date`|La date de l'élection (an ISO 8601 date string).
`election_type`|`proporz` pour proportionnelle, `majorz` pour le système majoritaire.
`election_mandates`|Nombre de mandats.
`election_absolute_majority`|La majorité absolue. Uniquement valable pour les élections basées sur le système majoritaire.
`election_status`|Interim results (`interim`), final results (`final`) or unknown (`unknown`).
`election_counted_entities`|Le nombre de municipalités déjà comptées.
`election_total_entities`|Le nombre total de municipalités.
`entity_name`|Le nom de la municipalité.
`entity_id`|L'identifiant de la municipalité. A value `0` represents the expats.
`entity_elegible_voters`|Le nombre de personnes éligible à voter pour cette municipalité.
`entity_received_ballots`|Le nombre de bulletins de vote reçus pour cette municipalité.
`entity_blank_ballots`|Le nombre de bulletins blancs pour cette municipalité.
`entity_invalid_ballots`|Le nombre de bulletins nuls pour cette municipalité.
`entity_unaccounted_ballots`|Le nombre de bulletins de vote non comptabilisés pour cette municipalité.
`entity_accounted_ballots`|Le nombre de bulletins de votes comptabilisés pour cette municipalité.
`entity_blank_votes`|Le nombre de votes en blanc pour cette municipalité.
`entity_invalid_votes`|Le nombre de votes valides pour cette municipalité. Zéro pour les élections sur la base de la représentation proportionnelle.
`entity_accounted_votes`|Le nombre de votes comptabilisés pour cette municipalité.
`list_name`|Le nom de la liste sur laquelle ce candidat apparaît. Uniquement valable pour les élections sur la base de la représentation proportionnelle.
`list_id`|L'identifiant de liste de ce candidat apparaît dessus. Uniquement valable pour les élections basées sur la représentation proportionnelle.
`list_number_of_mandates`|Le nombre de mandats que cette liste a obtenus. Uniquement valable pour les élections basées sur la représentation proportionnelle.
`list_votes`|Le nombre de votes que cette liste a obtenu. Uniquement valable pour les élections sur la base de la représentation proportionnelle.
`list_connection`|L'Identifiant de la connexion de la liste à laquelle cette liste est connectée. Uniquement valable pour les élections sur la base de la représentation proportionnelle.
`list_connection_parent`|L'Identifiant de la connexion de liste parent à laquelle cette liste est connectée. Uniquement valable pour les élections sur la base de la représentation proportionnelle.
`candidate_family_name`|Le nom de famille du candidat.
`candidate_first_name`|Le prénom du candidat.
`candidate_id`|L'identifiant du candidat.
`candidate_elected`|Vrai si le candidat a été élu.
`candidate_votes`|Le nombre de voix que ce candidat a obtenu.
`panachage_votes_from_list_XX`|The number of votes the list got from the list with `list_id = XX`. A `list_id` with the value `999` marks the votes from the blank list.

Les municipalités qui n’ont pas encore été comptées ne sont pas incluses.

### Party results

```
URL: /election/{id}/{data-parties}
```

The raw data is available as CSV. The following fields are included:

Name|Description
---|---
`year`|The year of the election.
`total_votes`|The total votes of the election.
`name`|The name of the party.
`color`|The color of the party.
`mandates`|The number of mandates.
`votes`|The number of votes.

3 Les résultats de la votation
------------------------------

### Résultats transformés

```
URL: /vote/{id}/json
```

Retourne les données de la vue principale sous une forme structurée.

### Données brutes

```
URL: /vote/{id}/{data-format}
```

Les données brutes utilisées pour afficher les résultats de votes sont disponibles dans les formats suivants:

Format|URL
---|---
JSON|`/data-json`
CSV|`/data-csv`
XLSX|`/data-xlsx`

Les champs suivants sont inclus dans tous les formats:

Nom|Description
---|---
`title`|Nom du vote.
`date`|La date du vote (une chaîne de date ISO 8601).
`shortcode`|Shortcode interne (définit l'ordre des votes ayant lieu le même jour).
`domain`|`federation` pour fédéral, `canton` for les votes cantonaux.
`status`|Interim results (`interim`), final results (`final`) or unknown (`unknown`).
`type`|`proposal` (proposition), `counter-proposal` (contre-proposition) ou `tie-breaker` (jeu décisif).
`group`|La désignation du résultat. Peut être le district, le nom de la ville divisé par un slash, le nom de la ville et le district de la ville divisés par un slash ou simplement le nom de la ville. Cela dépend entièrement du canton.
`entity_id`|La référence de la municipalité/localité. A value `0` represents the expats.
`counted`|Vrai si le résultat a été compté, faux si le résultat n'est pas encore connu (le compte des votes n'est pas encore fini).
`yeas`|Nombre de votes oui
`nays`|Nombre de votes non
`invalid`|Nombre de votes invalides.
`empty`|Nombre de votes blancs
`elegible_voters`|Nombre de personne aptes à voter.
