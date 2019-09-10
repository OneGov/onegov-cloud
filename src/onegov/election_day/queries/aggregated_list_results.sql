WITH

agg_election_results AS (
  SELECT
    election_id,
    sum(er.received_ballots) as received_ballots,
    sum(er.eligible_voters) as eligible_voters,

    sum(e.number_of_mandates * (
        er.received_ballots - er.blank_ballots - er.invalid_ballots
            - er.blank_votes - er.invalid_votes)) as accounted_votes
    FROM election_results er LEFT JOIN elections e on er.election_id = e.id
    GROUP BY
             er.election_id
    ),

list_results AS (
    SELECT
        l.election_id,
        l.id,
        l.list_id,
        number_of_mandates,
        name,
        sum(lr.votes) as list_votes
    FROM lists l
    LEFT JOIN list_results lr ON l.id = lr.list_id
    GROUP BY
            lr.list_id,     -- e.g. List 05
            l.election_id,
            l.id,
            l.number_of_mandates,
            l.name
),

election_total_list_votes AS (
    SELECT
        election_id,
        SUM(lr.list_votes) as election_list_votes
    FROM list_results lr
    GROUP BY election_id
),

candidate_results as (
    SELECT
           c.election_id,
           c.list_id,
           c.family_name,
           c.first_name,
           sum(cr.votes) as candidate_votes
    FROM candidates c
    LEFT JOIN candidate_results cr on c.id = cr.candidate_id
    GROUP BY
            cr.candidate_id,
            c.election_id,
            c.list_id,
            c.family_name,
            c.first_name
),

candidate_results_by_list AS (
    SELECT
           list_id,
           election_id,
           SUM(cr.candidate_votes) as candidate_votes_by_list

    FROM candidate_results cr
    GROUP BY
            list_id,
            election_id
),

election_total_candidate_votes AS (
    SELECT
           election_id,
           SUM(candidate_votes) as election_candidate_votes
    FROM candidate_results
    GROUP BY election_id
)

SELECT
    CAST(l.id AS TEXT) AS id,     -- TEXT
    l.list_id,                    -- TEXT
    l.election_id,          -- UUID
    l.name,                 -- Text
    l.list_votes,                -- Numeric
    crbl.candidate_votes_by_list,  -- Numeric
    etl.election_list_votes,    -- Numeric
    etcv.election_candidate_votes,    -- Numeric
    c.candidate_votes,      -- Numeric
    l.number_of_mandates,   --Numeric
    c.family_name,          --Text
    c.first_name,           --Text

    CASE
        WHEN etl.election_list_votes = 0
            THEN 0
        ELSE round(l.list_votes::DECIMAL / etl.election_list_votes * 100, 1)        -- Numeric
    END as perc_to_total_votes,
    CASE
        WHEN l.list_votes = 0
            THEN 0
        ELSE round(c.candidate_votes::DECIMAL / l.list_votes * 100, 1)
    END as perc_to_list_votes                                               -- Numeric

FROM list_results l
LEFT JOIN candidate_results c ON l.id = c.list_id
LEFT JOIN agg_election_results ar ON l.election_id = ar.election_id
LEFT JOIN election_total_list_votes etl ON l.election_id = etl.election_id
LEFT JOIN election_total_candidate_votes etcv ON l.election_id = etcv.election_id
LEFT JOIN candidate_results_by_list crbl ON l.id = crbl.list_id
ORDER BY
    l.list_votes DESC,
    c.candidate_votes DESC,
    l.name,
    c.family_name

