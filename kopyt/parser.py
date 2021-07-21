"""Module for parsing Kotlin code."""

from typing import (
    Callable,
    Iterable,
    NoReturn,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from .debugger import debugger
from .exception import ParserException
from .iterator import PeekableIterator
from .lexer import (
    At,
    BinLiteral,
    BooleanLiteral,
    CharacterLiteral,
    DoubleLiteral,
    EOF,
    FloatLiteral,
    HexLiteral,
    Identifier,
    IntegerLiteral,
    LineStringLiteral,
    LiteralConstant,
    LongLiteral,
    MultiLineStringLiteral,
    NewLine,
    NullLiteral,
    Operator,
    OptionalNewLines as NL,
    ShebangLine,
    StringLiteral,
    UnsignedLiteral,
)
from .lexer import Lexer, Token
from .position import Position
from . import node

__all__ = ["Parser"]

CLASS_MODIFIERS = (
    "enum",
    "sealed",
    "annotation",
    "data",
    "inner",
    "value",
)

MEMBER_MODIFIERS = (
    "override",
    "lateinit",
)

VISIBILITY_MODIFIERS = (
    "public",
    "private",
    "internal",
    "protected",
)

VARIANCE_MODIFIERS = (
    "in",
    "out",
)

FUNCTION_MODIFIERS = (
    "tailrec",
    "operator",
    "infix",
    "inline",
    "external",
    "suspend",
)

PROPERTY_MODIFIERS = ("const", )

INHERITANCE_MODIFIERS = (
    "abstract",
    "final",
    "open",
)

PARAMETER_MODIFIERS = (
    "vararg",
    "noinline",
    "crossinline",
)

REIFICATION_MODIFIERS = ("reified", )

PLATFORM_MODIFIERS = (
    "expect",
    "actual",
)

TYPE_PARAMETER_MODIFIERS = frozenset(REIFICATION_MODIFIERS +
                                     VARIANCE_MODIFIERS)

MODIFIERS = frozenset(CLASS_MODIFIERS + MEMBER_MODIFIERS +
                      VISIBILITY_MODIFIERS + FUNCTION_MODIFIERS +
                      PROPERTY_MODIFIERS + INHERITANCE_MODIFIERS +
                      PARAMETER_MODIFIERS + PLATFORM_MODIFIERS)

AcceptableType = TypeVar("AcceptableType", str, Token)

ParseFunc = Callable[[], node.NodeType]


@debugger
class Parser:
    """
    Parser class to parse Kotlin code.
    """
    def __init__(self, code: str) -> None:
        lexer = Lexer(code, yield_comments=False)
        self.tokens = PeekableIterator(lexer, default=lexer.eof)

    def parse(self) -> node.KotlinFile:
        """Parse code as a whole Kotlin file.

        Returns:
            KotlinFile object.

        Raises:
            ParserException: An error occured while parsing the code.
        """
        return self.parse_kotlin_file()

    def parse_kotlin_file(self) -> node.KotlinFile:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-kotlinFile

        kotlinFile:
            [shebangLine]
            {NL}
            {fileAnnotation}
            packageHeader
            importList
            {topLevelObject}
            EOF
        """
        if self._would_accept(ShebangLine):
            shebang = self.parse_shebang_line()
        else:
            shebang = None

        self._consume_new_lines()
        annotations = self.parse_annotations(("file", ))

        if self._would_accept("package"):
            package = self.parse_package_header()
        else:
            package = None

        imports = self.parse_import_list()

        declarations: Sequence[node.Declaration] = []
        while not self._try_accept(EOF):
            declarations.append(
                self.parse_declaration(top_level_declaration=True))
            self._consume_semis()

        return node.KotlinFile(
            position=Position(1, 1),
            shebang=shebang,
            annotations=annotations,
            package=package,
            imports=imports,
            declarations=declarations,
        )

    def parse_script(self) -> node.Script:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-script

        script:
            [shebangLine]
            {NL}
            {fileAnnotation}
            packageHeader
            importList
            {statement semi}
            EOF
        """
        if self._would_accept(ShebangLine):
            shebang = self.parse_shebang_line()
        else:
            shebang = None

        self._consume_new_lines()
        annotations = self.parse_annotations(("file", ))

        if self._would_accept("package"):
            package = self.parse_package_header()
        else:
            package = None

        imports = self.parse_import_list()

        statements: node.Statements = []
        while not self._try_accept(EOF):
            statements.append(self.parse_statement(top_level_declaration=True))
            self._consume_semi()

        return node.Script(
            position=Position(1, 1),
            shebang=shebang,
            annotations=annotations,
            package=package,
            imports=imports,
            statements=statements,
        )

    def parse_shebang_line(self) -> node.ShebangLine:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-shebangLine

        shebangLine:
            ShebangLine (NL {NL})
        """
        token = self._accept(ShebangLine, NewLine, NL)
        return node.ShebangLine(
            position=token.position,
            value=token.value,
        )

    def parse_package_header(self) -> node.PackageHeader:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-packageHeader

        packageHeader:
            ['package' identifier [semi]]
        """
        token = self._accept("package")
        ident = self.parse_identifier()
        self._consume_semi()
        return node.PackageHeader(
            position=token.position,
            name=ident.value,
        )

    def parse_import_list(self) -> node.ImportList:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-importList

        importList:
            {importHeader}
        """
        imports: node.ImportList = []
        while self._would_accept("import"):
            imports.append(self.parse_import_header())
        return imports

    def parse_import_header(self) -> node.ImportHeader:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-importHeader

        importHeader:
            'import' identifier [('.' '*') | importAlias] [semi]

        importAlias:
            'as' simpleIdentifier
        """
        token = self._accept("import")
        ident = self.parse_identifier()

        wildcard = False
        alias: Optional[str] = None

        if self._try_accept(".", "*"):
            wildcard = True
        elif self._try_accept("as"):
            alias = self.parse_simple_identifier().value

        self._consume_semi()

        return node.ImportHeader(
            position=token.position,
            name=ident.value,
            wildcard=wildcard,
            alias=alias,
        )

    def parse_declaration(self,
                          top_level_declaration: bool = False
                          ) -> node.Declaration:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-declaration

        declaration:
            | classDeclaration | objectDeclaration | functionDeclaration
            | propertyDeclaration | typeAlias
        """
        mapping: dict[type, ParseFunc] = {
            node.ClassDeclaration: self.parse_class_declaration,
            node.ObjectDeclaration: self.parse_object_declaration,
            node.FunctionDeclaration: self.parse_function_declaration,
            node.PropertyDeclaration: self.parse_property_declaration,
            node.TypeAlias: self.parse_type_alias,
        }
        declaration_type = self._get_declaration_type()
        func = mapping.get(declaration_type, None)
        if func is None:
            self._raise("expecting a declaration")

        if declaration_type == node.PropertyDeclaration:
            kwargs = {"top_level_declaration": top_level_declaration}
        else:
            kwargs = dict()

        return func(**kwargs)

    def parse_type_alias(self) -> node.TypeAlias:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-typeAlias

        typeAlias:
            [modifiers]
            'typealias'
            {NL}
            simpleIdentifier
            [{NL} typeParameters]
            {NL}
            '='
            {NL}
            type
        """
        modifiers = self.parse_modifiers()
        token = self._accept("typealias", NL)
        name = self.parse_simple_identifier().value

        if self._would_accept(NL, "<"):
            self._consume_new_lines()
            generics = self.parse_type_parameters()
        else:
            generics = tuple()

        self._accept(NL, "=", NL)
        aliased = self.parse_type()

        return node.TypeAlias(
            position=token.position,
            modifiers=modifiers,
            name=name,
            generics=generics,
            type=aliased,
        )

    def parse_class_declaration(self) -> node.ClassDeclaration:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-classDeclaration

        classDeclaration:
            [modifiers]
            ('class' | (['fun' {NL}] 'interface'))
            {NL}
            simpleIdentifier
            [{NL} typeParameters]
            [{NL} primaryConstructor]
            [{NL} ':' {NL} delegationSpecifiers]
            [{NL} typeConstraints]
            [({NL} classBody) | ({NL} enumClassBody)]
        """
        modifiers = self.parse_modifiers()
        if self._would_accept("class"):
            token = self._accept("class")
            ret_type = node.ClassDeclaration
        elif self._would_accept("interface"):
            token = self._accept("interface")
            ret_type = node.InterfaceDeclaration
        elif self._would_accept("fun", NL, "interface"):
            token = self._accept("fun")
            self._accept(NL, "interface")
            ret_type = node.FunctionalInterfaceDeclaration
        else:
            self._raise("expecting 'class', 'interface', or 'fun interface'")

        self._consume_new_lines()
        name = self.parse_simple_identifier().value

        if self._would_accept(NL, "<"):
            self._consume_new_lines()
            generics = self.parse_type_parameters()
        else:
            generics = tuple()

        self._consume_new_lines()
        constructor = self._try_parse(self.parse_primary_constructor)

        if self._try_accept(NL, ":", NL):
            supertypes = self.parse_delegation_specifiers()
        else:
            supertypes = tuple()

        if self._would_accept(NL, "where"):
            self._consume_new_lines()
            constraints = self.parse_type_constraints()
        else:
            constraints = tuple()

        if self._would_accept(NL, "{"):
            self._consume_new_lines()
            if "enum" in modifiers:
                ret_type = node.EnumDeclaration
                body = self.parse_enum_class_body()
            else:
                body = self.parse_class_body()
        else:
            body = None

        return ret_type(
            position=token.position,
            modifiers=modifiers,
            name=name,
            generics=generics,
            constructor=constructor,
            supertypes=supertypes,
            constraints=constraints,
            body=body,
        )

    def parse_primary_constructor(self) -> node.PrimaryConstructor:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-primaryConstructor

        primaryConstructor:
            [[modifiers] 'constructor' {NL}] classParameters
        """
        try:
            modifiers = self.parse_modifiers()
            token = self._accept("constructor")
            self._consume_new_lines()
        except ParserException:
            modifiers = tuple()
            token = None

        parameters = self.parse_class_parameters()
        if token:
            position = token.position
        else:
            position = parameters.position

        return node.PrimaryConstructor(
            position=position,
            modifiers=modifiers,
            parameters=parameters,
        )

    def parse_class_body(self) -> node.ClassBody:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-classBody

        classBody:
            '{' {NL} classMemberDeclarations {NL} '}'
        """
        token = self._accept("{", NL)
        self._consume_semis()

        members: Sequence[node.ClassMemberDeclarations] = []
        while not self._would_accept(NL, "}"):
            members.append(self.parse_class_member_declaration())
            self._consume_semis()
        self._accept(NL, "}")

        return node.ClassBody(
            position=token.position,
            members=members,
        )

    def parse_class_parameters(self) -> node.ClassParameters:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-classParameters

        classParameters:
            '('
            {NL}
            [classParameter {{NL} ',' {NL} classParameter} [{NL} ',']]
            {NL}
            ')'
        """
        token = self._accept("(")

        parameters: Sequence[node.ClassParameter] = []
        while not self._would_accept(NL, ")"):
            self._consume_new_lines()
            parameters.append(self.parse_class_parameter())
            if self._would_accept(NL, ")"):
                break
            self._accept(NL, ",")
        self._accept(NL, ")")

        return node.ClassParameters(
            position=token.position,
            sequence=parameters,
        )

    def parse_class_parameter(self) -> node.ClassParameter:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-classParameter

        classParameter:
            [modifiers]
            ['val' | 'var']
            {NL}
            simpleIdentifier
            ':'
            {NL}
            type
            [{NL} '=' {NL} expression]
        """
        modifiers = self.parse_modifiers()

        if self._try_accept("val"):
            mutability = node.Mutability.VAL
        elif self._try_accept("var"):
            mutability = node.Mutability.VAR
        else:
            mutability = None

        self._consume_new_lines()
        token = self.parse_simple_identifier()
        self._accept(":", NL)
        param_type = self.parse_type()

        if self._would_accept(NL, "="):
            self._accept(NL, "=", NL)
            default = self.parse_expression()
        else:
            default = None

        return node.ClassParameter(
            position=token.position,
            modifiers=modifiers,
            mutability=mutability,
            name=token.value,
            type=param_type,
            default=default,
        )

    def parse_delegation_specifiers(self) -> node.DelegationSpecifiers:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-delegationSpecifiers

        delegationSpecifiers:
            annotatedDelegationSpecifier {{NL} ',' {NL} annotatedDelegationSpecifier}
        """
        delegations = [self.parse_annotated_delegation_specifier()]
        while self._would_accept(NL, ","):
            self._accept(NL, ",", NL)
            delegations.append(self.parse_annotated_delegation_specifier())
        return delegations

    def parse_delegation_specifier(self) -> node.DelegationSpecifier:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-delegationSpecifier

        delegationSpecifier:
            constructorInvocation
            | explicitDelegation
            | userType
            | functionType
        """
        delegation = self._try_parse(
            self.parse_explicit_delegation,
            self.parse_function_type,
            self.parse_constructor_invocation,
            self.parse_user_type,
        )
        if delegation is not None:
            return delegation
        self._raise("expecting a delegation specifier")

    def parse_constructor_invocation(self) -> node.ConstructorInvocation:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-constructorInvocation

        constructorInvocation:
            userType valueArguments
        """
        invoker = self.parse_user_type()
        self._consume_new_lines()
        arguments = self.parse_value_arguments()
        return node.ConstructorInvocation(
            position=invoker.position,
            invoker=invoker,
            arguments=arguments,
        )

    def parse_annotated_delegation_specifier(
            self) -> node.AnnotatedDelegationSpecifier:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-annotatedDelegationSpecifier

        annotatedDelegationSpecifier:
            {annotation} {NL} delegationSpecifier
        """
        annotations = self.parse_annotations()
        delegate = self.parse_delegation_specifier()
        return node.AnnotatedDelegationSpecifier(
            position=delegate.position,
            annotations=annotations,
            delegate=delegate,
        )

    def parse_explicit_delegation(self) -> node.ExplicitDelegation:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-explicitDelegation

        explicitDelegation:
            (userType | functionType)
            {NL}
            'by'
            {NL}
            expression
        """
        interface = self._try_parse(self.parse_function_type,
                                    self.parse_user_type)
        if interface is None:
            self._raise("expecting a user type or function type")

        self._accept(NL, "by", NL)
        delegate = self.parse_expression()

        return node.ExplicitDelegation(
            position=interface.position,
            interface=interface,
            delegate=delegate,
        )

    def parse_type_parameters(self) -> node.TypeParameters:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-typeParameters

        typeParameters:
            '<'
            {NL}
            typeParameter
            {{NL} ',' {NL} typeParameter}
            [{NL} ',']
            {NL}
            '>'
        """
        token = self._accept("<", NL)

        parameters = [self.parse_type_parameter()]
        while not self._would_accept(NL, ">"):
            self._accept(NL, ",", NL)
            if self._would_accept(NL, ">"):
                break
            parameters.append(self.parse_type_parameter())
        self._accept(NL, ">")

        return node.TypeParameters(
            position=token.position,
            sequence=parameters,
        )

    def parse_type_parameter(self) -> node.TypeParameter:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-typeParameter

        typeParameter:
            [typeParameterModifiers] {NL} simpleIdentifier [{NL} ':' {NL} type]
        """
        modifiers = self.parse_modifiers(REIFICATION_MODIFIERS +
                                         VARIANCE_MODIFIERS)

        self._consume_new_lines()
        token = self.parse_simple_identifier()

        if self._try_accept(NL, ":", NL):
            param_type = self.parse_type()
        else:
            param_type = None

        return node.TypeParameter(
            position=token.position,
            modifiers=modifiers,
            name=token.value,
            type=param_type,
        )

    def parse_type_constraints(self) -> node.TypeConstraints:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-typeConstraints

        typeConstraints:
            'where' {NL} typeConstraint {{NL} ',' {NL} typeConstraint}
        """
        token = self._accept("where", NL)

        constraints = [self.parse_type_constraint()]
        while self._try_accept(NL, ",", NL):
            constraints.append(self.parse_type_constraint())

        return node.TypeConstraints(
            position=token.position,
            sequence=constraints,
        )

    def parse_type_constraint(self) -> node.TypeConstraint:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-typeConstraint

        typeConstraint:
            {annotation}
            simpleIdentifier
            {NL}
            ':'
            {NL}
            type
        """
        annotations = self.parse_annotations()
        token = self.parse_simple_identifier()
        self._accept(NL, ":", NL)
        constraint_type = self.parse_type()
        return node.TypeConstraint(
            position=token.position,
            annotations=annotations,
            name=token.value,
            type=constraint_type,
        )

    def parse_class_member_declarations(self) -> node.ClassMemberDeclarations:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-classMemberDeclarations

        classMemberDeclarations:
            {classMemberDeclaration [semis]}
        """
        # Note: this is not implemented as it's very ambiguous
        raise NotImplementedError

    def parse_class_member_declaration(self) -> node.ClassMemberDeclaration:
        """Reference:

        classMemberDeclaration:
            declaration
            | companionObject
            | anonymousInitializer
            | secondaryConstructor
        """
        if self._would_accept("init"):
            return self.parse_anonymous_initializer()

        kwargs = dict()
        with self.tokens.simulate():
            _ = self.parse_modifiers()
            token = self.tokens.peek().value
            if token == "companion":
                func = self.parse_companion_object
            elif token == "constructor":
                func = self.parse_secondary_constructor
            elif token in ("class", "interface", "fun", "object", "val", "var",
                           "typealias"):
                func = self.parse_declaration
                kwargs = {"top_level_declaration": True}
            else:
                func = None

        if func is None:
            self._raise("expecting a class member declaration")

        return func(**kwargs)

    def parse_anonymous_initializer(self) -> node.AnonymousInitializer:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-anonymousInitializer

        anonymousInitializer:
            'init' {NL} block
        """
        token = self._accept("init", NL)
        block = self.parse_block()
        return node.AnonymousInitializer(
            position=token.position,
            body=block,
        )

    def parse_companion_object(self) -> node.CompanionObject:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-companionObject

        companionObject:
            [modifiers]
            'companion' {NL} 'object'
            [{NL} simpleIdentifier]
            [{NL} ':' {NL} delegationSpecifiers]
            [{NL} classBody]
        """
        modifiers = self.parse_modifiers()
        token = self._accept("companion")
        self._accept(NL, "object")

        if self._would_accept(NL, Identifier):
            name = self.parse_simple_identifier().value
        else:
            name = None

        if self._try_accept(NL, ":", NL):
            interfaces = self.parse_delegation_specifiers()
        else:
            interfaces = tuple()

        if self._would_accept(NL, "{"):
            self._consume_new_lines()
            body = self.parse_class_body()
        else:
            body = None

        return node.CompanionObject(
            position=token.position,
            modifiers=modifiers,
            name=name,
            interfaces=interfaces,
            body=body,
        )

    def parse_function_value_parameters(self) -> node.FunctionValueParameters:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-functionValueParameters

        functionValueParameters:
            '('
            {NL}
            [functionValueParameter {{NL} ',' {NL} functionValueParameter} [{NL} ',']]
            {NL}
            ')'
        """
        token = self._accept("(")
        parameters: Sequence[node.FunctionValueParameter] = []
        while not self._would_accept(NL, ")"):
            self._consume_new_lines()
            parameters.append(self.parse_function_value_parameter())
            if not self._try_accept(NL, ","):
                break
        self._accept(NL, ")")
        return node.FunctionValueParameters(
            position=token.position,
            sequence=parameters,
        )

    def parse_function_value_parameter(self) -> node.FunctionValueParameter:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-functionValueParameter

        functionValueParameter:
            [parameterModifiers] parameter [{NL} '=' {NL} expression]
        """
        modifiers = self.parse_modifiers(PARAMETER_MODIFIERS)
        parameter = self.parse_parameter()
        if self._try_accept(NL, "=", NL):
            default = self.parse_expression()
        else:
            default = None
        return node.FunctionValueParameter(
            position=parameter.position,
            modifiers=modifiers,
            parameter=parameter,
            default=default,
        )

    def parse_function_declaration(self) -> node.FunctionDeclaration:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-functionDeclaration

        functionDeclaration:
            [modifiers]
            'fun'
            [{NL} typeParameters]
            [{NL} receiverType {NL} '.']
            {NL}
            simpleIdentifier
            {NL}
            functionValueParameters
            [{NL} ':' {NL} type]
            [{NL} typeConstraints]
            [{NL} functionBody]
        """
        modifiers = self.parse_modifiers()
        token = self._accept("fun")

        if self._would_accept(NL, "<"):
            self._consume_new_lines()
            generics = self.parse_type_parameters()
        else:
            generics = tuple()

        self._consume_new_lines()
        consumed, receiver = self._parse_ambiguous_receiver()

        if consumed is not None:
            name = consumed.value
        else:
            self._consume_new_lines()
            if receiver is not None:
                self._accept(".")
            name = self.parse_simple_identifier().value

        self._consume_new_lines()
        parameters = self.parse_function_value_parameters()

        if self._try_accept(NL, ":", NL):
            fun_type = self.parse_type()
        else:
            fun_type = None

        if self._would_accept(NL, "where"):
            self._consume_new_lines()
            constraints = self.parse_type_constraints()
        else:
            constraints = tuple()

        if self._would_accept_either((NL, "{"), (NL, "=")):
            self._consume_new_lines()
            body = self.parse_function_body()
        else:
            body = None

        return node.FunctionDeclaration(
            position=token.position,
            modifiers=modifiers,
            generics=generics,
            receiver=receiver,
            name=name,
            parameters=parameters,
            type=fun_type,
            constraints=constraints,
            body=body,
        )

    def parse_function_body(self) -> node.FunctionBody:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-functionBody

        functionBody:
            block | ('=' {NL} expression)
        """
        if self._would_accept("{"):
            return self.parse_block()
        if self._try_accept("=", NL):
            return self.parse_expression()
        self._raise("expecting '{' or '='")

    def parse_variable_declaration(self) -> node.VariableDeclaration:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-variableDeclaration

        variableDeclaration:
            {annotation} {NL} simpleIdentifier [{NL} ':' {NL} type]
        """
        annotations = self.parse_annotations()
        self._consume_new_lines()
        ident = self.parse_simple_identifier()

        if self._try_accept(NL, ":", NL):
            var_type = self.parse_type()
        else:
            var_type = None

        return node.VariableDeclaration(
            position=ident.position,
            annotations=annotations,
            name=ident.value,
            type=var_type,
        )

    def parse_multi_variable_declaration(
            self) -> node.MultiVariableDeclaration:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-multiVariableDeclaration

        multiVariableDeclaration:
            '('
            {NL}
            variableDeclaration
            {{NL} ',' {NL} variableDeclaration}
            [{NL} ',']
            {NL}
            ')'
        """
        token = self._accept("(", NL)

        declarations = [self.parse_variable_declaration()]
        while not self._would_accept(NL, ")"):
            self._accept(NL, ",", NL)
            if self._would_accept(NL, ")"):
                break
            declarations.append(self.parse_variable_declaration())
        self._accept(NL, ")")

        return node.MultiVariableDeclaration(
            position=token.position,
            sequence=declarations,
        )

    def parse_property_declaration(
            self,
            top_level_declaration: bool = False) -> node.PropertyDeclaration:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-propertyDeclaration

        propertyDeclaration:
            [modifiers]
            ('val' | 'var')
            [{NL} typeParameters]
            [{NL} receiverType {NL} '.']
            ({NL} (multiVariableDeclaration | variableDeclaration))
            [{NL} typeConstraints]
            [{NL} (('=' {NL} expression) | propertyDelegate)]
            [(NL {NL}) ';']
            {NL}
            (([getter] [{NL} [semi] setter]) | ([setter] [{NL} [semi] getter]))
        """
        modifiers = self.parse_modifiers()
        if self._would_accept_either("val", "var"):
            token = self._accept(Token)
        else:
            self._raise("expecting 'val' or 'var'")

        if self._would_accept(NL, "<"):
            generics = self.parse_type_parameters()
        else:
            generics = tuple()

        self._consume_new_lines()
        consumed, receiver = self._parse_ambiguous_receiver()

        self._consume_new_lines()
        if consumed is not None:
            if self._try_accept(":", NL):
                var_type = self.parse_type()
            else:
                var_type = None
            declaration = node.VariableDeclaration(
                position=consumed.position,
                annotations=tuple(),
                name=consumed.value,
                type=var_type,
            )
        elif self._would_accept("("):
            declaration = self.parse_multi_variable_declaration()
            if self._would_accept(NL, ":"):
                self._raise(
                    "type annotations are not allowed on a destructuring declaration",
                    verbose=False)
        else:
            assert receiver is not None
            if self._try_accept("."):
                if self._would_accept("("):
                    self._raise(
                        "receiver type is not allowed on a destructuring declaration",
                        verbose=False)
                declaration = self.parse_variable_declaration()
            else:
                assert isinstance(receiver.subtype, node.ParenthesizedType)
                if self._would_accept(":"):
                    self._raise(
                        "type annotations are not allowed on a destructuring declaration",
                        verbose=False)
                declaration = node.VariableDeclaration(
                    position=receiver.subtype.subtype.position,
                    annotations=tuple(),
                    name=str(receiver.subtype.subtype),
                    type=None,
                )
                declaration = node.MultiVariableDeclaration(
                    position=receiver.position,
                    sequence=(declaration, ),
                )
                receiver = None

        if self._would_accept(NL, "where"):
            self._consume_new_lines()
            constraints = self.parse_type_constraints()
        else:
            constraints = tuple()

        if self._try_accept(NL, "=", NL):
            self._consume_new_lines()
            value = self.parse_expression()
            delegate = None
        elif self._would_accept(NL, "by"):
            self._consume_new_lines()
            value = None
            delegate = self.parse_property_delegate()
        else:
            value = None
            delegate = None

        self._try_accept(NL, ";")

        def accepting() -> Tuple[bool, bool]:
            with self.tokens.simulate():
                self._consume_new_lines()
                _ = self.parse_modifiers()
                token = self.tokens.peek().value
                accepting_get = token == "get"
                accepting_set = token == "set"
                return (accepting_get, accepting_set)

        getter: Optional[node.Getter] = None
        setter: Optional[node.Setter] = None
        if top_level_declaration:
            for _ in range(2):
                accepting_get, accepting_set = accepting()
                if accepting_get:
                    if getter is not None:
                        token = self.tokens.peek()
                        self._raise(f"duplicate getter at {token.position!s}",
                                    verbose=False)
                    self._consume_new_lines()
                    getter = self.parse_getter()
                    self._consume_semi()
                elif accepting_set:
                    if setter is not None:
                        token = self.tokens.peek()
                        self._raise(f"duplicate setter at {token.position!s}",
                                    verbose=False)
                    self._consume_new_lines()
                    setter = self.parse_setter()
                    self._consume_semi()
                else:
                    break

        return node.PropertyDeclaration(
            position=token.position,
            modifiers=modifiers,
            mutability=node.Mutability(token.value),
            generics=generics,
            receiver=receiver,
            declaration=declaration,
            constraints=constraints,
            value=value,
            delegate=delegate,
            getter=getter,
            setter=setter,
        )

    def parse_property_delegate(self) -> node.PropertyDelegate:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-propertyDelegate

        propertyDelegate:
            'by' {NL} expression
        """
        token = self._accept("by", NL)
        value = self.parse_expression()
        return node.PropertyDelegate(
            position=token.position,
            value=value,
        )

    def parse_getter(self) -> node.Getter:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-getter

        getter:
            [modifiers] 'get' [{NL} '(' {NL} ')' [{NL} ':' {NL} type] {NL} functionBody]
        """
        modifiers = self.parse_modifiers()
        token = self._accept("get")

        get_type = None
        body = None
        if self._try_accept(NL, "(", NL):
            self._accept(")")
            if self._try_accept(NL, ":", NL):
                get_type = self.parse_type()
            self._consume_new_lines()
            body = self.parse_function_body()

        return node.Getter(
            position=token.position,
            modifiers=modifiers,
            type=get_type,
            body=body,
        )

    def parse_setter(self) -> node.Setter:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-setter

        setter:
            [modifiers] 'set'
            [
                {NL} '('
                {NL} functionValueParameterWithOptionalType
                [{NL} ',']
                {NL} ')'
                [{NL} ':' {NL} type]
                {NL} functionBody
            ]
        """
        modifiers = self.parse_modifiers()
        token = self._accept("set")

        parameter = None
        set_type = None
        body = None
        if self._try_accept(NL, "(", NL):
            parameter = self.parse_function_value_parameter_with_optional_type(
            )
            self._try_accept(NL, ",")
            self._accept(NL, ")")
            if self._try_accept(NL, ":", NL):
                set_type = self.parse_type()
            self._consume_new_lines()
            body = self.parse_function_body()

        return node.Setter(
            position=token.position,
            modifiers=modifiers,
            parameter=parameter,
            type=set_type,
            body=body,
        )

    def parse_parameters_with_optional_type(
            self) -> node.ParametersWithOptionalType:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-parametersWithOptionalType

        parametersWithOptionalType:
            '('
            {NL}
            [functionValueParameterWithOptionalType
                {{NL} ',' {NL} functionValueParameterWithOptionalType} [{NL} ',']]
            {NL}
            ')'
        """
        token = self._accept("(")
        self._consume_new_lines()

        parameters: Sequence[node.FunctionValueParameterWithOptionalType] = []
        while not self._would_accept(NL, ")"):
            parameters.append(
                self.parse_function_value_parameter_with_optional_type())
            if self._would_accept(NL, ")"):
                break
            self._accept(NL, ",", NL)

        self._accept(NL, ")")

        return node.ParametersWithOptionalType(
            position=token.position,
            sequence=parameters,
        )

    def parse_function_value_parameter_with_optional_type(
            self) -> node.FunctionValueParameterWithOptionalType:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-functionValueParameterWithOptionalType

        functionValueParameterWithOptionalType:
            [parameterModifiers] parameterWithOptionalType [{NL} '=' {NL} expression]
        """
        modifiers = self.parse_modifiers()
        parameter = self.parse_parameter_with_optional_type()
        if self._try_accept(NL, "=", NL):
            default = self.parse_expression()
        else:
            default = None
        return node.FunctionValueParameterWithOptionalType(
            position=parameter.position,
            modifiers=modifiers,
            parameter=parameter,
            default=default,
        )

    def parse_parameter_with_optional_type(
            self) -> node.ParameterWithOptionalType:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-parameterWithOptionalType

        parameterWithOptionalType:
            simpleIdentifier {NL} [':' {NL} type]
        """
        ident = self.parse_simple_identifier()
        self._consume_new_lines()
        if self._try_accept(":", NL):
            param_type = self.parse_type()
        else:
            param_type = None
        return node.ParameterWithOptionalType(
            position=ident.position,
            name=ident.value,
            type=param_type,
        )

    def parse_parameter(self) -> node.Parameter:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-parameter

        parameter:
            simpleIdentifier {NL} ':' {NL} type
        """
        ident = self.parse_simple_identifier()
        self._accept(NL, ":", NL)
        param_type = self.parse_type()
        return node.Parameter(
            position=ident.position,
            name=ident.value,
            type=param_type,
        )

    def parse_object_declaration(self) -> node.ObjectDeclaration:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-objectDeclaration

        objectDeclaration:
            [modifiers] 'object'
            {NL} simpleIdentifier
            [{NL} ':' {NL} delegationSpecifiers]
            [{NL} classBody]
        """
        modifiers = self.parse_modifiers()
        token = self._accept("object")

        self._consume_new_lines()
        ident = self.parse_simple_identifier()

        if self._try_accept(NL, ":", NL):
            supertypes = self.parse_delegation_specifiers()
        else:
            supertypes = tuple()

        if self._would_accept(NL, "{"):
            self._consume_new_lines()
            body = self.parse_class_body()
        else:
            body = None

        return node.ObjectDeclaration(
            position=token.position,
            modifiers=modifiers,
            name=ident.value,
            supertypes=supertypes,
            body=body,
        )

    def parse_secondary_constructor(self) -> node.SecondaryConstructor:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-secondaryConstructor

        secondaryConstructor:
            [modifiers] 'constructor' {NL} functionValueParameters
            [{NL} ':' {NL} constructorDelegationCall]
            {NL}
            [block]
        """
        modifiers = self.parse_modifiers()
        token = self._accept("constructor", NL)
        parameters = self.parse_function_value_parameters()

        if self._try_accept(NL, ":", NL):
            delegation = self.parse_constructor_delegation_call()
        else:
            delegation = None

        if self._would_accept(NL, "{"):
            self._consume_new_lines()
            body = self.parse_block()
        else:
            body = None

        return node.SecondaryConstructor(
            position=token.position,
            modifiers=modifiers,
            parameters=parameters,
            delegation=delegation,
            body=body,
        )

    def parse_constructor_delegation_call(
            self) -> node.ConstructorDelegationCall:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-constructorDelegationCall

        constructorDelegationCall:
            ('this' | 'super') {NL} valueArguments
        """
        if self._would_accept("this"):
            token = self._accept("this", NL)
        elif self._would_accept("super"):
            token = self._accept("super", NL)
        else:
            self._raise("expecting 'this' or 'super'")

        arguments = self.parse_value_arguments()

        return node.ConstructorDelegationCall(
            position=token.position,
            delegate=node.ConstructorDelegate(token.value),
            arguments=arguments,
        )

    def parse_enum_class_body(self) -> node.EnumClassBody:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-enumClassBody

        enumClassBody:
            '{'
            {NL}
            [enumEntries]
            [{NL} ';' {NL} classMemberDeclarations]
            {NL}
            '}'
        """
        token = self._accept("{")
        self._consume_new_lines()

        if not self._would_accept_either(";", "}"):
            entries = self.parse_enum_entries()
        else:
            entries = tuple()

        if self._try_accept(NL, ";", NL):
            members: node.ClassMemberDeclarations = []
            while not self._would_accept(NL, "}"):
                members.append(self.parse_class_member_declaration())
                self._consume_semis()
        else:
            members = tuple()

        self._accept(NL, "}")

        return node.EnumClassBody(
            position=token.position,
            entries=entries,
            members=members,
        )

    def parse_enum_entries(self) -> node.EnumEntries:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-enumEntries

        enumEntries:
            enumEntry {{NL} ',' {NL} enumEntry} {NL} [',']
        """
        entries = [self.parse_enum_entry()]
        while self._try_accept(NL, ","):
            if self._would_accept_either(EOF, (NL, ";"), (NL, "}")):
                break
            self._consume_new_lines()
            entries.append(self.parse_enum_entry())
        return entries

    def parse_enum_entry(self) -> node.EnumEntry:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-enumEntry

        enumEntry:
            [modifiers {NL}] simpleIdentifier [{NL} valueArguments] [{NL} classBody]
        """
        modifiers = self.parse_modifiers()
        if modifiers:
            self._consume_new_lines()

        ident = self.parse_simple_identifier()

        if self._would_accept(NL, "("):
            self._consume_new_lines()
            arguments = self.parse_value_arguments()
        else:
            arguments = tuple()

        if self._would_accept(NL, "{"):
            self._consume_new_lines()
            body = self.parse_class_body()
        else:
            body = None

        return node.EnumEntry(
            position=ident.position,
            modifiers=modifiers,
            name=ident.value,
            arguments=arguments,
            body=body,
        )

    def parse_type(self) -> node.Type:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-type

        type:
            [typeModifiers] (parenthesizedType | nullableType | typeReference | functionType)
        """
        modifiers = self.parse_modifiers(("suspend", ))
        subtype = self._try_parse(
            self.parse_function_type,
            self.parse_nullable_type,
            self.parse_type_reference,
            self.parse_parenthesized_type,
        )
        if subtype is None:
            self._raise("expecting a type")

        return node.Type(
            position=subtype.position,
            modifiers=modifiers,
            subtype=subtype,
        )

    def parse_type_reference(self) -> node.TypeReference:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-typeReference

        typeReference:
            userType | 'dynamic'
        """
        if self._would_accept("dynamic"):
            token = self._accept("dynamic")
            return node.TypeReference(
                position=token.position,
                subtype="dynamic",
            )
        subtype = self.parse_user_type()
        return node.TypeReference(
            position=subtype.position,
            subtype=subtype,
        )

    def parse_nullable_type(self) -> node.NullableType:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-nullableType

        nullableType:
            (typeReference | parenthesizedType) {NL} (quest {quest})
        """
        if self._would_accept("("):
            subtype = self.parse_parenthesized_type()
        else:
            subtype = self.parse_type_reference()

        self._accept(NL, "?")
        count = 1
        while self._try_accept("?"):
            count += 1
        return node.NullableType(
            position=subtype.position,
            subtype=subtype,
            nullable="?" * count,
        )

    def parse_user_type(self) -> node.UserType:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-userType

        userType:
            simpleUserType {{NL} '.' {NL} simpleUserType}
        """
        types = [self.parse_simple_user_type()]
        while self._would_accept(NL, ".", NL, Identifier):
            self._accept(NL, ".", NL)
            types.append(self.parse_simple_user_type())
        return node.UserType(
            position=types[0].position,
            sequence=types,
        )

    def parse_simple_user_type(self) -> node.SimpleUserType:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-simpleUserType

        simpleUserType:
            simpleIdentifier [{NL} typeArguments]
        """
        token = self._accept(Identifier)
        if self._would_accept(NL, "<"):
            self._consume_new_lines()
            generics = self.parse_type_arguments()
        else:
            generics = tuple()

        return node.SimpleUserType(
            position=token.position,
            name=token.value,
            generics=generics,
        )

    def parse_type_projection(self) -> node.TypeProjection:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-typeProjection

        typeProjection:
            ([typeProjectionModifiers] type) | '*'
        """
        if self._would_accept("*"):
            token = self._accept("*")
            return node.TypeProjectionStar(position=token.position, )
        modifiers = self.parse_modifiers(VARIANCE_MODIFIERS)
        projection = self.parse_type()
        return node.TypeProjectionWithType(
            position=projection.position,
            modifiers=modifiers,
            projection=projection,
        )

    def parse_function_type(self) -> node.FunctionType:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-functionType

        functionType:
            [receiverType {NL} '.' {NL}]
            functionTypeParameters
            {NL}
            '->'
            {NL}
            type
        """
        # try to parse without receiver first
        try:
            with self.tokens:
                parameters = self.parse_function_type_parameters()
                self._accept(NL, "->", NL)
                fun_type = self.parse_type()
                return node.FunctionType(
                    position=parameters.position,
                    receiver=None,
                    parameters=parameters,
                    type=fun_type,
                )
        except ParserException:
            pass

        receiver = self.parse_receiver_type()
        self._accept(NL, ".", NL)
        parameters = self.parse_function_type_parameters()
        self._accept(NL, "->", NL)
        fun_type = self.parse_type()

        return node.FunctionType(
            position=parameters.position,
            receiver=receiver,
            parameters=parameters,
            type=fun_type,
        )

    def parse_function_type_parameters(self) -> node.FunctionTypeParameters:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-functionTypeParameters

        functionTypeParameters:
            '('
            {NL}
            [parameter | type]
            {{NL} ',' {NL} (parameter | type)}
            [{NL} ',']
            {NL}
            ')'
        """
        token = self._accept("(")
        parameters: Sequence[node.FunctionTypeParameter] = []
        while not self._would_accept(NL, ")"):
            self._consume_new_lines()
            if self._would_accept(Identifier, NL, ":"):
                parameter = self.parse_parameter()
            else:
                parameter = self.parse_type()
            parameters.append(parameter)
            if self._would_accept(NL, ")"):
                break
            self._accept(NL, ",")
        self._accept(NL, ")")

        return node.FunctionTypeParameters(
            position=token.position,
            sequence=parameters,
        )

    def parse_parenthesized_type(self) -> node.ParenthesizedType:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-parenthesizedType

        parenthesizedType:
            '(' {NL} type {NL} ')'
        """
        token = self._accept("(", NL)
        subtype = self.parse_type()
        self._accept(NL, ")")
        return node.ParenthesizedType(
            position=token.position,
            subtype=subtype,
        )

    def parse_receiver_type(self) -> node.ReceiverType:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-receiverType

        receiverType:
            [typeModifiers] (parenthesizedType | nullableType | typeReference)
        """
        modifiers = self.parse_modifiers(("suspend", ))
        subtype = self._try_parse(
            self.parse_nullable_type,
            self.parse_type_reference,
            self.parse_parenthesized_type,
        )
        if subtype is None:
            self._raise("expecting a receiver type")

        return node.ReceiverType(
            position=subtype.position,
            modifiers=modifiers,
            subtype=subtype,
        )

    def parse_statements(self) -> node.Statements:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-statements

        statements:
            [statement {semis statement}] [semis]
        """
        def is_stop() -> bool:
            return self._would_accept(NL, "}") or self._would_accept(EOF)

        statements: node.Statements = []
        while not is_stop():
            statements.append(self.parse_statement())
            if is_stop():
                break
            self._consume_semis()
        return statements

    def parse_statement(self,
                        top_level_declaration: bool = False) -> node.Statement:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-statement

        statement:
            {label | annotation} (declaration | assignment | loopStatement | expression)
        """
        labels: Sequence[node.Label] = []
        annotations: Sequence[node.Annotation] = []
        while True:
            if self._would_accept(NL, At):
                annotations.append(self.parse_annotation())
            elif self._would_accept(Identifier, At):
                labels.append(self.parse_label())
            else:
                break  # pragma: no cover

        if self._is_accepting_declaration():
            statement = self.parse_declaration(
                top_level_declaration=top_level_declaration)
        elif self._is_accepting_loop_statement():
            statement = self.parse_loop_statement()
        else:
            statement = self.parse_expression()
            token_value = self.tokens.peek().value
            if token_value in ("=", "+=", "-=", "*=", "/=", "%="):
                self._accept(Operator, NL)
                value = self.parse_expression()
                statement = node.Assignment(
                    position=statement.position,
                    assignable=statement,
                    operator=token_value,
                    value=value,
                )

        return node.Statement(
            position=statement.position,
            labels=labels,
            annotations=annotations,
            statement=statement,
        )

    def parse_label(self) -> node.Label:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-label

        label:
            simpleIdentifier (AT_NO_WS | AT_POST_WS) {NL}
        """
        token = self.parse_simple_identifier()
        self._accept(At, NL)
        return node.Label(
            position=token.position,
            name=token.value,
        )

    def parse_control_structure_body(self) -> node.ControlStructureBody:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-controlStructureBody

        controlStructureBody:
            block | statement
        """
        def is_lambda_literal():
            offset = 1
            token = self.tokens.peek()
            while not token.value == "}" and not isinstance(token, EOF):
                if token.value == "->":
                    return True
                offset += 1
                token = self.tokens.peek(offset)
            return False

        if self._would_accept("{"):
            if is_lambda_literal():
                return self.parse_lambda_literal()
            return self.parse_block()
        return self.parse_statement()

    def parse_block(self) -> node.Block:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-block

        block:
            '{' {NL} statements {NL} '}'
        """
        token = self._accept("{", NL)
        self._consume_semis()

        statements: node.Statements = []
        while not self._try_accept(NL, "}"):
            self._consume_new_lines()
            statements.append(self.parse_statement())
            self._consume_semis()

        return node.Block(
            position=token.position,
            sequence=statements,
        )

    def parse_loop_statement(self) -> node.LoopStatement:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-loopStatement

        loopStatement:
            forStatement | whileStatement | doWhileStatement
        """
        if self._would_accept("for"):
            return self.parse_for_statement()
        if self._would_accept("while"):
            return self.parse_while_statement()
        if self._would_accept("do"):
            return self.parse_do_while_statement()
        self._raise("expecting a loop statement")

    def parse_for_statement(self) -> node.ForStatement:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-forStatement

        forStatement:
            'for'
            {NL}
            '('
            {annotation}
            (variableDeclaration | multiVariableDeclaration)
            'in'
            expression
            ')'
            {NL}
            [controlStructureBody]
        """
        token = self._accept("for")
        self._accept(NL, "(")
        annotations = self.parse_annotations()

        if self._would_accept("("):
            variable = self.parse_multi_variable_declaration()
        else:
            variable = self.parse_variable_declaration()

        self._accept("in")
        container = self.parse_expression()
        self._accept(")", NL)

        if self._would_accept(NL, ";"):
            body = None
        else:
            body = self.parse_control_structure_body()

        return node.ForStatement(
            position=token.position,
            annotations=annotations,
            variable=variable,
            container=container,
            body=body,
        )

    def parse_while_statement(self) -> node.WhileStatement:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-whileStatement

        whileStatement:
            'while' {NL} '(' expression ')' {NL} (controlStructureBody | ';')
        """
        token = self._accept("while")

        self._accept(NL, "(")
        condition = self.parse_expression()
        self._accept(")", NL)

        if self._try_accept(";"):
            body = None
        else:
            body = self.parse_control_structure_body()

        return node.WhileStatement(
            position=token.position,
            condition=condition,
            body=body,
        )

    def parse_do_while_statement(self) -> node.DoWhileStatement:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-doWhileStatement

        doWhileStatement:
            'do' {NL} [controlStructureBody] {NL} 'while' {NL} '(' expression ')'
        """
        token = self._accept("do", NL)

        if self._would_accept("{") or not self._would_accept("while"):
            body = self.parse_control_structure_body()
        else:
            body = None

        self._accept(NL, "while", NL, "(")
        condition = self.parse_expression()
        self._accept(")")

        return node.DoWhileStatement(
            position=token.position,
            body=body,
            condition=condition,
        )

    def parse_assignment(self) -> node.Assignment:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-semi

        assignment:
            ((directlyAssignableExpression '=')
            | (assignableExpression assignmentAndOperator)) {NL} expression
        """
        directly_assignable: Optional[node.DirectlyAssignableExpression] = None
        try:
            with self.tokens:
                directly_assignable = self.parse_directly_assignable_expression(
                )
                self._accept("=", NL)
        except ParserException:
            directly_assignable = None

        if directly_assignable is not None:
            expr = self.parse_expression()
            return node.Assignment(
                position=directly_assignable.position,
                assignable=directly_assignable,
                operator="=",
                value=expr,
            )

        assignable: Optional[node.AssignableExpression] = None
        operators = ("+=", "-=", "*=", "/=", "%=")
        try:
            with self.tokens:
                assignable = self.parse_assignable_expression()
                if not self._would_accept_either(*operators):
                    raise ParserException
        except ParserException:
            assignable = None

        if assignable is not None:
            operator = self._accept(Operator, NL).value
            expr = self.parse_expression()
            return node.Assignment(
                position=assignable.position,
                assignable=assignable,
                operator=operator,
                value=expr,
            )

        self._raise("expecting an assignment")

    def parse_expression(self) -> node.Expression:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-expression

        expression:
            disjunction
        """
        return self.parse_disjunction()

    def parse_disjunction(self) -> node.Expression:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-disjunction

        disjunction:
            conjunction {{NL} '||' {NL} conjunction}
        """
        left = self.parse_conjunction()
        while self._try_accept(NL, "||", NL):
            right = self.parse_conjunction()
            left = node.Disjunction(
                position=left.position,
                left=left,
                right=right,
            )
        return left

    def parse_conjunction(self) -> node.Expression:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-conjunction

        conjunction:
            equality {{NL} '&&' {NL} equality}
        """
        left = self.parse_equality()
        while self._try_accept(NL, "&&", NL):
            right = self.parse_equality()
            left = node.Conjunction(
                position=left.position,
                left=left,
                right=right,
            )
        return left

    def parse_equality(self) -> node.Expression:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-equality

        equality:
            comparison {equalityOperator {NL} comparison}
        """
        operators = ("==", "!=", "===", "!==")
        left = self.parse_comparison()
        while self._would_accept_either(*operators):
            operator = self._accept(Operator, NL).value
            right = self.parse_comparison()
            left = node.Equality(
                position=left.position,
                operator=operator,
                left=left,
                right=right,
            )
        return left

    def parse_comparison(self) -> node.Expression:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-comparison

        comparison:
            genericCallLikeComparison {comparisonOperator {NL} genericCallLikeComparison}
        """
        operators = ("<", ">", "<=", ">=")
        left = self.parse_generic_call_like_comparison()
        while self._would_accept_either(*operators):
            operator = self._accept(Operator, NL).value
            right = self.parse_generic_call_like_comparison()
            left = node.Comparison(
                position=left.position,
                operator=operator,
                left=left,
                right=right,
            )
        return left

    def parse_generic_call_like_comparison(self) -> node.Expression:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-genericCallLikeComparison

        genericCallLikeComparison:
            infixOperation {callSuffix}
        """
        # Note: call suffixes are consumed in postfix expression
        return self.parse_infix_operation()

    def parse_infix_operation(self) -> node.Expression:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-infixOperation

        infixOperation:
            elvisExpression {(inOperator {NL} elvisExpression) | (isOperator {NL} type)}
        """
        in_operator = ("in", "!in")
        is_operator = ("is", "!is")
        operators = in_operator + is_operator

        left = self.parse_elvis_expression()
        while self._would_accept_either(*operators):
            operator = self._accept(Operator, NL).value
            if operator in in_operator:
                right = self.parse_elvis_expression()
            else:
                right = self.parse_type()

            left = node.InfixOperation(
                position=left.position,
                operator=operator,
                left=left,
                right=right,
            )
        return left

    def parse_elvis_expression(self) -> node.Expression:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-elvisExpression

        elvisExpression:
            infixFunctionCall {{NL} elvis {NL} infixFunctionCall}
        """
        left = self.parse_infix_function_call()
        while self._try_accept(NL, "?:", NL):
            right = self.parse_infix_function_call()
            left = node.ElvisExpression(
                position=left.position,
                left=left,
                right=right,
            )
        return left

    def parse_infix_function_call(self) -> node.Expression:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-infixFunctionCall

        infixFunctionCall:
            rangeExpression {simpleIdentifier {NL} rangeExpression}
        """
        left = self.parse_range_expression()
        while self._would_accept(Identifier):
            operator = self._accept(Identifier, NL).value
            right = self.parse_range_expression()
            left = node.InfixFunctionCall(
                position=left.position,
                operator=operator,
                left=left,
                right=right,
            )
        return left

    def parse_range_expression(self) -> node.Expression:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-rangeExpression

        rangeExpression:
            additiveExpression {'..' {NL} additiveExpression}
        """
        left = self.parse_additive_expression()
        while self._try_accept("..", NL):
            right = self.parse_additive_expression()
            left = node.RangeExpression(
                position=left.position,
                left=left,
                right=right,
            )
        return left

    def parse_additive_expression(self) -> node.Expression:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-additiveExpression

        additiveExpression:
            multiplicativeExpression {additiveOperator {NL} multiplicativeExpression}
        """
        operators = ("+", "-")
        left = self.parse_multiplicative_expression()
        while self._would_accept_either(*operators):
            operator = self._accept(Operator, NL).value
            right = self.parse_multiplicative_expression()
            left = node.AdditiveExpression(position=left.position,
                                           operator=operator,
                                           left=left,
                                           right=right)
        return left

    def parse_multiplicative_expression(self) -> node.Expression:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-multiplicativeExpression

        multiplicativeExpression:
            asExpression {multiplicativeOperator {NL} asExpression}
        """
        operators = ("*", "/", "%")
        left = self.parse_as_expression()
        while self._would_accept_either(*operators):
            operator = self._accept(Operator, NL).value
            right = self.parse_as_expression()
            left = node.MultiplicativeExpression(
                position=left.position,
                operator=operator,
                left=left,
                right=right,
            )
        return left

    def parse_as_expression(self) -> node.Expression:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-asExpression

        asExpression:
            prefixUnaryExpression {{NL} asOperator {NL} type}
        """
        left = self.parse_prefix_unary_expression()
        while self._would_accept_either((NL, "as"), (NL, "as?")):
            operator = self._accept(NL, Operator, NL).value
            right = self.parse_type()
            left = node.AsExpression(
                position=left.position,
                operator=operator,
                left=left,
                right=right,
            )
        return left

    def parse_prefix_unary_expression(self) -> node.Expression:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-prefixUnaryExpression

        prefixUnaryExpression:
            {unaryPrefix} postfixUnaryExpression
        """
        prefixes = self.parse_unary_prefixes()
        if prefixes:
            expression = self.parse_postfix_unary_expression()
            return node.PrefixUnaryExpression(
                position=expression.position,
                prefixes=prefixes,
                expression=expression,
            )
        return self.parse_postfix_unary_expression()

    def parse_unary_prefixes(self) -> node.UnaryPrefixes:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-unaryPrefix

        unaryPrefixes:
            {unaryPrefix}
        """
        prefixes: node.UnaryPrefixes = []
        while self._would_accept_either((NL, At), (Identifier, At), "++", "--",
                                        "-", "+", "!"):
            prefixes.append(self.parse_unary_prefix())
        return prefixes

    def parse_unary_prefix(self) -> node.UnaryPrefix:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-unaryPrefix

        unaryPrefix:
            annotation | label | (prefixUnaryOperator {NL})
        """
        if self._would_accept(NL, At):
            return self.parse_annotation()
        if self._would_accept(Identifier, At):
            return self.parse_label()
        if self._would_accept_either("++", "--", "-", "+", "!"):
            return self._accept(Token, NL).value
        self._raise("expecting a unary prefix")

    def parse_postfix_unary_expression(self) -> node.Expression:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-postfixUnaryExpression

        postfixUnaryExpression:
            primaryExpression {postfixUnarySuffix}
        """
        expression = self.parse_primary_expression()

        suffixes: node.PostfixUnarySuffixes = []
        while True:
            suffix = self._try_parse(self.parse_postfix_unary_suffix)
            if suffix is None:
                break
            suffixes.append(suffix)

        if not suffixes:
            return expression

        return node.PostfixUnaryExpression(
            position=expression.position,
            expression=expression,
            suffixes=suffixes,
        )

    def parse_postfix_unary_suffix(self) -> node.PostfixUnarySuffix:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-postfixUnarySuffix

        postfixUnarySuffix:
            postfixUnaryOperator | typeArguments | callSuffix | indexingSuffix | navigationSuffix
        """
        if self._would_accept_either("++", "--"):
            return self._accept(Token).value
        if self._try_accept("!", "!"):
            return "!!"
        if self._would_accept_either((NL, "."), (NL, "?", "."), "::"):
            return self.parse_navigation_suffix()
        if self._would_accept("["):
            return self.parse_indexing_suffix()
        call_suffix = self._try_parse(self.parse_call_suffix)
        if call_suffix is not None:
            return call_suffix
        if self._would_accept("<"):
            return self.parse_type_arguments()
        self._raise("expecting a postfix unary suffix")

    def parse_directly_assignable_expression(
            self) -> node.DirectlyAssignableExpression:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-directlyAssignableExpression

        directlyAssignableExpression:
            (postfixUnaryExpression assignableSuffix)
            | simpleIdentifier
            | parenthesizedDirectlyAssignableExpression
        """
        parenthesized = self._try_parse(
            self.parse_parenthesized_directly_assignable_expression)
        if parenthesized is not None:
            return parenthesized

        try:
            with self.tokens:
                postfix = self._try_parse(self.parse_postfix_unary_expression)
                if isinstance(postfix, node.PostfixUnaryExpression):
                    assignable_suffixes = (node.TypeArguments,
                                           node.IndexingSuffix,
                                           node.NavigationSuffix)
                    has_suffix = isinstance(postfix.suffixes[-1],
                                            assignable_suffixes)
                    if not has_suffix:
                        raise ParserException

                    return node.DirectlyAssignableExpression(
                        position=postfix.position,
                        expression=postfix,
                    )
                raise ParserException
        except ParserException:
            pass

        ident = self.parse_simple_identifier()
        return node.DirectlyAssignableExpression(
            position=ident.position,
            expression=ident,
        )

    def parse_parenthesized_directly_assignable_expression(
            self) -> node.ParenthesizedDirectlyAssignableExpression:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-parenthesizedDirectlyAssignableExpression

        parenthesizedDirectlyAssignableExpression:
            '(' {NL} directlyAssignableExpression {NL} ')'
        """
        token = self._accept("(", NL)
        expression = self.parse_directly_assignable_expression()
        self._accept(NL, ")")
        return node.ParenthesizedDirectlyAssignableExpression(
            position=token.position,
            expression=expression,
        )

    def parse_assignable_expression(self) -> node.AssignableExpression:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-assignableExpression

        assignableExpression:
            prefixUnaryExpression | parenthesizedAssignableExpression
        """
        if self._would_accept("("):
            return self.parse_parenthesized_assignable_expression()
        return self.parse_prefix_unary_expression()

    def parse_parenthesized_assignable_expression(
            self) -> node.ParenthesizedAssignableExpression:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-parenthesizedAssignableExpression

        parenthesizedAssignableExpression:
            '(' {NL} assignableExpression {NL} ')'
        """
        token = self._accept("(", NL)
        expression = self.parse_assignable_expression()
        self._accept(NL, ")")
        return node.ParenthesizedAssignableExpression(
            position=token.position,
            expression=expression,
        )

    def parse_assignable_suffix(self) -> node.AssignableSuffix:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-indexingSuffix

        assignableSuffix:
            typeArguments | indexingSuffix | navigationSuffix
        """
        # Note: this is not implemented as the suffix is already consumed in
        # parse_postfix_unary_expression
        raise NotImplementedError

    def parse_indexing_suffix(self) -> node.IndexingSuffix:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-indexingSuffix

        indexingSuffix:
            '[' {NL} expression {{NL} ',' {NL} expression} [{NL} ','] {NL} ']'
        """
        token = self._accept("[", NL)

        expressions = [self.parse_expression()]
        while not self._would_accept(NL, "]"):
            self._accept(NL, ",", NL)
            if self._would_accept("]"):
                break
            expressions.append(self.parse_expression())
        self._accept(NL, "]")

        return node.IndexingSuffix(
            position=token.position,
            sequence=expressions,
        )

    def parse_navigation_suffix(self) -> node.NavigationSuffix:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-navigationSuffix

        navigationSuffix:
            memberAccessOperator {NL} (simpleIdentifier | parenthesizedExpression | 'class')
        """
        if self._would_accept(NL, "."):
            token = self._accept(NL, ".")
            operator = "."
        elif self._would_accept(NL, "?", "."):
            token = self._accept(NL, "?", ".")
            operator = "?."
        elif self._would_accept("::"):
            token = self._accept("::")
            operator = "::"
        else:
            self._raise("expecting a member access operator (., ?., or ::)")

        self._consume_new_lines()
        if self._try_accept("class"):
            suffix = "class"
        elif self._would_accept(Identifier):
            suffix = self.parse_simple_identifier().value
        elif self._would_accept("("):
            suffix = self.parse_parenthesized_expression()
        else:
            self._raise(
                "expecting a suffix ('class', identifier, or parenthesized expression)"
            )

        return node.NavigationSuffix(
            position=token.position,
            operator=operator,
            suffix=suffix,
        )

    def parse_call_suffix(self) -> node.CallSuffix:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-callSuffix

        callSuffix:
            [typeArguments] (([valueArguments] annotatedLambda) | valueArguments)
        """
        if self._would_accept("<"):
            generics = self.parse_type_arguments()
        else:
            generics = tuple()

        if self._would_accept("("):
            arguments = self.parse_value_arguments()
        else:
            arguments = None

        if self._is_accepting_annotated_lambda():
            lambda_expression = self.parse_annotated_lambda()
        else:
            lambda_expression = None

        if generics:
            position = generics.position
        elif arguments is not None:
            position = arguments.position
        elif lambda_expression is not None:
            position = lambda_expression.position
        else:
            self._raise("expecting a call suffix")

        return node.CallSuffix(
            position=position,
            generics=generics,
            arguments=arguments,
            lambda_expression=lambda_expression,
        )

    def parse_annotated_lambda(self) -> node.AnnotatedLambda:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-annotatedLambda

        annotatedLambda:
            {annotation} [label] {NL} lambdaLiteral
        """
        annotations = self.parse_annotations()

        if self._would_accept(Identifier, At):
            label = self.parse_label()
        else:
            label = None

        self._consume_new_lines()
        literal = self.parse_lambda_literal()

        return node.AnnotatedLambda(
            position=literal.position,
            annotations=annotations,
            label=label,
            value=literal,
        )

    def parse_type_arguments(self) -> node.TypeArguments:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-typeArguments

        typeArguments:
            '<' {NL} typeProjection {{NL} ',' {NL} typeProjection} [{NL} ','] {NL} '>'
        """
        token = self._accept("<", NL)

        projections = [self.parse_type_projection()]
        while not self._would_accept(NL, ">"):
            self._accept(NL, ",")
            if self._would_accept(NL, ">"):
                break
            self._consume_new_lines()
            projections.append(self.parse_type_projection())
        self._accept(NL, ">")

        return node.TypeArguments(
            position=token.position,
            sequence=projections,
        )

    def parse_value_arguments(self) -> node.ValueArguments:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-valueArguments

        valueArguments:
            '(' {NL} [valueArgument {{NL} ',' {NL} valueArgument} [{NL} ','] {NL}] ')'
        """
        token = self._accept("(")

        arguments: Sequence[node.ValueArgument] = []
        while not self._would_accept(NL, ")"):
            self._consume_new_lines()
            arguments.append(self.parse_value_argument())
            if self._would_accept(NL, ")"):
                break
            self._accept(NL, ",")
        self._accept(NL, ")")

        return node.ValueArguments(
            position=token.position,
            sequence=arguments,
        )

    def parse_value_argument(self) -> node.ValueArgument:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-valueArgument

        valueArgument:
            [annotation]
            {NL}
            [simpleIdentifier {NL} '=' {NL}]
            ['*']
            {NL}
            expression
        """
        if self._would_accept(NL, At):
            annotation = self.parse_annotation()
        else:
            annotation = None

        self._consume_new_lines()

        if self._would_accept(Identifier, NL, "="):
            ident = self.parse_simple_identifier()
            name = ident.value
            self._accept(NL, "=", NL)
        else:
            name = None

        spread = self._try_accept("*")

        self._consume_new_lines()
        value = self.parse_expression()

        return node.ValueArgument(
            position=value.position,
            annotation=annotation,
            name=name,
            spread=spread,
            value=value,
        )

    def parse_primary_expression(self) -> node.PrimaryExpression:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-primaryExpression

        primaryExpression:
            | parenthesizedExpression | simpleIdentifier | literalConstant
            | stringLiteral | callableReference | functionLiteral
            | objectLiteral | collectionLiteral | thisExpression
            | superExpression | ifExpression | whenExpression | tryExpression
            | jumpExpression
        """
        reference = self._try_parse(self.parse_callable_reference)
        if reference is not None:
            return reference

        token = self.tokens.peek()
        if isinstance(token, LiteralConstant):
            return self.parse_literal_constant()
        if isinstance(token, StringLiteral):
            return self.parse_string_literal()
        if isinstance(token, Identifier):
            return self.parse_simple_identifier()

        token_value = token.value
        if token_value == "if":
            return self.parse_if_expression()
        if token_value == "when":
            return self.parse_when_expression()
        if token_value == "try":
            return self.parse_try_expression()
        if token_value in ("return", "return@", "continue", "continue@",
                           "break", "break@", "throw"):
            return self.parse_jump_expression()
        if token_value == "(":
            return self.parse_parenthesized_expression()
        if token_value in ("this", "this@"):
            return self.parse_this_expression()
        if token_value in ("super", "super@"):
            return self.parse_super_expression()
        if token_value in ("{", "fun"):
            return self.parse_function_literal()
        if token_value == "object":
            return self.parse_object_literal()
        if token_value == "[":
            return self.parse_collection_literal()
        self._raise("expecting a primary expression")

    def parse_parenthesized_expression(self) -> node.ParenthesizedExpression:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-parenthesizedExpression

        parenthesizedExpression:
            '(' {NL} expression {NL} ')'
        """
        token = self._accept("(", NL)
        expression = self.parse_expression()
        self._accept(NL, ")")
        return node.ParenthesizedExpression(
            position=token.position,
            expression=expression,
        )

    def parse_collection_literal(self) -> node.CollectionLiteral:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-collectionLiteral

        collectionLiteral:
            '[' {NL} [expression {{NL} ',' {NL} expression} [{NL} ','] {NL}] ']'
        """
        token = self._accept("[")

        expressions: Sequence[node.Expression] = []
        while not self._would_accept(NL, "]"):
            self._consume_new_lines()
            expressions.append(self.parse_expression())
            if self._would_accept(NL, "]"):
                break
            self._accept(NL, ",")
        self._accept(NL, "]")

        return node.CollectionLiteral(
            position=token.position,
            sequence=expressions,
        )

    def parse_literal_constant(self) -> node.LiteralConstant:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-literalConstant

        literalConstant:
            | BooleanLiteral | IntegerLiteral | HexLiteral | BinLiteral
            | CharacterLiteral | RealLiteral | NullLiteral | LongLiteral
            | UnsignedLiteral
        """
        mapping: dict[Type[Token], Type[node.LiteralConstant]] = {
            BooleanLiteral: node.BooleanLiteral,
            IntegerLiteral: node.IntegerLiteral,
            HexLiteral: node.HexLiteral,
            BinLiteral: node.BinLiteral,
            CharacterLiteral: node.CharacterLiteral,
            FloatLiteral: node.FloatLiteral,
            DoubleLiteral: node.DoubleLiteral,
            NullLiteral: node.NullLiteral,
            LongLiteral: node.LongLiteral,
            UnsignedLiteral: node.UnsignedLiteral,
        }
        token = self._accept(LiteralConstant)
        node_type = mapping[type(token)]
        return node_type(
            position=token.position,
            value=token.value,
        )

    def parse_string_literal(self) -> node.StringLiteral:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-stringLiteral

        stringLiteral:
            lineStringLiteral | multiLineStringLiteral
        """
        if self._would_accept(LineStringLiteral):
            token = self._accept(LineStringLiteral)
            return node.LineStringLiteral(
                position=token.position,
                value=token.value,
            )
        if self._would_accept(MultiLineStringLiteral):
            token = self._accept(MultiLineStringLiteral)
            return node.MultiLineStringLiteral(
                position=token.position,
                value=token.value,
            )
        self._raise("expecting a string literal")

    def parse_lambda_literal(self) -> node.LambdaLiteral:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-lambdaLiteral

        lambdaLiteral:
            '{' {NL} [[lambdaParameters] {NL} '->' {NL}] statements {NL} '}'
        """
        token = self._accept("{", NL)
        try:
            with self.tokens:
                parameters = self.parse_lambda_parameters()
                self._accept(NL, "->", NL)
        except ParserException:
            parameters = ()

        statements = self.parse_statements()
        self._accept(NL, "}")

        return node.LambdaLiteral(
            position=token.position,
            parameters=parameters,
            statements=statements,
        )

    def parse_lambda_parameters(self) -> node.LambdaParameters:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-lambdaParameters

        lambdaParameters:
            lambdaParameter {{NL} ',' {NL} lambdaParameter} [{NL} ',']
        """
        parameters = [self.parse_lambda_parameter()]
        while self._try_accept(NL, ","):
            if self._would_accept_either(EOF, (NL, "->")):
                break
            parameters.append(self.parse_lambda_parameter())
        return parameters

    def parse_lambda_parameter(self) -> node.LambdaParameter:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-lambdaParameter

        lambdaParameter:
            variableDeclaration
            | (multiVariableDeclaration [{NL} ':' {NL} type])
        """
        param_type: Optional[Type] = None
        if self._would_accept("("):
            variable = self.parse_multi_variable_declaration()
            if self._try_accept(NL, ":", NL):
                param_type = self.parse_type()
        else:
            variable = self.parse_variable_declaration()
            param_type = variable.type
        return node.LambdaParameter(
            position=variable.position,
            variable=variable,
            type=param_type,
        )

    def parse_anonymous_function(self) -> node.AnonymousFunction:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-anonymousFunction

        anonymousFunction:
            'fun'
            [{NL} type {NL} '.']
            {NL}
            parametersWithOptionalType
            [{NL} ':' {NL} type]
            [{NL} typeConstraints]
            [{NL} functionBody]
        """
        token = self._accept("fun", NL)

        try:
            with self.tokens:
                receiver = self.parse_type()
                self._accept(NL, ".", NL)
        except ParserException:
            receiver = None

        parameters = self.parse_parameters_with_optional_type()

        if self._try_accept(NL, ":", NL):
            fun_type = self.parse_type()
        else:
            fun_type = None

        if self._would_accept(NL, "where"):
            constraints = self.parse_type_constraints()
        else:
            constraints = tuple()

        if self._would_accept_either((NL, "{"), (NL, "=")):
            body = self.parse_function_body()
        else:
            body = None

        return node.AnonymousFunction(
            position=token.position,
            receiver=receiver,
            parameters=parameters,
            type=fun_type,
            constraints=constraints,
            body=body,
        )

    def parse_function_literal(self) -> node.FunctionLiteral:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-functionLiteral

        functionLiteral:
            lambdaLiteral | anonymousFunction
        """
        if self._would_accept("{"):
            return self.parse_lambda_literal()
        if self._would_accept("fun"):
            return self.parse_anonymous_function()
        self._raise("expecting a lambda literal or anonymous function")

    def parse_object_literal(self) -> node.ObjectLiteral:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-objectLiteral

        objectLiteral:
            'object' [{NL} ':' {NL} delegationSpecifiers {NL}] [{NL} classBody]
        """
        token = self._accept("object")

        if self._try_accept(NL, ":", NL):
            supertypes = self.parse_delegation_specifiers()
        else:
            supertypes = tuple()

        if self._would_accept(NL, "{"):
            self._consume_new_lines()
            body = self.parse_class_body()
        else:
            body = None

        return node.ObjectLiteral(
            position=token.position,
            supertypes=supertypes,
            body=body,
        )

    def parse_this_expression(self) -> node.ThisExpression:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-thisExpression

        thisExpression:
            'this' | THIS_AT
        """
        if self._would_accept("this@"):
            token = self._accept("this@")
            label = self.parse_simple_identifier().value
        else:
            token = self._accept("this")
            label = None
        return node.ThisExpression(
            position=token.position,
            label=label,
        )

    def parse_super_expression(self) -> node.SuperExpression:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-ifExpression

        superExpression:
            ('super' ['<' {NL} type {NL} '>'] [AT_NO_WS simpleIdentifier]) | SUPER_AT
        """
        if self._would_accept("super@"):
            token = self._accept("super@")
            label = self.parse_simple_identifier().value
            return node.SuperExpression(
                position=token.position,
                supertype=None,
                label=label,
            )

        token = self._accept("super")
        if self._try_accept("<", NL):
            supertype = self.parse_type()
            self._accept(NL, ">")
        else:
            supertype = None

        if self._try_accept(At):
            label = self.parse_simple_identifier().value
        else:
            label = None

        return node.SuperExpression(
            position=token.position,
            supertype=supertype,
            label=label,
        )

    def parse_if_expression(self) -> node.IfExpression:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-ifExpression

        ifExpression:
            'if' {NL} '(' {NL} expression {NL} ')' {NL}
            (controlStructureBody
            | ([controlStructureBody] {NL} [';'] {NL} 'else' {NL} (controlStructureBody | ';'))
            | ';')
        """
        token = self._accept("if", NL, "(", NL)
        condition = self.parse_expression()
        self._accept(NL, ")", NL)

        if_body: Optional[node.ControlStructureBody] = None
        else_body: Optional[node.ControlStructureBody] = None

        if self._would_accept(NL, "else"):
            pass
        elif not self._would_accept(";"):
            if_body = self.parse_control_structure_body()

        if self._try_accept(";") or self._would_accept(NL, "else"):
            # case: if expression is used in when expression entry without else
            # e.g.: when { x -> if { } else -> x }
            if self._would_accept(NL, "else", NL, "->"):
                pass
            elif self._try_accept(NL, "else", NL):
                if not self._try_accept(";"):
                    else_body = self.parse_control_structure_body()

        return node.IfExpression(
            position=token.position,
            condition=condition,
            if_body=if_body,
            else_body=else_body,
        )

    def parse_when_expression(self) -> node.WhenExpression:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-whenExpression

        whenExpression:
            'when'
            {NL}
            [whenSubject]
            {NL}
            '{'
            {NL}
            {whenEntry {NL}}
            {NL}
            '}'
        """
        token = self._accept("when", NL)

        if self._would_accept("("):
            subject = self.parse_when_subject()
        else:
            subject = None

        self._accept(NL, "{", NL)

        entries: Sequence[node.WhenEntry] = []
        while not self._would_accept(NL, "}"):
            self._consume_new_lines()
            entries.append(self.parse_when_entry())

        self._accept(NL, "}")

        return node.WhenExpression(
            position=token.position,
            subject=subject,
            entries=entries,
        )

    def parse_when_subject(self) -> node.WhenSubject:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-whenSubject

        whenSubject:
            '(' [{annotation} {NL} 'val' {NL} variableDeclaration {NL} '=' {NL}] expression ')'
        """
        token = self._accept("(")

        with self.tokens.simulate():
            _ = self.parse_annotations()
            accepting_val = self._would_accept(NL, "val")

        if accepting_val:
            annotations = self.parse_annotations()
            self._accept(NL, "val", NL)
            declaration = self.parse_variable_declaration()
            self._accept(NL, "=", NL)
        else:
            annotations = tuple()
            declaration = None

        value = self.parse_expression()
        self._accept(")")
        return node.WhenSubject(
            position=token.position,
            annotations=annotations,
            declaration=declaration,
            value=value,
        )

    def parse_when_entry(self) -> node.WhenEntry:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-whenEntry

        whenEntry:
            (whenCondition {{NL} ',' {NL} whenCondition} [{NL} ',']
                {NL} '->' {NL} controlStructureBody [semi])
            | ('else' {NL} '->' {NL} controlStructureBody [semi])
        """
        if self._would_accept("else"):
            token = self._accept("else")
            self._accept(NL, "->", NL)
            body = self.parse_control_structure_body()
            if self._would_accept(NL, ";"):
                self._consume_semi()
            return node.WhenElseEntry(
                position=token.position,
                body=body,
            )

        conditions = [self.parse_when_condition()]
        while self._try_accept(NL, ",", NL):
            if self._would_accept("->"):
                break
            conditions.append(self.parse_when_condition())

        self._accept(NL, "->", NL)
        body = self.parse_control_structure_body()
        if self._would_accept(NL, ";"):
            self._consume_semi()

        return node.WhenConditionEntry(
            position=conditions[0].position,
            conditions=conditions,
            body=body,
        )

    def parse_when_condition(self) -> node.WhenCondition:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-whenCondition

        whenCondition:
            expression
            | rangeTest
            | typeTest
        """
        if self._would_accept_either("in", "!in"):
            return self.parse_range_test()
        if self._would_accept_either("is", "!is"):
            return self.parse_type_test()
        return self.parse_expression()

    def parse_range_test(self) -> node.RangeTest:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-rangeTest

        rangeTest:
            inOperator {NL} expression
        """
        if not self._would_accept_either("in", "!in"):
            self._raise("expecting 'in' or '!in'")

        token = self._accept(Token, NL)
        operand = self.parse_expression()
        return node.RangeTest(
            position=token.position,
            operator=token.value,
            operand=operand,
        )

    def parse_type_test(self) -> node.TypeTest:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-typeTest

        typeTest:
            isOperator {NL} type
        """
        if not self._would_accept_either("is", "!is"):
            self._raise("expecting 'is' or '!is'")

        token = self._accept(Token, NL)
        operand = self.parse_type()
        return node.TypeTest(
            position=token.position,
            operator=token.value,
            operand=operand,
        )

    def parse_try_expression(self) -> node.TryExpression:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-tryExpression

        tryExpression:
            'try' {NL} block
            ((({NL} catchBlock {{NL} catchBlock}) [{NL} finallyBlock]) | ({NL} finallyBlock))
        """
        token = self._accept("try", NL)
        try_block = self.parse_block()

        catch_blocks: Sequence[node.CatchBlock] = []
        while self._would_accept(NL, "catch"):
            self._consume_new_lines()
            catch_blocks.append(self.parse_catch_block())

        if self._would_accept(NL, "finally"):
            self._consume_new_lines()
            finally_block = self.parse_finally_block()
        else:
            finally_block = None

        if not catch_blocks and not finally_block:
            self._raise("expecting a catch/finally block")

        return node.TryExpression(
            position=token.position,
            try_block=try_block,
            catch_blocks=catch_blocks,
            finally_block=finally_block,
        )

    def parse_catch_block(self) -> node.CatchBlock:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-catchBlock

        catchBlock:
            'catch'
            {NL}
            '('
            {annotation}
            simpleIdentifier
            ':'
            type
            [{NL} ',']
            ')'
            {NL}
            block
        """
        token = self._accept("catch")
        self._accept(NL, "(")
        annotations = self.parse_annotations()
        name = self.parse_simple_identifier().value
        self._accept(":")
        catch_type = self.parse_type()
        self._try_accept(NL, ",")
        self._accept(")", NL)
        block = self.parse_block()
        return node.CatchBlock(
            position=token.position,
            annotations=annotations,
            name=name,
            type=catch_type,
            block=block,
        )

    def parse_finally_block(self) -> node.FinallyBlock:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-finallyBlock

        finallyBlock:
            'finally' {NL} block
        """
        token = self._accept("finally", NL)
        block = self.parse_block()
        return node.FinallyBlock(
            position=token.position,
            block=block,
        )

    def parse_jump_expression(self) -> node.JumpExpression:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-jumpExpression

        jumpExpression:
            throwExpression | returnExpression | continueExpression | breakExpression
        """
        if self._would_accept("throw"):
            return self.parse_throw_expression()
        if self._would_accept_either("return", "return@"):
            return self.parse_return_expression()
        if self._would_accept_either("continue", "continue@"):
            return self.parse_continue_expression()
        if self._would_accept_either("break", "break@"):
            return self.parse_break_expression()
        self._raise("expecting a jump expression")

    def parse_throw_expression(self) -> node.ThrowExpression:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-jumpExpression

        throwExpression:
            'throw' {NL} expression
        """
        token = self._accept("throw", NL)
        expression = self.parse_expression()
        return node.ThrowExpression(
            position=token.position,
            expression=expression,
        )

    def parse_return_expression(self) -> node.ReturnExpression:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-jumpExpression

        returnExpression:
            ('return' | RETURN_AT) [expression]
        """
        if self._would_accept("return@"):
            token = self._accept("return@")
            label = self._accept(Identifier).value
        else:
            token = self._accept("return")
            label = None

        expression = self._try_parse(self.parse_expression)

        return node.ReturnExpression(
            position=token.position,
            label=label,
            expression=expression,
        )

    def parse_continue_expression(self) -> node.ContinueExpression:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-jumpExpression

        continueExpression:
            'continue' | CONTINUE_AT
        """
        if self._would_accept("continue@"):
            token = self._accept("continue@")
            label = self._accept(Identifier).value
        else:
            token = self._accept("continue")
            label = None

        return node.ContinueExpression(
            position=token.position,
            label=label,
        )

    def parse_break_expression(self) -> node.BreakExpression:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-jumpExpression

        breakExpression:
            'break' | BREAK_AT
        """
        if self._would_accept("break@"):
            token = self._accept("break@")
            label = self._accept(Identifier).value
        else:
            token = self._accept("break")
            label = None

        return node.BreakExpression(
            position=token.position,
            label=label,
        )

    def parse_callable_reference(self) -> node.CallableReference:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-callableReference

        callableReference:
            [receiverType] '::' {NL} (simpleIdentifier | 'class')
        """
        if not self._would_accept("::"):
            receiver = self.parse_receiver_type()
        else:
            receiver = None

        token = self._accept("::", NL)

        if self._try_accept("class"):
            member = "class"
        else:
            member = self.parse_simple_identifier().value

        return node.CallableReference(
            position=token.position,
            receiver=receiver,
            member=member,
        )

    def parse_modifiers(
            self,
            allowed_modifiers: Optional[Iterable[str]] = None
    ) -> node.Modifiers:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-modifiers

        modifiers:
            annotation | modifier {annotation | modifier}
        """
        if allowed_modifiers is not None:
            allowed = set(allowed_modifiers)
        else:
            allowed = MODIFIERS

        modifiers: node.Modifiers = []
        while True:
            if self._would_accept_either(*allowed):
                # edge case: when variable name is a modifier
                # e.g. syntax is ({modifiers} name) and tokens are (value)
                # we will reject `value` and let it be parsed as identifier
                if self._would_accept_either((Token, NL, ")"),
                                             (Token, NL, ":")):
                    break
                modifier = self._accept(Token).value
                modifiers.append(modifier)
            elif self._would_accept(NL, At):
                modifier = self.parse_annotation()
                modifiers.append(modifier)
            else:
                break  # pragma: no cover
            self._consume_new_lines()

        if not modifiers:
            return tuple()
        return modifiers

    def parse_annotations(
        self,
        allowed_targets: Optional[Sequence[str]] = None
    ) -> Sequence[node.Annotation]:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-annotation

        annotations:
            {annotation}
        """
        annotations: Sequence[node.Annotation] = []
        while self._would_accept(NL, At):
            annotations.append(self.parse_annotation(allowed_targets))
        return annotations

    def parse_annotation(
            self,
            allowed_targets: Optional[Sequence[str]] = None
    ) -> node.Annotation:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-annotation

        annotation:
            (singleAnnotation | multiAnnotation) {NL}
        """
        token = self._accept(NL, At)

        if allowed_targets is None:
            targets = ("file", "field", "property", "get", "set", "receiver",
                       "param", "setparam", "delegate")
        else:
            targets = allowed_targets

        for target in targets:
            if self._try_accept(target, NL, ":", NL):
                break
        else:
            target = None

        if not self._try_accept("["):
            unescaped = self.parse_unescaped_annotation()
            self._consume_new_lines()
            return node.SingleAnnotation(
                position=token.position,
                target=target,
                name=unescaped.name,
                arguments=unescaped.arguments,
            )

        annotations = [self.parse_unescaped_annotation()]
        while not self._try_accept("]"):
            annotations.append(self.parse_unescaped_annotation())
        self._consume_new_lines()

        return node.MultiAnnotation(
            position=token.position,
            target=target,
            sequence=annotations,
        )

    def parse_unescaped_annotation(self) -> node.UnescapedAnnotation:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-unescapedAnnotation

        unescapedAnnotation:
            constructorInvocation | userType
        """
        def is_type_ahead() -> bool:
            # this handles form of (@Annotation type), for example:
            # - @Annotation () -> Unit
            # - @Annotation (() -> Unit)
            # we don't want to consume `()` as it is used in function type
            # however we want to consume it if the form is @Annotation() () -> Unit
            try:
                with self.tokens.simulate():
                    ahead = self.parse_type()
            except ParserException:
                return False

            while isinstance(ahead, (node.Type, node.ParenthesizedType)):
                ahead = ahead.subtype
            return isinstance(ahead, (node.FunctionType, node.NullableType))

        user_type = self.parse_user_type()
        if self._would_accept("("):
            if is_type_ahead():
                arguments = tuple()
            else:
                arguments = self.parse_value_arguments()
        else:
            arguments = tuple()
        return node.UnescapedAnnotation(
            position=user_type.position,
            name=str(user_type),
            arguments=arguments,
        )

    def parse_simple_identifier(self) -> node.SimpleIdentifier:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-simpleIdentifier

        simpleIdentifier:
            Identifier | SoftKeyword
        """
        token = self._accept(Identifier)
        return node.SimpleIdentifier(
            position=token.position,
            value=token.value,
        )

    def parse_identifier(self) -> node.Identifier:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-identifier

        identifier:
            simpleIdentifier {{NL} '.' simpleIdentifier}
        """
        token = self._accept(Identifier)
        idents = [token.value]
        while self._would_accept(NL, ".", Identifier):
            self._accept(NL, ".")
            idents.append(self._accept(Identifier).value)

        return node.Identifier(
            position=token.position,
            value=".".join(idents),
        )

    def _raise(self,
               message: str,
               token: Optional[Token] = None,
               verbose: bool = True) -> NoReturn:
        """Raise ParserException with message.

        Args:
            - message:
                Exception message.
            - token:
                Token to be reported in the verbose error message. If set to
                None, last token in the buffer will be used.
            - verbose:
                If set to False, the message will not be altered.

        Raises:
            ParserException
        """
        if not verbose:
            raise ParserException(message)

        if token is None:
            token = self.tokens.peek()

        if isinstance(token, EOF):
            message = f"{message}, but reached end of file"
        else:
            message = f"{message}, but found {repr(str(token))} at {token.position!s}"

        raise ParserException(message)

    def _accept(self,
                *acceptables: AcceptableType,
                consume: bool = True,
                raise_error: bool = True) -> Optional[Token]:
        """Accept specified tokens.

        Args:
            - *acceptables: Tokens to be accepted.
            - consume: If set to True and acceptable tokens match the current
                state, move the state forward. Otherwise the state is not
                modified.
            - raise_error: If set to True, raises ParserException if acceptable
                tokens don't match tokens in current state.

        Returns:
            A Token object which is the first non-optional token found in the
            current state. For example:

            *acceptables = A (Optional) B, current state = A B
            It will return token A.

            If current state does not match the acceptable tokens, returns None.

        Raises:
            - ParserException: if raise_error is set to True and acceptable
                tokens don't match tokens in current state.
        """

        offset = 0
        found_token: Optional[Token] = None

        for acceptable in acceptables:
            current_token = self.tokens.peek(offset)

            optional = acceptable == NL
            if optional:
                if not isinstance(current_token, NewLine):
                    continue

            if current_token != acceptable:
                if raise_error:
                    if isinstance(acceptable, type):
                        expected = f"{acceptable.__name__} token"
                    else:
                        expected = repr(acceptable)
                    self._raise(f"expecting {expected}")
                return None

            offset += 1
            if optional:
                while isinstance(self.tokens.peek(offset), NewLine):
                    offset += 1
            elif found_token is None:
                found_token = current_token

        if not consume:
            return found_token

        for _ in range(offset):
            try:
                next(self.tokens)
            except StopIteration:
                break
        return found_token

    def _try_accept(self, *acceptables: AcceptableType) -> bool:
        return self._accept(*acceptables, consume=True,
                            raise_error=False) is not None

    def _would_accept(self, *acceptables: AcceptableType) -> bool:
        return self._accept(*acceptables, consume=False,
                            raise_error=False) is not None

    def _would_accept_either(
            self, *acceptables: Union[AcceptableType,
                                      Iterable[AcceptableType]]) -> bool:
        for accept in acceptables:
            if isinstance(accept, (str, type)):
                if self._would_accept(accept):
                    return True
            else:
                if self._would_accept(*accept):
                    return True
        return False

    def _try_parse(self, *parse_funcs: ParseFunc) -> Optional[node.NodeType]:
        """Attempt to parse a node with specified parse functions. Token state
        will be reset and not modified from current state if all functions
        failed.

        Args:
            *parse_funcs: Functions which will be called to parse.

        Returns:
            NodeType object returned from first successful called function.
            None if all functions failed to parse.
        """
        for parse_func in parse_funcs:
            try:
                with self.tokens:
                    return parse_func()
            except ParserException:
                pass
        return None

    def _consume_semi(self, optional: bool = True) -> None:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-semi

        semi:
            ((';' | NL) {NL}) | EOF
        """
        if self._try_accept(EOF):
            return
        if self._try_accept(";") or self._try_accept(NewLine):
            pass
        elif not optional:
            self._raise("expecting a semicolon ';' or a new line")
        self._consume_new_lines()

    def _consume_semis(self, optional: bool = True) -> None:
        """Reference:
        https://kotlinlang.org/spec/syntax-and-grammar.html#grammar-rule-semis

        semis:
            (';' | NL {';' | NL}) | EOF
        """
        if self._try_accept(EOF):
            return
        if self._try_accept(";") or self._try_accept(NewLine):
            pass
        elif not optional:
            self._raise("expecting a semicolon ';' or a new line")
        while self._try_accept(";") or self._try_accept(NewLine):
            pass

    def _consume_new_lines(self) -> None:
        while self._try_accept(NewLine):
            pass

    def _get_declaration_type(self) -> Optional[Type[node.Declaration]]:
        def is_anonymous_fun() -> bool:
            try:
                self._accept("fun")
                if self._would_accept(NL, "<"):
                    return False

                with self.tokens:
                    self.parse_type()
                return self._would_accept(NL, ".", NL, "(")
            except ParserException:
                pass
            return not self._would_accept(Identifier)

        ret = None
        with self.tokens.simulate():
            _ = self.parse_modifiers()
            if self._would_accept_either("class", "interface",
                                         ("fun", NL, "interface")):
                ret = node.ClassDeclaration
            elif self._would_accept("object", NL, Identifier):
                ret = node.ObjectDeclaration
            elif self._would_accept("fun"):
                if not is_anonymous_fun():
                    ret = node.FunctionDeclaration
            elif self._would_accept_either("val", "var"):
                ret = node.PropertyDeclaration
            elif self._would_accept("typealias"):
                ret = node.TypeAlias
        return ret

    def _is_accepting_declaration(self) -> bool:
        return self._get_declaration_type() is not None

    def _is_accepting_loop_statement(self) -> bool:
        return self._would_accept_either("for", "while", "do")

    def _is_accepting_annotated_lambda(self) -> bool:
        with self.tokens.simulate():
            _ = self.parse_annotations()
            _ = self._try_accept(Identifier, At)
            return self._would_accept(NL, "{")

    def _parse_ambiguous_receiver(
        self
    ) -> Tuple[Optional[node.SimpleIdentifier], Optional[node.ReceiverType]]:
        """A helper to parse ambiguous receiver and identifier syntax:
        [{NL} receiverType {NL} '.'] {NL} simpleIdentifier.

        Returns:
            A tuple of: identifier (None if identifier was not consumed)
            and a receiver (None if failed to parse a receiver).
        """
        def is_name_consumed(receiver: node.ReceiverType) -> bool:
            return (isinstance(receiver.subtype, node.TypeReference)
                    and isinstance(receiver.subtype.subtype, node.UserType)
                    and len(receiver.subtype.subtype) > 0
                    and len(receiver.subtype.subtype[-1].generics) == 0
                    and not self._would_accept(NL, "."))

        def consumed_identifier(
                receiver: node.ReceiverType) -> node.SimpleIdentifier:
            ident_type = receiver.subtype.subtype[-1]
            ident = node.SimpleIdentifier(
                value=str(ident_type),
                position=ident_type.position,
            )
            return ident

        def remove_receiver_name(
                receiver: node.ReceiverType) -> Optional[node.ReceiverType]:
            user_type: node.UserType = receiver.subtype.subtype
            if len(user_type) == 1:
                return None
            user_type = node.UserType(
                position=user_type.position,
                sequence=tuple(user_type[i]
                               for i in range(len(user_type) - 1)),
            )
            type_reference: node.TypeReference = receiver.subtype
            type_reference = node.TypeReference(
                position=type_reference.position,
                subtype=user_type,
            )
            return node.ReceiverType(
                position=receiver.position,
                modifiers=receiver.modifiers,
                subtype=type_reference,
            )

        receiver = self._try_parse(self.parse_receiver_type)
        if receiver is not None and is_name_consumed(receiver):
            ident = consumed_identifier(receiver)
            receiver = remove_receiver_name(receiver)
        else:
            ident = None
        return ident, receiver
