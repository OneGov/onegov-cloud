from onegov.chat import MessageCollection
from onegov.gazette import _
from onegov.gazette.models import GazetteNotice
from onegov.notice import OfficialNoticeCollection
from uuid import uuid4


TRANSLATIONS = {
    'drafted': _("drafted"),
    'submitted': _("submitted"),
    'rejected': _("rejected"),
    'published': _("published"),
}


class GazetteNoticeCollection(OfficialNoticeCollection):
    """ Manage a list of gazette specific official notices. """

    def query(self):
        query = self.session.query(GazetteNotice)
        if self.state:
            query = query.filter(GazetteNotice.state == self.state)
        return query

    def add(self, title, text, category, issues, user_id):
        """ Add a new notice.

        A unique, URL-friendly name is created automatically for this notice
        using the title and optionally numbers for duplicate names.

        A entry is added automatically to the audit trail.

        Returns the created notice.
        """

        notice = GazetteNotice(
            id=uuid4(),
            state='drafted',
            title=title,
            name=self._get_unique_name(title),
            category=category,
            user_id=user_id
        )
        notice.text = text
        notice.issues = issues
        self.session.add(notice)
        self.session.flush()

        audit_trail = MessageCollection(self.session, type='gazette_notice')
        audit_trail.add(
            channel_id=str(notice.id),
            owner=str(user_id),
            text=_("created")
        )

        return notice
