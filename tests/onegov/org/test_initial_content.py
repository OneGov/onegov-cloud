from __future__ import annotations

import os

from onegov.core.utils import module_path
from onegov.event import EventCollection, OccurrenceCollection
from onegov.form import FormCollection
from onegov.reservation import ResourceCollection
from onegov.page import PageCollection


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import TestOrgApp


def test_initial_content(org_app: TestOrgApp) -> None:
    pages_query = PageCollection(org_app.session()).query()
    pages = {p.name: p.title for p in pages_query}

    assert pages == {
        'organisation': 'Organisation',
        'themen': 'Themen',
        'kontakt': 'Kontakt',
        'news': 'Aktuelles',
        'wir-haben-eine-neue-webseite': 'Wir haben eine neue Webseite!'
    }

    forms_query = FormCollection(org_app.session()).definitions.query()
    forms = {form.name for form in forms_query}

    builtin_forms_path = module_path('onegov.org', 'forms/builtin/de')

    paths = (p for p in os.listdir(builtin_forms_path))
    paths = (p for p in paths if p.endswith('.form'))
    paths = (os.path.basename(p) for p in paths)
    builtin_forms = {p.removesuffix('.form') for p in paths}

    assert builtin_forms == forms

    resources_query = ResourceCollection(org_app.libres_context).query()
    resources = {r.name: r.type for r in resources_query}

    assert resources == {
        'konferenzraum': 'room',
        'tageskarte': 'daypass',
    }

    assert EventCollection(org_app.session()).query().count() == 4
    assert OccurrenceCollection(org_app.session()).query().count() > 4
