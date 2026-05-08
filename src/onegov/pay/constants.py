from __future__ import annotations

from decimal import Decimal

# total digits (for invoice item amounts)
PRECISION = 8

# digits after the point (for invoice item amounts)
SCALE = 2

# the maximum amount that can be precisely represented
MAX_AMOUNT = Decimal(('9' * (PRECISION - SCALE)) + '.99')
