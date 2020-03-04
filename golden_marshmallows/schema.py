import re

from marshmallow import (
    fields, post_load, Schema)
from sqlalchemy.dialects.postgresql import (
    ARRAY as pgARRAY, BIGINT, ENUM, TIMESTAMP, UUID)
from sqlalchemy.sql.sqltypes import (
    ARRAY, Boolean, BOOLEAN, DATE, Integer, INTEGER, JSON, String, TEXT)


def camelcase(string):
    """ Convert a snake_cased string to camelCase. """
    if "_" not in string:
        return string

    return "".join([
        x.capitalize() if i > 0 else x
        for i, x in enumerate(string.split("_"))
    ])


def snakecase(string):
    """ Converts a camelCase string to snake_case """
    snaked = re.sub(r'([^A-Z]+?)([A-Z])(.)', r'\1_\2\3', string)
    return snaked.lower()


class EnumField(fields.Method):

    def __init__(self, snake_to_camel=False, camel_to_snake=True, **kwargs):
        if snake_to_camel and camel_to_snake:
            raise Exception(
                'Only one of snake_to_camel or camel_to_snake can be True')

        self.snake_to_camel = snake_to_camel
        self.camel_to_snake = camel_to_snake
        return super(EnumField, self).__init__(**kwargs)

    def _serialize(self, value, attr, obj):
        """ Serializes a SQLAlchemy ENUM type field.

        If the value of the field is not None, returns the `name`
        attribute of the field value.

        For example: `<UpdatePolicy.NO_UPDATES: 1>`, will serialize to
        "NO_UPDATES".
        """
        # By now attributes have been case-converted; this must be
        # reversed to access the original object attribute by name
        attribute = attr
        if self.snake_to_camel:
            attribute = snakecase(attr)
        if self.camel_to_snake:
            attribute = camelcase(attr)

        enum = getattr(obj, attribute)

        if enum is None:
            return None
        return enum.name


class CaseChangingSchema(Schema):
    """ Subclass of marshmallow.Schema whose instances can auto-convert
    from camelCase to snake_case or vice versa during SerDe.
    """

    def __init__(self, snake_to_camel=False, camel_to_snake=False,
                 *args, **kwargs):
        """ Initialize the Schema and set casing properties, then
        perform casing.

        Args:
            snake_to_camel (bool) - Whether to serialize from snake_case
                to camelCase and deserialize from camelCase to
                snake_case; only one of this or `camel_to_snake` should
                be set to True
            camel_to_snake (bool) - Whether to serialize from camelCase
                to snake_case and deserialize from snake_case to
                camelCase; only one of this or `snake_to_camel` should
                be set to True
        """
        if snake_to_camel and camel_to_snake:
            raise ValueError(
                'Only one of snake_to_camel or camel_to_snake can be True')

        self.snake_to_camel = snake_to_camel
        self.camel_to_snake = camel_to_snake

        # This will cause the Schema to actually raise errors by default
        kwargs.update({'strict': True})
        super(CaseChangingSchema, self).__init__(*args, **kwargs)

        self.alter_case()

    def alter_case(self):
        """ Convert all fields to load_from and dump_to the camelCase or
        snake_case version of each field name.
        """
        for name, field in self.declared_fields.items():

            if self.snake_to_camel:
                field.load_from = camelcase(name)
                field.dump_to = camelcase(name)
            elif self.camel_to_snake:
                field.load_from = snakecase(name)
                field.dump_to = snakecase(name)


class GoldenSchema(CaseChangingSchema):
    """ Subclass of CaseChangingSchema that auto-generates fields based
    on a passed-in SQLAlchemy class.

    Use it to avoid writing a new Schema sublcass when you're happy with
    the sensible defaults, or subclass to add/overwrite more customized
    additional fields.
    """

    FIELD_TYPE_MAP = {
        TEXT: fields.String,
        String: fields.String,
        JSON: fields.Raw,
        ENUM: EnumField,
        INTEGER: fields.Integer,
        Integer: fields.Integer,
        BIGINT: fields.Integer,
        TIMESTAMP: fields.DateTime,
        DATE: fields.Date,
        ARRAY: fields.List,
        pgARRAY: fields.List,
        BOOLEAN: fields.Boolean,
        Boolean: fields.Boolean,
        UUID: fields.UUID
    }

    def __init__(self, sqlalchemy_cls, nested_map={}, new_obj=False,
                 *args, **kwargs):
        """ Introspects and creates fields for each attribute of the
        given SQLAlchemy class.

        Args:
            sqlalchemy_cls (cls) - The SQLAlchemy class whose attributes
                will be auto-translated into Marshmallow fields for the
                top-level object type to be serialized/deserialized
            nested_map (dict) - A map of attributes on the top-level
                object type to SQLAlchemy classes used to serialize/
                deserialize related objects
            new_obj (bool) - Whether this instance will be used to
                deserialize to new objects; basically just skips adding
                any field named 'id'
        """
        super(GoldenSchema, self).__init__(*args, **kwargs)

        self.new_obj = new_obj

        self.sqlalchemy_cls = sqlalchemy_cls

        # Introspect the correct field types from the SQLAlchemy class
        columns = sqlalchemy_cls.__mapper__.columns._data

        # Auto-generate new fields from SQLAlchemy class columns
        fields = self.generate_fields(columns, nested_map)

        # Finally, add fields to Schema instance
        self.add_fields(fields)

    def generate_nested_fields(self, nested_map, new_fields):
        """ Auto-generate `Nested` Marshmallow fields using a field-to-
        SQLAlchemy class map.

        Each new `Nested` field is created with a GoldenSchema
        instance which will in turn create recursively nested fields.
        """
        for key, val in nested_map.items():
            fieldtype = fields.Nested(
                GoldenSchema(
                    val['class'],
                    nested_map=val.get('nested_map') or {},
                    snake_to_camel=self.snake_to_camel,
                    camel_to_snake=self.camel_to_snake,
                    many=val['many'],
                    new_obj=self.new_obj),
                many=val['many']
            )
            new_fields[key] = fieldtype

        return new_fields

    def generate_fields(self, columns, nested_map):
        """ Introspects and creates fields for each SQLAlchemy class
        column

        Args:
            columns (dict) - A map of column names to sqlalchemy.Column
                instances
            nested_map (dict) - A map of attributes on the top-level
                object type to SQLAlchemy classes used to serialize/
                deserialize related objects

        Returns:
            A dict that maps new field names to marshmallow.field.Field
        objects
        """
        new_fields = {}
        for key, val in columns.items():

            fieldtype = self.FIELD_TYPE_MAP[type(val.type)]

            # Handle list-type attributes
            if type(val.type) in [ARRAY, pgARRAY]:
                new_fields[key] = fieldtype(
                    self.FIELD_TYPE_MAP[type(val.type.item_type)],
                    allow_none=val.nullable)
            elif type(val.type) == ENUM:
                new_fields[key] = fieldtype(
                    snake_to_camel=self.snake_to_camel,
                    camel_to_snake=self.camel_to_snake,
                    allow_none=val.nullable)
            # Handle everything else
            else:
                new_fields[key] = fieldtype(allow_none=val.nullable)

        # Create nested fields using the passed-in `nested_map` param
        return self.generate_nested_fields(nested_map, new_fields)

    def add_fields(self, new_fields):
        """ Adds fields to the SQLAlchemySchema instance

        Args:
            new_fields (dict) - Map of new field names to
                marshmallow.field.Field objects
        """
        for name, field in new_fields.items():
            # Only add fields if they haven't already been defined (this
            # allows subclasses of this class to still define custom
            # fields)
            if name not in self.declared_fields:
                if self.new_obj and name == 'id':
                    continue

                field.attribute = name
                if self.snake_to_camel:
                    name = camelcase(name)
                elif self.camel_to_snake:
                    name = snakecase(name)

                self.fields[name] = field
                self.declared_fields[name] = field

    @post_load
    def make_sqlalchemy_object(self, data):
        """ Convert deserialized data into a new SQLAlchemy object. """
        return self.sqlalchemy_cls(**data)
