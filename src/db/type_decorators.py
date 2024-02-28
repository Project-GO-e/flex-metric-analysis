
from enum import Enum
from typing import Type

from sqlalchemy import String, TypeDecorator


class MappedEnum(TypeDecorator):
    """
    Enables passing in a Python enum and storing the enum's *value* in the db.
    The default would have stored the enum's *name* (ie the string).
    """
    impl = String

    def __init__(self, enumtype: Type[Enum], *args, **kwargs):
        super(MappedEnum, self).__init__(*args, **kwargs)
        self._enumtype = enumtype

    def process_bind_param(self, name, dialect):
        if isinstance(name, str):
            return name
        return name.name

    def process_result_value(self, name, dialect):
        return self._enumtype[name]