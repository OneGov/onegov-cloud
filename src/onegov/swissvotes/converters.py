from __future__ import annotations

import morepath

from onegov.swissvotes.models.policy_area import PolicyArea


def policy_area_decode(s: str) -> PolicyArea | None:
    return PolicyArea.from_url_param(s)


def policy_area_encode(p: PolicyArea | None) -> str:
    return p.value if p else ''


policy_area_converter: morepath.Converter[PolicyArea | None] = (
    morepath.Converter(decode=policy_area_decode, encode=policy_area_encode)
)
