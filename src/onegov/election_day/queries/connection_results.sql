WITH

list_results AS (
    SELECT
    l.election_id,
    c.connection_id,
    pc.connection_id as parent_connection_id,
    CASE
        WHEN pc.connection_id IS NULL
            THEN c.connection_id
            ELSE pc.connection_id
    END as parent_group,
    l.name as list_name,
    SUM(lr.votes) AS list_votes
    FROM lists l
    JOIN list_results lr ON l.id = lr.list_id
    RIGHT JOIN list_connections c ON l.connection_id = c.id
    LEFT JOIN list_connections pc ON c.parent_id = pc.id
    GROUP BY
             l.id,
             l.name,
             l.connection_id,
             c.connection_id,
             parent_connection_id
),

sublist_results AS (
    SELECT
        lr.connection_id,
        lr.election_id,
        SUM(lr.list_votes) AS sublist_votes
    FROM list_results lr
    WHERE lr.parent_connection_id IS NOT NULL
    GROUP BY lr.connection_id, lr.election_id

),

main_list_results AS (
    SELECT
        lr.election_id,
        lr.parent_group,
        SUM(lr.list_votes) AS mainlist_votes
    FROM list_results lr
    GROUP BY lr.parent_group, lr.election_id
),
result as (
    SELECT
        lr.election_id,
        lr.connection_id,
        lr.list_name,
        lr.list_votes,
        lr.parent_group,
--         sr.sublist_votes
        mr.mainlist_votes
    FROM list_results lr
--     JOIN sublist_results sr ON lr.connection_id = sr.connection_id
    LEFT JOIN main_list_results mr ON lr.parent_group = mr.parent_group
)

-- I would like to add the main_list_results to result, but
--  the table grows as it should'nt after the left join. Why is that?

-- SELECT * FROM result v
SELECT * FROM main_list_results v

WHERE v.election_id = 'nationalratswahlen-2019'
-- ORDER BY v.connection_id


