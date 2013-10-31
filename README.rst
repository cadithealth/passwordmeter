=======================
Password Strength Meter
=======================

A configurable, extensible password strength measuring library.

TL;DR
=====

Install:

.. code-block:: bash

  $ pip install passwordmeter

Use from within an application with the default factors:

.. code-block:: python

  import passwordmeter

  strength, improvements = passwordmeter.test(sys.argv[1])

  if strength < 0.5:
    print 'Your password is too weak.'

Use on the command line:

.. code-block:: bash

  $ pwm 'password'
  Password strength: 0.132549901057 (Extremely weak)
  Possible improvements:
    - Use a good mix of numbers, letters, and symbols
    - Avoid using one of the ten thousand most common passwords
    - Use a good mix of UPPER case and lower case letters

Overview
========

The main function provided by the `passwordmeter` package is the
``Meter.test()`` method, which returns a tuple of (float, dict). The
float is the strength of the password in the range 0 to 1 (inclusive),
where 0 is extremely weak and 1 is extremely strong. The second
parameter, which may be ``None``, is a dictionary of ways the password
could be improved. The keys of the dict are general "categories" of
ways to improve the password (e.g. "length") that are fixed strings,
and the values are internationalizable strings that are human-friendly
descriptions and possibly tailored to the specific password.

A password's strength is determined by doing a weighted, skewed,
average of a set of "factors". The `Meter` constructor takes a
`settings` dictionary that configures, customizes, and/or supplements
the default set of factors.

The `passwordmeter.test` is a helper function that simply uses the
default settings to test the strength of a password, and is
effectively a shorthand for ``Meter().test(...)``.

For example, to use a custom selection of factors:

.. code-block:: python

  import passwordmeter

  # use only the 'length' and 'charmix' factors
  meter = passwordmeter.Meter(settings=dict(factors='length,charmix'))

  strength, improvements = meter.test('s3cr3t p4ssW0RD!')


Settings
========

The `settings` attribute to the `Meter` constructor is a dictionary
with the following keys:

* ``factors``:

  This is a comma-separated list of factors to use in calculating the
  strength of a password. Each element in the list is either the name
  of a known factor or a symbol-spec as defined by the `asset module
  <https://pypi.python.org/pypi/asset>`_. See
  ``passwordmeter.DEFAULT_FACTORS`` for the default list of factors
  (and their names).

  For example, to use only the 'length' factor and a custom factor:

  .. code-block:: python

    import passwordmeter

    class SillyFactor(passwordmeter.Factor):
      category = 'silly'
      def test(self, value, extra):
        if value == 'silly':
          return (0, 'That is a silly password!')
        return (1, None)

    meter = passwordmeter.Meter(
      settings=dict(factors='length,mypackage.SillyFactor'))

Custom Factors
==============

A custom factor should subclass `passwordmeter.Factor`, implement the
`test` method, and have a unique `category` (string) attribute.

The `test` method takes two parameters: the `value` to be tested, and
an opaque `extra` parameter that is supplied by the calling
application (and can be ignored if not needed). It should return a
tuple of (float, str).

The first element (float) of the return tuple must be greater or equal
to zero. Although it should generally not be greater than 1.0, a
factor *may* return a greater value: this is used to artificially
boost the strength of the total outcome relative to the other factors
if applicable. Note, however, that the Meter class will always clip
the final outcome to the inclusive range [0, 1].

The second element of the return tuple should be a string, which is a
description of how to improve the provided password. This string can
be ``None`` if no known way exists to improve this password for this
specific factor. Note that Meter class will associate this description
with the factor's category in the final outcome.
