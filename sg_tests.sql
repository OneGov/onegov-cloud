WITH

result_overview AS (
SELECT
    ep.shortcode as compound_shortcode,
    e.shortcode as election_shortcode,
    er.district as result_district,
    er.entity_id,
    er.name as entity_name
FROM election_compounds ep
JOIN election_compound_associations eca on ep.id = eca.election_compound_id
JOIN elections e on eca.election_id = e.id
JOIN election_results er on e.id = er.election_id
WHERE ep.id = 'kantonsratswahl-2020'
ORDER BY er.entity_id

),

linkage_overview AS (
    SELECT
    ep.id,
    e.id as election_id
FROM election_compounds ep
JOIN election_compound_associations eca on ep.id = eca.election_compound_id
JOIN elections e on eca.election_id = e.id
WHERE ep.id = 'kantonsratswahl-2020'
)

SELECT * FROM linkage_overview

