import pytest

from pytwitcher import event


class TestEvent:
    def test___init__(self):
        func = lambda x: x
        instance = event.event('ABC', callback=func)
        assert instance.callback == func

    def test_decorator(self):
        func = lambda x: x
        instance = event.event('ABC')
        assert instance.callback is None
        decorated = instance(func)
        assert decorated.callback == func

    def test_regexp(self):
        func = lambda x: x
        decorated = event.event('ABC')(func)
        assert decorated.regexp == 'ABC'

    def test_raw_event(self):
        func = lambda x: x
        decorated = event.event(event.PRIVMSG)(func)
        assert decorated.key == event.PRIVMSG.re

    def test_compile_no_config(self):
        func = lambda x: x
        decorated = event.event(r'\S+')(func)
        matcher = decorated.compile()
        assert matcher('ABC') is not None
        assert matcher('ABC ') is None

    """
    def test_compile_config(self):
        func = lambda x: x
        decorated = event.event(r'{encoding}')(func)
        matcher = decorated.compile(#use fixture))
        assert matcher('utf8') is not None
        assert matcher('utf8 ') is None
    """
