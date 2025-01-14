from __future__ import annotations

from onegov.core.security import Secret
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.exports.base import FeriennetExport
from onegov.org.forms import ExportForm
from onegov.user import UserCollection, User


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from sqlalchemy.orm import Query, Session


@FeriennetApp.export(
    id='benutzer',
    form_class=ExportForm,
    permission=Secret,
    title=_('Users'),
    explanation=_('Exports user accounts.'),
)
class UserExport(FeriennetExport):

    def run(
        self,
        form: ExportForm,  # type:ignore[override]
        session: Session
    ) -> Iterator[Iterator[tuple[str, Any]]]:

        return self.rows(session)

    def query(self, session: Session) -> Query[User]:
        return UserCollection(session).query().order_by(User.username)

    def rows(
        self,
        session: Session
    ) -> Iterator[Iterator[tuple[str, Any]]]:

        for user in self.query(session):
            yield ((k, v) for k, v in self.fields(user))

    def fields(self, user: User) -> Iterator[tuple[str, Any]]:
        yield from self.user_fields(user)
