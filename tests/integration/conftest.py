import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, ContextManager, List, Optional, cast

import pytest
from pytest import TempPathFactory
from pytest_mock import MockerFixture
from starkware.starknet.public.abi import AbiType
from typing_extensions import Protocol

from protostar.cairo import CairoVersion
from protostar.commands.test.test_command import TestCommand
from protostar.compiler.project_cairo_path_builder import ProjectCairoPathBuilder
from protostar.io.log_color_provider import LogColorProvider
from protostar.testing import TestingSummary
from protostar.cli import MessengerFactory
from tests.conftest import TESTS_ROOT_PATH, run_devnet
from tests.integration._conftest import ProtostarFixture, create_protostar_fixture
from tests.integration._conftest import (
    assert_cairo_test_cases as _assert_cairo_test_cases,
)

assert_cairo_test_cases = _assert_cairo_test_cases


@pytest.fixture(name="devnet_gateway_url", scope="module")
def devnet_gateway_url_fixture(
    devnet_port: int,
):
    cwd = os.getcwd()
    os.chdir(TESTS_ROOT_PATH.parent.resolve())
    proc = run_devnet(
        ["poetry", "run", "starknet-devnet"],
        devnet_port,
    )
    os.chdir(cwd)
    yield f"http://localhost:{devnet_port}"
    proc.kill()


class RunTestRunnerFixture(Protocol):
    async def __call__(
        self,
        path: Path,
        seed: Optional[int] = None,
        max_steps: Optional[int] = None,
        disable_hint_validation: bool = False,
        profiling: bool = False,
        cairo_path: Optional[List[Path]] = None,
        test_cases: Optional[List[str]] = None,
        ignored_test_cases: Optional[List[str]] = None,
    ) -> TestingSummary:
        ...


@pytest.fixture(name="log_color_provider", scope="module")
def log_color_provider_fixture() -> LogColorProvider:
    log_color_provider = LogColorProvider()
    log_color_provider.is_ci_mode = False
    return log_color_provider


@pytest.fixture(name="run_test_runner", scope="module")
def run_test_runner_fixture(
    session_mocker: MockerFixture, log_color_provider: LogColorProvider
) -> RunTestRunnerFixture:
    async def run_test_runner(
        path: Path,
        seed: Optional[int] = None,
        max_steps: Optional[int] = None,
        disable_hint_validation: bool = False,
        profiling: bool = False,
        cairo_path: Optional[List[Path]] = None,
        test_cases: Optional[List[str]] = None,
        ignored_test_cases: Optional[List[str]] = None,
    ) -> TestingSummary:
        protostar_directory_mock = session_mocker.MagicMock()
        protostar_directory_mock.protostar_test_only_cairo_packages_path = Path()

        project_cairo_path_builder = cast(
            ProjectCairoPathBuilder, session_mocker.MagicMock()
        )
        project_cairo_path_builder.build_project_cairo_path_list = (
            lambda relative_cairo_path_list: relative_cairo_path_list
        )

        targets: List[str] = []
        if test_cases is None:
            targets.append(str(path))
        else:
            for test_case in test_cases:
                targets.append(f"{str(path)}::{test_case}")

        ignored_targets: Optional[List[str]] = None
        if ignored_test_cases:
            ignored_targets = [
                f"{str(path)}::{ignored_test_case}"
                for ignored_test_case in ignored_test_cases
            ]

        def fake_indicator(_: str) -> ContextManager:
            ...

        messenger_factory = MessengerFactory(
            log_color_provider=log_color_provider,
            activity_indicator=fake_indicator,
        )

        return await TestCommand(
            project_root_path=Path(),
            protostar_directory=protostar_directory_mock,
            project_cairo_path_builder=project_cairo_path_builder,
            log_color_provider=log_color_provider,
            active_profile_name=None,
            cwd=Path(),
            messenger_factory=messenger_factory,
        ).test(
            targets=targets,
            ignored_targets=ignored_targets,
            seed=seed,
            max_steps=max_steps,
            profiling=profiling,
            disable_hint_validation=disable_hint_validation,
            cairo_path=cairo_path or [],
            messenger=messenger_factory.human(),
        )

    return run_test_runner


class CreateProtostarProjectFixture(Protocol):
    def __call__(
        self, cairo_version: CairoVersion = CairoVersion.cairo0
    ) -> ContextManager[ProtostarFixture]:
        ...


@pytest.fixture(name="create_protostar_project", scope="module")
def create_protostar_project_fixture(
    session_mocker: MockerFixture,
    tmp_path_factory: TempPathFactory,
) -> CreateProtostarProjectFixture:
    @contextmanager
    def create_protostar_project(cairo_version: CairoVersion = CairoVersion.cairo0):
        tmp_path = tmp_path_factory.mktemp("project_name")
        project_root_path = tmp_path
        cwd = Path().resolve()
        protostar = create_protostar_fixture(
            mocker=session_mocker,
            project_root_path=tmp_path,
        )

        project_name = "project_name"
        if cairo_version == CairoVersion.cairo0:
            protostar.init_sync(project_name)
        else:
            protostar.init_cairo1_sync(project_name)

        project_root_path = project_root_path / project_name
        os.chdir(project_root_path)
        # rebuilding protostar fixture to reload configuration file
        yield create_protostar_fixture(
            mocker=session_mocker,
            project_root_path=project_root_path,
        )
        os.chdir(cwd)

    return create_protostar_project


GetAbiFromContractFixture = Callable[[str], AbiType]


@pytest.fixture(name="get_abi_from_contract", scope="module")
def get_abi_from_contract_fixture(
    create_protostar_project: CreateProtostarProjectFixture,
) -> GetAbiFromContractFixture:
    def get_abi_from_contract(contract_source_code: str) -> AbiType:
        with create_protostar_project() as protostar:
            protostar.create_files({"src/main.cairo": contract_source_code})
            protostar.build_sync()
            with open("build/main_abi.json") as f:
                abi = json.load(f)
                return abi

    return get_abi_from_contract
