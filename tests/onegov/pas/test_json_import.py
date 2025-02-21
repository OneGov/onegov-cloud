from __future__ import annotations

from onegov.pas.json_import import import_zug_kub_data

import traceback
from pathlib import Path
import pytest
from click.testing import CliRunner

from onegov.org.cli import cli as org_cli
from onegov.pas.cli import cli
from onegov.pas.models import (
    Commission,
    CommissionMembership,
    Parliamentarian,
    ParliamentaryGroup,
    Party
)


def test_successful_import(
    session, people_json, organization_json, memberships_json
):
    """Test successful import of all data.

    *1. Understanding the Data and Models**

     Let's solidify our understanding of how these relate.

     **people.json**: Contains individual person data (Parliamentarians).
     Key fields are firstName, officialName, primaryEmail, tags, title,
     id.  This maps to the Parliamentarian model.

    **organizations.json**:
        Contains organization data. Crucially, organizationTypeTitle dictates
        the type of organization.
        - "Kommission":  Maps to your Commission model.
        - "Kantonsrat":  This is a special case. It's not a Commission.
        It represents the Parliament itself. We link this as ParliamentarianRole
        directly on the Parliamentarian model with role='member' and associated with
        the Kantonsrat organization.

    - "Fraktion":  Maps to ParliamentaryGroup.
    - "Sonstige":  Could be various types.  Let's see how these are intended to be modeled.
        We need more clarity on how "Sonstige" is categorized.

    **memberships.json**:  Connects person and organization.
    It defines the role within that organization, start, end dates.
    The nested person and organization blocks are crucial for establishing
    relationships.
    """
    import_zug_kub_data(
        session,
        people_source=people_json,
        organizations_source=organization_json,
        memberships_source=memberships_json,
    )

    # Verify parliamentarians were imported
    parliamentarians = session.query(Parliamentarian).all()
    assert len(parliamentarians) == 2

    assert any(p.first_name == "Daniel" and p.last_name == "Abt" for p in
               parliamentarians)
    assert any(p.first_name == "Heinz" and p.last_name == "Achermann" for p in
               parliamentarians)

    # Verify commissions were imported
    commissions = session.query(Commission).all()
    assert len(commissions) == 2
    assert any(
        c.name == "amtliche Kommission Test" and c.type == "official" for c in
        commissions)
    assert any(
        c.name == "Interkantonale Kommission Test" and c.type == "intercantonal"
        for c in commissions)

    # Verify memberships were imported
    memberships = session.query(CommissionMembership).all()
    assert len(memberships) == 2

    # Check specific membership details
    president_membership = next(
        m for m in memberships
        if m.parliamentarian.first_name == "Daniel"
    )
    assert president_membership.role == "president"
    assert president_membership.end is None

    member_membership = next(
        m for m in memberships
        if m.parliamentarian.first_name == "Heinz"
    )
    assert member_membership.role == "member"
    assert member_membership.end is not None
