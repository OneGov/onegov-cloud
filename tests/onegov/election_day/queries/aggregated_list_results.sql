WITH
-- aggregated
list_results AS (
    SELECT
        array_agg(distinct l.list_id) as list_id,
        array_agg(distinct l.number_of_mandates) as number_of_mandates,
        array_agg(distinct l.name) as name,
        sum(lr.votes) as total_votes
    FROM lists l
    LEFT JOIN list_results lr ON l.id = lr.list_id
    GROUP BY lr.list_id
    ORDER BY total_votes DESC
)
SELECT * from list_results
;
SELECT
    lists.list_id,
    lists.name as list_name,
    lists.number_of_mandates

FROM lists
LEFT JOIN list_results lr ON lists.id = lr.list_id
WHERE lists.election_id = 'erneuerungswahl-des-nationalrates-2'
GROUP BY lr.list_id
;



-- SELECT
--     lists.list_id,
--     lists.name as list_name,
--     c.party,
--     c.family_name,
--     c.first_name
-- FROM candidates as c RIGHT JOIN lists ON c.list_id = lists.id
-- WHERE lists.election_id = 'erneuerungswahl-des-nationalrates-2';