import base64
import hashlib
import json

from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, TYPE_CHECKING, cast

import pytest
import yaml

from click.testing import CliRunner
from tests.shared.utils import create_image
from onegov.org.cli import cli
from onegov.core.utils import Bunch
from sqlalchemy import text as sql_text
from onegov.org.upgrade import add_horw_political_business_enums
from onegov.org.models.political_business import POLITICAL_BUSINESS_TYPE
from onegov.org.models import (
    Meeting,
    MeetingItem,
    PoliticalBusiness,
    PoliticalBusinessParticipation,
    RISCommissionMembership,
    RISParliamentarian,
    RISParliamentarianRole,
)
from onegov.org.ris_import import OGIArchive, parse_date

if TYPE_CHECKING:
    from onegov.core.orm import SessionManager
    from onegov.core.upgrade import UpgradeContext
    from .conftest import TestOrgApp


def text(value: str) -> dict[str, Any]:
    return {'type': 'Text', 'text': value}


def link(value: str, kind: str, source: str) -> dict[str, Any]:
    return {
        'type': 'Link',
        'text': value,
        'url': f'https://www.horw.ch/_rte/{kind}/{source}',
    }


def paragraph(*children: dict[str, Any]) -> dict[str, Any]:
    return {'type': 'Paragraph', 'children': list(children)}


def table(
    headers: list[str], rows: list[list[dict[str, Any]]]
) -> dict[str, Any]:
    return {
        'type': 'Table',
        'headers': [text(header) for header in headers],
        'rows': [{'type': 'Row', 'cells': cells} for cells in rows],
    }


def page(title: str, *elements: dict[str, Any]) -> dict[str, Any]:
    return {'metadata': {'title': title}, 'elements': list(elements)}


def seal(root: Path) -> None:
    manifest_path = root / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['files'] = {
        str(path.relative_to(root)): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in root.glob('*/*.json')
    }
    manifest_path.write_text(json.dumps(manifest))


def make_archive(root: Path) -> Path:
    records: dict[str, dict[str, Any]] = {
        'lists/businesses': page(
            'Geschäfte',
            table(['Geschäft'], [[link('Geschäft', 'information', '10')]]),
        ),
        'lists/people': page(
            'Aktive',
            table(
                ['Name'], [[link('Beck Bertschmann Bettina', 'person', '1')]]
            ),
        ),
        'lists/council': page(
            'Einwohnerrat',
            table(
                ['Name', 'Funktion'],
                [
                    [
                        link('Beck Bertschmann Bettina', 'person', '1'),
                        text('Stimmenzählerin'),
                    ]
                ],
            ),
        ),
        'parliamentarians/unknown_1': page(
            'Bettina Beck Bertschmann',
            paragraph(
                {
                    'type': 'Link',
                    'text': 'Mail',
                    'url': 'mailto:bettina@example.org',
                }
            ),
        ),
        'parliamentarians/unknown_2': page(
            'Former Member',
            {'type': 'Heading', 'text': 'Politische Vorstösse', 'level': 2},
            table(['Geschäft'], [[link('Test', 'information', '10')]]),
        ),
        'parliamentarians/unknown_3': page('Excluded Person'),
        'political-business/unknown_10': page(
            'Testgeschäft',
            {
                'type': 'EmbeddedImage',
                'content': 'data:image/png;base64,'
                + base64.b64encode(create_image().getvalue()).decode(),
                'alt': 'Illustration',
            },
            paragraph(text('Nummer')),
            paragraph(text('2010-1')),
            paragraph(text('Geschäftsart')),
            paragraph(text('Interpellation')),
            paragraph(text('Status')),
            paragraph(text('Zur Kenntnis genommen')),
            paragraph(text('Datum')),
            paragraph(text('1. Januar 2010')),
            paragraph(text('Beschreibung')),
            paragraph(
                text('<script>'),
                {
                    'type': 'UnorderedList',
                    'children': [
                        {
                            'type': 'ListItem',
                            'children': [text('Inhalt & mehr')],
                        }
                    ],
                },
            ),
            paragraph(text('Verfasser/Beteiligte')),
            paragraph(
                link('Beck Bertschmann Bettina', 'person', '1'),
                text('(Erstunterzeichner/-in),'),
                text('Ruth Strässle-Erismann, FDP (Mitunterzeichner/in)'),
                {'type': 'Break'},
                text('Ruth Strässle-Erismann (Mitunterzeichner/in)'),
            ),
            paragraph(text('Fraktion')),
            paragraph(link('Fraktion', 'behoerde', '30')),
            paragraph(link('Sitzung', 'anlass', '20')),
            table(
                ['Dokument'],
                [
                    [
                        {
                            'type': 'Link',
                            'text': 'Vorstoss',
                            'url': 'https://www.horw.ch/_docn/100/test.pdf',
                        }
                    ]
                ],
            ),
        ),
        'meetings/unknown_20': page(
            'Einwohnerratssitzung',
            paragraph(text('7. Nov. 2024, 17.00 Uhr')),
            {'type': 'Heading', 'text': 'Ort', 'level': 2},
            paragraph(text('Aula Zentrum')),
            {'type': 'Heading', 'text': 'Traktanden', 'level': 2},
            table(
                ['Nr.', 'Bezeichnung', 'Geschäft'],
                [
                    [
                        text('01'),
                        text('Testgeschäft'),
                        link('Vorstoss', 'information', '10'),
                    ],
                    [
                        text('02'),
                        text('Zweite Beratung'),
                        link('Vorstoss', 'information', '10'),
                    ],
                    [
                        text('03'),
                        text('Historisch ausserhalb Stichtag'),
                        link('Alt', 'information', '9'),
                    ],
                ],
            ),
        ),
        'parliamentary_groups/unknown_30': page(
            'Fraktion',
            {'type': 'Heading', 'text': 'Personen', 'level': 2},
            table(
                ['Name Vorname', 'Funktion'],
                [
                    [
                        link('Beck Bertschmann Bettina', 'person', '1'),
                        text('Präsidentin'),
                    ]
                ],
            ),
        ),
        'commissions/unknown_40': page(
            'Kommission',
            {'type': 'Heading', 'text': 'Personen', 'level': 2},
            table(
                ['Name Vorname', 'Funktion'],
                [
                    [
                        link('Beck Bertschmann Bettina', 'person', '1'),
                        text('Mitglied'),
                    ]
                ],
            ),
        ),
    }
    for name, record in records.items():
        path = root / f'{name}.json'
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(record))
    document = root / 'document.pdf'
    document.write_bytes(b'%PDF-1.4\n%%EOF')
    (root / 'manifest.json').write_text(
        json.dumps(
            {
                'format': 'ogi-ris-1',
                'source': 'https://www.horw.ch',
                'since': '2010-01-01',
                'business_count': 1,
                'files': {},
                'assets': {
                    'https://www.horw.ch/_docn/100/test.pdf': {
                        'path': 'document.pdf',
                        'title': 'Vorstoss',
                        'sha256': hashlib.sha256(
                            document.read_bytes()
                        ).hexdigest(),
                    }
                },
            }
        )
    )
    seal(root)
    return root


def test_ogi_import(org_app: TestOrgApp, tmp_path: Path) -> None:
    archive = OGIArchive(make_archive(tmp_path))
    session = org_app.session()
    existing = RISParliamentarian(
        first_name='Bettina', last_name='Beck Bertschmann'
    )
    session.add(existing)
    original_business = PoliticalBusiness(
        title='Existing business',
        number='I 2010-1 ',
        entry_date=date(2010, 1, 1),
        political_business_type='interpellation',
        meta={'custom': 'preserve'},
    )
    session.add(original_business)
    session.flush()
    first = archive.importer(session).run()
    assert first['political-business'] == 1
    assert first['skipped_inactive'] == 1
    business = session.query(PoliticalBusiness).one()
    assert business.id == original_business.id
    assert business.meta['custom'] == 'preserve'
    assert len(business.meta['ogi_images']) == 1
    assert business.political_business_type == 'interpellation'
    assert business.status == 'zur_kenntnis_genommen'
    assert business.entry_date == date(2010, 1, 1)
    assert '<script>' not in (business.chronology or '')
    assert '<li>Inhalt &amp; mehr</li>' in (business.chronology or '')
    assert len(business.files) == 2
    assert len(business.participants) == 3
    assert len(business.parliamentary_groups) == 1
    assert existing.active
    assert any(role.role == 'vote_counter' for role in existing.roles)
    assert existing.email_primary == 'bettina@example.org'
    assert existing.meta['parliamentarian_id'] == '1'
    assert session.query(RISParliamentarian).count() == 3
    former = (
        session.query(RISParliamentarian).filter_by(first_name='Former').one()
    )
    assert not former.active
    historical = (
        session.query(RISParliamentarian).filter_by(first_name='Ruth').one()
    )
    assert not historical.active
    assert historical.meta['ogi_unresolved_name'] == 'Ruth Strässle-Erismann'
    meeting = session.query(Meeting).one()
    assert meeting.start_datetime is not None
    assert meeting.start_datetime == datetime(2024, 11, 7, 16, tzinfo=UTC)
    assert meeting.end_datetime is None
    assert 'Aula Zentrum' in meeting.address
    assert (
        session.query(MeetingItem)
        .filter_by(political_business_id=business.id)
        .count()
        == 2
    )
    models: tuple[Any, ...] = (
        PoliticalBusiness,
        RISParliamentarian,
        PoliticalBusinessParticipation,
        Meeting,
        MeetingItem,
        RISCommissionMembership,
        RISParliamentarianRole,
    )
    snapshot = {
        model: {row[0] for row in session.query(model.id)} for model in models
    }
    second = archive.importer(session).run()
    assert second.get('created', 0) == 0
    assert snapshot == {
        model: {row[0] for row in session.query(model.id)}
        for model in snapshot
    }
    assert len(business.files) == 2


@pytest.mark.parametrize(
    'active,linked',
    [
        (False, False),
        (False, True),
        (True, False),
    ],
)
def test_ogi_member_updates(
    org_app: TestOrgApp,
    tmp_path: Path,
    active: bool,
    linked: bool,
) -> None:
    root = make_archive(tmp_path)
    path = root / 'lists/people.json'
    listing = json.loads(path.read_text())
    if active:
        listing['elements'].append(
            paragraph(link('Person Excluded', 'person', '3'))
        )
    path.write_text(json.dumps(listing))
    if linked:
        path = root / 'parliamentarians/unknown_3.json'
        data = json.loads(path.read_text())
        data['elements'].append(
            table(['Geschäft'], [[link('Test', 'information', '10')]])
        )
        path.write_text(json.dumps(data))
    seal(root)
    session = org_app.session()
    person = RISParliamentarian(
        first_name='Before',
        last_name='Person',
        meta={'parliamentarian_id': '3', 'custom': 'preserve'},
        content={'custom': 'preserve'},
    )
    session.add(person)
    session.flush()
    OGIArchive(root).importer(session).run()
    assert person.first_name == ('Excluded' if active or linked else 'Before')
    assert person.meta['custom'] == 'preserve'
    assert person.content['custom'] == 'preserve'
    assert person.active is active


@pytest.mark.parametrize(
    'damage',
    [
        'page',
        'asset',
        'missing',
        'count',
        'traversal',
        'cutoff',
        'enum',
    ],
)
def test_ogi_invalid_archive(tmp_path: Path, damage: str) -> None:
    root = make_archive(tmp_path)
    manifest_path = root / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    if damage == 'page':
        (root / 'political-business/unknown_10.json').write_text('{}')
    elif damage == 'asset':
        (root / 'document.pdf').write_bytes(b'broken')
    elif damage == 'missing':
        del manifest['files']['parliamentarians/unknown_1.json']
    elif damage == 'count':
        manifest['business_count'] = 2
    elif damage == 'traversal':
        manifest['files']['../escape.json'] = 'bad'
    elif damage == 'cutoff':
        manifest['since'] = '2011-01-01'
    else:
        path = root / 'political-business/unknown_10.json'
        path.write_text(path.read_text().replace('Interpellation', 'Unknown'))
        manifest['files'][str(path.relative_to(root))] = hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        OGIArchive(root)


@pytest.mark.parametrize(
    'value,expected',
    [
        ('1. März 2010', date(2010, 3, 1)),
        ('7. Nov. 2024, 17.00 Uhr', date(2024, 11, 7)),
        ('01.01.2010', date(2010, 1, 1)),
        ('', None),
    ],
)
def test_ogi_dates(value: str, expected: date | None) -> None:
    assert parse_date(value) == expected


def test_ogi_cli(
    cfg_path: str,
    session_manager: SessionManager,
    tmp_path: Path,
) -> None:
    root = make_archive(tmp_path)
    config_path = Path(cfg_path)
    config = yaml.safe_load(config_path.read_text())
    application = config['applications'][0]
    application['application'] = 'onegov.org.OrgApp'
    application['configuration'][
        'depot_backend'
    ] = 'depot.io.memory.MemoryFileStorage'
    application['configuration']['websockets'] = {
        'client_url': 'ws://localhost:8766',
        'manage_url': 'ws://localhost:8766',
        'manage_token': 'horw-local-test-token',
    }
    application['configuration']['filestorage'] = 'fs.osfs.OSFS'
    application['configuration']['filestorage_options'] = {
        'root_path': str(tmp_path / 'storage'),
        'create': True,
    }
    config_path.write_text(yaml.safe_dump(config))
    runner = CliRunner()
    command = [
        '--config',
        cfg_path,
        '--select',
        '/foo/bar',
        'import-ris',
        str(root),
    ]
    result = runner.invoke(cli, [*command, '--dry-run'])
    assert result.exit_code == 0, result.output
    assert 'OGI validated (no changes)' in result.output
    session_manager.set_current_schema('foo-bar')
    assert session_manager.session().query(PoliticalBusiness).count() == 0
    for _repeat in range(2):
        result = runner.invoke(cli, command, catch_exceptions=False)
        assert result.exit_code == 0, result.output
    # Individual, existing commands use the same OGI data and are repeatable.
    for name, directory in (
        ('parliamentarians', 'parliamentarians'),
        ('commissions', 'commissions'),
        ('parliamentary_groups', 'parliamentary_groups'),
        ('political-business', 'political-business'),
        ('meetings', 'meetings'),
    ):
        result = runner.invoke(
            cli,
            [*command[:4], f'import-{name}', str(root / directory)],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.output
    for name in (
        'create-commission-memberships',
        'create-political-business-participants',
        'create-parliamentarian-roles',
        'connect-political-business-meeting-items',
    ):
        result = runner.invoke(
            cli, [*command[:4], name], catch_exceptions=False
        )
        assert result.exit_code == 0, result.output
    session_manager.set_current_schema('foo-bar')
    session = session_manager.session()
    assert session.query(PoliticalBusiness).count() == 1
    assert session.query(RISParliamentarian).count() == 3
    assert session.query(PoliticalBusinessParticipation).count() == 3
    assert session.query(MeetingItem).count() == 3


def test_ogi_enum_upgrade(org_app: TestOrgApp) -> None:
    session = org_app.session()
    business = PoliticalBusiness(
        title='Existing', political_business_type='motion'
    )
    session.add(business)
    session.flush()
    session.execute(
        sql_text(
            '''
        ALTER TABLE par_political_businesses
        ALTER COLUMN political_business_type TYPE text;
        DROP TYPE par_political_business_type;
        CREATE TYPE par_political_business_type AS ENUM ('motion');
        ALTER TABLE par_political_businesses
        ALTER COLUMN political_business_type TYPE par_political_business_type
        USING political_business_type::par_political_business_type;
    '''
        )
    )
    context = cast(
        'UpgradeContext',
        Bunch(
            session=session,
            schema=org_app.session_manager.current_schema,
            has_table=lambda name: name == 'par_political_businesses',
        ),
    )
    assert add_horw_political_business_enums(context)
    assert not add_horw_political_business_enums(context)
    labels = set(
        session.execute(
            sql_text(
                '''
        SELECT e.enumlabel FROM pg_enum e
        JOIN pg_type t ON t.oid = e.enumtypid
        JOIN pg_namespace n ON n.oid = t.typnamespace
        WHERE t.typname = 'par_political_business_type' AND n.nspname = :schema
    '''
            ),
            {'schema': context.schema},
        ).scalars()
    )
    assert labels == set(POLITICAL_BUSINESS_TYPE)
    session.refresh(business)
    assert business.political_business_type == 'motion'


def test_ogi_multiple_agenda_businesses(
    org_app: TestOrgApp,
    tmp_path: Path,
) -> None:
    root = make_archive(tmp_path)
    original = root / 'political-business/unknown_10.json'
    other = json.loads(original.read_text().replace('2010-1', '2010-2'))
    other['metadata']['title'] = 'Beschluss zum Geschäft'
    (root / 'political-business/unknown_11.json').write_text(json.dumps(other))
    listing_path = root / 'lists/businesses.json'
    listing = json.loads(listing_path.read_text())
    listing['elements'].append(
        paragraph(link('Beschluss', 'information', '11'))
    )
    listing_path.write_text(json.dumps(listing))
    meeting_path = root / 'meetings/unknown_20.json'
    meeting = json.loads(meeting_path.read_text())
    meeting['elements'][-1]['rows'][0]['cells'][2] = paragraph(
        link('Antrag', 'information', '10'),
        {'type': 'Break'},
        link('Beschluss', 'information', '11'),
    )
    meeting_path.write_text(json.dumps(meeting))
    manifest_path = root / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['business_count'] = 2
    manifest_path.write_text(json.dumps(manifest))
    seal(root)
    archive = OGIArchive(root)
    session = org_app.session()
    archive.importer(session).run()
    item = session.query(MeetingItem).filter_by(number='01').one()
    assert {b.meta['self_id'] for b in item.political_businesses} == {
        '10',
        '11',
    }
    assert session.query(MeetingItem).count() == 3
    archive.importer(session).run()
    assert len(item.political_businesses) == 2
    assert session.query(MeetingItem).count() == 3


def test_ogi_adopts_existing_business_after_import(
    org_app: TestOrgApp,
    tmp_path: Path,
) -> None:
    archive = OGIArchive(make_archive(tmp_path))
    session = org_app.session()
    archive.importer(session).run()
    imported = session.query(PoliticalBusiness).one()
    original = PoliticalBusiness(
        title='Original business',
        number='I 2010-1 ',
        entry_date=date(2010, 1, 1),
        political_business_type='interpellation',
        meta={'custom': 'keep'},
    )
    session.add(original)
    session.flush()
    original_id = original.id
    source_id = imported.id
    counts = archive.importer(session).run()
    assert counts['merged'] == 1
    assert session.query(PoliticalBusiness).count() == 1
    assert original.id == original_id != source_id
    assert len(original.files) == 2
    assert len(original.participants) == 3
    assert len(original.agenda_items) == 2
    assert original.meta['custom'] == 'keep'
    assert all(
        item.political_business_id == original_id
        for item in session.query(MeetingItem).filter_by(
            political_business_link_id='10'
        )
    ), [
        (item.number, item.political_business_id, original_id)
        for item in session.query(MeetingItem)
    ]
    assert archive.importer(session).run().get('created', 0) == 0


def test_ogi_normalizes_historical_names_and_roles(
    org_app: TestOrgApp,
    tmp_path: Path,
) -> None:
    root = make_archive(tmp_path)
    path = root / 'political-business/unknown_10.json'
    data = json.loads(path.read_text())
    label = paragraph(text('Verfasser/Beteiligte'))
    index = data['elements'].index(label)
    data['elements'][index + 1]['children'].extend(
        [
            {'type': 'Break'},
            text('Francesca Schoch, FDP (Mitunterzeichner/in)'),
        ]
    )
    path.write_text(json.dumps(data))
    seal(root)
    archive = OGIArchive(root)
    session = org_app.session()
    archive.importer(session).run()
    business = session.query(PoliticalBusiness).one()
    old = RISParliamentarian(
        first_name='\u200bFrancesca',
        last_name='Schoch',
        meta={
            'parliamentarian_id': 'unlinked-old',
            'ogi_unresolved_name': '\u200bFrancesca Schoch',
        },
    )
    session.add(old)
    business.participants.append(
        PoliticalBusinessParticipation(
            parliamentarian=old, participant_type='Mitunterzeichner/in'
        )
    )
    business.meta = {
        **business.meta,
        'people_ids': [
            *business.meta['people_ids'],
            ('unlinked-old', 'Mitunterzeichner/in'),
        ],
    }
    person = (
        session.query(RISParliamentarian).filter_by(first_name='Bettina').one()
    )
    manual = PoliticalBusinessParticipation(
        parliamentarian=person, participant_type='First signatory'
    )
    business.participants.append(manual)
    session.flush()
    manual_id = manual.id
    counts = archive.importer(session).run()
    assert counts['merged_parliamentarians'] == 1
    assert session.query(RISParliamentarian).count() == 4
    assert len(business.participants) == 4
    assert session.get(PoliticalBusinessParticipation, manual_id)
    assert manual.participant_type == 'Erstunterzeichner/-in'
    assert archive.importer(session).run().get('created', 0) == 0


def test_ogi_misspelled_signatory_role(
    org_app: TestOrgApp, tmp_path: Path
) -> None:
    importer = OGIArchive(make_archive(tmp_path)).importer(org_app.session())
    records = importer.participants(
        paragraph(text('Pia Koefoed (Mitunterzeichenr/in)'))
    )
    assert len(records) == 1
    source, role = records[0]
    assert role == 'Mitunterzeichenr/in'
    person = importer.people[source]
    assert person.first_name == 'Pia'
    assert person.last_name == 'Koefoed'
