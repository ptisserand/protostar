from pathlib import Path
import re
import pytest

from protostar.protostar_exception import ProtostarException
from tests.integration.conftest import (
    RunTestRunnerFixture,
)


@pytest.mark.skip
async def test_testing_output(run_test_runner: RunTestRunnerFixture):
    await run_test_runner(
        Path(__file__).parent / "example_profile_contract_test.cairo", profiling=True
    )
    assert False


async def test_failed_profile_multiple_tests(
    run_test_runner: RunTestRunnerFixture,
):
    with pytest.raises(
        ProtostarException,
        match=re.escape(
            "Only one test case can be profiled at the time. Please specify path to a single test case."
        ),
    ):
        await run_test_runner(
            Path(__file__).parent,
            profiling=True,
        )
