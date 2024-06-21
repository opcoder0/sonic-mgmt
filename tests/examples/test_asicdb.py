import logging
import pytest

pytestmark = [
    pytest.mark.examples
]

logger = logging.getLogger(__name__)


def test_verify_asicdb_tables_exist(duthosts, enum_frontend_dut_hostname, enum_asic_index):
    per_host = duthosts[enum_frontend_dut_hostname]
    logger.info(f'verifying asicdb tables for {per_host.hostname}')
    asic = per_host.asics[enum_asic_index if enum_asic_index is not None else 0]
    assert asic is not None
