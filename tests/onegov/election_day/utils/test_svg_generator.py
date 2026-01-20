from __future__ import annotations

from datetime import timedelta
from freezegun import freeze_time
from io import StringIO
from onegov.election_day.models import ElectionCompoundPart
from onegov.election_day.utils import svg_filename
from onegov.election_day.utils.svg_generator import SvgGenerator
from tests.onegov.election_day.utils.common import add_election_compound
from tests.onegov.election_day.utils.common import add_majorz_election
from tests.onegov.election_day.utils.common import add_proporz_election
from tests.onegov.election_day.utils.common import add_vote
from tests.onegov.election_day.utils.common import PatchedD3Renderer
from unittest.mock import patch
from pytest import mark


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from ..conftest import TestApp


class PatchedSvgGenerator(SvgGenerator):
    def __init__(self, app: TestApp) -> None:
        super().__init__(app)
        self.renderer = PatchedD3Renderer(app)


@mark.flaky(reruns=3, only_rerun=None)
def test_generate_svg(
    election_day_app_gr: TestApp,
    session: Session
) -> None:

    assert election_day_app_gr.filestorage is not None
    election_day_app_gr.filestorage.makedir('svg')
    generator = SvgGenerator(election_day_app_gr)

    def generate(item: Any, type_: str, locale: str) -> int:
        filename = svg_filename(item, type_, locale)
        return generator.generate_svg(item, type_, filename, locale)

    item: object
    svg = StringIO('<svg></svg>')
    with patch.object(generator.renderer, 'get_chart', return_value=svg) as gc:

        with freeze_time("2014-04-04 14:00"):
            item = add_majorz_election(session)
            assert generate(item, 'lists', 'de_CH') == 0
            assert generate(item, 'candidates', 'de_CH') == 1
            assert generate(item, 'candidates', 'fr_CH') == 1
            assert generate(item, 'connections', 'de_CH') == 0
            assert generate(item, 'seat-allocation', 'de_CH') == 0
            assert generate(item, 'party-strengths', 'de_CH') == 0
            assert generate(item, 'parties-panachage', 'de_CH') == 0
            assert generate(item, 'lists-panachage', 'de_CH') == 0
            assert generate(item, 'entities-map', 'de_CH') == 0
            assert generate(item, 'districts-map', 'de_CH') == 0

            item = add_proporz_election(session)
            assert generate(item, 'lists', 'de_CH') == 1
            assert generate(item, 'candidates', 'de_CH') == 1
            assert generate(item, 'connections', 'de_CH') == 1
            assert generate(item, 'seat-allocation', 'de_CH') == 1
            assert generate(item, 'party-strengths', 'de_CH') == 1
            assert generate(item, 'parties-panachage', 'de_CH') == 1
            assert generate(item, 'lists-panachage', 'de_CH') == 1
            assert generate(item, 'entities-map', 'de_CH') == 0
            assert generate(item, 'districts-map', 'de_CH') == 0

            item = add_election_compound(
                session, elections=[item], pukelsheim=True,
            )
            item.horizontal_party_stengths = True  # type: ignore[attr-defined]
            assert generate(item, 'list-groups', 'de_CH') == 1
            assert generate(item, 'lists', 'de_CH') == 0
            assert generate(item, 'candidates', 'de_CH') == 0
            assert generate(item, 'connections', 'de_CH') == 0
            assert generate(item, 'seat-allocation', 'de_CH') == 1
            assert generate(item, 'party-strengths', 'de_CH') == 1
            assert generate(item, 'parties-panachage', 'de_CH') == 1
            assert generate(item, 'lists-panachage', 'de_CH') == 0
            assert generate(item, 'entities-map', 'de_CH') == 0
            assert generate(item, 'districts-map', 'de_CH') == 0

            item = ElectionCompoundPart(item, 'superregion', 'Region 1')
            party_result = item.election_compound.party_results[0]
            party_result.domain = 'superregion'
            party_result.domain_segment = 'Region 1'
            assert generate(item, 'list-groups', 'de_CH') == 0
            assert generate(item, 'lists', 'de_CH') == 0
            assert generate(item, 'candidates', 'de_CH') == 0
            assert generate(item, 'connections', 'de_CH') == 0
            assert generate(item, 'seat-allocation', 'de_CH') == 0
            assert generate(item, 'party-strengths', 'de_CH') == 1
            assert generate(item, 'parties-panachage', 'de_CH') == 0
            assert generate(item, 'lists-panachage', 'de_CH') == 0
            assert generate(item, 'entities-map', 'de_CH') == 0
            assert generate(item, 'districts-map', 'de_CH') == 0

            item = add_vote(session, 'complex').proposal
            assert generate(item, 'lists', 'de_CH') == 0
            assert generate(item, 'candidates', 'de_CH') == 0
            assert generate(item, 'connections', 'de_CH') == 0
            assert generate(item, 'seat-allocation', 'de_CH') == 0
            assert generate(item, 'party-strengths', 'de_CH') == 0
            assert generate(item, 'parties-panachage', 'de_CH') == 0
            assert generate(item, 'lists-panachage', 'de_CH') == 0
            assert generate(item, 'entities-map', 'de_CH') == 1
            assert generate(item, 'districts-map', 'de_CH') == 1
            assert generate(item, 'entities-map', 'it_CH') == 1
            assert generate(item, 'entities-map', 'it_CH') == 1

        with freeze_time("2015-05-05 15:00"):
            assert generate(item, 'map', 'it_CH') == 0

        assert gc.call_count == 18

        ts = '1396620000'
        hm = '41c18975bf916862ed817b7c569b6f242ca7ad9f86ca73bbabd8d9cb26858440'
        hp = '624b5f68761f574adadba4145283baf97f21e2bd8b87d054b57d936dac6dedff'
        hc = '9130b66132f65a4d5533fecad8cdf1f9620a42733d6dfd7d23ea123babecf4c7'
        hb = item.id
        files = election_day_app_gr.filestorage.listdir('svg')
        assert sorted(files) == sorted([
            f'election-{hm}.{ts}.candidates.de_CH.svg',
            f'election-{hm}.{ts}.candidates.fr_CH.svg',
            f'election-{hp}.{ts}.lists.de_CH.svg',
            f'election-{hp}.{ts}.candidates.de_CH.svg',
            f'election-{hp}.{ts}.connections.de_CH.svg',
            f'election-{hp}.{ts}.seat-allocation.de_CH.svg',
            f'election-{hp}.{ts}.party-strengths.de_CH.svg',
            f'election-{hp}.{ts}.parties-panachage.de_CH.svg',
            f'election-{hp}.{ts}.lists-panachage.de_CH.svg',
            f'elections-{hc}.{ts}.list-groups.de_CH.svg',
            f'elections-{hc}.{ts}.seat-allocation.de_CH.svg',
            f'elections-{hc}.{ts}.party-strengths.de_CH.svg',
            f'elections-{hc}.{ts}.parties-panachage.de_CH.svg',
            f'elections-{hc}-region-1.{ts}.party-strengths.de_CH.svg',
            f'ballot-{hb}.{ts}.entities-map.de_CH.svg',
            f'ballot-{hb}.{ts}.districts-map.de_CH.svg',
            f'ballot-{hb}.{ts}.entities-map.it_CH.svg'
        ])


def test_create_svgs(election_day_app_gr: TestApp) -> None:
    generator = SvgGenerator(election_day_app_gr)
    session = election_day_app_gr.session()
    fs = election_day_app_gr.filestorage
    assert fs is not None

    svg = StringIO('<svg></svg>')
    with patch.object(generator.renderer, 'get_chart', return_value=svg):

        # no data yet
        assert generator.create_svgs() == (0, 0)
        assert fs.listdir('svg') == []

        with freeze_time("2014-04-04 14:00"):
            majorz = add_majorz_election(session)
            proporz = add_proporz_election(session)
            compound = add_election_compound(
                session, elections=[proporz],
                pukelsheim=True, completes_manually=True,
                manually_completed=True,
            )
            vote = add_vote(session, 'complex')
            assert majorz.last_result_change is None  # used later

        # generate
        assert generator.create_svgs() == (68, 0)
        assert len(fs.listdir('svg')) == 68

        # don't recreate
        assert generator.create_svgs() == (0, 0)
        assert len(fs.listdir('svg')) == 68

        # remove foreign files
        fs.touch('svg/somefile')
        fs.touch('svg/some.file')
        fs.touch('svg/.somefile')

        assert generator.create_svgs() == (0, 3)
        assert len(fs.listdir('svg')) == 68

        # remove obsolete
        session.delete(vote)
        session.delete(compound)
        session.delete(proporz)
        session.flush()

        assert generator.create_svgs() == (0, 64)
        assert len(fs.listdir('svg')) == 4

        # recreate after changes
        with freeze_time("2014-04-05 14:00"):
            majorz.title = 'Election'
            session.flush()

        assert generator.create_svgs() == (4, 4)
        assert len(fs.listdir('svg')) == 4

        # recreate with new results
        majorz.last_result_change = majorz.timestamp()
        majorz.last_result_change += timedelta(days=1)
        session.flush()

        assert generator.create_svgs() == (4, 4)
        assert len(fs.listdir('svg')) == 4

        # recreate when clearing results
        old = fs.listdir('svg')
        majorz.last_result_change = None
        session.flush()

        assert generator.create_svgs() == (4, 4)
        assert len(fs.listdir('svg')) == 4
        assert set(old) & set(fs.listdir('svg')) == set()

        # remove obsolete
        session.delete(majorz)
        session.flush()

        assert generator.create_svgs() == (0, 4)
        assert len(fs.listdir('svg')) == 0
