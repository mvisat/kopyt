"""Module for all node classes."""

from __future__ import annotations

from dataclasses import dataclass
from textwrap import indent as _indent
from typing import (
    Generic,
    Literal,
    Optional,
    TypeVar,
    Union,
    Sequence,
    Iterator,
)

from .lexer import Position


@dataclass
class Node:
    """Base class for all objects in the parsed tree."""

    position: Position

    __slots__ = ("position", )


NodeType = TypeVar("NodeType", Node, str)


@dataclass
class Nodes(Node, Generic[NodeType]):
    """Nodes represents a sequence of Node objects, surrounded by enclosing
    characters. For example, `node.Block` is sequence of `node.Statement`
    objects, which are surrounded by `{` and `}` character.

    Nodes implements all Sequence traits, so it can be treated as sequence-like
    objects (such as list and tuple):
    ```
    body: node.Block = parsed.body
    first_statement = body[0] # indexing is supported
    for statement in body: # Nodes is iterable
        pass # do something with each statement
    ```
    """
    sequence: Sequence[NodeType]

    __slots__ = ("sequence", )

    def __str__(self) -> str:
        return ", ".join(map(str, self.sequence))

    def __len__(self) -> int:
        return self.sequence.__len__()

    def __getitem__(self, i) -> NodeType:
        return self.sequence.__getitem__(i)

    def __iter__(self) -> Iterator[NodeType]:
        return self.sequence.__iter__()

    def __contains__(self, x: object) -> bool:
        return self.sequence.__contains__(x)


@dataclass
class KotlinFile(Node):
    shebang: Optional[ShebangLine]
    annotations: Sequence[Annotation]
    package: Optional[PackageHeader]
    imports: ImportList
    declarations: Sequence[Declaration]

    __slots__ = (
        "shebang",
        "annotations",
        "package",
        "imports",
        "declarations",
    )

    def __str__(self) -> str:
        if self.shebang is not None:
            shebang = f"{self.shebang!s}\n\n"
        else:
            shebang = ""

        if self.annotations:
            annotations = "\n".join(map(str, self.annotations))
            annotations = f"{annotations}\n\n"
        else:
            annotations = ""

        if self.package is not None:
            package = f"{self.package!s}\n\n"
        else:
            package = ""

        if self.imports:
            imports = "\n".join(map(str, self.imports))
            if self.declarations:
                imports = f"{imports}\n\n"
        else:
            imports = ""

        if self.declarations:
            declarations = "\n\n".join(map(str, self.declarations))
        else:
            declarations = ""

        return f"{shebang}{annotations}{package}{imports}{declarations}"


@dataclass
class Script(Node):
    shebang: Optional[ShebangLine]
    annotations: Sequence[Annotation]
    package: Optional[PackageHeader]
    imports: ImportList
    statements: Sequence[Statement]

    __slots__ = ("shebang", "annotations", "package", "imports", "statements")

    def __str__(self) -> str:
        if self.shebang is not None:
            shebang = f"{self.shebang!s}\n\n"
        else:
            shebang = ""

        if self.annotations:
            annotations = "\n".join(map(str, self.annotations))
            annotations = f"{annotations}\n\n"
        else:
            annotations = ""

        if self.package is not None:
            package = f"{self.package!s}\n\n"
        else:
            package = ""

        if self.imports:
            imports = "\n".join(map(str, self.imports))
            if self.statements:
                imports = f"{imports}\n\n"
        else:
            imports = ""

        if self.statements:
            statements = "\n".join(map(str, self.statements))
        else:
            statements = ""

        return f"{shebang}{annotations}{package}{imports}{statements}"


@dataclass
class ShebangLine(Node):
    value: str

    __slots__ = ("value", )

    def __str__(self) -> str:
        return self.value


@dataclass
class PackageHeader(Node):
    name: str

    __slots__ = ("name", )

    def __str__(self) -> str:
        return f"package {self.name}"


ImportList = Sequence["ImportHeader"]


@dataclass
class ImportHeader(Node):
    name: str
    wildcard: bool
    alias: Optional[str]

    __slots__ = ("name", "wildcard", "alias")

    def __str__(self) -> str:
        if self.wildcard:
            wildcard = ".*"
        else:
            wildcard = ""

        if self.alias is not None:
            alias = f" as {self.alias}"
        else:
            alias = ""

        return f"import {self.name}{wildcard}{alias}"


@dataclass
class Declaration(Node):
    pass


@dataclass
class TypeAlias(Declaration):
    modifiers: Modifiers
    name: str
    generics: TypeParameters
    type: Type

    __slots__ = ("modifiers", "name", "generics", "type")

    def __str__(self) -> str:
        if self.modifiers:
            modifiers = f"{' '.join(map(str, self.modifiers))} "
        else:
            modifiers = ""

        if self.generics:
            generics = str(self.generics)
        else:
            generics = ""

        return f"{modifiers}typealias {self.name}{generics} = {self.type!s}"


@dataclass
class ClassDeclaration(Declaration):
    modifiers: Modifiers
    name: str
    generics: TypeParameters
    constructor: Optional[PrimaryConstructor]
    supertypes: DelegationSpecifiers
    constraints: TypeConstraints
    body: Union[None, ClassBody, EnumClassBody]

    __slots__ = (
        "modifiers",
        "name",
        "generics",
        "constructor",
        "supertypes",
        "constraints",
        "body",
    )

    def __str__(self) -> str:
        if self.modifiers:
            modifiers = f"{' '.join(map(str, self.modifiers))} "
        else:
            modifiers = ""

        if isinstance(self, InterfaceDeclaration):
            declaration = "interface"
        elif isinstance(self, FunctionalInterfaceDeclaration):
            declaration = "fun interface"
        else:
            declaration = "class"

        if self.generics:
            generics = str(self.generics)
        else:
            generics = ""

        if self.constructor is not None:
            constructor = str(self.constructor)
        else:
            constructor = ""

        if self.supertypes:
            supertypes = f" : {', '.join(map(str, self.supertypes))}"
        else:
            supertypes = ""

        if self.constraints:
            constraints = f" {self.constraints!s}"
        else:
            constraints = ""

        if self.body is not None:
            body = f" {self.body!s}"
        else:
            body = ""

        return (f"{modifiers}{declaration} {self.name}{generics}{constructor}"
                f"{supertypes}{constraints}{body}")


@dataclass
class EnumDeclaration(ClassDeclaration):
    pass


@dataclass
class InterfaceDeclaration(ClassDeclaration):
    pass


@dataclass
class FunctionalInterfaceDeclaration(ClassDeclaration):
    pass


@dataclass
class PrimaryConstructor(Node):
    modifiers: Modifiers
    parameters: ClassParameters

    __slots__ = ("modifiers", "parameters")

    def __str__(self) -> str:
        if self.modifiers:
            modifiers = f" {' '.join(map(str, self.modifiers))} constructor"
        else:
            modifiers = ""
        return f"{modifiers}{self.parameters!s}"


@dataclass
class ClassBody(Node):
    members: ClassMemberDeclarations

    __slots__ = ("members", )

    def __str__(self) -> str:
        if not self.members:
            return "{ }"

        members = "\n\n".join(indent(str(member)) for member in self.members)
        return f"{{\n{members}\n}}"


@dataclass
class ClassParameter(Node):
    modifiers: Modifiers
    mutability: Optional[Literal["val", "var"]]
    name: str
    type: Type
    default: Optional[Expression]

    __slots__ = ("modifiers", "mutability", "name", "type", "default")

    def __str__(self) -> str:
        if self.modifiers:
            modifiers = f"{' '.join(map(str, self.modifiers))} "
        else:
            modifiers = ""

        if self.mutability:
            mutability = f"{self.mutability} "
        else:
            mutability = ""

        if self.default:
            default = f" = {self.default!s}"
        else:
            default = ""

        return f"{modifiers}{mutability}{self.name}: {self.type!s}{default}"


@dataclass
class ClassParameters(Nodes[ClassParameter]):
    def __str__(self) -> str:
        return f"({super().__str__()})"


DelegationSpecifiers = Sequence["AnnotatedDelegationSpecifier"]
DelegationSpecifier = Union["ConstructorInvocation", "ExplicitDelegation",
                            "UserType", "FunctionType"]


@dataclass
class ConstructorInvocation(Node):
    invoker: UserType
    arguments: ValueArguments

    __slots__ = ("invoker", "arguments")

    def __str__(self) -> str:
        return f"{self.invoker!s}{self.arguments!s}"


@dataclass
class AnnotatedDelegationSpecifier(Node):
    annotations: Sequence[Annotation]
    delegate: DelegationSpecifier

    __slots__ = ("annotations", "delegate")

    def __str__(self) -> str:
        if self.annotations:
            annotations = f"{' '.join(map(str, self.annotations))} "
        else:
            annotations = ""
        return f"{annotations}{self.delegate!s}"


@dataclass
class ExplicitDelegation(Node):
    interface: Union[UserType, FunctionType]
    delegate: Expression

    __slots__ = ("interface", "delegate")

    def __str__(self) -> str:
        return f"{self.interface!s} by {self.delegate!s}"


@dataclass
class TypeParameter(Node):
    modifiers: Modifiers
    name: str
    type: Optional[Type]

    __slots__ = ("modifiers", "name", "type")

    def __str__(self) -> str:
        if self.modifiers:
            modifiers = f"{' '.join(map(str, self.modifiers))} "
        else:
            modifiers = ""

        if self.type is not None:
            type_ = f": {self.type!s}"
        else:
            type_ = ""

        return f"{modifiers}{self.name}{type_}"


@dataclass
class TypeParameters(Nodes[TypeParameter]):
    def __str__(self) -> str:
        return f"<{super().__str__()}>"


@dataclass
class TypeConstraint(Node):
    annotations: Sequence[Annotation]
    name: str
    type: Type

    __slots__ = ("annotations", "name", "type")

    def __str__(self) -> str:
        if self.annotations:
            annotations = f"{' '.join(map(str, self.annotations))} "
        else:
            annotations = ""

        return f"{annotations}{self.name} : {self.type!s}"


@dataclass
class TypeConstraints(Nodes[TypeConstraint]):
    def __str__(self) -> str:
        return f"where {super().__str__()}"


ClassMemberDeclaration = Union["Declaration", "CompanionObject",
                               "AnonymousInitializer",
                               "SecondaryConstructor", ]
ClassMemberDeclarations = Sequence[ClassMemberDeclaration]


@dataclass
class AnonymousInitializer(Node):
    body: Block

    __slots__ = ("body", )

    def __str__(self) -> str:
        return f"init {self.body!s}"


@dataclass
class CompanionObject(Node):
    modifiers: Modifiers
    name: Optional[str]
    interfaces: DelegationSpecifiers
    body: Optional[ClassBody]

    __slots__ = ("modifiers", "name", "interfaces", "body")

    def __str__(self) -> str:
        if self.modifiers:
            modifiers = f"{' '.join(map(str, self.modifiers))} "
        else:
            modifiers = ""

        if self.name is not None:
            name = f" {self.name}"
        else:
            name = ""

        if self.interfaces:
            interfaces = f" : {', '.join(map(str, self.interfaces))}"
        else:
            interfaces = ""

        if self.body is not None:
            body = f" {self.body!s}"
        else:
            body = ""

        return f"{modifiers}companion object{name}{interfaces}{body}"


@dataclass
class FunctionValueParameter(Node):
    modifiers: Modifiers
    parameter: Parameter
    default: Optional[Expression]

    __slots__ = ("modifiers", "parameter", "default")

    def __str__(self) -> str:
        if self.modifiers:
            modifiers = f"{' '.join(map(str, self.modifiers))} "
        else:
            modifiers = ""

        if self.default:
            default = f" = {self.default}"
        else:
            default = ""

        return f"{modifiers}{self.parameter!s}{default}"

    @property
    def name(self) -> str:
        return self.parameter.name

    @property
    def type(self) -> str:
        return str(self.parameter.type)


@dataclass
class FunctionValueParameters(Nodes[FunctionValueParameter]):
    def __str__(self) -> str:
        return f"({super().__str__()})"


@dataclass
class FunctionDeclaration(Declaration):
    modifiers: Modifiers
    generics: TypeParameters
    receiver: Optional[ReceiverType]
    name: str
    parameters: FunctionValueParameters
    type: Optional[Type]
    constraints: TypeConstraints
    body: Optional[FunctionBody]

    __slots__ = (
        "modifiers",
        "generics",
        "receiver",
        "name",
        "parameters",
        "type",
        "constraints",
        "body",
    )

    def __str__(self) -> str:
        if self.modifiers:
            modifiers = f"{' '.join(map(str, self.modifiers))} "
        else:
            modifiers = ""

        if self.generics:
            generics = f"{self.generics!s} "
        else:
            generics = ""

        if self.receiver is not None:
            receiver = f"{self.receiver!s}."
        else:
            receiver = ""

        if self.type is not None:
            type_ = f": {self.type!s}"
        else:
            type_ = ""

        if self.constraints:
            constraints = f" {self.constraints!s}"
        else:
            constraints = ""

        if self.body is not None:
            if isinstance(self.body, Expression):
                body = f" = {self.body!s}"
            else:
                body = f" {self.body!s}"
        else:
            body = ""

        return (f"{modifiers}fun {generics}{receiver}{self.name}"
                f"{self.parameters!s}{type_}{constraints}{body}")


FunctionBody = Union["Block", "Expression", ]


@dataclass
class VariableDeclaration(Node):
    annotations: Sequence[Annotation]
    name: str
    type: Optional[Type]

    __slots__ = ("annotations", "name", "type")

    def __str__(self) -> str:
        if self.annotations:
            annotations = f"{' '.join(map(str, self.annotations))} "
        else:
            annotations = ""

        if self.type is not None:
            type_ = f": {self.type!s}"
        else:
            type_ = ""

        return f"{annotations}{self.name}{type_}"


@dataclass
class MultiVariableDeclaration(Nodes[VariableDeclaration]):
    def __str__(self) -> str:
        return f"({super().__str__()})"


@dataclass
class PropertyDeclaration(Declaration):
    modifiers: Modifiers
    mutability: Literal["val", "var"]
    generics: TypeParameters
    receiver: Optional[ReceiverType]
    declaration: Union[VariableDeclaration, MultiVariableDeclaration]
    constraints: TypeConstraints
    value: Optional[Expression]
    delegate: Optional[PropertyDelegate]
    getter: Optional[Getter]
    setter: Optional[Setter]

    __slots__ = (
        "modifiers",
        "mutability",
        "generics",
        "receiver",
        "declaration",
        "constraints",
        "value",
        "delegate",
        "getter",
        "setter",
    )

    def __str__(self) -> str:
        if self.modifiers:
            modifiers = f"{' '.join(map(str, self.modifiers))} "
        else:
            modifiers = ""

        if self.generics:
            generics = f"{self.generics!s} "
        else:
            generics = ""

        if self.receiver is not None:
            receiver = f"{self.receiver!s}."
        else:
            receiver = ""

        if self.constraints:
            constraints = f" {self.constraints!s}"
        else:
            constraints = ""

        if self.value is not None:
            value = f" = {self.value!s}"
        elif self.delegate is not None:
            value = f" {self.delegate!s}"
        else:
            value = ""

        if self.getter is not None:
            if self.setter is not None or self.constraints:
                getter = f"\n{indent(str(self.getter))}"
            else:
                getter = f" {self.getter!s}"
        else:
            getter = ""

        if self.setter is not None:
            setter = f"\n{indent(str(self.setter))}"
        else:
            setter = ""

        return (f"{modifiers}{self.mutability} {generics}{receiver}"
                f"{self.declaration!s}{constraints}{value}{getter}{setter}")


@dataclass
class PropertyDelegate(Node):
    value: Expression

    __slots__ = ("value", )

    def __str__(self) -> str:
        return f"by {self.value!s}"


@dataclass
class Getter(Node):
    modifiers: Modifiers
    type: Optional[Type]
    body: Optional[FunctionBody]

    __slots__ = ("modifiers", "type", "body")

    def __str__(self) -> str:
        if self.modifiers:
            modifiers = f"{' '.join(map(str, self.modifiers))} "
        else:
            modifiers = ""

        if self.body is not None:
            if self.type is not None:
                type_ = f": {self.type!s}"
            else:
                type_ = ""
            if isinstance(self.body, Expression):
                body = f"(){type_} = {self.body!s}"
            else:
                body = f"(){type_} {self.body!s}"
        else:
            body = ""

        return f"{modifiers}get{body}"


@dataclass
class Setter(Node):
    modifiers: Modifiers
    parameter: Optional[FunctionValueParameterWithOptionalType]
    type: Optional[Type]
    body: Optional[FunctionBody]

    __slots__ = ("modifiers", "parameter", "type", "body")

    def __str__(self) -> str:
        if self.modifiers:
            modifiers = f"{' '.join(map(str, self.modifiers))} "
        else:
            modifiers = ""

        if self.body is not None:
            if self.parameter is not None:
                parameter = f"({self.parameter!s})"
            else:
                parameter = "()"  # pragma: no cover

            if self.type is not None:
                type_ = f": {self.type}"
            else:
                type_ = ""

            if isinstance(self.body, Expression):
                body = f"{parameter}{type_} = {self.body!s}"
            else:
                body = f"{parameter}{type_} {self.body!s}"
        else:
            body = ""

        return f"{modifiers}set{body}"


@dataclass
class FunctionValueParameterWithOptionalType(Node):
    modifiers: modifiers
    parameter: ParameterWithOptionalType
    default: Optional[Expression]

    __slots__ = ("modifiers", "parameter", "default")

    def __str__(self) -> str:
        if self.modifiers:
            modifiers = f"{' '.join(map(str, self.modifiers))} "
        else:
            modifiers = ""

        if self.default is not None:
            default = f" = {self.default!s}"
        else:
            default = ""

        return f"{modifiers}{self.parameter!s}{default}"


@dataclass
class ParametersWithOptionalType(Nodes[FunctionValueParameterWithOptionalType]
                                 ):
    def __str__(self) -> str:
        return f"({super().__str__()})"


@dataclass
class ParameterWithOptionalType(Node):
    name: str
    type: Optional[Type]

    __slots__ = ("name", "type")

    def __str__(self) -> str:
        if self.type is not None:
            return f"{self.name}: {self.type}"
        return self.name


@dataclass
class Parameter(Node):
    name: str
    type: Type

    __slots__ = ("name", "type")

    def __str__(self):
        return f"{self.name}: {self.type}"


@dataclass
class ObjectDeclaration(Declaration):
    modifiers: Modifiers
    name: str
    supertypes: DelegationSpecifiers
    body: Optional[ClassBody]

    __slots__ = ("modifiers", "name", "supertypes", "body")

    def __str__(self) -> str:
        if self.modifiers:
            modifiers = f"{' '.join(map(str, self.modifiers))} "
        else:
            modifiers = ""

        if self.supertypes:
            supertypes = f" : {', '.join(map(str, self.supertypes))}"
        else:
            supertypes = ""

        if self.body is not None:
            body = f" {self.body!s}"
        else:
            body = ""

        return f"{modifiers}object {self.name}{supertypes}{body}"


@dataclass
class SecondaryConstructor(Node):
    modifiers: Modifiers
    parameters: FunctionValueParameters
    delegation: Optional[ConstructorDelegationCall]
    body: Optional[Block]

    __slots__ = ("modifiers", "parameters", "delegation", "body")

    def __str__(self) -> str:
        if self.modifiers:
            modifiers = f"{' '.join(map(str, self.modifiers))} "
        else:
            modifiers = ""

        if self.delegation is not None:
            delegation = f" : {self.delegation!s}"
        else:
            delegation = ""

        if self.body is not None:
            body = f" {self.body!s}"
        else:
            body = ""

        return f"{modifiers}constructor{self.parameters!s}{delegation}{body}"


@dataclass
class ConstructorDelegationCall(Node):
    delegate: Literal["this", "super"]
    arguments: ValueArguments

    __slots__ = ("delegate", "arguments")

    def __str__(self) -> str:
        return f"{self.delegate}{self.arguments}"


@dataclass
class EnumClassBody(Node):
    entries: EnumEntries
    members: ClassMemberDeclarations

    __slots__ = ("entries", "members")

    def __str__(self) -> str:
        if not self.entries and not self.members:
            return "{ }"

        entries = ",\n".join(indent(str(entry)) for entry in self.entries)
        if not self.members:
            return f"{{\n{entries}\n}}"

        members = "\n\n".join(indent(str(member)) for member in self.members)
        return f"{{\n{entries};\n\n{members}\n}}"


@dataclass
class EnumEntry(Node):
    modifiers: Modifiers
    name: str
    arguments: ValueArguments
    body: Optional[ClassBody]

    __slots__ = ("modifiers", "name", "arguments", "body")

    def __str__(self) -> str:
        if self.modifiers:
            modifiers = f"{' '.join(map(str, self.modifiers))} "
        else:
            modifiers = ""

        if self.arguments:
            arguments = str(self.arguments)
        else:
            arguments = ""

        if self.body is not None:
            body = f" {self.body!s}"
        else:
            body = ""

        return f"{modifiers}{self.name}{arguments}{body}"


EnumEntries = Sequence[EnumEntry]


@dataclass
class Type(Node):
    modifiers: Modifiers
    subtype: Union[ParenthesizedType, NullableType, TypeReference,
                   FunctionType]

    __slots__ = ("modifiers", "subtype")

    def __str__(self) -> str:
        if self.modifiers:
            modifiers = " ".join(map(str, self.modifiers))
            return f"{modifiers} {self.subtype!s}"
        return str(self.subtype)


@dataclass
class TypeReference(Node):
    subtype: Union[UserType, Literal["dynamic"]]

    __slots__ = ("subtype", )

    def __str__(self) -> str:
        return str(self.subtype)


@dataclass
class NullableType(Node):
    subtype: Union[TypeReference, ParenthesizedType]
    nullable: str

    __slots__ = ("subtype", "nullable")

    def __str__(self) -> str:
        return f"{self.subtype!s}{self.nullable}"


@dataclass
class SimpleUserType(Node):
    name: str
    generics: TypeArguments

    __slots__ = ("name", "generics")

    def __str__(self) -> str:
        if self.generics:
            return f"{self.name}{self.generics!s}"
        return self.name


@dataclass
class UserType(Nodes[SimpleUserType]):
    def __str__(self) -> str:
        return ".".join(map(str, self.sequence))


@dataclass
class TypeProjection(Node):
    pass


@dataclass
class TypeProjectionStar(TypeProjection):
    def __str__(self):
        return "*"


@dataclass
class TypeProjectionWithType(TypeProjection):
    modifiers: Modifiers
    projection: Type

    __slots__ = ("modifiers", "projection")

    def __str__(self) -> str:
        if self.modifiers:
            modifiers = " ".join(map(str, self.modifiers))
            return f"{modifiers} {self.projection!s}"
        return str(self.projection)


@dataclass
class FunctionType(Node):
    receiver: Optional[ReceiverType]
    parameters: FunctionTypeParameters
    type: Type

    __slots__ = ("receiver", "parameters", "type")

    def __str__(self) -> str:
        if self.receiver:
            return f"{self.receiver!s}.{self.parameters!s} -> {self.type!s}"
        return f"{self.parameters!s} -> {self.type!s}"


FunctionTypeParameter = Union[Parameter, Type]


@dataclass
class FunctionTypeParameters(Nodes[FunctionTypeParameter]):
    def __str__(self) -> str:
        return f"({super().__str__()})"


@dataclass
class ParenthesizedType(Node):
    subtype: Type

    __slots__ = ("subtype", )

    def __str__(self) -> str:
        return f"({self.subtype!s})"


@dataclass
class ReceiverType(Node):
    modifiers: Modifiers
    subtype: Union[ParenthesizedType, NullableType, TypeReference]

    __slots__ = ("modifiers", "subtype")

    def __str__(self) -> str:
        if self.modifiers:
            modifiers = " ".join(map(str, self.modifiers))
            return f"{modifiers} {self.subtype!s}"
        return str(self.subtype)


@dataclass
class ControlStructureBody(Node):
    pass


@dataclass
class Statement(ControlStructureBody):
    annotations: Sequence[Annotation]
    labels: Sequence[Label]
    statement: Union[Declaration, Assignment, LoopStatement, Expression]

    __slots__ = ("annotations", "labels", "statement")

    def __str__(self) -> str:
        if self.annotations:
            annotations = f"{' '.join(map(str, self.annotations))} "
        else:
            annotations = ""

        if self.labels:
            labels = f"{' '.join(map(str, self.labels))} "
        else:
            labels = ""

        return f"{annotations}{labels}{self.statement!s}"


Statements = Sequence[Statement]


@dataclass
class Label(Node):
    name: str

    __slots__ = ("name", )

    def __str__(self) -> str:
        return f"{self.name}@"


@dataclass
class Block(ControlStructureBody, Nodes[Statement]):
    def __str__(self) -> str:
        if not self.sequence:
            return "{ }"

        statements = "\n".join(map(str, self.sequence))
        return f"{{\n{indent(statements)}\n}}"


@dataclass
class LoopStatement(Node):
    pass


@dataclass
class ForStatement(LoopStatement):

    annotations: Sequence[Annotation]
    variable: Union[VariableDeclaration, MultiVariableDeclaration]
    container: Expression
    body: Optional[ControlStructureBody]

    __slots__ = ("annotations", "variable", "container", "body")

    def __str__(self) -> str:
        if self.annotations:
            annotations = f"{' '.join(map(str, self.annotations))} "
        else:
            annotations = ""

        if self.body is not None:
            body = f" {self.body!s}"
        else:
            body = ";"

        return (f"for ({annotations}{self.variable!s} in {self.container!s})"
                f"{body}")


@dataclass
class WhileStatement(LoopStatement):
    condition: Expression
    body: Optional[ControlStructureBody]

    __slots__ = ("condition", "body")

    def __str__(self) -> str:
        if self.body is not None:
            return f"while ({self.condition!s}) {self.body!s}"
        return f"while ({self.condition!s});"


@dataclass
class DoWhileStatement(LoopStatement):
    body: Optional[ControlStructureBody]
    condition: Expression

    __slots__ = ("body", "condition")

    def __str__(self) -> str:
        if self.body is not None:
            return f"do {self.body!s} while ({self.condition!s})"
        return f"do while ({self.condition!s})"


@dataclass
class Assignment(Node):
    assignable: Union[DirectlyAssignableExpression, AssignableExpression]
    operator: str
    value: Expression

    __slots__ = ("assignable", "operator", "value")

    def __str__(self) -> str:
        return f"{self.assignable!s} {self.operator} {self.value!s}"


@dataclass
class Expression(Node):
    pass


@dataclass
class BinaryExpression(Expression):
    left: Expression
    right: Expression
    operator: str

    __slots__ = ("left", "right", "operator")

    def __str__(self):
        return f"{self.left!s} {self.operator} {self.right!s}"


@dataclass
class Disjunction(BinaryExpression):
    operator: str = "||"


@dataclass
class Conjunction(BinaryExpression):
    operator: str = "&&"


@dataclass
class Equality(BinaryExpression):
    pass


@dataclass
class Comparison(BinaryExpression):
    pass


class InfixOperation(BinaryExpression):
    pass


@dataclass
class ElvisExpression(BinaryExpression):
    operator: str = "?:"


@dataclass
class InfixFunctionCall(BinaryExpression):
    pass


@dataclass
class RangeExpression(BinaryExpression):
    operator: str = ".."


@dataclass
class AdditiveExpression(BinaryExpression):
    pass


@dataclass
class MultiplicativeExpression(BinaryExpression):
    pass


@dataclass
class AsExpression(BinaryExpression):
    pass


@dataclass
class UnaryExpression(Expression):
    expression: Expression

    __slots__ = ("expression", )


@dataclass
class PrefixUnaryExpression(UnaryExpression):
    prefixes: UnaryPrefixes

    __slots__ = ("prefixes", )

    def __str__(self) -> str:
        def str_from(prefix: UnaryPrefix) -> str:
            if isinstance(prefix, (Label, Annotation)):
                return f"{prefix!s} "
            return str(prefix)

        prefixes = "".join(map(str_from, self.prefixes))
        return f"{prefixes}{self.expression!s}"


UnaryPrefix = Union["Annotation", "Label", str]
UnaryPrefixes = Sequence[UnaryPrefix]


@dataclass
class PostfixUnaryExpression(UnaryExpression):
    suffixes: PostfixUnarySuffixes

    __slots__ = ("suffixes", )

    def __str__(self) -> str:
        suffixes = "".join(map(str, self.suffixes))
        return f"{self.expression!s}{suffixes}"


PostfixUnarySuffix = Union[str, "TypeArguments", "CallSuffix",
                           "IndexingSuffix", "NavigationSuffix", ]
PostfixUnarySuffixes = Sequence[PostfixUnarySuffix]


@dataclass
class DirectlyAssignableExpression(Expression):
    expression: Union[PostfixUnaryExpression, SimpleIdentifier,
                      ParenthesizedDirectlyAssignableExpression]

    __slots__ = ("expression", )

    def __str__(self) -> str:
        return str(self.expression)


@dataclass
class ParenthesizedDirectlyAssignableExpression(DirectlyAssignableExpression):
    def __str__(self) -> str:
        return f"({self.expression!s})"


AssignableExpression = Union["PrefixUnaryExpression",
                             "ParenthesizedAssignableExpression", ]


@dataclass
class ParenthesizedAssignableExpression(Expression):
    expression: Expression

    __slots__ = ("expression", )

    def __str__(self) -> str:
        return f"({self.expression!s})"


AssignableSuffix = Union["TypeArguments", "IndexingSuffix",
                         "NavigationSuffix", ]


@dataclass
class IndexingSuffix(Nodes[Expression]):
    def __str__(self) -> str:
        return f"[{super().__str__()}]"


@dataclass
class NavigationSuffix(Node):
    operator: str
    suffix: Union[str, ParenthesizedExpression]

    __slots__ = ("operator", "suffix")

    def __str__(self) -> str:
        return f"{self.operator}{self.suffix!s}"


@dataclass
class CallSuffix(Node):
    generics: TypeArguments
    arguments: Optional[ValueArguments]
    lambda_expression: Optional[AnnotatedLambda]

    __slots__ = ("generics", "arguments", "lambda_expression")

    def __str__(self) -> str:
        values: Sequence[str] = []
        if self.generics:
            values.append(str(self.generics))

        if self.arguments is not None:
            values.append(str(self.arguments))

        if self.lambda_expression is not None:
            values.append(f" {self.lambda_expression!s}")

        return "".join(values)


@dataclass
class AnnotatedLambda(Node):
    annotations: Sequence[Annotation]
    label: Optional[Label]
    value: LambdaLiteral

    __slots__ = ("annotations", "label", "value")

    def __str__(self) -> str:
        if self.annotations:
            annotations = f"{' '.join(map(str, self.annotations))} "
        else:
            annotations = ""

        if self.label is not None:
            label = f"{self.label!s}"
        else:
            label = ""

        return f"{annotations}{label}{self.value!s}"


@dataclass
class TypeArguments(Nodes[TypeProjection]):
    def __str__(self) -> str:
        return f"<{super().__str__()}>"


@dataclass
class ValueArgument(Node):
    annotation: Optional[Annotation]
    name: Optional[str]
    spread: bool
    value: Expression

    __slots__ = ("annotation", "name", "spread", "value")

    def __str__(self) -> str:
        if self.annotation is not None:
            annotation = f"{self.annotation!s} "
        else:
            annotation = ""

        if self.name is not None:
            name = f"{self.name} = "
        else:
            name = ""

        if self.spread:
            spread = "*"
        else:
            spread = ""

        return f"{annotation}{name}{spread}{self.value!s}"


@dataclass
class ValueArguments(Nodes[ValueArgument]):
    def __str__(self) -> str:
        return f"({super().__str__()})"


@dataclass
class PrimaryExpression(Expression):
    pass


@dataclass
class LiteralConstant(PrimaryExpression):
    value: str

    __slots__ = ("value", )

    def __str__(self) -> str:
        return self.value


@dataclass
class RealLiteral(LiteralConstant):
    pass


@dataclass
class FloatLiteral(RealLiteral):
    pass


@dataclass
class DoubleLiteral(RealLiteral):
    pass


@dataclass
class IntegerLiteral(LiteralConstant):
    pass


@dataclass
class HexLiteral(LiteralConstant):
    pass


@dataclass
class BinLiteral(LiteralConstant):
    pass


@dataclass
class UnsignedLiteral(LiteralConstant):
    pass


@dataclass
class LongLiteral(LiteralConstant):
    pass


@dataclass
class BooleanLiteral(LiteralConstant):
    pass


@dataclass
class NullLiteral(LiteralConstant):
    value: str = "null"


@dataclass
class CharacterLiteral(LiteralConstant):
    pass


@dataclass
class ParenthesizedExpression(PrimaryExpression):
    expression: Expression

    __slots__ = ("expression", )

    def __str__(self) -> str:
        return f"({self.expression!s})"


@dataclass
class CollectionLiteral(PrimaryExpression, Nodes[Expression]):
    def __str__(self) -> str:
        return f"[{super().__str__()}]"


@dataclass
class StringLiteral(PrimaryExpression):
    value: str

    __slots__ = ("value", )

    def __str__(self) -> str:
        return self.value


@dataclass
class LineStringLiteral(StringLiteral):
    pass


@dataclass
class MultiLineStringLiteral(StringLiteral):
    pass


@dataclass
class FunctionLiteral(PrimaryExpression):
    pass


@dataclass
class LambdaLiteral(FunctionLiteral):
    parameters: LambdaParameters
    statements: Statements

    __slots__ = ("parameters", "statements")

    def __str__(self) -> str:
        statements = "\n".join(map(str, self.statements))
        if len(self.statements) > 1:
            statements = f"\n{indent(statements)}\n"
        elif len(self.statements) == 1:
            statements = f" {statements} "

        if self.parameters:
            parameters = ", ".join(map(str, self.parameters))
            return f"{{ {parameters} ->{statements}}}"
        return f"{{{statements}}}"


@dataclass
class LambdaParameter(Node):
    variable: Union[VariableDeclaration, MultiVariableDeclaration]
    type: Optional[Type]

    __slots__ = ("variable", "type")

    def __str__(self) -> str:
        if self.type is not None and isinstance(self.variable,
                                                MultiVariableDeclaration):
            return f"{self.variable!s}: {self.type!s}"
        return str(self.variable)


LambdaParameters = Sequence[LambdaParameter]


@dataclass
class AnonymousFunction(FunctionLiteral):
    receiver: Optional[Type]
    parameters: ParametersWithOptionalType
    type: Optional[Type]
    constraints: TypeConstraints
    body: Optional[FunctionBody]

    __slots__ = ("receiver", "parameters", "type", "constraints", "body")

    def __str__(self) -> str:
        if self.receiver is not None:
            receiver = f" {self.receiver!s}."
        else:
            receiver = ""

        if self.type is not None:
            type_ = f": {self.type!s}"
        else:
            type_ = ""

        if self.constraints:
            constraints = f" {self.constraints!s}"
        else:
            constraints = ""

        if self.body is not None:
            if isinstance(self.body, Expression):
                body = f" = {self.body!s}"
            else:
                body = f" {self.body!s}"
        else:
            body = ""

        return f"fun{receiver}{self.parameters!s}{type_}{constraints}{body}"


@dataclass
class ObjectLiteral(PrimaryExpression):
    supertypes: DelegationSpecifiers
    body: Optional[ClassBody]

    __slots__ = ("delegations", "body")

    def __str__(self) -> str:
        if self.supertypes:
            supertypes = f" : {', '.join(map(str, self.supertypes))}"
        else:
            supertypes = ""

        if self.body is not None:
            body = f" {self.body!s}"
        else:
            body = ""

        return f"object{supertypes}{body}"


@dataclass
class ThisExpression(PrimaryExpression):
    label: Optional[str]

    __slots__ = ("label", )

    def __str__(self) -> str:
        if self.label is not None:
            return f"this@{self.label}"
        return "this"


@dataclass
class SuperExpression(PrimaryExpression):
    supertype: Optional[Type]
    label: Optional[str]

    __slots__ = ("supertype", "label")

    def __str__(self) -> str:
        if self.supertype is not None:
            supertypes = f"<{self.supertype!s}>"
        else:
            supertypes = ""

        if self.label is not None:
            label = f"@{self.label}"
        else:
            label = ""

        return f"super{supertypes}{label}"


@dataclass
class IfExpression(PrimaryExpression):
    condition: Expression
    if_body: Optional[ControlStructureBody]
    else_body: Optional[ControlStructureBody]

    __slots__ = ("condition", "if_body", "else_body")

    def __str__(self) -> str:
        if self.if_body is not None:
            if_body = f" {self.if_body!s}"
        else:
            if_body = ";"

        if self.else_body is not None:
            else_body = f" else {self.else_body!s}"
        else:
            else_body = ""

        return f"if ({self.condition!s}){if_body}{else_body}"


@dataclass
class WhenExpression(PrimaryExpression):
    subject: Optional[WhenSubject]
    entries: Sequence[WhenEntry]

    __slots__ = ("subject", "entries")

    def __str__(self) -> str:
        if self.subject is not None:
            subject = f" {self.subject!s}"
        else:
            subject = ""

        if self.entries:
            entries = "\n".join(map(str, self.entries))
            entries = f"{{\n{indent(entries)}\n}}"
        else:
            entries = "{ }"

        return f"when{subject} {entries}"


@dataclass
class WhenSubject(Node):
    annotations: Sequence[Annotation]
    declaration: Optional[VariableDeclaration]
    value: Expression

    __slots__ = ("annotations", "declaration", "value")

    def __str__(self) -> str:
        if self.annotations:
            annotations = f"{' '.join(map(str, self.annotations))} "
        else:
            annotations = ""

        if self.declaration is not None:
            declaration = f"val {self.declaration!s} = {self.value!s}"
        else:
            declaration = str(self.value)

        return f"({annotations}{declaration})"


@dataclass
class WhenEntry(Node):
    body: ControlStructureBody

    __slots__ = ("body", )


@dataclass
class WhenConditionEntry(WhenEntry):
    conditions: Sequence[WhenCondition]

    __slots__ = ("conditions", )

    def __str__(self) -> str:
        conditions = ", ".join(map(str, self.conditions))
        return f"{conditions} -> {self.body!s}"


@dataclass
class WhenElseEntry(WhenEntry):
    def __str__(self) -> str:
        return f"else -> {self.body!s}"


WhenCondition = Union[Expression, "RangeTest", "TypeTest", ]


@dataclass
class RangeTest(Node):
    operator: str
    operand: Expression

    __slots__ = ("operator", "operand")

    def __str__(self) -> str:
        return f"{self.operator} {self.operand!s}"


@dataclass
class TypeTest(Node):
    operator: str
    operand: Type

    __slots__ = ("operator", "operand")

    def __str__(self) -> str:
        return f"{self.operator} {self.operand!s}"


@dataclass
class TryExpression(PrimaryExpression):
    try_block: Block
    catch_blocks: Sequence[CatchBlock]
    finally_block: Optional[FinallyBlock]

    __slots__ = ("try_block", "catch_blocks", "finally_block")

    def __str__(self) -> str:
        if self.catch_blocks:
            catch_blocks = f" {' '.join(map(str, self.catch_blocks))}"
        else:
            catch_blocks = ""

        if self.finally_block is not None:
            finally_block = f" {self.finally_block!s}"
        else:
            finally_block = ""

        return f"try {self.try_block!s}{catch_blocks}{finally_block}"


@dataclass
class CatchBlock(Node):
    annotations: Sequence[Annotation]
    name: str
    type: Type
    block: Block

    __slots__ = ("annotations", "name", "type", "block")

    def __str__(self) -> str:
        if self.annotations:
            annotations = f"{' '.join(map(str, self.annotations))} "
        else:
            annotations = ""
        return f"catch ({annotations}{self.name}: {self.type!s}) {self.block!s}"


@dataclass
class FinallyBlock(Node):
    block: Block

    __slots__ = ("block", )

    def __str__(self) -> str:
        return f"finally {self.block!s}"


@dataclass
class JumpExpression(PrimaryExpression):
    pass


@dataclass
class ThrowExpression(JumpExpression):
    expression: Expression

    __slots__ = ("expression", )

    def __str__(self) -> str:
        return f"throw {self.expression!s}"


@dataclass
class ReturnExpression(JumpExpression):
    label: Optional[str]
    expression: Optional[Expression]

    __slots__ = ("label", "expression")

    def __str__(self) -> str:
        if self.label is not None:
            label = f"@{self.label}"
        else:
            label = ""

        if self.expression is not None:
            expression = f" {self.expression!s}"
        else:
            expression = ""

        return f"return{label}{expression}"


@dataclass
class ContinueExpression(JumpExpression):
    label: Optional[str]

    __slots__ = ("label", )

    def __str__(self):
        if self.label is not None:
            return f"continue@{self.label}"
        return "continue"


@dataclass
class BreakExpression(JumpExpression):
    label: Optional[str]

    __slots__ = ("label", )

    def __str__(self):
        if self.label is not None:
            return f"break@{self.label}"
        return "break"


@dataclass
class CallableReference(PrimaryExpression):
    receiver: Optional[ReceiverType]
    member: str

    __slots__ = ("receiver", "member")

    def __str__(self) -> str:
        if self.receiver is not None:
            return f"{self.receiver!s}::{self.member}"
        return f"::{self.member}"


Modifier = Union[str, "Annotation"]
Modifiers = Sequence[Modifier]


@dataclass
class Annotation(Node):
    target: Optional[str]

    __slots__ = ()

    def __str__(self) -> str:
        if self.target is not None:
            return f"@{self.target}:"
        return "@"


@dataclass
class UnescapedAnnotation(Node):
    name: str
    arguments: ValueArguments

    __slots__ = ("target", "name", "arguments")

    def __str__(self) -> str:
        if self.arguments:
            return f"{self.name}{self.arguments!s}"
        return self.name


@dataclass
class SingleAnnotation(Annotation, UnescapedAnnotation):
    def __str__(self) -> str:
        annotation = Annotation.__str__(self)
        unescaped = UnescapedAnnotation.__str__(self)
        return f"{annotation}{unescaped}"


@dataclass
class MultiAnnotation(Annotation, Nodes[UnescapedAnnotation]):
    def __str__(self) -> str:
        annotation = Annotation.__str__(self)
        unescaped = " ".join(
            UnescapedAnnotation.__str__(instance)
            for instance in self.sequence)
        return f"{annotation}[{unescaped}]"


@dataclass
class Identifier(Node):
    value: str

    __slots__ = ("value", )

    def __str__(self) -> str:
        return self.value


@dataclass
class SimpleIdentifier(PrimaryExpression, Identifier):
    pass


INDENT_PREFIX = " " * 4


def indent(code: str, prefix: str = INDENT_PREFIX) -> str:
    """Indent all lines of code with indentation prefix (default: 4 spaces)"""
    return _indent(code, prefix, predicate=lambda _: True)
