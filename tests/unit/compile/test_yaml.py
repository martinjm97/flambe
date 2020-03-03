import pytest
from ruamel.yaml.compat import StringIO

import flambe
from flambe.compile.yaml import load_config, dump_config, Registrable, YAMLLoadType, TagError
from flambe.compile.schema import Schema

class A:
    test_none = None
    test_attr = {}

    def __init__(self, x=None, y=None):
        self.x = x
        self.y = y
    @classmethod
    def from_other(cls, z=None):
        return cls(z, z)
    @classmethod
    def yaml_load_type(cls) -> str:
        return "schematic"
    def test_method(self):
        return self.x + self.y

class B:
    def __init__(self, *, x=None, y=None):
        self.x = x
        self.y = y
    @classmethod
    def from_other(cls, z=None):
        return cls(z, z)
    @classmethod
    def yaml_load_type(cls) -> str:
        return YAMLLoadType.KWARGS

class C:
    def __init__(self, *args, **kwargs):
        if len(kwargs) == 0:
            assert len(args) <= 1
            self.x = args[0] if len(args) > 0 else None
            self.y = None
        else:
            assert len(args) == 0
            self.x = kwargs['x']
            self.y = kwargs['y'] if 'y' in kwargs else None
    @classmethod
    def from_other(cls, z=None):
        return cls(z, z)
    @classmethod
    def yaml_load_type(cls) -> str:
        return "kwargs_or_arg"

class D:
    def __init__(self, x=None, y=None):
        self.x = x
        self.y = y
    @classmethod
    def from_other(cls, z=None):
        return cls(z, z)
    @classmethod
    def yaml_load_type(cls) -> str:
        return "kwargs_or_posargs"


class E:
    def __init__(self, x, *args, y=None):
        self.x = x
        self.args = args
        self.y = y
    @classmethod
    def yaml_load_type(cls) -> str:
        return "schematic"


class F:
    def __init__(self, x, *args):
        self.x = x
        self.args = args
    @classmethod
    def yaml_load_type(cls) -> str:
        return "schematic"

nothing = None
const = 3


def adder(x=None, y=None):
    return x+y if x is not None and y is not None else None


def load_one_config(config):
    return list(load_config(config))[0]


def dump_one_config(obj):
    return dump_config([obj])


class TestErrors:

    def test_missing_module(self):
        config = '!tes.units.compile.test_yaml.A\n'
        with pytest.raises(TagError):
            load_one_config(config)

    def test_bad_import_path(self):
        config = '!tests.units.compile.test_yaml.A\n'
        with pytest.raises(TagError):
            load_one_config(config)

    def test_none_ref(self):
        config = '!tests.unit.compile.test_yaml.nothing\n'
        with pytest.raises(TagError):
            load_one_config(config)

    def test_const_ref(self):
        config = '!tests.unit.compile.test_yaml.nothing\n'
        with pytest.raises(TagError):
            load_one_config(config)

    def test_bad_kwargs(self):
        configA = '!tests.unit.compile.test_yaml.A\nz: 4\n'
        configB = '!tests.unit.compile.test_yaml.B\nz: 4\n'
        configD = '!tests.unit.compile.test_yaml.D\nz: 4\n'
        for c in (configA, configB, configD):
            with pytest.raises(TypeError):
                load_one_config(c)

    def test_bad_posargs(self):
        configA = '!tests.unit.compile.test_yaml.A\n- 1\n- 2\n- 3\n'
        configB = '!tests.unit.compile.test_yaml.A\n- 1\n- 2\n- 3\n'
        configD = '!tests.unit.compile.test_yaml.A\n- 1\n- 2\n- 3\n'
        for c in (configA, configB, configD):
            with pytest.raises(TypeError):
                load_one_config(c)


class TestSchematic:

    def test_empty_args_load(self):
        config = '!tests.unit.compile.test_yaml.A\n'
        a_schema = load_one_config(config)
        assert isinstance(a_schema, Schema)
        assert len(a_schema.arguments) == 2
        assert all([x is None for x in a_schema.arguments.values()])

    def test_kwargs_load(self):
        config = '!tests.unit.compile.test_yaml.A {x: 5}\n'
        a_schema = load_one_config(config)
        assert isinstance(a_schema, Schema)
        assert len(a_schema.arguments) == 2
        assert a_schema['x'] == 5
        a = a_schema()
        assert a.x == 5
        assert a.y is None

    def test_empty_args_dump(self):
        config = '!tests.unit.compile.test_yaml.A\n'
        a_schema = load_one_config(config)
        expected_config = '!tests.unit.compile.test_yaml.A\nx:\ny:\n'
        assert expected_config == dump_one_config(a_schema)

    def test_nested_dump_two_trip(self):
        config = ("!tests.unit.compile.test_yaml.A\n"
                  "x: !tests.unit.compile.test_yaml.A\n"
                  "y:\n")
        expected_config = ("!tests.unit.compile.test_yaml.A\n"
                  "x: !tests.unit.compile.test_yaml.A\n"
                  "  x:\n"
                  "  y:\n"
                  "y:\n")
        b = load_one_config(config)
        dumped = dump_one_config(b)
        b = load_one_config(dumped)
        dumped = dump_one_config(b)
        assert expected_config == dumped

    def test_factory_nested_dump_two_trip(self):
        config = ("!tests.unit.compile.test_yaml.A.from_other\n"
                  "z: !tests.unit.compile.test_yaml.A\n")
        expected_config = ("!tests.unit.compile.test_yaml.A.from_other\n"
                  "z: !tests.unit.compile.test_yaml.A\n"
                  "  x:\n"
                  "  y:\n")
        b = load_one_config(config)
        dumped = dump_one_config(b)
        b = load_one_config(dumped)
        dumped = dump_one_config(b)
        assert expected_config == dumped

    def test_instance_method_fails(self):
        config = ("!tests.unit.compile.test_yaml.A.test_method\n")
        expected_config = ("!tests.unit.compile.test_yaml.A.test_method\n")
        with pytest.raises(TagError):
            b = load_one_config(config)

    def test_none_fails(self):
        config = ("!tests.unit.compile.test_yaml.A.test_none\n")
        expected_config = ("!tests.unit.compile.test_yaml.A.test_none\n")
        with pytest.raises(TagError):
            b = load_one_config(config)

    def test_non_callable_fails(self):
        config = ("!tests.unit.compile.test_yaml.A.test_attr\n")
        expected_config = ("!tests.unit.compile.test_yaml.A.test_attr\n")
        with pytest.raises(TagError):
            b = load_one_config(config)

    def test_function_empty(self):
        config = "!tests.unit.compile.test_yaml.adder\n"
        adder_schema = load_one_config(config)
        assert adder_schema['x'] is None
        assert adder_schema['y'] is None
        expected_config = "!tests.unit.compile.test_yaml.adder\nx:\ny:\n"
        dumped = dump_one_config(adder_schema)
        assert expected_config == dumped

    def test_function_with_args(self):
        config = "!tests.unit.compile.test_yaml.adder\nx: 3\ny: 4\n"
        the_sum = load_one_config(config)
        the_sum = the_sum()
        assert the_sum == 7

    def test_nested_dump_two_trip_pos_to_kw(self):
        config = ("!tests.unit.compile.test_yaml.A\n"
                  "- !tests.unit.compile.test_yaml.A\n"
                  "- Null\n")
        expected_config = ("!tests.unit.compile.test_yaml.A\n"
                  "x: !tests.unit.compile.test_yaml.A\n"
                  "  x:\n"
                  "  y:\n"
                  "y:\n")
        a = load_one_config(config)
        dumped = dump_one_config(a)
        a = load_one_config(dumped)
        dumped = dump_one_config(a)
        assert expected_config == dumped

    def test_nested_dump_two_trip_varpos_to_kw(self):
        config = ("!tests.unit.compile.test_yaml.E\n"
                  "- !tests.unit.compile.test_yaml.E\n"
                  "  - Null\n"
                  "- Null\n")
        expected_config = ("!tests.unit.compile.test_yaml.E\n"
                  "0: !tests.unit.compile.test_yaml.E\n"
                  "  x:\n"
                  "  y:\n"
                  "1:\n"
                  "y:\n")
        a = load_one_config(config)
        dumped = dump_one_config(a)
        assert expected_config == dumped
        a = load_one_config(dumped)
        dumped = dump_one_config(a)
        assert expected_config == dumped

    def test_nested_dump_two_trip_varpos_to_kw(self):
        config = ("!tests.unit.compile.test_yaml.F\n"
                  "- !tests.unit.compile.test_yaml.F\n"
                  "  - Null\n"
                  "- Null\n")
        expected_config = ("!tests.unit.compile.test_yaml.F\n"
                  "- !tests.unit.compile.test_yaml.F\n"
                  "  x:\n"
                  "- \n")
        a = load_one_config(config)
        y = flambe.compile.yaml.SchematicLoader.to_yaml(a)
        dumped = dump_one_config(y)
        assert expected_config == dumped
        a = load_one_config(dumped)
        dumped = dump_one_config(a)
        assert expected_config == dumped


class TestKwargs:

    def test_empty_args(self):
        config = '!tests.unit.compile.test_yaml.B'
        b = load_one_config(config)
        assert isinstance(b, B)

    def test_empty_args_dump(self):
        config = '!tests.unit.compile.test_yaml.B'
        b = load_one_config(config)
        dumped = dump_one_config(b)
        expected_config = '!tests.unit.compile.test_yaml.B {}\n'
        assert expected_config == dumped

    def test_nested_dump_two_trip(self):
        config = ("!tests.unit.compile.test_yaml.B\n"
                  "x: !tests.unit.compile.test_yaml.B\n"
                  "y:\n")
        expected_config = ("!tests.unit.compile.test_yaml.B\n"
                  "x: !tests.unit.compile.test_yaml.B {}\n"
                  "y:\n")
        b = load_one_config(config)
        dumped = dump_one_config(b)
        b = load_one_config(dumped)
        dumped = dump_one_config(b)
        assert expected_config == dumped


class TestKwargsOrArg:

    def test_empty_args(self):
        config = '!tests.unit.compile.test_yaml.C\n'
        c = load_one_config(config)
        assert isinstance(c, C)

    def test_empty_args_dump(self):
        config = '!tests.unit.compile.test_yaml.C\n'
        c = load_one_config(config)
        dumped = dump_one_config(c)
        expected_config = '!tests.unit.compile.test_yaml.C {}\n'
        assert expected_config == dumped

    def test_nested_dump_two_trip(self):
        config = ("!tests.unit.compile.test_yaml.C\n"
                  "x: !tests.unit.compile.test_yaml.C\n"
                  "y:\n")
        expected_config = ("!tests.unit.compile.test_yaml.C\n"
                  "x: !tests.unit.compile.test_yaml.C {}\n"
                  "y:\n")
        c = load_one_config(config)
        dumped = dump_one_config(c)
        c = load_one_config(dumped)
        dumped = dump_one_config(c)
        assert expected_config == dumped

class TestKwargsOrPosArgs:

    def test_empty_args(self):
        config = '!tests.unit.compile.test_yaml.D\n'
        d = load_one_config(config)
        # assert False
        assert isinstance(d, D)

    def test_empty_args_dump(self):
        config = '!tests.unit.compile.test_yaml.D\n'
        d = load_one_config(config)
        dumped = dump_one_config(d)
        expected_config = '!tests.unit.compile.test_yaml.D {}\n'
        assert expected_config == dumped

    def test_nested_dump_two_trip(self):
        config = ("!tests.unit.compile.test_yaml.D\n"
                  "x: !tests.unit.compile.test_yaml.D\n"
                  "y:\n")
        expected_config = ("!tests.unit.compile.test_yaml.D\n"
                  "x: !tests.unit.compile.test_yaml.D {}\n"
                  "y:\n")
        d = load_one_config(config)
        dumped = dump_one_config(d)
        d = load_one_config(dumped)
        dumped = dump_one_config(d)
        assert expected_config == dumped