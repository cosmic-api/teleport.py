from unittest2 import TestCase

from copy import deepcopy

from teleport import *

array_schema = {
    "type": "array",
    "items": {
        "type": "boolean"
    }
}
struct_schema = {
    "type": "struct",
    "fields": [
        {
            "name": "foo",
            "schema": {"type": "boolean"}
        },
        {
            "name": "bar",
            "schema": {"type": "integer"}
        }
    ]
}
deep_schema = {
    "type": "array",
    "items": {
        "type": "struct",
        "fields": [
            {
                "name": "foo",
                "schema": {"type": "boolean"}
            },
            {
                "name": "bar",
                "schema": {"type": "integer"}
            }
        ]
    }
}
array_normalizer = SchemaTemplate().deserialize(array_schema)
struct_normalizer = SchemaTemplate().deserialize(struct_schema)
deep_normalizer = SchemaTemplate().deserialize(deep_schema)

class TestSchema(TestCase):

    def test_serialize_schema(self):
        self.assertEqual(array_schema, SchemaTemplate().serialize(array_normalizer))
        self.assertEqual(struct_schema, SchemaTemplate().serialize(struct_normalizer))
        self.assertEqual(deep_schema, SchemaTemplate().serialize(deep_normalizer))

    def test_schema_subclass_delegation(self):
        self.assertTrue(isinstance(SchemaTemplate().deserialize({"type": "integer"}), IntegerTemplate))
        self.assertTrue(isinstance(SchemaTemplate().deserialize({"type": "float"}), FloatTemplate))
        self.assertTrue(isinstance(SchemaTemplate().deserialize({"type": "boolean"}), BooleanTemplate))
        self.assertTrue(isinstance(SchemaTemplate().deserialize({"type": "string"}), StringTemplate))
        self.assertTrue(isinstance(SchemaTemplate().deserialize({"type": "binary"}), BinaryTemplate))
        self.assertTrue(isinstance(SchemaTemplate().deserialize({"type": "schema"}), SchemaTemplate))

    def test_schema_extra_parts(self):
        # struct with items
        s = deepcopy(array_schema)
        s["fields"] = struct_schema["fields"]
        with self.assertRaisesRegexp(ValidationError, "Unexpected fields"):
            SchemaTemplate().deserialize(s)
        # array with fields
        s = deepcopy(struct_schema)
        s["items"] = array_schema["items"]
        with self.assertRaisesRegexp(ValidationError, "Unexpected fields"):
            SchemaTemplate().deserialize(s)

    def test_schema_duplicate_fields(self):
        s = deepcopy(struct_schema)
        s["fields"][1]["name"] = "foo"
        with self.assertRaisesRegexp(ValidationError, "Duplicate fields"):
            SchemaTemplate().deserialize(s)

    def test_schema_not_struct(self):
        with self.assertRaisesRegexp(ValidationError, "Invalid schema: True"):
            SchemaTemplate().deserialize(True)

    def test_schema_unknown_type(self):
        with self.assertRaisesRegexp(ValidationError, "Unknown type"):
            SchemaTemplate().deserialize({"type": "number"})

    def test_deep_schema_validation_stack(self):
        # Test Python representatioon
        with self.assertRaisesRegexp(ValidationError, "\[0\]\[u'bar'\]"):
            deep_normalizer.normalize_data([{"foo": True, "bar": False}])
        # Test JSON representation
        try:
            deep_normalizer.normalize_data([{"foo": True, "bar": False}])
        except ValidationError as e:
            self.assertRegexpMatches(e.print_json(), '\[0\]\["bar"\]')


class TestFloat(TestCase):

    def test_normalize(self):
        self.assertEqual(FloatTemplate().deserialize(1), 1.0)
        self.assertEqual(FloatTemplate().deserialize(1.0), 1.0)
        with self.assertRaisesRegexp(ValidationError, "Invalid float"):
            FloatTemplate().deserialize(True)

    def test_serialize(self):
        self.assertEqual(FloatTemplate().serialize(1.1), 1.1)


class TestInteger(TestCase):

    def test_normalize(self):
        self.assertEqual(IntegerTemplate().deserialize(1), 1)
        self.assertEqual(IntegerTemplate().deserialize(1.0), 1)
        with self.assertRaisesRegexp(ValidationError, "Invalid integer"):
            IntegerTemplate().deserialize(1.1)

    def test_serialize(self):
        self.assertEqual(IntegerTemplate().serialize(1), 1)


class TestBoolean(TestCase):

    def test_normalize(self):
        self.assertEqual(BooleanTemplate().deserialize(True), True)
        with self.assertRaisesRegexp(ValidationError, "Invalid boolean"):
            BooleanTemplate().deserialize(0)

    def test_serialize(self):
        self.assertEqual(BooleanTemplate().serialize(True), True)


class TestString(TestCase):

    def test_string(self):
        self.assertEqual(StringTemplate().deserialize("omg"), u"omg")
        self.assertEqual(StringTemplate().deserialize(u"omg"), u"omg")
        with self.assertRaisesRegexp(ValidationError, "Invalid string"):
            StringTemplate().deserialize(0)
        with self.assertRaisesRegexp(UnicodeDecodeValidationError, "invalid start byte"):
            StringTemplate().deserialize("\xff")

    def test_serialize(self):
        self.assertEqual(StringTemplate().serialize("yo"), "yo")


class TestBinary(TestCase):

    def test_binary(self):
        self.assertEqual(BinaryTemplate().deserialize('YWJj'), "abc")
        self.assertEqual(BinaryTemplate().deserialize(u'YWJj'), "abc")
        with self.assertRaisesRegexp(ValidationError, "Invalid base64"):
            # Will complain about incorrect padding
            BinaryTemplate().deserialize("a")
        with self.assertRaisesRegexp(ValidationError, "Invalid binary"):
            BinaryTemplate().deserialize(1)

    def test_serialize(self):
        self.assertEqual(BinaryTemplate().serialize("abc"), "YWJj")


class TestArray(TestCase):

    def test_normalize(self):
        self.assertEqual(array_normalizer.normalize_data([True, False]), [True, False])
        with self.assertRaisesRegexp(ValidationError, "Invalid array"):
            array_normalizer.normalize_data(("no", "tuples",))
        with self.assertRaisesRegexp(ValidationError, "Invalid boolean"):
            array_normalizer.normalize_data([True, False, 1])


class TestStruct(TestCase):

    def test_normalize(self):
        res = struct_normalizer.normalize_data({"foo": True, "bar": 2.0})
        self.assertEqual(res, {"foo": True, "bar": 2})
        with self.assertRaisesRegexp(ValidationError, "Invalid struct"):
            struct_normalizer.normalize_data([])
        with self.assertRaisesRegexp(ValidationError, "Unexpected fields"):
            struct_normalizer.normalize_data({"foo": True, "barr": 2.0})


