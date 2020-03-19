# Originally engineered by Benoît Bryon
# Source addressed here: https://tech.people-doc.com/python-class-based-decorators.html#the-decorator-class

# Sentinel to detect undefined function argument.
UNDEFINED_FUNCTION = object()


class Decorator(object):
    """Base class to easily create convenient decorators.

    Override :py:meth:`setup`, :py:meth:`run` or :py:meth:`decorate` to create
    custom decorators:

    * :py:meth:`setup` is dedicated to setup, i.e. setting decorator's internal
      options.
      :py:meth:`__init__` calls :py:meth:`setup`.

    * :py:meth:`decorate` is dedicated to wrapping function, i.e. remember the
      function to decorate.
      :py:meth:`__init__` and :py:meth:`__call__` may call :py:meth:`decorate`,
      depending on the usage.

    * :py:meth:`run` is dedicated to execution, i.e. running the decorated
      function.
      :py:meth:`__call__` calls :py:meth:`run` if a function has already been
      decorated.

    Decorator instances are callables. The :py:meth:`__call__` method has a
    special implementation in Decorator. Generally, consider overriding
    :py:meth:`run` instead of :py:meth:`__call__`.

    """
    def __init__(self, func=UNDEFINED_FUNCTION, *args, **kwargs):
        """Constructor.

        Accepts one optional positional argument: the function to decorate.

        Other arguments **must** be keyword arguments.

        And beware passing ``func`` as keyword argument: it would be used as
        the function to decorate.

        """
        self.options = {}

        self.setup(*args, **kwargs)
        self.decorated = UNDEFINED_FUNCTION
        if func is not UNDEFINED_FUNCTION:
            # The first (implicit) argument passed by python on init for decorators is the function to decorate
            self.decorate(func)

    def decorate(self, func):
        """Remember the function to decorate.

        Raises TypeError if ``func`` is not a callable.

        """
        if not callable(func):
            raise TypeError('Cannot decorate non callable object "{func}"'
                            .format(func=func))
        self.decorated = func
        return self

    def setup(self, *args, **kwargs):
        """Store decorator's options"""
        self.options = kwargs
        return self

    def __call__(self, *args, **kwargs):
        """Run decorated function if available, else decorate first arg."""
        if self.decorated is UNDEFINED_FUNCTION:
            # This code path is run when we call the class initialization within the decorator
            # (i.e. the decorator has parentheses)
            func = args[0]
            if args[1:] or kwargs:
                raise ValueError('Cannot decorate and setup simultaneously '
                                 'with __call__(). Use __init__() or '
                                 'setup() for setup. Use __call__() or '
                                 'decorate() to decorate.')
            self.decorate(func)
            return self
        else:
            # This code path is run when we build the decorator "on the fly," because we've already run decorate in init
            # (i.e. when the decorator doesn't have parentheses)
            return self.run(*args, **kwargs)

    def run(self, *args, **kwargs):
        """Actually run the decorator.

        This base implementation is a transparent proxy to the decorated
        function: it passes positional and keyword arguments as is, and returns
        result.

        """
        return self.decorated(*args, **kwargs)
