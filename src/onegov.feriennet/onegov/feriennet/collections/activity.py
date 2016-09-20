from onegov.activity import Activity, ActivityCollection
from sqlalchemy import or_


class VacationActivityCollection(ActivityCollection):

    def __init__(self, session, user=None, page=0):
        super().__init__(session, type='vacation', page=page)
        self.user = user

    def subset(self):
        """ Limits the pagination results to activites visible by the
        current user.

        """
        if self.user is None or self.user.role == 'member':
            return self.public_subset()
        else:
            return self.private_subset()

    def public_subset(self):
        return super().subset().filter(Activity.state == 'accepted')

    def private_subset(self):
        return super().subset().filter(or_(
            Activity.state == 'accepted',
            Activity.username == self.user.username
        ))

    def page_by_index(self, index):
        return self.__class__(self.session, self.user, page=index)
