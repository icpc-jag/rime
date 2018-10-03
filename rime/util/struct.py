#!/usr/bin/python


class Struct(dict):
    """Dictionary-like object allowing attribute access."""

    def __getattribute__(self, name):
        try:
            return super(Struct, self).__getattribute__(name)
        except AttributeError as e:
            try:
                return self[name]
            except KeyError:
                pass
            raise e
