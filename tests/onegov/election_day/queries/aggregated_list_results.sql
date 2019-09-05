SELECT
    lists.list_id,
    lists.name as list_name,
    lists.number_of_mandates,
    c.party,
    c.family_name,
    c.first_name
FROM lists LEFT JOIN candidates as c ON lists.id = c.list_id
WHERE lists.election_id = 'erneuerungswahl-des-nationalrates-2';


SELECT
    lists.list_id,
    lists.name as list_name,
    c.party,
    c.family_name,
    c.first_name
FROM candidates as c RIGHT JOIN lists ON c.list_id = lists.id
WHERE lists.election_id = 'erneuerungswahl-des-nationalrates-2';