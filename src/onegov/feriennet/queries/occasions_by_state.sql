/*
    loads the occasions for the matching view, categorising them into
    states, like 'operable' or 'overfull'
*/
WITH

-- the first start/end pair of each occasion
first_date AS (
    SELECT DISTINCT ON(occasion_id)
        ((occasion_dates.START AT TIME ZONE 'UTC')
            AT TIME ZONE occasion_dates.timezone) AS START,
        ((occasion_dates.END AT TIME ZONE 'UTC')
            AT TIME ZONE occasion_dates.timezone) AS END,
        occasion_dates.occasion_id
    FROM occasion_dates
    ORDER BY occasion_id, "start"
),

-- the number of accepted bookings per occasion
booking_states AS (
    SELECT
        occasion_id,
    period_id,
    SUM(CASE WHEN "state" = 'accepted' THEN 1 ELSE 0 END) AS accepted_count,
    SUM(CASE WHEN "state" = 'accepted' THEN 0 ELSE 1 END) AS other_count
    FROM bookings
    GROUP BY occasion_id, period_id
),

-- the occasion parameters needed to assign a state
occasion_parameters AS (
    SELECT
        occasions.id AS occasion_id,
        activities.title,
        first_date.start,
        first_date.end,
        occasions.cancelled,
        LOWER(occasions.spots) AS min_spots,
        UPPER(occasions.spots) - 1 AS max_spots,
        LOWER(occasions.age) AS min_age,
        UPPER(occasions.age) - 1 AS max_age,
        COALESCE(booking_states.accepted_count, 0) AS accepted_bookings,
    COALESCE(booking_states.other_count, 0) AS other_bookings,
    COALESCE(booking_states.accepted_count + booking_states.other_count, 0) AS total_bookings,
    occasions.period_id
    FROM
        occasions

    LEFT JOIN activities
      ON activities.ID = occasions.activity_id

    LEFT JOIN first_date
      ON occasions.ID = first_date.occasion_id

    LEFT JOIN booking_states
      ON occasions.ID = booking_states.occasion_id
     AND occasions.period_id = booking_states.period_id
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
    END AS "state",
    *
    FROM occasion_parameters
)

-- the resulting query
SELECT
    "state",           -- Text
    occasion_id,       -- Integer
    title,             -- Text
    "start",           -- DateTime
    "end",             -- DateTime
    min_spots,         -- Integer
    max_spots,         -- Integer
    min_age,           -- Integer
    max_age,           -- Integer
    accepted_bookings, -- Integer
    other_bookings,    -- Integer
    total_bookings,    -- Integer
    period_id          -- UUID
FROM
    occasion_states
