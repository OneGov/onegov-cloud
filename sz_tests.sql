WITH result_overview AS (
    SELECT
    er.name,
    e.shortcode,
    er.eligible_voters,
    er.entity_id

FROM election_results er
JOIN elections e ON e.id = er.election_id
WHERE er.entity_id = 1321 AND e.domain = 'region'
),

linkage_overview AS (
    SELECT
    ep.id,
    e.id as election_id
FROM election_compounds ep
JOIN election_compound_associations eca on ep.id = eca.election_compound_id
JOIN elections e on eca.election_id = e.id
WHERE ep.id = 'e23f6e27-434f-46e3-8916-a1b632ee87c6'
)

SELECT * FROM result_overview

-- SELECT
--     ep.shortcode as compound_shortcode,
--     e.shortcode as election_shortcode,
--     er.district as result_district,
--     er.entity_id,
--     er.name as entity_name
-- FROM election_compounds ep
-- JOIN election_compound_associations eca on ep.id = eca.election_compound_id
-- JOIN elections e on eca.election_id = e.id
-- JOIN election_results er on e.id = er.election_id
-- WHERE ep.id = 'e23f6e27-434f-46e3-8916-a1b632ee87c6'
-- ORDER BY er.entity_id
