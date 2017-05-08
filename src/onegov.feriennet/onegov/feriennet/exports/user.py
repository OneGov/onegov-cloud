from onegov.core.security import Secret
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.exports.base import FeriennetExport
from onegov.org.forms import ExportForm
from onegov.user import UserCollection


@FeriennetApp.export(
    id='benutzer',
    form_class=ExportForm,
    permission=Secret,
    title=_("Users"),
    explanation=_("Exports user accounts."),
)
class UserExport(FeriennetExport):

    def run(self, form, session):
        return self.rows(session)

    def query(self, session):
        return UserCollection(session).query()

    def rows(self, session):
        for user in self.query(session):
            yield ((k, v) for k, v in self.fields(user))

    def fields(self, user):
        yield from self.user_fields(user)
