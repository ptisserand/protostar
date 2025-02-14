import asyncio
from typing import Any, Optional

from protostar.cheatable_starknet.callable_hint_locals.callable_hint_local import (
    CallableHintLocal,
)
from protostar.cheatable_starknet.controllers.contracts import (
    ContractsCheaterException,
    ContractsController,
)
from protostar.starknet import (
    Address,
    RawAddress,
    CairoOrPythonData,
    CheatcodeException,
    Selector,
)


class InvokeHintLocal(CallableHintLocal):
    def __init__(self, contracts_controller: ContractsController):
        self._contracts_controller = contracts_controller

    @property
    def name(self) -> str:
        return "invoke"

    def _build(self) -> Any:
        return self.invoke

    def invoke(
        self,
        contract_address: RawAddress,
        function_name: str,
        calldata: Optional[CairoOrPythonData] = None,
    ):
        self._invoke(
            entry_point_selector=Selector(function_name),
            calldata=calldata,
            contract_address=Address.from_user_input(contract_address),
        )

    def _invoke(
        self,
        contract_address: Address,
        entry_point_selector: Selector,
        calldata: Optional[CairoOrPythonData] = None,
    ):
        try:
            asyncio.run(
                self._contracts_controller.invoke(
                    contract_address=contract_address,
                    entry_point_selector=entry_point_selector,
                    calldata=calldata,
                )
            )
        except ContractsCheaterException as exc:
            raise CheatcodeException(self, exc.message) from exc
