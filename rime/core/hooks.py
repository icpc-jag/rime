#!/usr/bin/python


class HookPoint(object):
    def __init__(self):
        self.hooks = []

    def __call__(self, *args, **kwargs):
        for hook in self.hooks:
            hook(*args, **kwargs)

    def Register(self, hook):
        self.hooks.append(hook)
        return hook


pre_command = HookPoint()
post_command = HookPoint()
