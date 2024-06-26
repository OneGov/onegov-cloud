Elections et votes : Données ouvertes
=====================================

Conditions d’utilisation
------------------------

Utilisation libre. Obligation d’indiquer la source.

- Vous pouvez utiliser ce jeu de données à des fins non commerciales.
- Vous pouvez utiliser ce jeu de données à des fins commerciales.
- L’indication de la source (auteur, titre et lien vers le jeu de données) est obligatoire.

Introduction
------------

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
`type`|`election` pour les élections, `election_compound` pour les composantes des élections, `vote` pour les votations.
`title`|Un objet contenant les titres traduits.
`date`|La date (ISO 8601).
`domain`|Le domaine d'influence (fédération, canton, ...).
`url`|Un lien vers la vue détaillée.
`completed`|True, si le vote ou l'élection est terminé.
`progress`|Un objet contenant le nombre de municipalités/élections déjà comptées (`counted`) et le nombre total de municipalités/élections (`total`).
`last_modified`|La dernière fois que les données ont changé (ISO 8601).
`turnout`|Pourcentage de participation.

Les résultats de la votation contiennent les informations supplémentaires suivantes :

Nom|Description
---|---
`answer`|La réponse de la votation : `accepted` (acceptée), `rejected` (rejetée), `proposal` (proposition) ou `counter-proposal` (contre-proposition).
`yeas_percentage`|Pourcentage de oui.
`nays_percentage`|Pourcentage de non.
`local` (*optional*)|Federal and cantonal votes within a communal instance may contain additionally the results of the municipality in the form of an object with `answer`, `yeas_percentage` and `nays_percentage`.

Les résultats des élections contiennent les informations supplémentaires suivantes :

Nom|Description
---|---
`elected`|Une liste des candidats élus.

Les résultats des composantes des élections contiennent les informations supplémentaires suivantes :

Nom|Description
---|---
`elected`|Une liste des candidats élus.
`elections`|Une liste avec des liens vers les élections.


2 Résultats des élections
-------------------------

### Résultats transformés

```
URL: /election/{id}/json
```

Retourne les données de la vue principale sous une forme structurée.

### Données brutes

#### Résultats des candidats

```
URL: /election/{id}/data-{format}
```

Les données brutes des candidats sont disponibles dans les formats suivants :

Format|URL
---|---
JSON|`/data-json`
CSV|`/data-csv`

Les champs suivants sont inclus dans tous les formats:

Nom|Description
---|---
`election_id`|ID de l'élection. Utilisé dans l'URL.
`election_title_{locale}`|Les titres traduits, par exemple `title_de_ch` pour le titre en allemand.
`election_short_title_{locale}`|Les titres abrégés traduits, par exemple `title_de_ch` pour le titre abrégé en allemand.
`election_date`|La date de l'élection (an ISO 8601 date string).
`election_domain`|fédéral (`federation`), cantonal (`canton`), régional (`region`) ou municipal (`municipality`)
`election_type`|proportionnelle (`proporz`) ou système majoritaire (`majorz`).
`election_mandates`|Nombre de mandats/sièges.
`election_absolute_majority`|La majorité absolue. Uniquement valable pour les élections basées sur le système majoritaire.
`election_status`|Résultats intermédiaires (`interim`), résultats finaux (`final`) or inconnu (`unknown`).
`entity_id`|L'identifiant de la municipalité. A value `0` represents the expats.
`entity_name`|Le nom de la municipalité.
`entity_district`|La circonscription de la municipalité.
`entity_counted`|`True` si le résultat a été compté.
`entity_eligible_voters`|Le nombre de personnes éligible à voter pour cette municipalité.
`entity_expats`|Nombre d'expatriés pour cette municipalité.
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
`list_color`|La couleur de la liste en valeur hexadécimale, par exemple `#a6b784`.
`list_number_of_mandates`|Le nombre de mandats que cette liste a obtenus. Uniquement valable pour les élections basées sur la représentation proportionnelle.
`list_votes`|Le nombre de votes que cette liste a obtenu. Uniquement valable pour les élections sur la base de la représentation proportionnelle.
`list_connection`|L'Identifiant de la connexion de la liste à laquelle cette liste est connectée. Uniquement valable pour les élections sur la base de la représentation proportionnelle.
`list_connection_parent`|L'Identifiant de la connexion de liste parent à laquelle cette liste est connectée. Uniquement valable pour les élections sur la base de la représentation proportionnelle.
`list_panachage_votes_from_list_{XX}`|Le nombre de votes que la liste a obtenu de la liste `list_id = XX`. Une liste `list_id` avec la valeur `999` marque les votes de la liste vide. Ne contient pas de votes de la liste propre.
`candidate_family_name`|Le nom de famille du candidat.
`candidate_first_name`|Le prénom du candidat.
`candidate_id`|L'identifiant du candidat.
`candidate_elected`|Vrai si le candidat a été élu.
`candidate_party`|Nom de le parti.
`candidate_party_color`|La couleur du parti en valeur hexadécimale, par exemple `#a6b784`.
`candidate_gender`|Le sexe du candidat : `female` (féminin), `male` (masculin) ou `undetermined` (indéterminé).
`candidate_year_of_birth`|L'année de naissance du candidat.
`candidate_votes`|Le nombre de voix que ce candidat a obtenu.
`candidate_panachage_votes_from_list_{XX}`|Le nombre de votes que ce candidat a obtenu de la liste `list_id = XX`. Une liste `list_id` avec la valeur `999` marque les votes de la liste vide.

Les composantes des élections contiennent les informations supplémentaires suivantes :

Name|Description
---|---
`compound_id`|ID du composant des élections. Utilisé dans l'URL.
`compound_title_{locale}`|Les titres traduits, par exemple `title_de_ch` pour le titre en allemand.
`compound_short_title_{locale}`|Les titres abrégés traduits, par exemple `title_de_ch` pour le titre abrégé en allemand.
`compound_date`|La date de l'élection (an ISO 8601 date string).
`compound_mandates`|Nombre total de mandats/sièges.

Les municipalités qui n’ont pas encore été comptées ne sont pas incluses.

#### Résultats du parti

```
URL: /election/{id}/data-parties-{format}
```

Les données brutes des parties sont disponibles dans les formats suivants :

Format|URL
---|---
JSON|`/data-parties-json`
CSV|`/data-parties-csv`

Les champs suivants sont inclus dans tous les formats:

Nom|Description
---|---
`domain`|Le domaine d'influence auquel la ligne s'applique.
`domain_segment`|L'unité du domaine d'influence à laquelle s'applique la ligne.
`year`|Année de l'élection.
`total_votes`|Le total des votes de l'élection.
`name`|Le dénomination du parti dans la langue par défaut.
`name_{locale}`|Nom traduit du parti, par exemple `name_de_ch` pour le nom allemand.
`id`|Identifiant du parti.
`color`|La couleur du parti en valeur hexadécimale, par exemple `#a6b784`.
`mandates`|Le nombre de mandats.
`votes`|Le nombre de votes.
`voters_count`|Nombre de votants. Le nombre cumulé de voix par rapport au nombre total de mandats par élection. Uniquement pour les composantes des élections.
`voters_count_percentage`|Nombre de votants (pourcentages). Le nombre cumulé de voix par rapport au nombre total de mandats par élection (pourcentages). Uniquement pour les composantes des élections.
`panachage_votes_from_{XX}`|Le nombre de votes que le parti a obtenu de la part du parti avec un `id = XX`. Un `id` avec la valeur `999` marque les votes à partir de la liste vide.

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

Les champs suivants sont contenus dans les formats `JSON` et `CSV` :

Nom|Description
---|---
`id`|ID du vote. Utilisé dans l'URL.
`title_{locale}`|Les titres traduits, par exemple `title_de_ch` pour le titre en allemand.
`short_title_{locale}`|Les titres abrégés traduits, par exemple `title_de_ch` pour le titre abrégé en allemand.
`date`|La date du vote (une chaîne de date ISO 8601).
`shortcode`|Shortcode interne (définit l'ordre des votes ayant lieu le même jour).
`domain`|`federation` pour fédéral, `canton` for les votes cantonaux.
`status`|Interim results (`interim`), final results (`final`) or unknown (`unknown`).
`answer`|La réponse de la votation : `accepted` (acceptée), `rejected` (rejetée), `proposal` (proposition) ou `counter-proposal` (contre-proposition).
`type`|Type: `proposal` (proposition), `counter-proposal` (contre-proposition) ou `tie-breaker` (jeu décisif).
`ballot_answer`|La réponse par type : `accepted` (accepté) ou `rejected` (rejetée) pour `type=proposal` (proposition) et `type=counter-proposal` (contre-proposition) ; `proposal` (proposition) ou `counter-proposal` (contre-proposition) pour `type=tie-breaker` (jeu décisif).
`district`|La circonscription de la municipalité.
`name`|Le nom de la municipalité.
`entity_id`|La référence de la municipalité/localité. A value `0` represents the expats.
`counted`|Vrai si le résultat a été compté, faux si le résultat n'est pas encore connu (le compte des votes n'est pas encore fini).
`yeas`|Nombre de votes oui
`nays`|Nombre de votes non
`invalid`|Nombre de votes invalides.
`empty`|Nombre de votes blancs
`eligible_voters`|Nombre de personne aptes à voter.
`expats`|Nombre d'expatriés.

4 Sitemap
---------

```
URL: /sitemap.xml
```

Renvoie un plan du site au format XML (https://www.sitemaps.org/protocol.html)

```
URL: /sitemap.json
```

Renvoie le plan du site en JSON.
