
import os

from onegov.core.utils import module_path, rchop
from onegov.event import EventCollection, OccurrenceCollection
from onegov.form import FormCollection
from onegov.libres import ResourceCollection
from onegov.page import PageCollection


def test_initial_content(town_app):
    pages = PageCollection(town_app.session()).query().all()
    pages = {p.name: p.title for p in pages}

    assert pages == {
        'leben-wohnen': 'Leben & Wohnen',
        'kultur-freizeit': 'Kultur & Freizeit',
        'bildung-gesellschaft': 'Bildung & Gesellschaft',
        'gewerbe-tourismus': 'Gewerbe & Tourismus',
        'politik-verwaltung': 'Politik & Verwaltung',
        'aktuelles': 'Aktuelles',
        'willkommen-bei-onegov': 'Willkommen bei OneGov'
    }

    forms = FormCollection(town_app.session()).definitions.query().all()
    forms = set(form.name for form in forms)

    paths = (p for p in os.listdir(module_path('onegov.town', 'forms')))
    paths = (p for p in paths if p.endswith('.form'))
    paths = (os.path.basename(p) for p in paths)
    builtin_forms = set(rchop(p, '.form') for p in paths)

    assert builtin_forms == forms

    resources = ResourceCollection(town_app.libres_context).query().all()
    resources = {r.name: r.type for r in resources}

    assert resources == {
        'sbb-tageskarte': 'daypass'
    }

    assert EventCollection(town_app.session()).query().count() == 4
    assert OccurrenceCollection(town_app.session()).query().count() > 4
