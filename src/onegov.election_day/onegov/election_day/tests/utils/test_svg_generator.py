from freezegun import freeze_time
from io import StringIO
from onegov.election_day.tests.utils import add_majorz_election
from onegov.election_day.tests.utils import add_proporz_election
from onegov.election_day.tests.utils import add_vote
from onegov.election_day.tests.utils import PatchedD3Renderer
from onegov.election_day.utils.svg_generator import SvgGenerator
from pytest import raises
from unittest.mock import patch


class PatchedSvgGenerator(SvgGenerator):
    def __init__(self, app):
        super(PatchedSvgGenerator, self).__init__(app)
        self.renderer = PatchedD3Renderer(app)


def test_generate_svg(election_day_app, session):

    generator = SvgGenerator(election_day_app)

    with raises(AttributeError):
        generator.generate_svg(None, 'things', 'de_CH')

    svg = StringIO('<svg></svg>')
    with patch.object(generator.renderer, 'get_chart', return_value=svg) as gc:

        with freeze_time("2014-04-04 14:00"):
            item = add_majorz_election(session)
            generator.generate_svg(item, 'lists', 'de_CH')
            generator.generate_svg(item, 'candidates', 'de_CH')
            generator.generate_svg(item, 'candidates')
            generator.generate_svg(item, 'connections', 'de_CH')
            generator.generate_svg(item, 'party-strengths', 'de_CH')
            generator.generate_svg(item, 'lists-panachage', 'de_CH')
            generator.generate_svg(item, 'map', 'de_CH')

            item = add_proporz_election(session)
            generator.generate_svg(item, 'lists', 'de_CH')
            generator.generate_svg(item, 'candidates', 'de_CH')
            generator.generate_svg(item, 'connections', 'de_CH')
            generator.generate_svg(item, 'party-strengths', 'de_CH')
            generator.generate_svg(item, 'lists-panachage', 'de_CH')
            generator.generate_svg(item, 'map', 'de_CH')

            item = add_vote(session, 'complex').proposal
            generator.generate_svg(item, 'lists', 'de_CH')
            generator.generate_svg(item, 'candidates', 'de_CH')
            generator.generate_svg(item, 'connections', 'de_CH')
            generator.generate_svg(item, 'party-strengths', 'de_CH')
            generator.generate_svg(item, 'lists-panachage', 'de_CH')
            generator.generate_svg(item, 'map', 'de_CH')
            generator.generate_svg(item, 'map', 'it_CH')

        with freeze_time("2015-05-05 15:00"):
            generator.generate_svg(item, 'map', 'it_CH')

        assert gc.call_count == 9  # 2 + 5 + 2 + 0

        ts = '1396620000'
        h1 = '41c18975bf916862ed817b7c569b6f242ca7ad9f86ca73bbabd8d9cb26858440'
        h2 = '624b5f68761f574adadba4145283baf97f21e2bd8b87d054b57d936dac6dedff'
        h3 = item.id
        assert sorted(election_day_app.filestorage.listdir('svg')) == sorted([
            'election-{}.{}.candidates.de_CH.svg'.format(h1, ts),
            'election-{}.{}.candidates.any.svg'.format(h1, ts),
            'election-{}.{}.lists.de_CH.svg'.format(h2, ts),
            'election-{}.{}.candidates.de_CH.svg'.format(h2, ts),
            'election-{}.{}.connections.de_CH.svg'.format(h2, ts),
            'election-{}.{}.party-strengths.de_CH.svg'.format(h2, ts),
            'election-{}.{}.lists-panachage.de_CH.svg'.format(h2, ts),
            'ballot-{}.{}.map.de_CH.svg'.format(h3, ts),
            'ballot-{}.{}.map.it_CH.svg'.format(h3, ts)
        ])


def test_create_svgs(election_day_app):
    generator = SvgGenerator(election_day_app)
    session = election_day_app.session()
    fs = election_day_app.filestorage

    svg = StringIO('<svg></svg>')
    with patch.object(generator.renderer, 'get_chart', return_value=svg) as gc:

        generator.create_svgs()
        assert gc.call_count == 0
        assert election_day_app.filestorage.listdir('svg') == []

        majorz_election = add_majorz_election(session)
        proporz_election = add_proporz_election(session)
        vote = add_vote(session, 'complex')

        generator.create_svgs()
        assert gc.call_count == 18
        assert len(fs.listdir('svg')) == 18

        generator.create_svgs()
        assert gc.call_count == 18
        assert len(fs.listdir('svg')) == 18

        fs.touch('svg/somefile')
        fs.touch('svg/some.file')
        fs.touch('svg/.somefile')

        generator.create_svgs()
        assert gc.call_count == 18
        assert len(fs.listdir('svg')) == 18

        session.delete(vote)
        session.delete(proporz_election)
        session.flush()

        generator.create_svgs()
        assert gc.call_count == 18
        assert len(fs.listdir('svg')) == 1

        majorz_election.title = 'Election'
        session.flush()

        generator.create_svgs()
        assert gc.call_count == 19
        assert len(fs.listdir('svg')) == 1

        session.delete(majorz_election)
        session.flush()

        generator.create_svgs()
        assert gc.call_count == 19
        assert len(fs.listdir('svg')) == 0
