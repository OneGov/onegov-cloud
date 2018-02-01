""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
import textwrap

from onegov.core.upgrade import upgrade_task
from onegov.feriennet.models import NotificationTemplate
from onegov.feriennet.utils import NAME_SEPARATOR
from onegov.org.models import Organisation
from onegov.user import UserCollection, User


@upgrade_task('Install the default feriennet page structure 2')
def install_default_feriennet_page_structure(context):

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
def reinstate_daily_ticket_status_email(context):
    org = context.session.query(Organisation).first()

    if org is None:
        return

    # not a feriennet
    if '<registration />' not in org.meta['homepage_structure']:
        return

    for user in UserCollection(context.session).by_roles('admin'):
        user.data = user.data or {}
        user.data['daily_ticket_statistics'] = True


@upgrade_task('Change Periode to Zeitraum')
def change_period_to_zeitraum(context):
    templates = context.session.query(NotificationTemplate)

    for template in templates:
        template.subject = template.subject.replace('[Periode]', '[Zeitraum]')
        template.text = template.text.replace('[Periode]', '[Zeitraum]')


@upgrade_task('Remove extra space from user')
def remove_extra_space_from_user(context):
    org = context.session.query(Organisation).first()

    if org is None:
        return

    # not a feriennet
    if '<registration />' not in org.meta['homepage_structure']:
        return

    users = UserCollection(context.session).query()
    users = users.filter(User.realname.like('%{}%'.format(NAME_SEPARATOR)))

    for user in users:
        user.realname = NAME_SEPARATOR.join(
            p.strip() for p in user.realname.split(NAME_SEPARATOR)
        )


@upgrade_task('Fix contact link')
def fix_contact_link(context):
    org = context.session.query(Organisation).first()

    if org is None:
        return

    # not a feriennet
    if '<registration />' not in org.meta['homepage_structure']:
        return

    org.meta['homepage_structure'] = org.meta['homepage_structure'].replace(
        './forms/', './form/')
