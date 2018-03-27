from freezegun import freeze_time
from io import StringIO
from onegov.election_day.tests.utils import add_election_compound
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
            generator.generate_svg(item, 'parties-panachage', 'de_CH')
            generator.generate_svg(item, 'lists-panachage', 'de_CH')
            generator.generate_svg(item, 'map', 'de_CH')

            item = add_proporz_election(session)
            generator.generate_svg(item, 'lists', 'de_CH')
            generator.generate_svg(item, 'candidates', 'de_CH')
            generator.generate_svg(item, 'connections', 'de_CH')
            generator.generate_svg(item, 'party-strengths', 'de_CH')
            generator.generate_svg(item, 'parties-panachage', 'de_CH')
            generator.generate_svg(item, 'lists-panachage', 'de_CH')
            generator.generate_svg(item, 'map', 'de_CH')

            item = add_election_compound(session)
            generator.generate_svg(item, 'lists', 'de_CH')
            generator.generate_svg(item, 'candidates', 'de_CH')
            generator.generate_svg(item, 'connections', 'de_CH')
            generator.generate_svg(item, 'party-strengths', 'de_CH')
            generator.generate_svg(item, 'parties-panachage', 'de_CH')
            generator.generate_svg(item, 'lists-panachage', 'de_CH')
            generator.generate_svg(item, 'map', 'de_CH')

            item = add_vote(session, 'complex').proposal
            generator.generate_svg(item, 'lists', 'de_CH')
            generator.generate_svg(item, 'candidates', 'de_CH')
            generator.generate_svg(item, 'connections', 'de_CH')
            generator.generate_svg(item, 'party-strengths', 'de_CH')
            generator.generate_svg(item, 'parties-panachage', 'de_CH')
            generator.generate_svg(item, 'lists-panachage', 'de_CH')
            generator.generate_svg(item, 'map', 'de_CH')
            generator.generate_svg(item, 'map', 'it_CH')

        with freeze_time("2015-05-05 15:00"):
            generator.generate_svg(item, 'map', 'it_CH')

        assert gc.call_count == 12  # 2 + 6 + 2 + 2 + 0

        ts = '1396620000'
        hm = '41c18975bf916862ed817b7c569b6f242ca7ad9f86ca73bbabd8d9cb26858440'
        hp = '624b5f68761f574adadba4145283baf97f21e2bd8b87d054b57d936dac6dedff'
        hc = '9130b66132f65a4d5533fecad8cdf1f9620a42733d6dfd7d23ea123babecf4c7'
        hb = item.id
        assert sorted(election_day_app.filestorage.listdir('svg')) == sorted([
            f'election-{hm}.{ts}.candidates.de_CH.svg',
            f'election-{hm}.{ts}.candidates.any.svg',
            f'election-{hp}.{ts}.lists.de_CH.svg',
            f'election-{hp}.{ts}.candidates.de_CH.svg',
            f'election-{hp}.{ts}.connections.de_CH.svg',
            f'election-{hp}.{ts}.party-strengths.de_CH.svg',
            f'election-{hp}.{ts}.parties-panachage.de_CH.svg',
            f'election-{hp}.{ts}.lists-panachage.de_CH.svg',
            f'election-{hc}.{ts}.party-strengths.de_CH.svg',
            f'election-{hc}.{ts}.parties-panachage.de_CH.svg',
            f'ballot-{hb}.{ts}.map.de_CH.svg',
            f'ballot-{hb}.{ts}.map.it_CH.svg'
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

        majorz = add_majorz_election(session)
        proporz = add_proporz_election(session)
        compound = add_election_compound(session)
        vote = add_vote(session, 'complex')

        generator.create_svgs()
        assert gc.call_count == 21
        assert len(fs.listdir('svg')) == 21

        generator.create_svgs()
        assert gc.call_count == 21
        assert len(fs.listdir('svg')) == 21

        fs.touch('svg/somefile')
        fs.touch('svg/some.file')
        fs.touch('svg/.somefile')

        generator.create_svgs()
        assert gc.call_count == 21
        assert len(fs.listdir('svg')) == 21

        session.delete(vote)
        session.delete(proporz)
        session.delete(compound)
        session.flush()

        generator.create_svgs()
        assert gc.call_count == 21
        assert len(fs.listdir('svg')) == 1

        majorz.title = 'Election'
        session.flush()

        generator.create_svgs()
        assert gc.call_count == 22
        assert len(fs.listdir('svg')) == 1

        session.delete(majorz)
        session.flush()

        generator.create_svgs()
        assert gc.call_count == 22
        assert len(fs.listdir('svg')) == 0
