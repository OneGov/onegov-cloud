from __future__ import annotations

from onegov.election_day.models import UploadToken


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query
    from sqlalchemy.orm import Session
    from uuid import UUID


class UploadTokenCollection:

    def __init__(self, session: Session):
        self.session = session

    def query(self) -> Query[UploadToken]:
        return self.session.query(UploadToken).order_by(UploadToken.created)

    def create(self) -> UploadToken:
        """ Creates a new token. """

        token = UploadToken()
        self.session.add(token)
        self.session.flush()
        return token

    def delete(self, item: UploadToken) -> None:
        """ Deletes the given token. """

        self.session.delete(item)
        self.session.flush()

    def by_id(self, id: UUID) -> UploadToken | None:
        """ Returns the token by its id. """

        return self.query().filter_by(id=id).first()
