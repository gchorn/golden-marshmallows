# golden-marshmallows
A better integration between SQLAlchemy and Marshmallow. A little (SQL)alchemy to turn `marshmallow`s into gold.

# Installation
Simply install with `pip`:
```
$ pip install golden-marshmallows
```
# Usage
## Serialization
Take these SQLAlchemy models as examples:
```python
class WizardCollege(Base):
    __tablename__ = 'wizard_college'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    alchemists = relationship('Alchemist')

    def __repr__(self):
        return '<WizardCollege(name={self.name!r})>'.format(self=self)

class Alchemist(Base):
    __tablename__ = 'alchemists'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    school_id = Column(Integer, ForeignKey('wizard_college.id'))
    formulae = relationship('Formula')

    def __repr__(self):
        return '<Alchemist(name={self.name!r})>'.format(self=self)

class Formula(Base):
    __tablename__ = 'forumulae'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    author_id = Column(Integer, ForeignKey('alchemists.id'))

    def __repr__(self):
        return '<Formula(title={self.title!r})>'.format(self=self)
```
The `GoldenSchema` class allows quick and easy generation of `marshmallow` schemas that can be used for SQLAlchemy object serialization/deserialization. Simply pass the model class on initialization and you're ready to go:
```python
import json
from golden_marshmallows.schema import GoldenSchema
from models import Alchemist, Formula, WizardCollege

alchemist = Alchemist(name='Albertus Magnus', school_id=1)
session.add(alchemist)
session.flush()

schema = GoldenSchema(Alchemist)

serialized = schema.dump(alchemist).data

print(json.dump(serialized, indent=4))
# {
#     "id": 1,
#     "name": "Albertus Magnus",
#     "school_id": 1
# }
```
That's it! No need to define your own `Schema` subclass, unless you really want to (more on that below).

## Nested objects
But what about this alchemist's formulae? Nested objects can easily be added to the mix by passing in a dictionary mapping each field that contains a nested object (or objects) to the relevant SQLAlchemy class:
```python
nested_map = {
    'formulae': {
        'class': Formula,
        'many': True
    }
}

formula = Formula(title='transmutation')
alchemist.formulae.append(formula)
session.commit()

schema = GoldenSchema(Alchemist, nested_map=nested_map)

serialized = schema.dump(alchemist).data

print(json.dump(serialized, indent=4))
# {
#     "id": 1,
#     "name": "Albertus Magnus",
#     "school_id": 1,
#     "formulae" : [
#         {
#             "title": "transmutation"
#         }
#     ]
# }
```
In fact, the `GoldenSchema` class supports arbitrary nesting in this fashion, simply adjust the map as necessary:
```python
nested_map = {
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

college = WizardCollege(name='Bogwarts')
college.alchemists.append(alchemist)
session.add(college)
session.flush()

schema = GoldenSchema(WizardCollege, nested_map=nested_map)

serialized = schema.dump(college).data

print(json.dump(serialized, indent=4))
# {
#     "id": 1,
#     "name": "Bogwarts",
#     "alchemists": [
#         {
#             "id": 1,
#             "school_id": 1,
#             "name": "Albertus Magnus",
#             "formulae": [
#                 {
#                     "title": "transmutation",
#                     "author_id": 1,
#                     "id": 1
#                 }
#             ]
#         }
#     ]
# }
```
You may need more control over the `GoldenSchema` instances that are nested into your top-level schema in the `nested_map` parameter. If that's the case, you can simply create a nested `GoldenSchema` instance and pass it in directly like so:
```python
from marshmallow.fields import List, String


FormulaSchema = GoldenSchema(Formula)


class FormulaSchemaWithIngredients(FormulaSchema):
    ingredients = List(String())


nested_map = {
    'formulae': {
        'class': FormulaSchemaWithIngredients,
        'many': True
    }
}

alchemist = session.query(Alchemist).first()
formula = alchemist.formulae[0]
formula.ingredients = ['lead', 'magic']

schema = GoldenSchema(Alchemist, nested_map=nested_map)

serialized = schema.dump(alchemist).data

print(json.dump(serialized, indent=4))
# {
#     "id": 1,
#     "name": "Albertus Magnus",
#     "school_id": 1,
#     "formulae" : [
#         {
#             "title": "transmutation",
#             "ingredients": [
#                 "lead",
#                 "magic"
#             ]
#         }
#     ]
# }
```
## Deserialization
Of course, you can deserialize data into SQLAlchemy objects just as easily:
```python
# Start at the end of the last example and work backwards
data = {
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

college = schema.load(data).data
print(college)
# <WizardCollege(name='Bogwarts')>
print(college.alchemists)
# [<Alchemist(name='Albertus Magnus')>]
print(college.alchemists[0].formulae)
# [<Formula(title='transmutation')>]
```
# Extra Features
## camelCasing/snake_casing
The `snake_to_camel` flag allows serde to/from camelCase, for example when serializing Python data into JSON to send as an API Response:
```python
# `Formula.author_id` is easily converted to camelCase
schema = GoldenSchema(Formula, snake_to_camel=True)

serialized = schema.dump(formula).data

print(json.dumps(serialized, indent=4))
# Notice `author_id` has become `authorId`
# {
#     "title": "transmutation",
#     "authorId": 1,
#     "id": 1
# }
```
The same `GoldenSchema` instance, when used to `load` (deserialize) data, will expect camelCased attributes and load them as snake_cased attributes:
```python
data = {
    "title": "transmutation",
    "authorId": 1,
    "id": 1
}
formula = schema.load(data).data

print(formula.author_id)
# 1
```
A flag with the opposite behavior, `camel_to_snake`, is also included.

This feature also works for manually declared fields; that is, fields you yourself declare when subclassing `GoldenSchema` like so:
```python
class MySchema(GoldenSchema):
    manually_declared = fields.Function(lambda obj: 'my special value')

my_schema = MySchema(Formula, snake_to_camel=True)

serialized = schema.dump(formula).data
print(json.dumps(serialized, indent=4))
# `manually_declared` has become camelCase
# {
#     "title": "transmutation",
#     "authorId": 1,
#     "id": 1,
#     "manuallyDeclared": "my special value"
# }
```
In fact, you can use this feature without involving SQLAlchemy at all; just use `CaseChangingSchema`, the parent class of `GoldenSchema`:
```python
from golden_marshmallows.schema import CaseChangingSchema

class SnakeSchema(CaseChangingSchema):
    attr_one = fields.String()
    attr_two = fields.Integer()

class SnakeObj:
    def __init__(self, attr_one, attr_two):
        self.attr_one = attr_one
        self.attr_two = attr_two

schema = SnakeSchema(snake_to_camel=True)
obj = SnakeObj('field1', 2)

serialized = schema.dump(obj).data
print(json.dumps(serialized, indent=4))
# {
#     'attrOne': 'field1',
#     'attrTwo': 2
# }
```

## Copying objects
As a minor convenience, you can pass the `new_obj` flag on initialization to indicate that any fields named `id` should be ignored during deserialization:
```python
schema = GoldenSchema(Formula, snake_to_camel=True, new_obj=True)

data = {
    "title": "transmutation",
    "authorId": 1,
    "id": 1
}

new_formula = schema.load(data).data
print(new_formula.title)
# 'transmutation'
print(new_formula.id)  # None
```
This allows you to quickly deserialize data representations of existing objects into new copies.
