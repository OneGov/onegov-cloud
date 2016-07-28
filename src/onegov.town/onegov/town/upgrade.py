""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
import lxml
import re

from base64 import b64decode
from json import loads, dumps
from onegov.core.orm import find_models
from onegov.core.orm.abstract import sort_siblings
from onegov.core.orm.mixins import ContentMixin
from onegov.core.upgrade import upgrade_task
from onegov.form import FormCollection, FormDefinition
from onegov.libres import ResourceCollection
from onegov.page import PageCollection
from onegov.people import Person
from onegov.town import TownApp
from onegov.town.initial_content import add_resources
from onegov.town.models.extensions import ContactExtension
from onegov.town.models.file import (
    GeneralFileCollection,
    ImageFile,
    ImageFileCollection
)
from pytz import utc


@upgrade_task('Add initial libres resources')
def add_initial_libres_resources(context):
    if isinstance(context.app, TownApp):
        add_resources(context.app.libres_context)


@upgrade_task('Add order to all pages')
def add_order_to_all_pages(context):
    pages = PageCollection(context.session)
    processed_siblings = set()

    for page in pages.query(ordered=False):
        siblings = page.siblings.all()

        ids = {sibling.id for sibling in siblings}
        if ids <= processed_siblings:
            continue

        sort_siblings(siblings, key=PageCollection.sort_key)

        processed_siblings.update(ids)


@upgrade_task('Update contact html')
def change_contact_html(context):
    items = []

    items.extend(PageCollection(context.session).query().all())
    items.extend(FormCollection(context.session).definitions.query().all())

    if isinstance(context.app, TownApp):
        items.extend(
            ResourceCollection(context.app.libres_context).query().all()
        )

    for item in items:
        if not isinstance(item, ContactExtension):
            continue
        if not item.contact:
            continue

        # forces a re-render of the contact html
        item.contact = item.contact


@upgrade_task('Convert builtin forms into custom forms')
def convert_builtin_forms(context):
    forms = FormCollection(context.session)

    query = forms.definitions.query()
    query = query.filter(FormDefinition.type == 'builtin')
    query.update({FormDefinition.type: 'custom'})


@upgrade_task('Migrate images/files to onegov.file')
def migrate_images_file_to_onegov_file(context):

    request, app = context.request, context.app

    mapping = {
        'images': ImageFileCollection(context.app.session()),
        'files': GeneralFileCollection(context.app.session())
    }

    for folder, collection in mapping.items():
        if not app.filestorage.isdir(folder):
            continue

        storage = app.filestorage.opendir(folder)
        rewrite = []

        for filename in storage.listdir(files_only=True):
            if filename.endswith('.r'):
                continue

            if '-' in filename:
                name = filename.split('-')[0].strip()
                name = b64decode(name).decode('utf-8')
            else:
                name = filename

            with storage.open(filename, mode='rb') as f:
                try:
                    new_file = collection.add(name, content=f)
                except FileExistsError as e:
                    new_file = e.args[0]

            with storage.open(filename + '.r', mode='w') as f:
                f.write(new_file.id)

            fileinfo = storage.getinfo(filename)
            new_file.created = fileinfo['created_time'].replace(tzinfo=utc)
            new_file.modified = fileinfo['modified_time'].replace(tzinfo=utc)

            old_url = request.filestorage_link('/'.join((folder, filename)))
            new_url = request.link(new_file)

            # only work with the last two parts of the url, as the front with
            # the domain may be different during the upgrade
            old_url = '/'.join(old_url.split('/')[-2:])
            new_url = '/'.join(new_url.split('/')[-2:])

            # adjust the prefix of the paths which was different when the
            # paths for it were still configured by onegov.town
            old_url = old_url.replace('images/', 'bild/')
            old_url = old_url.replace('files/', 'datei/')

            rewrite.append((old_url, new_url))

        # update all records with a meta/content mixin
        def is_match(cls):
            return issubclass(cls, ContentMixin)

        for base in app.session_manager.bases:
            for cls in find_models(base, is_match):
                for item in app.session().query(cls).all():
                    meta, content = dumps(item.meta), dumps(item.content)

                    for old, new in rewrite:
                        meta = meta.replace(old, new)
                        content = content.replace(old, new)

                    item.meta = loads(meta)
                    item.content = loads(content)

        # update the theme options
        town = app.load_town()
        theme_options = dumps(town.theme_options)

        for old, new in rewrite:
            theme_options = theme_options.replace(old, new)

        town.theme_options = loads(theme_options)

        # update the people images
        for person in app.session().query(Person).all():
            for old, new in rewrite:
                person.picture_url = person.picture_url.replace(old, new)


@upgrade_task('Migrate alt text',
              requires='onegov.town:Migrate images/files to onegov.file')
def migrate_alt_text(context):

    app = context.app
    url_expression = re.compile(r'^.*/storage/([a-z0-9]{64})/?.*$')

    # find all possible alt texts and transfer them to onegov.file
    def is_match(cls):
        return issubclass(cls, ContentMixin)

    items = []

    for base in app.session_manager.bases:
        for cls in find_models(base, is_match):
            for item in app.session().query(cls).all():
                if getattr(item, 'text', None):
                    items.append(item)

    alts = {}

    for item in items:
        html = lxml.html.fromstring(item.text)
        for img in html.xpath('//img'):
            src = (img.get('src') or '').strip()

            if not src:
                continue

            # check if it's one of the internal images
            match = url_expression.match(src)

            if not match:
                continue

            # remember the alt text for each image
            if img.get('alt'):
                fid = match.group(1)
                alts[fid] = img.get('alt')
                img.set('alt', '')

            # load the alt text lazily from now on (might be added later)
            img.set('class', 'lazyload-alt')

        item.text = lxml.html.tostring(html).decode('utf-8')

    if not alts:
        return

    query = ImageFileCollection(app.session()).query()
    query = query.filter(ImageFile.id.in_(alts.keys()))
    files = {f.id: f for f in query.all()}

    for fid in alts:
        if fid in files:
            files[fid].note = alts[fid]
