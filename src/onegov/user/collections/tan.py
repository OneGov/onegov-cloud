from __future__ import annotations

from hashlib import sha256
from secrets import choice

from onegov.core.collection import GenericCollection
from onegov.user.models import TAN
from onegov.user.models.tan import DEFAULT_EXPIRES_AFTER


from typing import cast, Any, TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import datetime, timedelta
    from sqlalchemy.orm import Query, Session

    class _GeneratedTAN(TAN):
        tan: str


ALPHABET = 'ABCDEFGHIJKLMNPQRSTUVWXYZ123456789'


# NOTE: The same TAN can be generated multiple times, but this
#       should occur only rarely and since we only query the
#       TANs that haven't expired yet, it shouldn't cause any
#       issues.
def generate_tan() -> str:
    return ''.join(choice(ALPHABET) for _ in range(6))


class TANCollection(GenericCollection[TAN]):

    def __init__(
        self,
        session: Session,
        # NOTE: For disambiguating between e.g. second factor TAN
        #       and temporary privilege escalation TAN
        scope: str,
        expires_after: timedelta = DEFAULT_EXPIRES_AFTER,
    ):
        super().__init__(session)
        self.expires_after = expires_after
        self.scope = scope

    @property
    def model_class(self) -> type[TAN]:
        return TAN

    def query(self) -> Query[TAN]:
        return self.session.query(TAN).filter(
            TAN.is_active(self.expires_after),
            TAN.scope == self.scope
        )

    def hash_tan(self, tan: str) -> str:
        return sha256(tan.encode('utf-8')).hexdigest()

    def add(  # type:ignore[override]
        self,
        *,
        client: str,
        created: datetime | None = None,  # for testing
        **meta: Any
    ) -> _GeneratedTAN:

        tan = generate_tan()
        obj = cast('_GeneratedTAN', TAN(
            hashed_tan=self.hash_tan(tan),
            created=created or TAN.timestamp(),
            client=client,
            scope=self.scope,
            meta=meta
        ))
        obj.tan = tan

        self.session.add(obj)
        self.session.flush()

        return obj

    def by_client(self, client: str) -> Query[TAN]:
        return self.query().filter(TAN.client == client)

    def by_tan(self, tan: str) -> TAN | None:
        hashed_tan = self.hash_tan(tan)
        return self.query().filter(TAN.hashed_tan == hashed_tan).first()
