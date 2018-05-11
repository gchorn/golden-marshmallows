import pytest
from marshmallow import fields
from sqlalchemy.orm import scoped_session, sessionmaker

from .sqlalchemy_classes import (
    Alchemist, CamelFormula, engine, Formula, WizardCollege)
from golden_marshmallows.schema import CaseChangingSchema, GoldenSchema


class SnakeSchema(CaseChangingSchema):
    attr_one = fields.String()
    attr_two = fields.Integer()


class CamelSchema(CaseChangingSchema):
    attrOne = fields.String()
    attrTwo = fields.Integer()


class SnakeObj:
    def __init__(self, attr_one, attr_two):
        self.attr_one = attr_one
        self.attr_two = attr_two


class CamelObj:
    def __init__(self, attr_one, attr_two):
        self.attrOne = attr_one
        self.attrTwo = attr_two


class TestCaseChangingSchema:

    def test_camel_casing(self):
        tschema = SnakeSchema(snake_to_camel=True)
        tobj = SnakeObj('field1', 2)

        expected = {
            'attrOne': 'field1',
            'attrTwo': 2
        }
        result = tschema.dump(tobj).data

        assert result == expected

    def test_snake_casing(self):
        tschema = CamelSchema(camel_to_snake=True)
        tobj = CamelObj('field1', 2)

        expected = {
            'attr_one': 'field1',
            'attr_two': 2
        }
        result = tschema.dump(tobj).data

        assert result == expected


class TestGoldenSchema:

    def setup_method(self):
        self.session = scoped_session(sessionmaker(bind=engine))

        self.school = WizardCollege(id=1, name='Bogwarts')
        self.alchemist = Alchemist(id=1, name='Albertus Magnus')
        self.formula = Formula(id=1, title='transmutation')

        self.alchemist.formulae.append(self.formula)
        self.school.alchemists.append(self.alchemist)

        self.session.add(self.school)
        self.session.flush()

        self.nested_map = {
            'alchemists': {
                'class': Alchemist,
                'many': True,
                'nested_map': {
                    'formulae': {
                        'class': Formula,
                        'many': True
                    }
                }
            }
        }

    def teardown_method(self):
        self.session.close()

    def test_serialization(self):
        gs = GoldenSchema(WizardCollege, nested_map=self.nested_map)

        serialized = gs.dump(self.school).data

        expected = {
            "id": 1,
            "name": "Bogwarts",
            "alchemists": [
                {
                    "formulae": [
                        {
                            "title": "transmutation",
                            "author_id": 1,
                            "id": 1
                        }
                    ],
                    "school_id": 1,
                    "id": 1,
                    "name": "Albertus Magnus"
                }
            ]
        }

        assert serialized == expected

    def test_deserialization(self):
        gs = GoldenSchema(WizardCollege, nested_map=self.nested_map)

        serialized = {
            "id": 1,
            "name": "Bogwarts",
            "alchemists": [
                {
                    "formulae": [
                        {
                            "title": "transmutation",
                            "author_id": 1,
                            "id": 1
                        }
                    ],
                    "school_id": 1,
                    "id": 1,
                    "name": "Albertus Magnus"
                }
            ]
        }

        college = gs.load(serialized).data

        assert isinstance(college, WizardCollege)
        assert college.id == 1
        assert college.name == 'Bogwarts'
        assert len(college.alchemists) == 1

        alchemist = college.alchemists[0]

        assert isinstance(alchemist, Alchemist)
        assert alchemist.id == 1
        assert alchemist.name == 'Albertus Magnus'
        assert alchemist.school_id == 1
        assert len(alchemist.formulae) == 1

        formula = alchemist.formulae[0]

        assert isinstance(formula, Formula)
        assert formula.id == 1
        assert formula.title == 'transmutation'

    def test_deserialization_new_object(self):
        gs = GoldenSchema(
            Alchemist,
            nested_map=self.nested_map['alchemists']['nested_map'],
            new_obj=True)

        serialized = {
            'formulae': [
                {
                    'author_id': 1,
                    'id': 1,
                    'title': 'transmutation'
                }
            ],
            'id': 1,
            'name': 'Albertus Magnus'
        }

        deserialized = gs.load(serialized).data

        assert isinstance(deserialized, Alchemist)
        assert deserialized.id is None

        assert len(deserialized.formulae) == 1
        formula = deserialized.formulae[0]
        assert isinstance(formula, Formula)
        assert formula.id is None

    def test_serialize_snake_to_camel(self):
        gs = GoldenSchema(
            Alchemist,
            nested_map=self.nested_map['alchemists']['nested_map'],
            snake_to_camel=True)

        serialized = gs.dump(self.alchemist).data

        expected = {
            'formulae': [
                {
                    'authorId': 1,
                    'id': 1,
                    'title': 'transmutation'
                }
            ],
            'id': 1,
            'name': 'Albertus Magnus',
            'schoolId': 1
        }

        assert serialized == expected

    def test_serialize_camel_to_snake(self):
        gs = GoldenSchema(CamelFormula, nested_map=self.nested_map,
                          camel_to_snake=True)

        camel_formula = CamelFormula(
            id=1, title='transmutation', extraAttribute='value')

        serialized = gs.dump(camel_formula).data

        expected = {
            'extra_attribute': 'value',
            'id': 1,
            'title': 'transmutation'
        }

        assert serialized == expected

    def test_error_when_setting_both_casing_types(self):
        with pytest.raises(ValueError) as excinfo:
            GoldenSchema(Alchemist, camel_to_snake=True, snake_to_camel=True)

        assert ('Only one of snake_to_camel or camel_to_snake can be True' in
                str(excinfo.value))
