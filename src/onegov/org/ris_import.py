"""Repeatable imports of OGI Page JSON produced by the RIS scraper."""

import base64
import hashlib
import json
import re

from collections import Counter
from datetime import date, datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Any, TYPE_CHECKING
from zoneinfo import ZoneInfo

from markupsafe import escape
from onegov.core.html import sanitize_html
from onegov.core.orm.mixins import ContentMixin
from onegov.org.models import (
    Meeting,
    MeetingItem,
    PoliticalBusiness,
    PoliticalBusinessParticipation,
    RISCommission,
    RISCommissionMembership,
    RISParliamentarian,
    RISParliamentarianRole,
    RISParliamentaryGroup,
)
from onegov.org.models.file import GeneralFileCollection
from onegov.org.models.political_business import (
    POLITICAL_BUSINESS_STATUS,
    PoliticalBusinessType,
)

if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.parliament.models.parliamentarian_role import Role
    from sqlalchemy.orm import Session

SECTIONS: tuple[str, ...] = (
    'parliamentarians',
    'commissions',
    'parliamentary_groups',
    'political-business',
    'meetings',
)
KEYS: dict[str, str] = {
    'parliamentarians': 'parliamentarian_id',
    'commissions': 'commission_id',
    'parliamentary_groups': 'parliamentary_group_id',
    'political-business': 'self_id',
    'meetings': 'meeting_id',
}
BUSINESS_TYPES: dict[str, PoliticalBusinessType] = {
    'Anfrage': 'inquiry',
    'Bericht und Antrag': 'report and proposal',
    'Beschluss': 'decision',
    'Dringliche Interpellation': 'urgent interpellation',
    'Dringliche Motion': 'urgent motion',
    'Dringliches Postulat': 'urgent postulate',
    'Einladung': 'invitation',
    'Interpellation': 'interpellation',
    'Kommissionsbericht': 'commission report',
    'Motion': 'motion',
    'Parlamentarische Erklärung': 'parliamentary statement',
    'Petition': 'petition',
    'Postulat': 'postulate',
    'Protokoll': 'protocol',
    'Resolution': 'resolution',
    'Verschiedenes': 'miscellaneous',
    'Vorlage': 'draft',
    'Wahlen': 'election',
}
COUNCIL_ROLES: dict[str, Role] = {
    'Präsident': 'president',
    'Präsidentin': 'president',
    'Vizepräsident': 'vice_president',
    'Vizepräsidentin': 'vice_president',
    'Stimmenzähler': 'vote_counter',
    'Stimmenzählerin': 'vote_counter',
    'Stimmenzähler-Stellvertreter': 'vote_counter',
    'Stimmenzähler-Stellvertreterin': 'vote_counter',
    'Sekretär': 'none',
    'Sekretär-Stellvertreterin': 'none',
    'Protokollführerin': 'none',
    'Gemeindeschreiber': 'none',
}

MONTHS: dict[str, int] = {
    name: index
    for index, names in enumerate(
        (
            ('Januar', 'Jan'),
            ('Februar', 'Feb'),
            ('März', 'Mär'),
            ('April', 'Apr'),
            ('Mai',),
            ('Juni', 'Jun'),
            ('Juli', 'Jul'),
            ('August', 'Aug'),
            ('September', 'Sept', 'Sep'),
            ('Oktober', 'Okt'),
            ('November', 'Nov'),
            ('Dezember', 'Dez'),
        ),
        1,
    )
    for name in names
}
REFERENCE = re.compile(
    r'/(?:_rte/|_rtr/)(information|person|behoerde|anlass)[/_](\d+)'
)
FIELD_NAMES: set[str] = {
    'Nummer',
    'Geschäftsart',
    'Status',
    'Datum',
    'Beschreibung',
    'Verfasser/Beteiligte',
    'Beteiligte',
    'Fraktion',
    'Fraktionen',
    'Funktion',
    'Partei',
    'Beruf',
    'Ort',
    'Kontakt',
}


def walk(node: Any) -> Iterator[dict[str, Any]]:
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk(value)


def text(node: Any) -> str:
    if isinstance(node, list):
        return ' '.join(filter(None, (text(child) for child in node)))
    if not isinstance(node, dict):
        return ''
    return ' '.join(
        (node.get('text', '') or text(node.get('children', []))).split()
    )


def references(node: Any, kind: str) -> set[str]:
    return {
        match[2]
        for child in walk(node)
        if (match := REFERENCE.search(child.get('url', '')))
        and match[1] == kind
    }


def fields(page: dict[str, Any]) -> dict[str, Any]:
    elements = page['elements']
    return {
        text(element): elements[index + 1]
        for index, element in enumerate(elements[:-1])
        if text(element) in FIELD_NAMES
        and (
            element['type'] == 'Heading'
            or (
                element['type'] == 'Paragraph'
                and len(element.get('children', [])) == 1
                and element['children'][0]['type'] == 'Text'
            )
        )
    }


def tables(page: dict[str, Any]) -> Iterator[tuple[str, dict[str, Any]]]:
    heading = ''
    for element in page['elements']:
        if element['type'] == 'Heading':
            heading = text(element)
        if element['type'] == 'Table':
            headers = [text(header) for header in element['headers']]
            for row in element['rows']:
                yield heading, dict(zip(headers, row['cells']))


def parse_date(value: str) -> date | None:
    if not value.strip():
        return None
    if match := re.search(r'(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})', value):
        day, month, year = map(int, match.groups())
        return date(year, month, day)
    match = re.search(r'(\d{1,2})\.\s*(\w+)\.?\s+(\d{4})', value)
    if not match or match[2] not in MONTHS:
        raise ValueError(f'Unrecognised date: {value!r}')
    return date(int(match[3]), MONTHS[match[2]], int(match[1]))


def normalize_name(value: str) -> str:
    return ' '.join(value.replace('\u200b', '').replace('\ufeff', '').split())


def role_key(value: str | None) -> str:
    key = re.sub(r'[\s/-]', '', (value or '').casefold())
    if key.startswith('erstunterzeich') or key == 'firstsignatory':
        return 'first'
    if key.startswith('mitunterzeich') or key == 'cosignatory':
        return 'co'
    if key.startswith('verfasser') or key == 'author':
        return 'author'
    return key


def markup(node: Any) -> str:
    if isinstance(node, list):
        return ' '.join(markup(child) for child in node)
    if not isinstance(node, dict):
        return ''
    kind = node['type']
    value = str(escape(node.get('text', '')))
    children = markup(node.get('children', []))
    if kind == 'Text':
        if node.get('bold'):
            value = f'<strong>{value}</strong>'
        if node.get('italic'):
            value = f'<em>{value}</em>'
        return value
    if kind == 'Link':
        return str(
            sanitize_html(f'<a href="{escape(node["url"])}">{value}</a>')
        )
    if kind == 'Table':
        headers = ''.join(
            f'<th>{markup(header)}</th>' for header in node['headers']
        )
        rows = ''.join(
            '<tr>'
            + ''.join(f'<td>{markup(cell)}</td>' for cell in row['cells'])
            + '</tr>'
            for row in node['rows']
        )
        return f'<table><thead>{headers}</thead><tbody>{rows}</tbody></table>'
    if kind == 'Break':
        return '<br>'
    if kind == 'Heading':
        level = min(6, max(1, int(node.get('level', 2))))
        return f'<h{level}>{value}</h{level}>'
    tag = {
        'Paragraph': 'div',
        'ListItem': 'li',
        'UnorderedList': 'ul',
        'OrderedList': 'ol',
    }.get(kind)
    return f'<{tag}>{children}</{tag}>' if tag else ''


def safe_path(root: Path, name: str) -> Path:
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f'Invalid OGI archive path: {name}')
    return path


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def source_id(path: Path) -> str:
    return path.stem.rsplit('_', 1)[-1]


class OGIArchive:
    def __init__(self, path: Path, section: str | None = None) -> None:
        self.root = path.parent if section else path
        self.pages: dict[str, dict[str, dict[str, Any]]] = {
            name: {} for name in (*SECTIONS, 'lists')
        }
        self.assets: dict[str, dict[str, str]] = {}
        self.manifest: dict[str, Any] = {}
        self.unavailable: dict[str, int] = {}
        manifest_path = self.root / 'manifest.json'
        if manifest_path.is_file():
            self.manifest = json.loads(manifest_path.read_text())
            if self.manifest.get('format') != 'ogi-ris-1':
                raise ValueError('Expected an OGI RIS acquisition manifest')
            self.assets = self.manifest['assets']
            self.unavailable = self.manifest.get('unavailable_documents', {})
            if any(
                code not in (404, 410) for code in self.unavailable.values()
            ):
                raise ValueError('Unexpected document download failure')
            for name, checksum in self.manifest['files'].items():
                file = safe_path(self.root, name)
                if digest(file) != checksum:
                    raise ValueError(f'OGI page checksum mismatch: {name}')
                directory = Path(name).parent.name
                if directory not in self.pages:
                    raise ValueError(f'Unknown OGI section: {directory}')
                key = source_id(file) if directory != 'lists' else file.stem
                if key in self.pages[directory]:
                    raise ValueError(f'Duplicate OGI source ID: {name}')
                self.pages[directory][key] = json.loads(file.read_text())
            checked: set[str] = set()
            for asset in self.assets.values():
                name = asset['path']
                if name not in checked:
                    if digest(safe_path(self.root, name)) != asset['sha256']:
                        raise ValueError(f'Document checksum mismatch: {name}')
                    checked.add(name)
        elif section:
            for file in sorted(path.glob('*.json')):
                key = source_id(file)
                if key in self.pages[section]:
                    raise ValueError(f'Duplicate OGI source ID: {file}')
                self.pages[section][key] = json.loads(file.read_text())
        else:
            raise ValueError('Missing complete OGI acquisition manifest')
        self.validate()

    def validate(self) -> None:
        for pages in self.pages.values():
            for page in pages.values():
                if not page['metadata']['title'] or 'elements' not in page:
                    raise ValueError('Invalid OGI Page')
        businesses = self.pages['political-business']
        if self.manifest:
            listed = references(
                self.pages['lists']['businesses'], 'information'
            )
            if (
                listed != businesses.keys()
                or len(listed) != self.manifest['business_count']
            ):
                raise ValueError('Incomplete business acquisition')
        for page in businesses.values():
            data = fields(page)
            kind = text(data.get('Geschäftsart'))
            if kind not in BUSINESS_TYPES:
                raise ValueError(f'Unknown business type: {kind}')
            status = text(data.get('Status'))
            if status and status not in POLITICAL_BUSINESS_STATUS.values():
                raise ValueError(f'Unknown business status: {status}')
            entry = parse_date(text(data.get('Datum')))
            if self.manifest and (
                entry is None
                or entry < date.fromisoformat(self.manifest['since'])
            ):
                raise ValueError(f'Business outside cutoff: {entry}')
            if self.manifest:
                for kind, section in (
                    ('person', 'parliamentarians'),
                    ('anlass', 'meetings'),
                ):
                    missing = (
                        references(page, kind) - self.pages[section].keys()
                    )
                    if missing:
                        raise ValueError(f'Missing {kind} pages: {missing}')
        if self.manifest:
            for pages in self.pages.values():
                for page in pages.values():
                    for node in walk(page['elements']):
                        url = node.get('url', '')
                        if re.search(r'/_(?:doc|docn)/', url):
                            if (
                                url not in self.assets
                                and url not in self.unavailable
                            ):
                                raise ValueError(f'Missing document: {url}')
        for page in self.pages['meetings'].values():
            meeting_times(page)

    def importer(self, session: Session) -> OGIImporter:
        return OGIImporter(self, session)


def meeting_times(
    page: dict[str, Any],
) -> tuple[datetime, datetime | None]:
    timestamp = next(
        (
            text(el)
            for el in page['elements']
            if el['type'] == 'Paragraph' and re.match(r'^\d{1,2}\.', text(el))
        ),
        '',
    )
    day = parse_date(timestamp)
    if day is None:
        raise ValueError(f'Missing meeting date: {page["metadata"]["title"]}')
    times = re.findall(r'(\d{1,2})[.:](\d{2})\s*Uhr', timestamp)
    zone = ZoneInfo('Europe/Zurich')
    hour, minute = map(int, times[0]) if times else (0, 0)
    start = datetime(day.year, day.month, day.day, hour, minute, tzinfo=zone)
    end = None
    if len(times) > 1:
        hour, minute = map(int, times[1])
        end = datetime(day.year, day.month, day.day, hour, minute, tzinfo=zone)
        if end < start:
            end += timedelta(days=1)
    return start, end


class OGIImporter:
    def __init__(self, archive: OGIArchive, session: Session) -> None:
        self.archive = archive
        self.session = session
        self.counts: Counter[str] = Counter()
        self.people: dict[str, RISParliamentarian] = {}
        self.businesses: dict[str, PoliticalBusiness] = {}
        self.groups: dict[str, RISParliamentaryGroup] = {}
        self.commissions: dict[str, RISCommission] = {}
        self.active: set[str] = set()
        self.council: set[str] = set()
        self.council_functions: dict[str, str] = {}
        self.names: dict[str, str] = {}
        for name in ('people', 'council'):
            page = archive.pages['lists'].get(name, {'elements': []})
            ids = references(page, 'person')
            self.active.update(ids)
            if name == 'council':
                self.council.update(ids)
                for _heading, row in tables(page):
                    for source in references(row, 'person'):
                        self.council_functions[source] = text(
                            row.get('Funktion')
                        )
        for section in ('lists', 'commissions', 'parliamentary_groups'):
            for page in archive.pages[section].values():
                for node in walk(page['elements']):
                    match = REFERENCE.search(node.get('url', ''))
                    if match and match[1] == 'person':
                        self.names[match[2]] = text(node)
                        if section != 'lists':
                            self.active.add(match[2])

        eligible = set(self.active)
        businesses = archive.pages['political-business']
        for page in businesses.values():
            eligible.update(references(page, 'person'))
        for source, page in archive.pages['parliamentarians'].items():
            if references(page, 'information') & businesses.keys():
                eligible.add(source)
        for (meta,) in session.query(PoliticalBusiness.meta).filter(
            PoliticalBusiness.meta['self_id'].astext.in_(businesses)
        ):
            eligible.update(
                source for source, _role in meta.get('people_ids', [])
            )
        for person in session.query(RISParliamentarian):
            existing_source = person.meta.get('parliamentarian_id')
            if existing_source and (
                not archive.manifest or existing_source in eligible
            ):
                self.people[existing_source] = person

    def upsert[T: ContentMixin](
        self,
        model: type[T],
        source: str,
        key: str,
        identity: dict[str, Any] | None = None,
    ) -> T:
        query = self.session.query(model)
        obj = query.filter(
            model.meta[key].astext.in_((source, source + '.json'))
        ).one_or_none()
        if obj is None and identity:
            obj = (
                query.filter_by(**identity)
                .filter(model.meta[key].astext.is_(None))
                .one_or_none()
            )
        if obj is None:
            obj = model()
            self.session.add(obj)
            self.counts['created'] += 1
        else:
            self.counts['updated'] += 1
        obj.meta = {**(obj.meta or {}), key: source}
        return obj

    def attach(
        self, obj: PoliticalBusiness | Meeting, page: dict[str, Any]
    ) -> None:
        collection = GeneralFileCollection(self.session)
        urls = {
            node['url']
            for node in walk(page['elements'])
            if node.get('url') in self.archive.assets
        }
        imported = dict(obj.meta.get('ogi_documents', {}))
        for url in sorted(urls):
            asset = self.archive.assets[url]
            if imported.get(url) == asset['sha256']:
                continue
            path = safe_path(self.archive.root, asset['path'])
            content = BytesIO(path.read_bytes())
            file = collection.by_content(content).first()
            if file is None:
                content.seek(0)
                title = asset['title'] or url.rsplit('/', 1)[-1]
                if content.getvalue().startswith(
                    b'%PDF-'
                ) and not title.endswith('.pdf'):
                    title += '.pdf'
                file = collection.add(filename=title, content=content)
            if file not in obj.files:
                obj.files.append(file)
                self.counts['attachments'] += 1
            imported[url] = asset['sha256']
        obj.meta = {**obj.meta, 'ogi_documents': imported}

    def attach_images(
        self,
        business: PoliticalBusiness,
        page: dict[str, Any],
    ) -> None:
        images: dict[str, dict[str, str]] = {}
        collection = GeneralFileCollection(self.session)
        for node in walk(page['elements']):
            if node.get('type') != 'EmbeddedImage':
                continue
            encoded = node['content']
            data = base64.b64decode(encoded.split(',', 1)[1])
            checksum = hashlib.sha256(data).hexdigest()
            if checksum in images:
                continue
            content = BytesIO(data)
            file = collection.by_content(content).first()
            if file is None:
                content.seek(0)
                extension = (
                    'png' if encoded.startswith('data:image/png') else ('jpg')
                )
                file = collection.add(
                    filename=f'illustration.{extension}', content=content
                )
            if file not in business.files:
                business.files.append(file)
                self.counts['illustrations'] += 1
            images[checksum] = {
                'file_id': file.id,
                'alt': node.get('alt') or '',
            }
        business.meta = {**business.meta, 'ogi_images': list(images.values())}

    def import_people(self) -> None:
        linked: set[str] = set()
        businesses = self.archive.pages['political-business']
        for page in businesses.values():
            linked.update(references(page, 'person'))
        for source, page in self.archive.pages['parliamentarians'].items():
            if references(page, 'information') & businesses.keys():
                linked.add(source)
            if self.archive.manifest and source not in self.active | linked:
                self.counts['skipped_inactive'] += 1
                continue
            title = page['metadata']['title']
            first, _, last = title.partition(' ')
            parts = title.split()
            if len(parts) == 1:
                first, last = '', title
            listed = self.names.get(source, '').split()
            for split in range(1, len(parts)):
                if parts[split:] + parts[:split] == listed:
                    first, last = ' '.join(parts[:split]), ' '.join(
                        parts[split:]
                    )
                    break
            person = self.upsert(
                RISParliamentarian,
                source,
                'parliamentarian_id',
                {'first_name': first, 'last_name': last or first},
            )
            person.first_name, person.last_name = first, last or first
            data = fields(page)
            person.party = text(data.get('Partei'))
            person.occupation = text(data.get('Beruf'))
            contact: list[dict[str, Any]] = []
            for el in page['elements']:
                if el['type'] == 'Table':
                    break
                contact.append(el)
            for node in walk(contact):
                url = node.get('url', '')
                if url.startswith('mailto:'):
                    person.email_primary = url[7:].split('?', 1)[0]
                elif url.startswith('tel:'):
                    person.phone_business = text(node)
                elif '/ortsplan/' in url:
                    address = text(node)
                    match = re.search(r'(\d{4})\s+(.+)$', address)
                    if match:
                        person.private_address = address[
                            : match.start()
                        ].strip()
                        person.private_address_zip_code = match[1]
                        person.private_address_city = match[2]
            if not person.occupation:
                person.occupation = next(
                    (
                        text(el).split(', im Einwohnerrat')[0]
                        for el in contact
                        if ', im Einwohnerrat' in text(el)
                    ),
                    '',
                )
            person.content = {
                **(person.content or {}),
                'info': str(sanitize_html(markup(contact))),
            }
            interest_rows = [
                row
                for heading, row in tables(page)
                if heading == 'Interessenbindungen'
            ]
            if interest_rows:
                person.interests = {
                    'headers': list(interest_rows[0]),
                    'rows': [
                        {key: text(value) for key, value in row.items()}
                        for row in interest_rows
                    ],
                }
            for node in walk(page['elements']):
                if node['type'] == 'EmbeddedImage':
                    image = base64.b64decode(node['content'].split(',', 1)[1])
                    checksum = hashlib.sha256(image).hexdigest()
                    if person.meta.get('ogi_portrait') != checksum:
                        person.picture = (image, 'portrait.jpg')
                        person.meta = {**person.meta, 'ogi_portrait': checksum}
                    break
            marker = next(
                (role for role in person.roles if role.meta.get('ogi_active')),
                None,
            )
            if source in self.active:
                if marker is None:
                    marker = RISParliamentarianRole(meta={'ogi_active': True})
                    person.roles.append(marker)
                function = self.council_functions.get(source, '')
                marker.role = (
                    COUNCIL_ROLES.get(function, 'member')
                    if source in self.council
                    else 'none'
                )
                marker.additional_information = function or None
                marker.end = None
            elif marker is not None:
                person.roles.remove(marker)
                self.session.delete(marker)
            person.meta = {
                **person.meta,
                'ogi_active': source in self.active,
                'ogi_source_name': self.names.get(source, title),
            }
            self.people[source] = person
            self.counts['parliamentarians'] += 1
        self.session.flush()

    def import_bodies(self, section: str) -> None:
        for source, page in self.archive.pages[section].items():
            title = page['metadata']['title']
            if section == 'parliamentary_groups':
                group = self.upsert(
                    RISParliamentaryGroup,
                    source,
                    KEYS[section],
                    {'name': title},
                )
                self.groups[source] = group
                body: RISParliamentaryGroup | RISCommission = group
            else:
                body = self.upsert(
                    RISCommission, source, KEYS[section], {'name': title}
                )
                self.commissions[source] = body
            body.name = title
            body.description = sanitize_html(
                markup(
                    [el for el in page['elements'] if el['type'] != 'Table']
                )
            )
            members: list[tuple[str, str]] = []
            for _heading, row in tables(page):
                name = row.get('Name Vorname', row.get('Name', {}))
                function = text(row.get('Funktion'))
                members.extend(
                    (person_id, function)
                    for person_id in sorted(references(name, 'person'))
                )
            body.meta = {**body.meta, 'people_ids': members}
        self.session.flush()
        self.counts[section] = len(self.archive.pages[section])

    def plain_historical(self, person: RISParliamentarian) -> bool:
        identity = {
            'id',
            'type',
            'external_kub_id',
            'first_name',
            'last_name',
            'created',
            'modified',
            'meta',
            'content',
            'gender',
            'shipping_method',
        }
        return (
            set(person.meta) <= {'parliamentarian_id', 'ogi_unresolved_name'}
            and not person.content
            and not person.roles
            and not person.commission_memberships
            and not person.picture
            and person.gender == 'male'
            and person.shipping_method == 'a'
            and all(
                getattr(person, column.key) in (None, '')
                for column in RISParliamentarian.__mapper__.column_attrs
                if column.key not in identity
            )
        )

    def merge_person(
        self,
        target: RISParliamentarian,
        duplicate: RISParliamentarian,
    ) -> None:
        old = duplicate.meta['parliamentarian_id']
        source = target.meta['parliamentarian_id']
        for participation in list(duplicate.political_businesses):
            business = participation.political_business
            participation.parliamentarian = target
            business.meta = {
                **business.meta,
                'people_ids': [
                    (source if key == old else key, role)
                    for key, role in business.meta.get('people_ids', [])
                ],
            }
        self.people.pop(old, None)
        self.session.delete(duplicate)
        self.session.flush()
        self.counts['merged_parliamentarians'] += 1

    def historical_person(self, name: str) -> str:
        name = normalize_name(name.strip(' ,'))
        # Only exact, unique source names establish identity.
        matches = [
            person
            for person in self.people.values()
            if name.casefold()
            in (
                normalize_name(
                    f'{person.first_name} {person.last_name}'
                ).casefold(),
                normalize_name(
                    f'{person.last_name} {person.first_name}'
                ).casefold(),
            )
        ]
        if len(matches) > 1:
            clean = [
                person
                for person in matches
                if not any(
                    character in person.meta.get('ogi_unresolved_name', '')
                    for character in ('\u200b', '\ufeff')
                )
            ]
            target = (
                clean[0]
                if len(clean) == 1
                else (
                    min(
                        matches,
                        key=lambda person: person.meta['parliamentarian_id'],
                    )
                    if not clean
                    else None
                )
            )
            if target is not None:
                for duplicate in list(matches):
                    if duplicate == target:
                        continue
                    if (
                        duplicate.meta.get('ogi_unresolved_name')
                        and any(
                            c in duplicate.meta['ogi_unresolved_name']
                            for c in ('\u200b', '\ufeff')
                        )
                        and self.plain_historical(duplicate)
                    ):
                        self.merge_person(target, duplicate)
                        matches.remove(duplicate)
        if len(matches) == 1:
            person = matches[0]
            if person.meta.get('ogi_unresolved_name'):
                person.first_name = normalize_name(person.first_name)
                person.last_name = normalize_name(person.last_name)
                person.meta = {
                    **person.meta,
                    'ogi_unresolved_name': normalize_name(
                        person.meta['ogi_unresolved_name']
                    ),
                }
            return person.meta['parliamentarian_id']
        source = (
            'unlinked-'
            + hashlib.sha256(name.casefold().encode()).hexdigest()[:20]
        )
        if source not in self.people:
            first, _, last = name.partition(' ')
            person = self.upsert(
                RISParliamentarian, source, 'parliamentarian_id'
            )
            person.first_name, person.last_name = first, last or first
            person.meta = {**person.meta, 'ogi_unresolved_name': name}
            self.people[source] = person
        return source

    def participants(self, node: dict[str, Any]) -> list[tuple[str, str]]:
        pieces: list[str] = []
        for child in walk(node):
            if child['type'] == 'Link':
                link_ids = references(child, 'person')
                if link_ids:
                    pieces.append(f'@@{next(iter(link_ids))}@@')
                else:
                    pieces.append(text(child))
            elif child['type'] == 'Text':
                pieces.append(text(child))
            elif child['type'] == 'Break':
                pieces.append('\n')
        value = ' '.join(pieces)
        records: list[tuple[str, str]] = []
        for segment in re.split(r'\n|(?<=\))\s*,?\s*', value):
            segment = segment.strip(' ,')
            if not segment:
                continue
            role_match = re.search(
                r'\(?((?:Erst|Mit)unterzeich[^)]*|Verfasser[^)]*|'
                r'keine Funktion)\)?$',
                segment,
            )
            role = role_match[1] if role_match else ''
            name = segment[: role_match.start()] if role_match else segment
            name = name.strip(' (,')
            ids = re.findall(r'@@(\d+)@@', name)
            if ids:
                records.extend((source, role) for source in ids)
            elif name:
                parts = [part.strip() for part in name.split(',')]
                if len(parts) > 2:
                    name = f'{parts[1]} {parts[0]}'
                else:
                    name = parts[0]
                records.append((self.historical_person(name), role))
        return records

    def merge_business(
        self,
        target: PoliticalBusiness,
        duplicate: PoliticalBusiness,
    ) -> None:
        for file in duplicate.files:
            if file not in target.files:
                target.files.append(file)
        for group in duplicate.parliamentary_groups:
            if group not in target.parliamentary_groups:
                target.parliamentary_groups.append(group)
        for participant in list(duplicate.participants):
            participant.political_business = target
        for item in list(duplicate.meeting_items):
            item.political_business = target
        for item in list(duplicate.agenda_items):
            item.political_businesses = list(
                dict.fromkeys(
                    target if business == duplicate else business
                    for business in item.political_businesses
                )
            )
        target.meta = {**duplicate.meta, **target.meta}
        target.content = {**duplicate.content, **target.content}
        self.session.delete(duplicate)
        self.session.flush()
        self.counts['merged'] += 1

    def import_businesses(self, source_ids: set[str] | None = None) -> None:
        statuses = {
            value: key for key, value in POLITICAL_BUSINESS_STATUS.items()
        }
        untagged = (
            self.session.query(PoliticalBusiness)
            .filter(PoliticalBusiness.meta['self_id'].astext.is_(None))
            .all()
        )
        for source, page in self.archive.pages['political-business'].items():
            if source_ids is not None and source not in source_ids:
                continue
            data = fields(page)
            number = text(data.get('Nummer')) or None
            entry = parse_date(text(data.get('Datum')))
            kind = BUSINESS_TYPES[text(data.get('Geschäftsart'))]
            candidates = [
                business
                for business in untagged
                if not business.meta.get('self_id')
                and number
                and business.entry_date == entry
                and re.sub(
                    r'^(?:Nr\.?|[A-Z])\s*', '', (business.number or '').strip()
                )
                == number
                and business.political_business_type.removeprefix('urgent ')
                == kind.removeprefix('urgent ')
            ]
            if len(candidates) > 1:
                raise ValueError(f'Ambiguous existing business: {number}')
            if candidates:
                existing = (
                    self.session.query(PoliticalBusiness)
                    .filter(PoliticalBusiness.meta['self_id'].astext == source)
                    .one_or_none()
                )
                if existing is not None and existing != candidates[0]:
                    self.merge_business(candidates[0], existing)
                candidates[0].meta = {**candidates[0].meta, 'self_id': source}
            business = self.upsert(PoliticalBusiness, source, 'self_id')
            business.title = page['metadata']['title']
            business.number = text(data.get('Nummer')) or None
            business.entry_date = parse_date(text(data.get('Datum')))
            business.political_business_type = BUSINESS_TYPES[
                text(data.get('Geschäftsart'))
            ]
            business.status = statuses.get(text(data.get('Status')))
            business.chronology = str(
                sanitize_html(markup(data.get('Beschreibung', [])))
            )
            participants = data.get(
                'Verfasser/Beteiligte', data.get('Beteiligte', {})
            )
            records = self.participants(participants) if participants else []
            business.meta = {
                **business.meta,
                'people_ids': records,
                'parliamentary_group_ids': sorted(
                    references(
                        [data.get('Fraktion'), data.get('Fraktionen')],
                        'behoerde',
                    )
                ),
                'ogi_meeting_ids': sorted(references(page, 'anlass')),
                'ogi_source_fields': {
                    key: text(value) for key, value in data.items()
                },
            }
            self.attach(business, page)
            self.attach_images(business, page)
            self.businesses[source] = business
        # Participation is sometimes exposed only on the person's page.
        for person_id, page in self.archive.pages['parliamentarians'].items():
            if person_id not in self.people:
                continue
            for _heading, row in tables(page):
                for source in references(row, 'information'):
                    linked_business = self.businesses.get(source)
                    if linked_business is None:
                        continue
                    records = list(linked_business.meta['people_ids'])
                    if not any(key == person_id for key, _role in records):
                        records.append((person_id, text(row.get('Rolle'))))
                        linked_business.meta = {
                            **linked_business.meta,
                            'people_ids': records,
                        }
        self.session.flush()
        self.counts['political-business'] = len(self.businesses)

    def import_meetings(self) -> None:
        for source, page in self.archive.pages['meetings'].items():
            meeting = self.upsert(Meeting, source, 'meeting_id')
            meeting.title = page['metadata']['title']
            meeting.start_datetime, meeting.end_datetime = meeting_times(page)
            data = fields(page)
            meeting.address = sanitize_html(markup(data.get('Ort', [])))
            meeting.description = sanitize_html(
                markup(data.get('Beschreibung', []))
            )
            meeting.meta = {
                **meeting.meta,
                'ogi_business_ids': sorted(references(page, 'information')),
            }
            self.attach(meeting, page)
            agenda_business_ids: dict[str, list[str]] = {}
            for heading, row in tables(page):
                if heading != 'Traktanden':
                    continue
                number = text(row.get('Nr.', row.get('Nr', {}))) or None
                title = text(row.get('Bezeichnung'))
                item = next(
                    (
                        item
                        for item in meeting.meeting_items
                        if item.number == number
                        and (number is not None or item.title == title)
                    ),
                    None,
                )
                if item is None:
                    item = MeetingItem(number=number)
                    meeting.meeting_items.append(item)
                item.title = title
                ids = list(
                    dict.fromkeys(
                        match[2]
                        for node in walk(row.get('Geschäft', {}))
                        if (match := REFERENCE.search(node.get('url', '')))
                        and match[1] == 'information'
                    )
                )
                included = [
                    source
                    for source in ids
                    if source in self.archive.pages['political-business']
                ]
                item.political_business_link_id = next(
                    iter(included or ids), None
                )
                agenda_business_ids[number or title] = ids
                self.counts['agenda_items'] += 1
            meeting.meta = {
                **meeting.meta,
                'ogi_agenda_business_ids': agenda_business_ids,
            }
        self.session.flush()
        self.counts['meetings'] = len(self.archive.pages['meetings'])

    def run(
        self,
        section: str | None = None,
        business_ids: set[str] | None = None,
    ) -> dict[str, int]:
        if section in (None, 'parliamentarians'):
            self.import_people()
        if section in (None, 'commissions'):
            self.import_bodies('commissions')
        if section in (None, 'parliamentary_groups'):
            self.import_bodies('parliamentary_groups')
        if section in (None, 'political-business'):
            self.import_businesses(business_ids)
        if section in (None, 'meetings'):
            self.import_meetings()
        connect_relationships(
            self.session, set(self.people) if self.archive.manifest else None
        )
        self.session.flush()
        self.counts['unavailable_documents'] = len(self.archive.unavailable)
        return dict(self.counts)


def connect_relationships(
    session: Session,
    allowed_people: set[str] | None = None,
) -> None:
    people = {
        person.meta['parliamentarian_id']: person
        for person in session.query(RISParliamentarian)
        if person.meta.get('parliamentarian_id')
        and (
            allowed_people is None
            or person.meta['parliamentarian_id'] in allowed_people
        )
    }
    groups = {
        group.meta['parliamentary_group_id']: group
        for group in session.query(RISParliamentaryGroup)
        if group.meta.get('parliamentary_group_id')
    }
    businesses = {
        business.meta['self_id']: business
        for business in session.query(PoliticalBusiness)
        if business.meta.get('self_id')
    }
    for commission in session.query(RISCommission):
        for source, function in commission.meta.get('people_ids', []):
            person = people.get(source)
            if person is None:
                continue
            existing = next(
                (
                    membership
                    for membership in person.commission_memberships
                    if membership.commission_id == commission.id
                ),
                None,
            )
            if existing is None:
                person.commission_memberships.append(
                    RISCommissionMembership(
                        commission_id=commission.id,
                        function=function,
                        role=(
                            'president'
                            if function in ('Präsident', 'Präsidentin')
                            else 'member'
                        ),
                    )
                )
            else:
                existing.function = function
    for group in groups.values():
        for member in group.meta.get('people_ids', []):
            source, function = (
                member if isinstance(member, (list, tuple)) else (member, '')
            )
            person = people.get(source)
            if person is None:
                continue
            role = next(
                (
                    role
                    for role in person.roles
                    if role.parliamentary_group_id == group.id
                ),
                None,
            )
            if role is None:
                role = RISParliamentarianRole(parliamentary_group_id=group.id)
                person.roles.append(role)
            role.parliamentary_group_role = (
                'president'
                if function in ('Präsident', 'Präsidentin')
                else 'member'
            )
    for business in businesses.values():
        for source, function in business.meta.get('people_ids', []):
            person = people.get(source)
            if person is None:
                if allowed_people is not None:
                    raise ValueError(f'Missing participant: {source}')
                continue
            matches = [
                participation
                for participation in business.participants
                if participation.parliamentarian_id == person.id
                and role_key(participation.participant_type)
                == role_key(function)
            ]
            if matches:
                existing_participant = next(
                    (
                        p
                        for p in matches
                        if p.participant_type
                        in ('First signatory', 'Co-signatory', 'Author')
                    ),
                    matches[0],
                )
                existing_participant.participant_type = function
                for duplicate in matches:
                    if duplicate != existing_participant:
                        existing_participant.meta = {
                            **duplicate.meta,
                            **existing_participant.meta,
                        }
                        business.participants.remove(duplicate)
                        session.delete(duplicate)
            else:
                business.participants.append(
                    PoliticalBusinessParticipation(
                        parliamentarian_id=person.id,
                        participant_type=function,
                    )
                )
        for source in business.meta.get('parliamentary_group_ids', []):
            linked_group = groups.get(source)
            if (
                linked_group is not None
                and linked_group not in business.parliamentary_groups
            ):
                business.parliamentary_groups.append(linked_group)
    for item in session.query(MeetingItem):
        ids = item.meeting.meta.get('ogi_agenda_business_ids', {}).get(
            item.number or item.title
        )
        if ids is not None:
            item.political_businesses = [
                businesses[source] for source in ids if source in businesses
            ]
        linked_business = businesses.get(item.political_business_link_id or '')
        if linked_business is not None:
            item.political_business = linked_business
