from __future__ import annotations

from onegov.core.utils import Bunch
from onegov.user import UserCollection
from onegov.user.upgrade import fix_stringified_user_tags

from typing import cast, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.upgrade import UpgradeContext
    from sqlalchemy.orm import Session


class FeriennetApp:
    pass


def _context(session: Session, app: object) -> UpgradeContext:
    context = Bunch(
        has_table=lambda table: True,
        session=session,
        app=app,
    )
    return cast('UpgradeContext', context)


def test_fix_stringified_user_tags(session: Session) -> None:
    users = UserCollection(session)
    user = users.add('user-a@example.org', 'hunter2', 'member')
    user.tags = ["['Sport']", "['[]']", '[]', 'Kultur']
    # single-element repr (array length 1) must be caught too
    single = users.add('user-b@example.org', 'hunter2', 'member')
    single.tags = ["['Musik']"]
    # a clean user must be left untouched
    clean = users.add('user-c@example.org', 'hunter2', 'member')
    clean.tags = ['Sport', 'Kultur']
    # tags that are pure empty-list reprs unwrap to nothing
    empty = users.add('user-d@example.org', 'hunter2', 'member')
    empty.tags = ['[]', "['[]']"]
    session.flush()

    fix_stringified_user_tags(_context(session, FeriennetApp()))
    session.flush()

    def tags_of(username: str) -> list[str] | None:
        user = users.by_username(username)
        assert user is not None
        return user.tags

    assert tags_of('user-a@example.org') == ['Sport', 'Kultur']
    assert tags_of('user-b@example.org') == ['Musik']
    assert tags_of('user-c@example.org') == ['Sport', 'Kultur']
    assert tags_of('user-d@example.org') == []


def test_fix_stringified_user_tags_skips_non_feriennet(
    session: Session
) -> None:
    users = UserCollection(session)
    user = users.add('user-b@example.org', 'hunter2', 'member')
    user.tags = ["['Sport']"]
    session.flush()

    fix_stringified_user_tags(_context(session, Bunch()))
    session.flush()

    # untouched on non-feriennet instances
    unchanged = users.by_username('user-b@example.org')
    assert unchanged is not None
    assert unchanged.tags == ["['Sport']"]
