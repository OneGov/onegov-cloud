from collections import OrderedDict
from onegov.ballot.models.mixins import StatusMixin
from onegov.ballot.models.mixins import TitleTranslationsMixin
from onegov.core.orm import Base
from onegov.core.orm import translation_hybrid
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import meta_property
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import HSTORE
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import Text
from sqlalchemy_utils import observes
from sqlalchemy.orm import backref
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship


class ElectionComposite(
    Base, ContentMixin, TimestampMixin, StatusMixin, TitleTranslationsMixin
):

    __tablename__ = 'election_composites'

    #: Identifies the election composite, may be used in the url
    id = Column(Text, primary_key=True)

    #: all translations of the title
    title_translations = Column(HSTORE, nullable=False)

    #: the translated title (uses the locale of the request, falls back to the
    #: default locale of the app)
    title = translation_hybrid(title_translations)

    @observes('title_translations')
    def title_observer(self, translations):
        if not self.id:
            self.id = self.id_from_title(object_session(self))

    #: Shortcode for cantons that use it
    shortcode = Column(Text, nullable=True)

    #: The date of the elections
    date = Column(Date, nullable=False)

    @property
    def number_of_mandates(self):
        """ The (total) number of mandates. """

        return sum([
            election.number_of_mandates for election in self.elections
        ])

    @property
    def allocated_mandates(self):
        """ Number of already allocated mandates/elected candidates. """

        return sum([
            election.allocated_mandates for election in self.elections
        ])

    def counted(self):
        """ True if all results have been counted. """

        for election in self.elections:
            if not election.counted:
                return False

        return True

    @property
    def progress(self):
        """ Returns a tuple with the first value being the number of counted
        election results and the second value being the number of total
        results.

        """

        progresses = [election.progress for election in self.elections]
        return sum(p[0] for p in progresses), sum(p[1] for p in progresses)

    @property
    def has_results(self):
        """ Returns True, if the election has any results. """

        for election in self.elections:
            if election.has_results:
                return True

        return False

    #: An election composite contains n elections
    elections = relationship(
        'Election',
        backref=backref('composite'),
        lazy='dynamic',
        order_by='Election.shortcode',
    )

    @property
    def last_modified(self):
        """ Returns last change of the elections. """

        changes = [election.last_modified for election in self.elections]
        changes.append(self.last_change)
        changes = [change for change in changes if change]
        return max(changes) if changes else None

    @property
    def last_result_change(self):
        """ Returns the last change of the results of the elections. """

        changes = [election.last_result_change for election in self.elections]
        changes = [change for change in changes if change]
        return max(changes) if changes else None

    @property
    def elected_candidates(self):
        """ Returns the first and last names of the elected candidates. """

        result = []
        for election in self.elections:
            result.extend(election.elected_candidates)

        return result

    #: may be used to store a link related to this election
    related_link = meta_property('related_link')

    def clear_results(self):
        """ Clears all the results of all elections. """

        for election in self.elections:
            election.clear_results()

    def export(self):
        """ Returns all data connected to this election composite as list with
        dicts.

        This is meant as a base for json/csv/excel exports. The result is
        therefore a flat list of dictionaries with repeating values to avoid
        the nesting of values. Each record in the resulting list is a single
        candidate result for each political entity. Party results are not
        included in the export (since they are not really connected with the
        lists).

        """

        common = OrderedDict()
        for locale, title in self.title_translations.items():
            common['composite_title_{}'.format(locale)] = (title or '').strip()
        common['composite_date'] = self.date.isoformat()
        common['composite_mandates'] = self.number_of_mandates
        common['composite_status'] = self.stats

        rows = []
        for election in self.elections:
            for row in election.export():
                rows.append(OrderedDict(common.items() + row.items()))
