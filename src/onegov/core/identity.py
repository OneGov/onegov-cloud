from __future__ import annotations

from morepath import Identity


from typing import TYPE_CHECKING


class OneGovIdentity(Identity):

    userid: str  # email
    uid: str  # actual user id
    groupids: frozenset[str]
    role: str
    application_id: str

    def __init__(
        self,
        userid: str,
        *,
        uid: str,
        groupids: frozenset[str],
        role: str,
        application_id: str
    ) -> None:
        super().__init__(
            userid,
            uid=uid,
            groupids=groupids,
            role=role,
            application_id=application_id
        )

    # NOTE: Pretend arbitrary attribute access is disabled
    if TYPE_CHECKING:
        __getattr__ = None  # type: ignore
