#!/usr/bin/python


class ClassRegistry(object):
    def __init__(self, base_class=object):
        self.classes = {}
        self.base_class = base_class

    def Get(self, name):
        return self.classes.get(name)

    def Add(self, clazz, name=None):
        if name is None:
            name = clazz.__name__
        assert name not in self.classes
        assert issubclass(clazz, self.base_class)
        self.classes[name] = clazz

    def Override(self, name, clazz):
        assert name in self.classes
        assert issubclass(clazz, self.classes[name])
        self.classes[name] = clazz

    def __getattribute__(self, name):
        try:
            return super(ClassRegistry, self).__getattribute__(name)
        except AttributeError as e:
            try:
                return self.classes[name]
            except KeyError:
                pass
            raise e
