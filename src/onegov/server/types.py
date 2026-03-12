from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    JSON = (
        dict[str, 'JSON'] | list['JSON']
        | str | int | float | bool | None
    )
    JSONObject = dict[str, JSON]
    JSONArray = list[JSON]

    # read only variant of JSON type that is covariant
    JSON_ro = (
        Mapping[str, 'JSON_ro'] | Sequence['JSON_ro']
        | str | int | float | bool | None
    )
    JSONObject_ro = Mapping[str, JSON_ro]
    JSONArray_ro = Sequence[JSON_ro]
