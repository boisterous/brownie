# coding: utf-8
"""
    brownie.proxies
    ~~~~~~~~~~~~~~~

    :copyright: 2010 by Daniel Neuhäuser
    :license: BSD, see LICENSE for details
"""
import textwrap
from functools import partial
from itertools import repeat

from brownie.itools import starmap
from brownie.datastructures import missing


#: All special methods with exception of :meth:`__new__` and :meth:`__init__`.
SPECIAL_METHODS = frozenset([
    # conversions
    '__str__',     # str()
    '__unicode__', # unicode()

    '__complex__', # complex()
    '__int__',     # int()
    '__long__',    # long()
    '__float__',   # float()
    '__oct__',     # oct()
    '__hex__',     # hex()

    '__nonzero__', # truth-testing, bool()
    '__index__',   # slicing, operator.index()
    '__coerce__',  # mixed-mode numeric arithmetic

    # comparisons
    '__lt__',  # <
    '__le__',  # <=
    '__eq__',  # ==
    '__ne__',  # !=
    '__gt__',  # >
    '__ge__',  # >=
    '__cmp__', # cmp()

    # hashability, required if ==/!= are implemented
    '__hash__', # hash()

    # descriptors
    '__get__',
    '__set__',
    '__delete__',

    # container
    '__len__',      # len()
    '__getitem__',  # ...[]
    '__setitem__',  # ...[] = ...
    '__delitem__',  # del ...[]
    '__iter__',     # iter()
    '__reversed__', # reversed()
    '__contains__'  # ... in ...

    # slicing (deprecated)
    '__getslice__',
    '__setslice__',
    '__delslice__',

    # numeric/arithmetic
    # regular       reversed         augmented assignment
    '__add__',      '__radd__',      '__iadd__',
    '__sub__',      '__rsub__',      '__isub__',
    '__mul__',      '__rmul__',      '__imul__',
    '__div__',      '__rdiv__',      '__idiv__',
    '__truediv__',  '__rtruediv__',  '__itruediv__'
    '__floordiv__', '__rfloordiv__', '__ifloordiv__',
    '__mod__',      '__rmod__',      '__imod__',
    '__divmod__',   '__rdivmod__',   '__ipow__',
    '__pow__',      '__rpow__',      '__ipow__',
    '__lshift__',   '__rlshift__',   '__ilshift__',
    '__rshift__',   '__rrshift__',   '__rlshift__',
    '__and__',      '__rand__',      '__iand__',
    '__xor__',      '__rxor__',      '__ixor__',
    '__or__',       '__ror__',       '__ior__',

    # unary arithmetic
    '__neg__',   # -
    '__pos__',   # +
    '__abs__',   # abs()
    '__invert__' # ~

    # overriding type checks
    '__instancecheck__', # isinstance()
    '__issubclass__',    # issubclass()

    '__call__', # ...()

    # context manager
    '__enter__',
    '__exit__'
])


class ProxyMeta(type):
    def _set_private(self, name, obj):
        setattr(self, '_ProxyBase__' + name, obj)

    def method(self, handler):
        self._set_private('method_handler', handler)

    def getattr(self, handler):
        self._set_private('getattr_handler', handler)

    def setattr(self, handler):
        self._set_private('setattr_handler', handler)

    def repr(self, repr_handler):
        self._set_private('repr_handler', repr_handler)


class ProxyBase(object):
    def __init__(self, proxied):
        self.__proxied = proxied

    def __method_handler(self, proxied, name, *args, **kwargs):
        return missing

    def __getattr_handler(self, proxied, name):
        return getattr(proxied, name)

    def __setattr_handler(self, proxied, name, obj):
        return setattr(proxied, name, obj)

    def __repr_handler(self, proxied):
        return repr(proxied)

    def __getattribute__(self, name):
        if name.startswith('_ProxyBase__'):
            return object.__getattribute__(self, name)
        return self.__getattr_handler(self.__proxied, name)

    def __setattr__(self, name, obj):
        if name.startswith('_ProxyBase__'):
            return object.__setattr__(self, name, obj)
        return self.__setattr_handler(self.__proxied, name, obj)

    def __repr__(self):
        return self.__repr_handler(self.__proxied)

    method_template = textwrap.dedent("""
        def %(name)s(self, *args, **kwargs):
            result = self._ProxyBase__method_handler(
                self._ProxyBase__proxied, '%(name)s', *args, **kwargs
            )
            if result is missing:
                return self._ProxyBase__proxied.%(name)s(*args, **kwargs)
            return result
    """)
    for method in SPECIAL_METHODS:
        method = method_template % dict(name=method)
        exec(method)
    del method_template, method


def make_proxy_class(name, doc=None):
    """
    Creates a generic proxy class like :class:`ProxyClass` with the given `name`
    and `doc` as it's docstring.

    .. class:: .ProxyClass(proxied)

       .. classmethod:: method(handler)

          Decorator which takes a `handler` which gets called with the
          `proxied` object, the name of the called special method, positional
          and keyword arguments of the called method. If the handler returns
          :data:`brownie.datastructures.missing` the special method is called,
          to achieve the usual behaviour.

       .. classmethod:: getattr(handler)

          Decorator which takes a `handler` which gets called with the
          `proxied` object and the name of the accessed attribute.

       .. classmethod:: setattr(handler)

          Decorator which takes a `handler` which gets called with the
          `proxied` object, the name of the attribute which is set and the
          object it is set with.

       .. classmethod:: repr(handler)

          Decorator which takes a `handler` which gets called with the
          `proxied` object and is supposed to return a representation of the
          object per default ``repr(proxied)`` is returned.

    .. warning::

        At the moment there are several issues:

        - When checking the type of a :class:`ProxyClass` instance using
          :class:`type()` the :class:`ProxyClass` will be returned.

        - Especially with built-in objects this may yield otherwise unexpected
          results such as ``proxy(1) + proxy(1)`` not working.

        - Operations like ``proxy(1) < proxy(1)`` do not work because
          ``getattr(1, '__lt__')`` fails with an :exc:`AttributeError`.
    """
    return ProxyMeta(name, (ProxyBase, ), {'__doc__': doc})