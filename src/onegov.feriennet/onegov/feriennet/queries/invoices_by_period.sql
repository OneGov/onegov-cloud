/*
    All invoices per period and username
*/
WITH

-- the invoice item rows
details AS (
    SELECT
        invoice_items.id,
        invoice_items.invoice_id,
        users.username,
        "group",
        "text",
        "family",
        paid as paid,
        unit * quantity as amount,
        invoices.period_id,
        source,
        ARRAY_LENGTH(payment.states, 1) > 0 AS has_online_payments,
        CASE
            WHEN paid
                THEN 0
            ELSE unit * quantity
        END as outstanding,
        CASE
            WHEN "source" is NULL
                THEN 'possible'
            WHEN "source" = 'xml'
                THEN 'discouraged'
            WHEN "source" = 'stripe_connect' AND NOT payment.states && ARRAY['open', 'paid']
                THEN 'possible'
            ELSE 'impossible'
        END AS changes
    FROM
        invoice_items
    LEFT JOIN invoices ON invoice_items.invoice_id = invoices.id
    LEFT JOIN users ON invoices.user_id = users.id
    LEFT JOIN (
        SELECT
            payments_for_invoice_items_payments.invoice_items_id,
            ARRAY_AGG(payments."state")::text[] as states

        FROM payments_for_invoice_items_payments
        LEFT JOIN payments
            ON payments_for_invoice_items_payments.payment_id = payments.id
        GROUP BY invoice_items_id
    ) AS payment ON invoice_items_id = invoice_items.id
),

-- the totals
totals AS (
    SELECT
        period_id,
        username,
        sum(outstanding) <= 0 as paid,
        sum(amount) as amount,
        sum(outstanding) as outstanding,
        array_agg(distinct changes) as changes
    FROM
        details
    GROUP BY
        period_id,
        username
),

-- details and totals combined
invoices AS (
    SELECT
        details.id,
        details.username,
        INITCAP(users.realname) as realname,
        details.group,
        details.text,
        details.family,
        details.paid,
        details.amount,
        details.period_id,
        details.changes,
        details.source,
        details.has_online_payments,
        details.invoice_id,
        totals.paid as invoice_paid,
        totals.amount as invoice_amount,
        totals.outstanding as invoice_outstanding,
        CASE
            WHEN totals.changes && '{impossible}'::text[]
                THEN 'impossible'
            WHEN totals.changes && '{discouraged}'::text[]
                THEN 'discouarged'
            ELSE 'possible'
        END as invoice_changes

    FROM
        details
    JOIN
        totals ON details.period_id = totals.period_id
              AND details.username = totals.username
    JOIN
        users ON users.username = details.username
    ORDER BY
        REGEXP_REPLACE(
            LOWER(users.realname),
            '[\u00A0]+', ' ', 'g'
        ),
        details.family NULLS FIRST,
        lower(details."group"),
        lower(details."text")
)

-- the resulting query
SELECT
    id,                  -- UUID
    realname,            -- Text
    username,            -- Text
    "group",             -- Text
    "text",              -- Text
    "family",            -- Text
    paid,                -- Boolean
    has_online_payments, -- Boolean
    amount,              -- Numeric
    source,              -- Text
    period_id,           -- UUID
    changes,             -- Text
    invoice_id,          -- Text
    invoice_paid,        -- Boolean
    invoice_amount,      -- Numeric
    invoice_outstanding, -- Numeric
    invoice_changes      -- Text
FROM invoices
