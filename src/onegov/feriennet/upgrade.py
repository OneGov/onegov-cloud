""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
# pragma: exclude file
from __future__ import annotations

import textwrap

from markupsafe import Markup
from onegov.core.upgrade import upgrade_task, UpgradeContext
from onegov.core.utils import module_path
from onegov.feriennet.models import NotificationTemplate
from onegov.feriennet.utils import NAME_SEPARATOR
from onegov.org.initial_content import load_content
from onegov.org.models import Organisation
from onegov.page import PageCollection
from onegov.user import UserCollection, User


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator


@upgrade_task('Install the default feriennet page structure 2')
def install_default_feriennet_page_structure(context: UpgradeContext) -> None:

    org = context.session.query(Organisation).first()

    if org is None:
        return

    # not a feriennet
    if '<registration />' not in org.meta['homepage_structure']:
        return

    org.meta['homepage_structure'] = textwrap.dedent("""\
        <row>
            <column span="8">
                <slider />
                <news />
            </column>
            <column span="4">
                <registration />

                <panel>
                    <links>
                        <link url="./personen"
                            description="Personen">
                            Team
                        </link>
                        <link url="./formular/kontakt"
                            description="Anfragen">
                            Kontakt
                        </link>
                        <link url="./aktuelles"
                            description="Neuigkeiten">
                            Aktuelles
                        </link>
                        <link url="./fotoalben"
                            description="Impressionen">
                            Fotoalben
                        </link>
                    </links>
                </panel>
            </column>
        </row>
    """)


@upgrade_task('Reinstate daily ticket status e-mail')
def reinstate_daily_ticket_status_email(context: UpgradeContext) -> None:
    org = context.session.query(Organisation).first()

    if org is None:
        return

    # not a feriennet
    if '<registration />' not in org.meta['homepage_structure']:
        return

    for user in UserCollection(context.session).by_roles('admin'):
        user.data = user.data or {}
        user.data['ticket_statistics'] = 'daily'


@upgrade_task('Change Periode to Zeitraum')
def change_period_to_zeitraum(context: UpgradeContext) -> None:
    templates = context.session.query(NotificationTemplate)

    for template in templates:
        template.subject = template.subject.replace('[Periode]', '[Zeitraum]')
        template.text = template.text.replace('[Periode]', '[Zeitraum]')


@upgrade_task('Remove extra space from user')
def remove_extra_space_from_user(context: UpgradeContext) -> None:
    org = context.session.query(Organisation).first()

    if org is None:
        return

    # not a feriennet
    if '<registration />' not in org.meta['homepage_structure']:
        return

    users = UserCollection(context.session).query()
    users = users.filter(User.realname.like('%{}%'.format(NAME_SEPARATOR)))

    for user in users:
        assert user.realname is not None
        user.realname = NAME_SEPARATOR.join(
            p.strip() for p in user.realname.split(NAME_SEPARATOR)
        )


@upgrade_task('Fix contact link')
def fix_contact_link(context: UpgradeContext) -> None:
    org = context.session.query(Organisation).first()

    if org is None:
        return

    # not a feriennet
    if '<registration />' not in org.meta['homepage_structure']:
        return

    org.meta['homepage_structure'] = org.meta['homepage_structure'].replace(
        './forms/', './form/')


@upgrade_task('Migrate bank payment rder type to reference schema')
def migrate_bank_settings(context: UpgradeContext) -> None:
    org = context.session.query(Organisation).first()

    if org is None:
        return

    # not a feriennet
    if '<registration />' not in org.meta['homepage_structure']:
        return

    if org.meta.get('bank_payment_order_type', 'basic') == 'basic':
        org.meta['bank_reference_schema'] = 'feriennet-v1'
    else:
        org.meta['bank_reference_schema'] = 'esr-v1'

    if 'bank_payment_order_type' in org.meta:
        del org.meta['bank_payment_order_type']


@upgrade_task('Add donation page')
def add_donation_page(context: UpgradeContext) -> None:

    org = context.session.query(Organisation).first()

    if org is None:
        return

    # not a feriennet
    if '<registration />' not in org.meta['homepage_structure']:
        return

    if org.locales == 'fr_CH':
        path = module_path('onegov.feriennet', 'content/fr.yaml')
    else:
        path = module_path('onegov.feriennet', 'content/de.yaml')

    page = next(
        p for p in load_content(path)['pages']
        if p['title'] in ('Spende', 'Dons')
    )

    pages = PageCollection(context.session)
    order = max(p.order for p in pages.roots) + 1

    meta = page.get('meta', {})
    meta['access'] = 'public'

    pages.add(
        parent=None,
        title=page['title'],
        type=page['type'],
        name=page.get('name', None),
        meta=meta,
        content=page.get('content', None),
        order=order
    )


def as_paragraphs(text: str) -> Iterator[Markup]:
    paragraph: list[str] = []

    for line in text.splitlines():
        if line.strip() == '':
            if paragraph:
                yield Markup('<p>{}</p>').format(
                    Markup('<br>').join(paragraph)
                )
                paragraph.clear()
        else:
            paragraph.append(line)

    if paragraph:
        yield Markup('<p>{}</p>').format(Markup('<br>').join(paragraph))


@upgrade_task('Convert text to html for notification templates 1')
def convert_text_to_html_for_notification_templates(
        context: UpgradeContext
) -> None:
    if context.has_column('notification_templates', 'text'):
        for template in context.session.query(NotificationTemplate):
            template.text = Markup('\n').join(as_paragraphs(template.text))

        context.session.flush()
