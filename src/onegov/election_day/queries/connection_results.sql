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
    END as list_group,
    CASE
        WHEN c.parent_id IS NULL
            THEN NULL
            ELSE c.connection_id
    END as sublist_group,
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
             parent_connection_id,
             sublist_group
),

result as (
    SELECT
        lr.election_id,
        lr.connection_id,
        lr.list_name,
        lr.list_group,
        lr.sublist_group,
        lr.list_votes,
        SUM(lr.list_votes) OVER (PARTITION BY lr.election_id, lr.sublist_group) as sublist_votes,
        SUM(lr.list_votes) OVER (PARTITION BY lr.election_id, lr.list_group) as mainlist_votes,
        SUM(lr.list_votes) OVER(PARTITION BY lr.election_id) AS total_votes
    FROM list_results lr
)

-- The resulting query
SELECT
       v.election_id,       -- Text
       v.connection_id,     -- Text
       v.list_name,         -- Text
       v.list_group,        -- Text
       v.sublist_group,     -- Text
       v.list_votes,        -- Numeric
       v.sublist_votes,     -- Numeric
       v.mainlist_votes,    -- Numeric
       v.total_votes        -- Numeric
FROM result v
ORDER BY v.list_group,
         v.sublist_group,
         v.sublist_votes DESC


