/*
    loads the occasions for the matching view, categorising them into
    states, like 'operable' or 'overfull'
*/

-- the period_id to which the occasions are scoped to
SET vars.period_id = :'';
SET vars.states = :'{cancaelled,overfull,empty,unoperable,full}'; -- ('cancelled', 'overfull', 'empty', 'unoperable', 'operable', 'full')

WITH
-- the first start/end pair of each occasion
first_date AS (
    SELECT DISTINCT ON(occasion_id)
        ((occasion_dates.start AT TIME ZONE 'UTC')
            AT TIME ZONE occasion_dates.timezone) as start,
        ((occasion_dates.end AT TIME ZONE 'UTC')
            AT TIME ZONE occasion_dates.timezone) as end,
        occasion_dates.occasion_id
    FROM occasion_dates
    ORDER BY occasion_id, "start"
),

-- the number of accepted bookings per occasion
accepted AS (
    SELECT
        occasion_id,
        COUNT(*) as count
    FROM bookings
    WHERE state = 'accepted'
      AND bookings.period_id = current_setting('vars.period_id')::uuid
    GROUP BY occasion_id
),

-- the number of other non-accepted bookings per occasion
other AS (
    SELECT
        occasion_id,
        COUNT(*) as count
    FROM bookings
    WHERE state != 'accepted'
      AND bookings.period_id = current_setting('vars.period_id')::uuid
    GROUP BY occasion_id
),

-- the occasion parameters needed to assign a state
occasion_parameters AS (
    SELECT
        occasions.id as occasion_id,
        activities.title,
        first_date.start,
        first_date.end,
        occasions.cancelled,
        lower(occasions.spots) as min_spots,
        upper(occasions.spots) - 1 as max_spots,
        lower(occasions.age) as min_age,
        upper(occasions.age) - 1 as max_age,
        coalesce(accepted.count, 0) as accepted_bookings,
        coalesce(other.count, 0) as other_bookings,
        coalesce(accepted.count, 0) + coalesce(other.count, 0) as total_bookings
    FROM
        occasions

    LEFT JOIN activities
      ON activities.id = occasions.activity_id

    LEFT JOIN first_date
      ON occasions.id = first_date.occasion_id

    LEFT JOIN other
      ON occasions.id = other.occasion_id

    LEFT JOIN accepted
      ON occasions.id = accepted.occasion_id

    WHERE
        occasions.period_id = current_setting('vars.period_id')::uuid
),

-- the occasion paramters combined with the state
occasion_states AS (
    SELECT
    CASE
        WHEN cancelled = TRUE
            THEN 'cancelled'
        WHEN total_bookings > max_spots
            THEN 'overfull'
        WHEN accepted_bookings = 0
            THEN 'empty'
        WHEN accepted_bookings < min_spots
            THEN 'unoperable'
        WHEN accepted_bookings < max_spots
            THEN 'operable'
        WHEN accepted_bookings >= max_spots
            THEN 'full'
        ELSE NULL
    END as "state",
    *
    FROM occasion_parameters
    ORDER BY
        title, "start"
)

-- the resulting query
SELECT
    occasion_id,       -- UUID
    title,             -- Text
    start,             -- UTCDateTime
    end,               -- UTCDateTime
    cancelled,         -- Boolean
    min_spots,         -- Integer
    max_spots,         -- Integer
    min_age,           -- Integer
    accepted_bookings, -- Integer
    other_bookings,    -- Integer
    total_bookings,    -- Integer
    state              -- Text
FROM occasion_states;
