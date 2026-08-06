from __future__ import annotations


from typing import Any, ClassVar, TYPE_CHECKING
if TYPE_CHECKING:
    from decimal import Decimal
    from onegov.form import Form
    from onegov.reservation import Reservation, Resource

    type AnyRequest = Any


PRICING_SCHEMES: dict[str, type[ResourcePricingScheme]] = {}


class ResourcePricingScheme:
    """ Defines a complex pricing scheme, that cannot be expressed using
    the regular available configuration knobs.

    These are generally extremely specific to single customers and while
    they do feature parameters that can be set per resource, the formula
    itself is static and should not be changed after its inital creation.

    If the formula needs to change we need to create a new scheme instead,
    so old reservations can keep relying on the old scheme.
    """

    __slots__ = ()

    name: ClassVar[str]
    label: ClassVar[str]

    def __init_subclass__(
        cls,
        name: str | None = None,
        label: str | None = None,
        **kwargs: Any,
    ) -> None:

        if name is not None:
            assert name not in PRICING_SCHEMES
            assert label is not None
            cls.name = name
            cls.label = label
            PRICING_SCHEMES[name] = cls

        super().__init_subclass__(**kwargs)

    @classmethod
    def reservation_unit_price(
        cls,
        reservation: Reservation,
        resource: Resource,
        allocation_data: dict[str, Any] | None,
        submission_data: dict[str, Any] | None
    ) -> Decimal | None:
        """ Calculates the unit price for the given reservation. """
        raise NotImplementedError

    @classmethod
    def extend_form[T: Form](
        cls,
        form_class: type[T],
        request: AnyRequest
    ) -> type[T]:
        """ Extends the resource form with any fields specific to this
        pricing scheme.

        The fields should always set `depends_on=('pricing_scheme', cls.name)`
        and the field names schould be prefixed with the name of the pricing
        scheme, so they never conflict with the fields added by other pricing
        schemes.

        """
        raise NotImplementedError
