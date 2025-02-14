from argparse import Namespace
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from starknet_py.net.gateway_client import GatewayClient
from starknet_py.net.signer import BaseSigner

from protostar.cli import ProtostarArgument, ProtostarCommand, MessengerFactory
from protostar.cli.common_arguments import (
    ACCOUNT_ADDRESS_ARG,
    PRIVATE_KEY_PATH_ARG,
    SIGNER_CLASS_ARG,
    BLOCK_EXPLORER_ARG,
    MAX_FEE_ARG,
    WAIT_FOR_ACCEPTANCE_ARG,
    TOKEN_ARG,
)
from protostar.cli.network_command_util import NetworkCommandUtil
from protostar.cli.signable_command_util import get_signer
from protostar.io import StructuredMessage, LogColorProvider
from protostar.starknet import Address
from protostar.starknet_gateway import (
    Fee,
    GatewayFacadeFactory,
    SuccessfulDeclareResponse,
    create_block_explorer,
)


@dataclass
class SuccessfulDeclareMessage(StructuredMessage):
    response: SuccessfulDeclareResponse
    class_url: Optional[str]
    tx_url: Optional[str]

    def format_human(self, fmt: LogColorProvider) -> str:
        lines: list[str] = []
        lines.append("Declare transaction was sent.")
        lines.append(f"Class hash: 0x{self.response.class_hash:064x}")
        if self.class_url:
            lines.append(self.class_url)
            lines.append("")
        lines.append(f"Transaction hash: 0x{self.response.transaction_hash:064x}")
        if self.tx_url:
            lines.append(self.tx_url)
        return "\n".join(lines)

    def format_dict(self) -> dict:
        return {
            "class_hash": f"0x{self.response.class_hash:064x}",
            "transaction_hash": f"0x{self.response.transaction_hash:064x}",
        }


class DeclareCommand(ProtostarCommand):
    def __init__(
        self,
        gateway_facade_factory: GatewayFacadeFactory,
        messenger_factory: MessengerFactory,
    ):
        self._gateway_facade_factory = gateway_facade_factory
        self._messenger_factory = messenger_factory

    @property
    def name(self) -> str:
        return "declare"

    @property
    def description(self) -> str:
        return "Sends a declare transaction to StarkNet."

    @property
    def example(self) -> Optional[str]:
        return None

    @property
    def arguments(self):
        return [
            ACCOUNT_ADDRESS_ARG,
            PRIVATE_KEY_PATH_ARG,
            SIGNER_CLASS_ARG,
            *NetworkCommandUtil.network_arguments,
            *MessengerFactory.OUTPUT_ARGUMENTS,
            BLOCK_EXPLORER_ARG,
            ProtostarArgument(
                name="contract",
                description="Path to compiled contract.",
                type="path",
                is_positional=True,
                is_required=True,
            ),
            TOKEN_ARG,
            MAX_FEE_ARG,
            WAIT_FOR_ACCEPTANCE_ARG,
        ]

    async def run(self, args: Namespace) -> SuccessfulDeclareResponse:
        write = self._messenger_factory.from_args(args)

        assert isinstance(args.contract, Path)
        assert args.gateway_url is None or isinstance(args.gateway_url, str)
        assert args.network is None or isinstance(args.network, str)
        assert args.token is None or isinstance(args.token, str)
        assert isinstance(args.wait_for_acceptance, bool)

        network_command_util = NetworkCommandUtil(args)
        network_config = network_command_util.get_network_config()
        gateway_client = network_command_util.get_gateway_client()
        signer = get_signer(args, network_config, args.account_address)

        block_explorer = create_block_explorer(
            block_explorer_name=args.block_explorer,
            network=network_config.network_name,
        )

        response = await self.declare(
            compiled_contract_path=args.contract,
            signer=signer,
            account_address=args.account_address,
            gateway_client=gateway_client,
            token=args.token,
            wait_for_acceptance=args.wait_for_acceptance,
            max_fee=args.max_fee,
        )

        write(
            SuccessfulDeclareMessage(
                response=response,
                class_url=block_explorer.create_link_to_class(response.class_hash),
                tx_url=block_explorer.create_link_to_transaction(
                    response.transaction_hash
                ),
            )
        )

        return response

    async def declare(
        self,
        compiled_contract_path: Path,
        max_fee: Fee,
        signer: BaseSigner,
        gateway_client: GatewayClient,
        account_address: Address,
        token: Optional[str] = None,
        wait_for_acceptance: bool = False,
    ) -> SuccessfulDeclareResponse:
        gateway_facade = self._gateway_facade_factory.create(gateway_client)
        return await gateway_facade.declare(
            compiled_contract_path=compiled_contract_path,
            signer=signer,
            account_address=account_address,
            wait_for_acceptance=wait_for_acceptance,
            token=token,
            max_fee=max_fee,
        )
