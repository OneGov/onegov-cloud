from __future__ import annotations

import morepath

from onegov.swissvotes.models.policy_area import PolicyArea


def policy_area_decode(s: str) -> PolicyArea:
    result = PolicyArea.from_url_param(s)
    if result is None:
        raise ValueError(f'Invalid policy area: {s!r}')
    return result


def policy_area_encode(p: PolicyArea | None) -> str:
    return p.value if p is not None else ''


policy_area_converter: morepath.Converter[PolicyArea] = (
    morepath.Converter(decode=policy_area_decode, encode=policy_area_encode)
)
