import unittest

from kopyt import node
from . import TestParserBase


class TestParserClass(TestParserBase):
    def do_test(self,
                code: str,
                test_str: bool = True) -> node.ClassDeclaration:
        return super().do_test("parse_declaration",
                               code,
                               node.ClassDeclaration,
                               test_str=test_str)

    def do_test_exception(self, code: str) -> None:
        return super().do_test_exception("parse_class_declaration", code)

    def test_parser_class(self):
        code = "class Empty"
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("Empty", result.name)
        self.assertEqual(0, len(result.generics))
        self.assertIsNone(result.constructor)
        self.assertEqual(0, len(result.supertypes))
        self.assertEqual(0, len(result.constraints))
        self.assertIsNone(result.body)

    def test_parser_class_with_body(self):
        code = "class Body { }"
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("Body", result.name)
        self.assertEqual(0, len(result.generics))
        self.assertIsNone(result.constructor)
        self.assertEqual(0, len(result.supertypes))
        self.assertEqual(0, len(result.constraints))
        self.assertIsNotNone(result.body)

    def test_parser_class_with_body_semi(self):
        code = "class Body {;}"
        result = self.do_test(code, False)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("Body", result.name)
        self.assertEqual(0, len(result.generics))
        self.assertIsNone(result.constructor)
        self.assertEqual(0, len(result.supertypes))
        self.assertEqual(0, len(result.constraints))
        self.assertIsNotNone(result.body)

    def test_parser_class_annotations(self):
        code = "open class Empty"
        result = self.do_test(code)
        self.assertEqual(1, len(result.modifiers))
        self.assertEqual("Empty", result.name)
        self.assertEqual(0, len(result.generics))
        self.assertIsNone(result.constructor)
        self.assertEqual(0, len(result.supertypes))
        self.assertEqual(0, len(result.constraints))
        self.assertIsNone(result.body)

    def test_parser_class_constructor(self):
        code = "class Person(firstName: String)"
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("Person", result.name)
        self.assertEqual(0, len(result.generics))
        self.assertIsNotNone(result.constructor)
        self.assertEqual(1, len(result.constructor.parameters))
        self.assertEqual("firstName: String",
                         str(result.constructor.parameters[0]))
        self.assertEqual(0, len(result.supertypes))
        self.assertEqual(0, len(result.constraints))
        self.assertIsNone(result.body)

    def test_parser_class_constructor_argument_modifier(self):
        code = "class Rectangle(override val vertexCount: Int = 4)"
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("Rectangle", result.name)
        self.assertEqual(0, len(result.generics))
        self.assertIsNotNone(result.constructor)
        self.assertEqual(1, len(result.constructor.parameters))
        self.assertEqual("override val vertexCount: Int = 4",
                         str(result.constructor.parameters[0]))
        self.assertEqual(0, len(result.supertypes))
        self.assertEqual(0, len(result.constraints))
        self.assertIsNone(result.body)

    def test_parser_class_explicit_constructor(self):
        code = "class Person constructor(firstName: String, lastName: String)"
        result = self.do_test(code, False)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("Person", result.name)
        self.assertEqual(0, len(result.generics))
        self.assertIsNotNone(result.constructor)
        self.assertEqual(2, len(result.constructor.parameters))
        self.assertEqual("firstName: String",
                         str(result.constructor.parameters[0]))
        self.assertEqual("lastName: String",
                         str(result.constructor.parameters[1]))
        self.assertEqual(0, len(result.supertypes))
        self.assertEqual(0, len(result.constraints))
        self.assertIsNone(result.body)

    def test_parser_class_constructor_default_value(self):
        code = "class Person(val firstName: String, val lastName: String, var isEmployed: Boolean = true)"
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("Person", result.name)
        self.assertEqual(0, len(result.generics))
        self.assertIsNotNone(result.constructor)
        self.assertEqual(3, len(result.constructor.parameters))
        self.assertEqual("val firstName: String",
                         str(result.constructor.parameters[0]))
        self.assertEqual("val lastName: String",
                         str(result.constructor.parameters[1]))
        self.assertEqual("var isEmployed: Boolean = true",
                         str(result.constructor.parameters[2]))
        self.assertEqual(0, len(result.supertypes))
        self.assertEqual(0, len(result.constraints))
        self.assertIsNone(result.body)

    def test_parser_class_constructor_modifiers(self):
        code = "class Person private constructor(name: String)"
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("Person", result.name)
        self.assertEqual(0, len(result.generics))
        self.assertIsNotNone(result.constructor)
        self.assertEqual(1, len(result.constructor.modifiers))
        self.assertEqual(1, len(result.constructor.parameters))
        self.assertEqual("name: String", str(result.constructor.parameters[0]))
        self.assertEqual(0, len(result.supertypes))
        self.assertEqual(0, len(result.constraints))
        self.assertIsNone(result.body)

    def test_parser_class_constructor_annotations(self):
        code = "class Person @Suppress private constructor(name: String)"
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("Person", result.name)
        self.assertEqual(0, len(result.generics))
        self.assertIsNotNone(result.constructor)
        self.assertEqual(2, len(result.constructor.modifiers))
        self.assertEqual(1, len(result.constructor.parameters))
        self.assertEqual("name: String", str(result.constructor.parameters[0]))
        self.assertEqual(0, len(result.supertypes))
        self.assertEqual(0, len(result.constraints))
        self.assertIsNone(result.body)

    def test_parser_class_inheritance(self):
        code = "class Derived : Base"
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("Derived", result.name)
        self.assertEqual(0, len(result.generics))
        self.assertIsNone(result.constructor)
        self.assertIsNotNone(result.supertypes)
        self.assertEqual("Base", str(result.supertypes[0]))
        self.assertEqual(0, len(result.constraints))
        self.assertIsNone(result.body)

    def test_parser_class_inheritance_annotations(self):
        code = "class Derived : @Annotation Base"
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("Derived", result.name)
        self.assertEqual(0, len(result.generics))
        self.assertIsNone(result.constructor)
        self.assertIsNotNone(result.supertypes)
        self.assertEqual(1, len(result.supertypes[0].annotations))
        self.assertEqual("@Annotation Base", str(result.supertypes[0]))
        self.assertEqual(0, len(result.constraints))
        self.assertIsNone(result.body)

    def test_parser_class_inheritance_with_constructor(self):
        code = "class Derived(p: Int) : Base(p)"
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("Derived", result.name)
        self.assertEqual(0, len(result.generics))
        self.assertIsNotNone(result.constructor)
        self.assertIsNotNone(result.supertypes)
        self.assertEqual("Base(p)", str(result.supertypes[0]))
        self.assertEqual(0, len(result.constraints))
        self.assertIsNone(result.body)

    def test_parser_class_inheritance_with_constructor_multilines(self):
        code = """\
class Derived
<
    T
>
(
    p: Int
)
:
Base
<
    T,
>
(
    p,
)"""
        result = self.do_test(code, False)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("Derived", result.name)
        self.assertEqual(1, len(result.generics))
        self.assertIsNotNone(result.constructor)
        self.assertIsNotNone(result.supertypes)
        self.assertEqual("Base<T>(p)", str(result.supertypes[0]))
        self.assertEqual(0, len(result.constraints))
        self.assertIsNone(result.body)

    def test_parser_class_generic(self):
        code = "class Array<T>(val size: Int)"
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("Array", result.name)
        self.assertIsNotNone(result.generics)
        self.assertEqual("<T>", str(result.generics))
        self.assertIsNotNone(result.constructor)
        self.assertEqual(0, len(result.supertypes))
        self.assertEqual(0, len(result.constraints))
        self.assertIsNone(result.body)

    def test_parser_class_generic_with_type(self):
        code = "class Array<in T: Iterable>(val size: Int)"
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("Array", result.name)
        self.assertIsNotNone(result.generics)
        self.assertEqual("<in T: Iterable>", str(result.generics))
        self.assertIsNotNone(result.constructor)
        self.assertEqual(0, len(result.supertypes))
        self.assertEqual(0, len(result.constraints))
        self.assertIsNone(result.body)

    def test_parser_class_generic_with_type_trailing_comma(self):
        code = """\
class Array<
        in K: Iterable,
        out V: Iterable,
    >(val size: Int)
"""
        result = self.do_test(code, False)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("Array", result.name)
        self.assertIsNotNone(result.generics)
        self.assertEqual(2, len(result.generics))
        self.assertEqual("in K: Iterable", str(result.generics[0]))
        self.assertEqual("out V: Iterable", str(result.generics[1]))
        self.assertIsNotNone(result.constructor)
        self.assertEqual(0, len(result.supertypes))
        self.assertEqual(0, len(result.constraints))
        self.assertIsNone(result.body)

    def test_parser_class_generic_constraint(self):
        code = "class Array<T>(val size: Int) where T : CharSequence"
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("Array", result.name)
        self.assertIsNotNone(result.generics)
        self.assertIsNotNone(result.constructor)
        self.assertEqual(0, len(result.supertypes))
        self.assertIsNotNone(result.constraints)
        self.assertEqual("where T : CharSequence", str(result.constraints))
        self.assertIsNone(result.body)

    def test_parser_class_generic_constraint_annotations(self):
        code = "class Array<T>(val size: Int) where @Annotation T : CharSequence"
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("Array", result.name)
        self.assertIsNotNone(result.generics)
        self.assertIsNotNone(result.constructor)
        self.assertEqual(0, len(result.supertypes))
        self.assertIsNotNone(result.constraints)
        self.assertEqual("where @Annotation T : CharSequence",
                         str(result.constraints))
        self.assertIsNone(result.body)

    def test_parser_class_delegation(self):
        code = "class Derived(b: Base) : Base by b"
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("Derived", result.name)
        self.assertEqual(0, len(result.generics))
        self.assertIsNotNone(result.constructor)
        self.assertIsNotNone(result.supertypes)
        self.assertEqual(1, len(result.supertypes))
        self.assertIsInstance(result.supertypes[0].delegate,
                              node.ExplicitDelegation)
        self.assertEqual("Base by b", str(result.supertypes[0]))
        self.assertIsNone(result.body)

    def test_parser_class_exception(self):
        codes = [
            "fun A",
            "class Derived(b: Base) : 1",
        ]
        for code in codes:
            with self.subTest(code=code):
                self.do_test_exception(code)


class TestParserEnumDeclaration(TestParserBase):
    def do_test(self,
                code: str,
                test_str: bool = True) -> node.EnumDeclaration:
        return super().do_test("parse_declaration",
                               code,
                               node.EnumDeclaration,
                               test_str=test_str)

    def test_parser_enum(self):
        code = """\
enum class Direction {
    NORTH,
    SOUTH,
    WEST,
    EAST
}"""
        result = self.do_test(code)
        self.assertEqual("Direction", result.name)
        self.assertIsNone(result.constructor)
        self.assertIsNotNone(result.body)
        self.assertIsInstance(result.body, node.EnumClassBody)
        self.assertEqual(4, len(result.body.entries))
        self.assertEqual("NORTH", str(result.body.entries[0]))
        self.assertEqual("SOUTH", str(result.body.entries[1]))
        self.assertEqual("WEST", str(result.body.entries[2]))
        self.assertEqual("EAST", str(result.body.entries[3]))
        self.assertEqual(0, len(result.body.members))

    def test_parser_enum_empty(self):
        code = """\
enum class Empty { }"""
        result = self.do_test(code)
        self.assertEqual("Empty", result.name)
        self.assertIsNone(result.constructor)
        self.assertIsNotNone(result.body)
        self.assertEqual(0, len(result.body.entries))
        self.assertEqual(0, len(result.body.members))

    def test_parser_enum_entries_arguments(self):
        code = """\
enum class Color(val rgb: Int) {
    RED(0xFF0000),
    GREEN(0x00FF00),
    BLUE(0x0000FF)
}"""
        result = self.do_test(code)
        self.assertEqual("Color", result.name)
        self.assertIsNotNone(result.constructor)
        self.assertIsNotNone(result.body)
        self.assertIsInstance(result.body, node.EnumClassBody)
        self.assertEqual(3, len(result.body.entries))
        for entry in result.body.entries:
            self.assertIsNotNone(entry.arguments)
            self.assertEqual(len(entry.arguments), 1)
            self.assertIsNone(entry.body)
        self.assertEqual(0, len(result.body.members))

    def test_parser_enum_entries_trailing_comma(self):
        code = """\
enum class RGB {
    RED,
    GREEN,
    @Inject
    BLUE,
}"""
        result = self.do_test(code, False)
        self.assertEqual("RGB", result.name)
        self.assertIsNone(result.constructor)
        self.assertIsNotNone(result.body)
        self.assertIsInstance(result.body, node.EnumClassBody)
        self.assertEqual(3, len(result.body.entries))
        self.assertEqual("RED", str(result.body.entries[0]))
        self.assertEqual("GREEN", str(result.body.entries[1]))
        self.assertEqual("@Inject BLUE", str(result.body.entries[2]))
        self.assertEqual(0, len(result.body.members))

    def test_parser_enum_entries_body(self):
        code = """\
enum class RGB {
    RED { },
    GREEN { },
    BLUE { }
}"""
        result = self.do_test(code)
        self.assertEqual("RGB", result.name)
        self.assertIsNone(result.constructor)
        self.assertIsNotNone(result.body)
        self.assertIsInstance(result.body, node.EnumClassBody)
        self.assertEqual(3, len(result.body.entries))
        for entry in result.body.entries:
            self.assertIsNotNone(entry.body)
        self.assertEqual(0, len(result.body.members))

    def test_parser_enum_entries_and_members(self):
        code = """\
enum class ProtocolState {
    WAITING,
    TALKING;

    val x = 1
}"""
        result = self.do_test(code)
        self.assertEqual("ProtocolState", result.name)
        self.assertIsNone(result.constructor)
        self.assertIsNotNone(result.body)
        self.assertIsInstance(result.body, node.EnumClassBody)
        self.assertEqual(2, len(result.body.entries))
        self.assertIsNotNone(result.body.members)
        self.assertEqual(1, len(result.body.members))


class TestParserInterface(TestParserBase):
    def do_test(self,
                code: str,
                test_str: bool = True) -> node.InterfaceDeclaration:
        return super().do_test("parse_declaration",
                               code,
                               node.InterfaceDeclaration,
                               test_str=test_str)

    def test_parser_interface(self):
        code = "interface Empty"
        result = self.do_test(code)
        self.assertEqual("Empty", result.name)


class TestParserFunctionalInterface(TestParserBase):
    def do_test(self,
                code: str,
                test_str: bool = True) -> node.FunctionalInterfaceDeclaration:
        return super().do_test("parse_declaration",
                               code,
                               node.FunctionalInterfaceDeclaration,
                               test_str=test_str)

    def test_parser_functional_interface(self):
        code = "fun interface Empty"
        result = self.do_test(code)
        self.assertEqual("Empty", result.name)


class TestParserClassMember(TestParserBase):
    def do_test(self,
                code: str,
                expected_type: type,
                test_str: bool = True) -> node.ClassMemberDeclaration:
        return super().do_test("parse_class_member_declaration",
                               code,
                               expected_type,
                               test_str=test_str)

    def do_test_exception(self, code: str) -> None:
        return super().do_test_exception("parse_class_member_declaration",
                                         code)

    def test_parser_class_member_declaration(self):
        codes = ("val A = B", )
        for code in codes:
            with self.subTest(code=code):
                self.do_test(code, node.Declaration)

    def test_parser_class_member_companion_object(self):
        code = "companion object"
        result = self.do_test(code, node.CompanionObject)
        self.assertIsNone(result.name)
        self.assertIsNone(result.body)
        self.assertEqual(0, len(result.interfaces))

    def test_parser_class_member_companion_object_named(self):
        code = "companion object Factory"
        result = self.do_test(code, node.CompanionObject)
        self.assertEqual("Factory", result.name)
        self.assertIsNone(result.body)
        self.assertEqual(0, len(result.interfaces))

    def test_parser_class_member_companion_object_modifiers(self):
        code = "private companion object Factory"
        result = self.do_test(code, node.CompanionObject)
        self.assertEqual(1, len(result.modifiers))
        self.assertEqual("Factory", result.name)
        self.assertIsNone(result.body)
        self.assertEqual(0, len(result.interfaces))

    def test_parser_class_member_companion_object_body(self):
        codes = [
            "companion object { }",
            "companion object Factory { }",
        ]
        for code in codes:
            with self.subTest(code=code):
                result = self.do_test(code, node.CompanionObject)
                self.assertIsNotNone(result.body)
                self.assertEqual(0, len(result.interfaces))

    def test_parser_class_member_companion_object_interfaces(self):
        codes = [
            "companion object : Factory<MyClass>",
            "companion object Named : Factory<A>, Factory<B>",
        ]
        for code in codes:
            with self.subTest(code=code):
                result = self.do_test(code, node.CompanionObject)
                self.assertIsNotNone(result.interfaces)
                self.assertTrue(len(result.interfaces) > 0)

    def test_parser_class_member_anonymous_initializer(self):
        code = "init { }"
        result = self.do_test(code, node.AnonymousInitializer)
        self.assertIsNotNone(result.body)

    def test_parser_class_member_fun(self):
        code = "override fun foo() { }"
        result = self.do_test(code, node.FunctionDeclaration)
        self.assertIsNotNone(result.body)

    def test_parser_class_member_interface(self):
        code = "private interface foo { }"
        result = self.do_test(code, node.InterfaceDeclaration)
        self.assertIsNotNone(result.body)

    def test_parser_class_member_secondary_constructor(self):
        code = "constructor()"
        result = self.do_test(code, node.SecondaryConstructor)
        self.assertEqual(0, len(result.modifiers))
        self.assertIsNone(result.body)
        self.assertEqual(0, len(result.parameters))

    def test_parser_class_member_secondary_constructor_modifiers(self):
        code = "private constructor()"
        result = self.do_test(code, node.SecondaryConstructor)
        self.assertEqual(1, len(result.modifiers))
        self.assertIsNone(result.body)
        self.assertEqual(0, len(result.parameters))

    def test_parser_class_member_secondary_constructor_parameters(self):
        code = "constructor(foo: A, bar: B)"
        result = self.do_test(code, node.SecondaryConstructor)
        self.assertEqual(0, len(result.modifiers))
        self.assertIsNone(result.body)
        self.assertEqual(2, len(result.parameters))
        self.assertEqual("foo", result.parameters[0].name)
        self.assertEqual("A", str(result.parameters[0].type))
        self.assertEqual("bar", result.parameters[1].name)
        self.assertEqual("B", str(result.parameters[1].type))

    def test_parser_class_member_secondary_constructor_body(self):
        code = "constructor() { }"
        result = self.do_test(code, node.SecondaryConstructor)
        self.assertEqual(0, len(result.modifiers))
        self.assertIsNotNone(result.body)

    def test_parser_class_member_secondary_constructor_delegation(self):
        codes = [
            "constructor() : this()",
            "constructor() : super(1) { }",
        ]
        for code in codes:
            with self.subTest(code=code):
                result = self.do_test(code, node.SecondaryConstructor)
                self.assertIsNotNone(result.delegation)

    def test_parser_class_member_secondary_constructor_delegation_expecting_this_or_super(
            self):
        code = "constructor() : foo()"
        self.do_test_exception(code)

    def test_parser_class_member_unexpected_statement(self):
        codes = [
            "println(1)",
        ]
        for code in codes:
            with self.subTest(code=code):
                self.do_test_exception(code)


if __name__ == "__main__":
    unittest.main()
