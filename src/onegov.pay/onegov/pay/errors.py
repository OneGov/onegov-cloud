import stripe

# the following exceptions should be caught and logged - the user should be
# informed that the payment failed, but not why
CARD_ERRORS = (stripe.error.CardError, )
