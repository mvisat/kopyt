import unittest

from kopyt import node
from . import TestParserBase


class TestParserProperty(TestParserBase):
    def do_test(
            self,
            code: str,
            test_str: bool = True,
            top_level_declaration: bool = True) -> node.PropertyDeclaration:
        return super().do_test(
            "parse_declaration",
            code,
            node.PropertyDeclaration,
            test_str=test_str,
            top_level_declaration=top_level_declaration,
        )

    def do_test_exception(self,
                          code: str,
                          top_level_declaration: bool = True) -> None:
        return super().do_test_exception(
            "parse_property_declaration",
            code,
            top_level_declaration=top_level_declaration,
        )

    def test_parser_property(self):
        code = "val simple: Int?"
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("val", result.mutability)
        self.assertEqual(0, len(result.generics))
        self.assertIsNone(result.receiver)
        self.assertIsInstance(result.declaration, node.VariableDeclaration)
        self.assertEqual("simple: Int?", str(result.declaration))
        self.assertEqual(0, len(result.constraints))
        self.assertIsNone(result.value)
        self.assertIsNone(result.delegate)
        self.assertIsNone(result.getter)
        self.assertIsNone(result.setter)

    def test_parser_property_modifiers(self):
        code = "@Annotated private val annotated: Int?"
        result = self.do_test(code)
        self.assertEqual(2, len(result.modifiers))
        self.assertEqual("val", result.mutability)
        self.assertEqual(0, len(result.generics))
        self.assertIsNone(result.receiver)
        self.assertIsInstance(result.declaration, node.VariableDeclaration)
        self.assertEqual("annotated: Int?", str(result.declaration))
        self.assertEqual(0, len(result.constraints))
        self.assertIsNone(result.value)
        self.assertIsNone(result.delegate)
        self.assertIsNone(result.getter)
        self.assertIsNone(result.setter)

    def test_parser_property_inferred(self):
        code = "var inferred = 1"
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("var", result.mutability)
        self.assertEqual(0, len(result.generics))
        self.assertIsNone(result.receiver)
        self.assertIsInstance(result.declaration, node.VariableDeclaration)
        self.assertEqual("inferred", str(result.declaration))
        self.assertEqual(0, len(result.constraints))
        self.assertIsNotNone(result.value)
        self.assertEqual("1", str(result.value))
        self.assertIsNone(result.delegate)
        self.assertIsNone(result.getter)
        self.assertIsNone(result.setter)

    def test_parser_property_destructure(self):
        code = "val (x) = X(1)"
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("val", result.mutability)
        self.assertEqual(0, len(result.generics))
        self.assertIsNone(result.receiver)
        self.assertIsInstance(result.declaration,
                              node.MultiVariableDeclaration)
        self.assertEqual("(x)", str(result.declaration))
        self.assertEqual(0, len(result.constraints))
        self.assertIsNotNone(result.value)
        self.assertEqual("X(1)", str(result.value))
        self.assertIsNone(result.delegate)
        self.assertIsNone(result.getter)
        self.assertIsNone(result.setter)

    def test_parser_property_destructure_multiple(self):
        code = "val (foo, bar: Int) get() = Tuple(1, 2)"
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("val", result.mutability)
        self.assertEqual(0, len(result.generics))
        self.assertIsNone(result.receiver)
        self.assertIsInstance(result.declaration,
                              node.MultiVariableDeclaration)
        self.assertEqual("(foo, bar: Int)", str(result.declaration))
        self.assertEqual(0, len(result.constraints))
        self.assertIsNone(result.value)
        self.assertIsNone(result.delegate)
        self.assertIsNotNone(result.getter)
        self.assertIsNone(result.setter)

    def test_parser_property_destructure_unexpected_type(self):
        code = "val (foo): bar = Baz(1)"
        self.do_test_exception(code)

    def test_parser_property_destructure_unexpected_type_multiple(self):
        code = "val (foo, bar: Int): Tuple get() = Tuple(1, 2)"
        self.do_test_exception(code)

    def test_parser_property_receiver(self):
        code = "val Int.foo: Int get() = this + 1"
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("val", result.mutability)
        self.assertEqual(0, len(result.generics))
        self.assertIsNotNone(result.receiver)
        self.assertEqual("Int", str(result.receiver))
        self.assertIsInstance(result.declaration, node.VariableDeclaration)
        self.assertEqual("foo: Int", str(result.declaration))
        self.assertEqual(0, len(result.constraints))
        self.assertIsNone(result.value)
        self.assertIsNone(result.delegate)
        self.assertIsNotNone(result.getter)
        self.assertIsNone(result.setter)

    def test_parser_property_parenthesized_receiver(self):
        code = "val (Int).foo: Int get() = this + 1"
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("val", result.mutability)
        self.assertEqual(0, len(result.generics))
        self.assertIsNotNone(result.receiver)
        self.assertEqual("(Int)", str(result.receiver))
        self.assertIsInstance(result.declaration, node.VariableDeclaration)
        self.assertEqual("foo: Int", str(result.declaration))
        self.assertEqual(0, len(result.constraints))
        self.assertIsNone(result.value)
        self.assertIsNone(result.delegate)
        self.assertIsNotNone(result.getter)
        self.assertIsNone(result.setter)

    def test_parser_property_nullable_receiver(self):
        code = "val String?.foo get() = this + \"bar\""
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("val", result.mutability)
        self.assertEqual(0, len(result.generics))
        self.assertIsNotNone(result.receiver)
        self.assertEqual("String?", str(result.receiver))
        self.assertIsInstance(result.declaration, node.VariableDeclaration)
        self.assertEqual("foo", str(result.declaration))
        self.assertEqual(0, len(result.constraints))
        self.assertIsNone(result.value)
        self.assertIsNone(result.delegate)
        self.assertIsNotNone(result.getter)
        self.assertIsNone(result.setter)

    def test_parser_property_receiver_unexpected_destructure(self):
        code = "val Int.(foo): Int get() = this + 1"
        self.do_test_exception(code)

    def test_parser_property_receiver_unexpected_destructure_parenthesized(
            self):
        code = "val (Int).(foo): Int get() = this + 1"
        self.do_test_exception(code)

    def test_parser_property_receiver_unexpected_destructure_nullable(self):
        code = "val Int?.(foo): Int get() = this + 1"
        self.do_test_exception(code)

    def test_parser_property_delegate(self):
        code = "val delegate by lazy { DelegateForObject() }"
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("val", result.mutability)
        self.assertEqual(0, len(result.generics))
        self.assertIsNone(result.receiver)
        self.assertIsInstance(result.declaration, node.VariableDeclaration)
        self.assertEqual("delegate", str(result.declaration))
        self.assertEqual(0, len(result.constraints))
        self.assertIsNone(result.value)
        self.assertIsNotNone(result.delegate)
        self.assertEqual("by lazy { DelegateForObject() }",
                         str(result.delegate))
        self.assertIsNone(result.getter)
        self.assertIsNone(result.setter)

    def test_parser_property_delegate_ignore_after_lambda(self):
        code = "val A = object : B by C() {}\noverride fun D() { }"
        result = self.do_test(code, False)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("val", result.mutability)
        self.assertEqual(0, len(result.generics))
        self.assertIsNone(result.receiver)
        self.assertIsInstance(result.declaration, node.VariableDeclaration)
        self.assertEqual("A", str(result.declaration))
        self.assertEqual(0, len(result.constraints))
        self.assertIsNotNone(result.value)
        self.assertEqual("object : B by C() {}", str(result.value))
        self.assertIsNone(result.delegate)
        self.assertIsNone(result.getter)
        self.assertIsNone(result.setter)

    def test_parser_property_getter(self):
        code = "val isEmpty: Boolean get"
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("val", result.mutability)
        self.assertEqual(0, len(result.generics))
        self.assertIsNone(result.receiver)
        self.assertIsInstance(result.declaration, node.VariableDeclaration)
        self.assertEqual("isEmpty: Boolean", str(result.declaration))
        self.assertEqual(0, len(result.constraints))
        self.assertIsNone(result.value)
        self.assertIsNone(result.delegate)
        self.assertIsNotNone(result.getter)
        self.assertIsNone(result.getter.body)
        self.assertIsNone(result.setter)

    def test_parser_property_getter_modifiers(self):
        code = "val isEmpty: Boolean private get() = this.size == 0"
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("val", result.mutability)
        self.assertEqual(0, len(result.generics))
        self.assertIsNone(result.receiver)
        self.assertIsInstance(result.declaration, node.VariableDeclaration)
        self.assertEqual("isEmpty: Boolean", str(result.declaration))
        self.assertEqual(0, len(result.constraints))
        self.assertIsNone(result.value)
        self.assertIsNone(result.delegate)
        self.assertIsNotNone(result.getter)
        self.assertEqual(1, len(result.getter.modifiers))
        self.assertIsNone(result.getter.type)
        self.assertIsNotNone(result.getter.body)
        self.assertIsNone(result.setter)

    def test_parser_property_getter_type(self):
        code = "val isEmpty get(): Boolean { }"
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("val", result.mutability)
        self.assertEqual(0, len(result.generics))
        self.assertIsNone(result.receiver)
        self.assertIsInstance(result.declaration, node.VariableDeclaration)
        self.assertEqual("isEmpty", str(result.declaration))
        self.assertEqual(0, len(result.constraints))
        self.assertIsNone(result.value)
        self.assertIsNone(result.delegate)
        self.assertIsNotNone(result.getter)
        self.assertIsNotNone(result.getter.type)
        self.assertIsNone(result.setter)

    def test_parser_property_getter_expression(self):
        code = "val isEmpty get() = true"
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("val", result.mutability)
        self.assertEqual(0, len(result.generics))
        self.assertIsNone(result.receiver)
        self.assertIsInstance(result.declaration, node.VariableDeclaration)
        self.assertEqual("isEmpty", str(result.declaration))
        self.assertEqual(0, len(result.constraints))
        self.assertIsNone(result.value)
        self.assertIsNone(result.delegate)
        self.assertIsNotNone(result.getter)
        self.assertIsNone(result.getter.type)
        self.assertIsNone(result.setter)

    def test_parser_property_setter(self):
        code = """\
var setterVisibility: String = "abc"
    private set"""
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("var", result.mutability)
        self.assertEqual(0, len(result.generics))
        self.assertIsNone(result.receiver)
        self.assertIsInstance(result.declaration, node.VariableDeclaration)
        self.assertEqual("setterVisibility: String", str(result.declaration))
        self.assertEqual(0, len(result.constraints))
        self.assertIsNotNone(result.value)
        self.assertIsNone(result.delegate)
        self.assertIsNone(result.getter)
        self.assertIsNotNone(result.setter)
        self.assertEqual(1, len(result.setter.modifiers))
        self.assertIsNone(result.setter.type)
        self.assertIsNone(result.setter.body)

    def test_parser_property_setter_type(self):
        code = """\
var setterVisibility: String = "abc"
    set(value): Unit { }"""
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("var", result.mutability)
        self.assertEqual(0, len(result.generics))
        self.assertIsNone(result.receiver)
        self.assertIsInstance(result.declaration, node.VariableDeclaration)
        self.assertEqual("setterVisibility: String", str(result.declaration))
        self.assertEqual(0, len(result.constraints))
        self.assertIsNotNone(result.value)
        self.assertIsNone(result.delegate)
        self.assertIsNone(result.getter)
        self.assertIsNotNone(result.setter)
        self.assertEqual(0, len(result.setter.modifiers))
        self.assertIsNotNone(result.setter.type)
        self.assertIsNotNone(result.setter.body)

    def test_parser_property_setter_parameter(self):
        code = """\
var setterVisibility: String = "abc"
    set(@Annotation value): Unit { }"""
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("var", result.mutability)
        self.assertEqual(0, len(result.generics))
        self.assertIsNone(result.receiver)
        self.assertIsInstance(result.declaration, node.VariableDeclaration)
        self.assertEqual("setterVisibility: String", str(result.declaration))
        self.assertEqual(0, len(result.constraints))
        self.assertIsNotNone(result.value)
        self.assertIsNone(result.delegate)
        self.assertIsNone(result.getter)
        self.assertIsNotNone(result.setter)
        self.assertEqual(0, len(result.setter.modifiers))
        self.assertIsNotNone(result.setter.parameter)
        self.assertEqual("@Annotation value", str(result.setter.parameter))
        self.assertIsNotNone(result.setter.type)
        self.assertIsNotNone(result.setter.body)

    def test_parser_property_setter_expression(self):
        code = """\
var setterVisibility: String = "abc"
    set(value) = 1"""
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("var", result.mutability)
        self.assertEqual(0, len(result.generics))
        self.assertIsNone(result.receiver)
        self.assertIsInstance(result.declaration, node.VariableDeclaration)
        self.assertEqual("setterVisibility: String", str(result.declaration))
        self.assertEqual(0, len(result.constraints))
        self.assertIsNotNone(result.value)
        self.assertIsNone(result.delegate)
        self.assertIsNone(result.getter)
        self.assertIsNotNone(result.setter)
        self.assertEqual(0, len(result.setter.modifiers))
        self.assertIsNone(result.setter.type)
        self.assertIsNotNone(result.setter.body)

    def test_parser_property_getter_setter(self):
        code = """\
var stringRepresentation: String
    get() = this.toString()
    set(value): Unit {
        setDataFromString(value)
    }"""
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("var", result.mutability)
        self.assertEqual(0, len(result.generics))
        self.assertIsNone(result.receiver)
        self.assertIsInstance(result.declaration, node.VariableDeclaration)
        self.assertEqual("stringRepresentation: String",
                         str(result.declaration))
        self.assertEqual(0, len(result.constraints))
        self.assertIsNone(result.value)
        self.assertIsNone(result.delegate)
        self.assertIsNotNone(result.getter)
        self.assertIsNone(result.getter.type)
        self.assertIsNotNone(result.getter.body)
        self.assertIsNotNone(result.setter)
        self.assertIsNotNone(result.setter.type)
        self.assertIsNotNone(result.setter.body)

    def test_parser_property_getter_duplicate(self):
        code = """\
val isEmpty: Boolean
    get() = this.size == 0
    get() = this.size == 0"""
        self.do_test_exception(code)

    def test_parser_property_setter_duplicate(self):
        code = """\
val isEmpty: Boolean
    set(value) = 1
    set(value) = 2"""
        self.do_test_exception(code)

    def test_parser_property_getter_without_body(self):
        code = """\
val isEmpty: Boolean
    get()"""
        self.do_test_exception(code)

    def test_parser_property_setter_without_body(self):
        code = """\
val isEmpty: Boolean
    set(value)"""
        self.do_test_exception(code)

    def test_parser_property_constraints(self):
        code = """\
val <T> List<T>.foo: T where T : CharSequence
    get(): T = this[0]"""
        result = self.do_test(code)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("val", result.mutability)
        self.assertIsNotNone(result.generics)
        self.assertEqual("<T>", str(result.generics))
        self.assertIsNotNone(result.receiver)
        self.assertEqual("List<T>", str(result.receiver))
        self.assertIsInstance(result.declaration, node.VariableDeclaration)
        self.assertEqual("foo: T", str(result.declaration))
        self.assertIsNotNone(result.constraints)
        self.assertEqual("where T : CharSequence", str(result.constraints))
        self.assertIsNone(result.value)
        self.assertIsNone(result.delegate)
        self.assertIsNotNone(result.getter)
        self.assertIsNone(result.setter)

    def test_parser_property_expecting_val_or_var(self):
        code = "isEmpty: Boolean"
        self.do_test_exception(code)

    def test_parser_property_local_declaration_ignoring_getter(self):
        code = """\
var x = 1
get()"""
        result = self.do_test(code, False, False)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("var", result.mutability)
        self.assertEqual(0, len(result.generics))
        self.assertIsNone(result.receiver)
        self.assertIsInstance(result.declaration, node.VariableDeclaration)
        self.assertEqual("x", str(result.declaration))
        self.assertEqual(0, len(result.constraints))
        self.assertEqual("1", str(result.value))
        self.assertIsNone(result.delegate)
        self.assertIsNone(result.getter)
        self.assertIsNone(result.setter)

    def test_parser_property_local_ignoring_setter(self):
        code = """\
var x = 1
set(x, y)"""
        result = self.do_test(code, False, False)
        self.assertEqual(0, len(result.modifiers))
        self.assertEqual("var", result.mutability)
        self.assertEqual(0, len(result.generics))
        self.assertIsNone(result.receiver)
        self.assertIsInstance(result.declaration, node.VariableDeclaration)
        self.assertEqual("x", str(result.declaration))
        self.assertEqual(0, len(result.constraints))
        self.assertEqual("1", str(result.value))
        self.assertIsNone(result.delegate)
        self.assertIsNone(result.getter)
        self.assertIsNone(result.setter)


if __name__ == "__main__":
    unittest.main()
