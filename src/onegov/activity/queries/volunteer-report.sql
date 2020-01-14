WITH occasion_numbers AS (
    SELECT
        occasions.id AS occasion_id,
        occasions.period_id,
        row_number() OVER (
            PARTITION BY
                occasions.activity_id,
                occasions.period_id
            ORDER BY
                occasions.order
        ) AS number
    FROM occasions
), needs_fulfilled AS (
    SELECT
        need_id,
        count(*) as fulfilled
    FROM volunteers
    WHERE state = 'confirmed'
    GROUP BY need_id
)
SELECT
    activities.id AS activity_id,                        -- UUID
    activities.title AS activity_title,                  -- Text
    activities.name AS activity_name,                    -- Text
    occasion_needs.id AS need_id,                        -- UUID
    occasion_needs.name AS need_name,                    -- Text
    lower(occasion_needs.number) AS min_required,        -- Integer
    upper(occasion_needs.number) - 1 AS max_required,    -- Integer
    coalesce(needs_fulfilled.fulfilled, 0) AS confirmed, -- Integer
    occasions.id AS occasion_id,                         -- UUID
    occasions.period_id AS period_id,                    -- UUID
    occasion_numbers.number AS occasion_number,          -- Integer
    volunteers.id AS volunteer_id,                       -- UUID
    volunteers.first_name AS first_name,                 -- Text
    volunteers.last_name AS last_name,                   -- Text
    volunteers.address AS address,                       -- Text
    volunteers.zip_code AS zip_code,                     -- Text
    volunteers.place AS place,                           -- Text
    volunteers.organisation AS organisation,             -- Text
    EXTRACT(
        YEAR FROM age(volunteers.birth_date)) as age,    -- Integer
    volunteers.email AS email,                           -- Text
    volunteers.phone AS phone,                           -- Text
    volunteers.state AS state,                           -- Text
    array_agg(
        ARRAY[
            occasion_dates.start
                AT TIME ZONE 'UTC'
                AT TIME ZONE occasion_dates.timezone,
            occasion_dates.end
                AT TIME ZONE 'UTC'
                AT TIME ZONE occasion_dates.timezone
        ]
    ) AS dates                                         -- ARRAY(DateTime)

FROM
    occasion_needs
    LEFT JOIN volunteers ON occasion_needs.id = volunteers.need_id
    LEFT JOIN needs_fulfilled ON volunteers.need_id = needs_fulfilled.need_id
    JOIN occasions ON occasion_needs.occasion_id = occasions.id
    JOIN activities ON occasions.activity_id = activities.id
    JOIN occasion_dates ON occasions.id = occasion_dates.occasion_id
    JOIN occasion_numbers ON occasions.id = occasion_numbers.occasion_id
GROUP BY
    activities.id,
    activities.title,
    activities.name,
    occasion_needs.id,
    occasion_needs.name,
    occasion_needs.number,
    occasions.period_id,
    occasions.order,
    occasions.id,
    occasion_numbers.number,
    volunteers.id,
    volunteers.first_name,
    volunteers.last_name,
    volunteers.state,
    volunteers.address,
    volunteers.zip_code,
    volunteers.place,
    volunteers.organisation,
    volunteers.birth_date,
    volunteers.email,
    volunteers.phone,
    needs_fulfilled.fulfilled
ORDER BY
    activity_title,
    activity_id,
    occasions.id,
    occasion_needs.name,
    first_name,
    last_name,
    organisation
