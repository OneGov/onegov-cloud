from __future__ import annotations

import traceback
from pathlib import Path
import pytest
from click.testing import CliRunner

from onegov.core.utils import module_path
from onegov.org.cli import cli as org_cli
from onegov.pas.cli import cli
from onegov.pas.models import (
    Commission,
    CommissionMembership,
    Parliamentarian,
    ParliamentaryGroup,
    Party
)


@pytest.fixture
def commission_test_files():
    csv = module_path('tests.onegov.pas', '/fixtures/commission_test.csv')
    xlsx = module_path('tests.onegov.pas', '/fixtures/commission_test.xlsx')
    return {
        'csv': csv,
        'xlsx': xlsx
    }

@pytest.mark.parametrize('file_type', ['xlsx', 'csv'])
def test_import_commission_data(
    cfg_path, session_manager, commission_test_files, file_type
):
    runner = CliRunner()
    try:
        # First create the application
        result = runner.invoke(
            org_cli,
            [
                '--config',
                cfg_path,
                '--select',
                '/pas/zg',
                'add',
                'Kanton Zug',
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0

        # Get the appropriate test file based on the file type
        test_file = commission_test_files[file_type]
        test_file = Path(test_file)
        assert test_file.exists(), f"Test file {test_file} does not exist"

        # Import the commission data
        result = runner.invoke(
            cli,
            [
                '--config',
                cfg_path,
                '--select',
                '/pas/zg',
                'import-commission-data',
                str(test_file),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert 'Ok' in result.stdout

        session_manager.set_current_schema('pas-zg')
        session = session_manager.session()

        # Check commission
        commission = session.query(Commission).first()
        commission: Commission
        # Name should be inferred from the filename
        assert commission.name == 'commission_test'
        assert commission.type == 'normal'

        # Check parties
        parties = session.query(Party).all()
        party_names = {p.name for p in parties}
        expected_parties = {'ALG', 'Die Mitte'}
        assert party_names == expected_parties

        # Check parliamentary groups
        groups = session.query(ParliamentaryGroup).all()
        group_names = {g.name for g in groups}
        assert group_names == expected_parties

        # Check parliamentarians
        parliamentarians = session.query(Parliamentarian).all()
        assert len(parliamentarians) == 2

        # Check specific parliamentarian
        vivianne = (
            session.query(Parliamentarian)
            .filter_by(personnel_number='5506')
            .one()
        )
        assert vivianne.first_name == 'Vivianne'
        assert vivianne.last_name == 'Gonzalez'
        assert vivianne.shipping_address == 'StrasseB'

        # Check memberships
        vivianne_memmbersh: CommissionMembership = (
            session.query(CommissionMembership)
            .filter_by(parliamentarian_id=vivianne.id)
            .one()
        )
        assert vivianne_memmbersh.commission.name == 'commission_test'
        assert vivianne_memmbersh.role == 'member'
        assert (
            vivianne_memmbersh.parliamentarian.title == 'Vivianne Gonzalez'
        )

        # Check president role
        president = (
            session.query(CommissionMembership)
            .join(Parliamentarian)
            .filter(Parliamentarian.first_name == 'Lea')
            .one()
        )
        assert president

    except Exception as e:
        print("\nDetailed error information:")
        print("=" * 80)
        print(f"Exception type: {type(e).__name__}")
        print(f"Exception message: {str(e)}")
        print("\nFull traceback:")
        traceback.print_exc()
        print("=" * 80)
        raise
