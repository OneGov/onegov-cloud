WITH
-- aggregated
election_result_accounted_votes AS (
  SELECT
    sum(er.received_ballots) as received_ballots,
    sum(er.eligible_voters) as eligible_voters,
    sum(e.number_of_mandates * (
        er.received_ballots - er.blank_ballots - er.invalid_ballots
            - er.blank_votes - er.invalid_votes)) as accounted_votes

    FROM election_results er LEFT JOIN elections e on er.election_id = e.id

    WHERE er.election_id = 'erneuerungswahl-des-nationalrates-2'
    GROUP BY er.election_id
    ),

list_results AS (
    SELECT
        array_agg(distinct l.id) as id,
        array_agg(distinct l.number_of_mandates) as number_of_mandates,
        array_agg(distinct l.name) as name,
        sum(lr.votes) as total_votes
    FROM lists l
    LEFT JOIN list_results lr ON l.id = lr.list_id
    GROUP BY lr.list_id
),
candidate_results as (
    SELECT DISTINCT
           array_agg(distinct c.list_id) as list_id,
           array_agg(distinct c.family_name) as family_name,
           array_agg(distinct c.first_name)as first_name,
           sum(cr.votes) as candidate_votes
    FROM candidates c
    LEFT JOIN candidate_results cr on c.id = cr.candidate_id
    GROUP BY cr.candidate_id    -- candidate has an election id, so is unique every election
)
SELECT * from election_result_accounted_votes;
-- SELECT
--     l.name,
--     l.total_votes,
--     l.number_of_mandates,
--     c.family_name,
--     c.first_name,
--     c.candidate_votes
--
--  from list_results l
-- LEFT JOIN candidate_results c ON l.id = c.list_id
-- ORDER BY
--          total_votes DESC ,
--          candidate_votes DESC


-- SELECT
--     lists.list_id,
--     lists.name as list_name,
--     c.party,
--     c.family_name,
--     c.first_name
-- FROM candidates as c RIGHT JOIN lists ON c.list_id = lists.id
-- WHERE lists.election_id = 'erneuerungswahl-des-nationalrates-2';