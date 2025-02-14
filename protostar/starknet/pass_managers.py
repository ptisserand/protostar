from dataclasses import dataclass, replace
from typing import Any

from starkware.starknet.public.abi_structs import prepare_type_for_abi
from starkware.cairo.lang.compiler.ast.code_elements import (
    CodeElementFunction,
    CodeElement,
    CodeBlock,
)
from starkware.starknet.compiler.starknet_preprocessor import StarknetPreprocessor
from starkware.cairo.lang.cairo_constants import DEFAULT_PRIME
from starkware.cairo.lang.compiler.cairo_compile import get_module_reader
from starkware.cairo.lang.compiler.preprocessor.pass_manager import (
    PassManager,
    PassManagerContext,
    VisitorStage,
)
from starkware.starknet.compiler.starknet_pass_manager import starknet_pass_manager
from starkware.cairo.lang.compiler.preprocessor.default_pass_manager import (
    PreprocessorStage,
    ModuleCollector,
)
from starkware.starknet.security.hints_whitelist import get_hints_whitelist
from starkware.starknet.compiler.external_wrapper import (
    parse_entry_point_decorators,
    get_abi_entry_type,
    CONSTRUCTOR_DECORATOR,
)
from starkware.starknet.public.abi import AbiType
from starkware.cairo.lang.compiler.ast.visitor import Visitor

from protostar.cairo import PassManagerFactory, PassManagerConfig


class StarknetPassManagerFactory(PassManagerFactory):
    @staticmethod
    def build(config: PassManagerConfig) -> PassManager:
        read_module = get_module_reader(cairo_path=config.include_paths).read
        return starknet_pass_manager(
            DEFAULT_PRIME,
            read_module,
            disable_hint_validation=config.disable_hint_validation,
        )


class TestCollectorPassManagerFactory(StarknetPassManagerFactory):
    """
    Very fast pass only collecting ABI functions
    """

    @staticmethod
    def build(config: PassManagerConfig) -> PassManager:
        read_module = get_module_reader(cairo_path=config.include_paths).read

        manager = PassManager()
        manager.add_stage(
            "module_collector",
            ModuleCollector(
                read_module=read_module,
                additional_modules=[],
            ),
        )
        manager.add_stage(
            "test_collector_preprocessor",
            new_stage=TestCollectorStage(),
        )
        return manager


class ProtostarPassMangerFactory(StarknetPassManagerFactory):
    """
    Standard StarkNet pass which includes types used for storage_vars in ABI.
    """

    @staticmethod
    def build(config: PassManagerConfig) -> PassManager:
        read_module = get_module_reader(cairo_path=config.include_paths).read
        manager = starknet_pass_manager(
            DEFAULT_PRIME,
            read_module,
            disable_hint_validation=config.disable_hint_validation,
        )
        hint_whitelist = (
            None if config.disable_hint_validation else get_hints_whitelist()
        )
        manager.replace(
            "preprocessor",
            PreprocessorStage(
                DEFAULT_PRIME,
                ProtostarPreprocessor,
                None,
                dict(hint_whitelist=hint_whitelist),
            ),
        )
        return manager


class TestSuitePassMangerFactory(ProtostarPassMangerFactory):
    """
    Does everything done by `ProtostarPassMangerFactory` and additionally auto-removes constructor from contract
    """

    @staticmethod
    def build(config: PassManagerConfig) -> PassManager:
        manager = ProtostarPassMangerFactory.build(config)
        manager.add_before(
            existing_stage="identifier_collector",
            new_stage_name="remove_constructors",
            new_stage=VisitorStage(PrepareTestCaseVisitor, modify_ast=True),
        )
        return manager


# pylint: disable=abstract-method
class ProtostarPreprocessor(StarknetPreprocessor):
    """
    This preprocessor includes types used in contracts storage variables in ABI
    """

    def add_abi_storage_var_types(self, elm: CodeElementFunction):
        """
        Adds an entry describing the function to the contract's ABI.
        """
        arg_types = []

        for arg in elm.arguments.identifiers:
            arg_types.append(arg.get_type())

        if elm.returns:
            arg_types.append(elm.returns)

        for unresolved_arg_type in arg_types:
            arg_type = self.resolve_type(unresolved_arg_type)
            abi_type_info = prepare_type_for_abi(arg_type)
            for struct_name in abi_type_info.structs:
                self.add_struct_to_abi(struct_name)

    def visit_CodeElementFunction(self, elm: CodeElementFunction):
        super().visit_CodeElementFunction(elm)
        attr = elm.additional_attributes.get("storage_var")
        if attr is not None:
            self.add_abi_storage_var_types(elm=attr)
            return


class TestCollectorStage(VisitorStage):
    def __init__(self):
        super().__init__(TestCollectorPreprocessor, modify_ast=True)

    def run(self, context: PassManagerContext):
        visitor = super().run(context)
        context.preprocessed_program = visitor.get_program()
        return visitor


@dataclass
class TestCollectorPreprocessedProgram:
    abi: AbiType


class TestCollectorPreprocessor(Visitor):
    """
    This preprocessor generates simpler and more limited ABI in exchange for performance.
    ABI includes only function types with only names.
    """

    # pylint: disable=unused-argument
    def __init__(self, context: PassManagerContext):
        super().__init__()
        self.abi: AbiType = []

    def add_simple_abi_function_entry(
        self, elm: CodeElementFunction, external_decorator_name: str
    ):
        """
        Adds an entry describing the function to the contract's ABI.
        """
        entry_type = get_abi_entry_type(external_decorator_name=external_decorator_name)
        self.abi.append(
            {
                "name": elm.name,
                "type": entry_type,
            }
        )

    def visit_CodeElementFunction(self, elm: CodeElementFunction):  # type: ignore
        external_decorator, _, _, _ = parse_entry_point_decorators(elm=elm)
        if external_decorator is not None:
            # Add a function/constructor entry to the ABI.
            self.add_simple_abi_function_entry(
                elm=elm,
                external_decorator_name=external_decorator.name,
            )

    def get_program(self):
        return TestCollectorPreprocessedProgram(abi=self.abi)

    def _visit_default(self, obj: Any):
        pass


class PrepareTestCaseVisitor(Visitor):
    """
    This preprocessor removes constructors from module.
    """

    # pylint: disable=unused-argument
    def __init__(self, context: PassManagerContext):
        super().__init__()

    @staticmethod
    def is_constructor(elm: CodeElement) -> bool:
        if not isinstance(elm, CodeElementFunction):
            return False
        external_decorator, _, _, _ = parse_entry_point_decorators(elm=elm)
        if not external_decorator:
            return False
        return external_decorator.name == CONSTRUCTOR_DECORATOR

    def visit_CodeBlock(self, elm: CodeBlock):
        visited = super().visit_CodeBlock(elm)
        removed_constructors = [
            el for el in visited.code_elements if not self.is_constructor(el.code_elm)
        ]

        return replace(visited, code_elements=removed_constructors)

    def _visit_default(self, obj: Any):
        return obj
