# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/10/26
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import sys, argparse, getpass

from .__init__ import Meter
from .i18n import _

ratings = (
  'Extremely weak',
  'Excessively weak',
  'Very weak',
  'Weak',
  'Moderately strong',
  'Strong',
  'Very strong',
  )

#------------------------------------------------------------------------------
def main(argv=None):

  cli = argparse.ArgumentParser(
    description = _(
      'Password strength meter - gives a coefficient of how strong'
      ' a password is (0 = extremely weak, 1 = extremely strong)'
      ' and lists ways that a password can be improved.')
    )

  cli.add_argument(
    _('-i'), _('--ini'), metavar=_('FILENAME'),
    dest='inifile', default=None,
    help=_('INI settings filename'))

  cli.add_argument(
    _('-s'), _('--setting'), metavar=_('NAME=VALUE'),
    dest='settings', default=[], action='append',
    help=_('override a specific setting'))

  cli.add_argument(
    _('-m'), _('--minimum'), metavar=_('FLOAT'),
    dest='minimum', default=0.75, type=float,
    help=_('minimum password strength for %(prog)s to return'
           ' a success status (default: %(default)s)'))

  cli.add_argument(
    'password', metavar=_('PASSWORD'), nargs='?',
    help=_('password to test; if exactly "-", the password is read from'
           ' STDIN and if not specified, it will be prompted for'))

  options = cli.parse_args(args=argv)

  settings = dict()
  # todo: load ini file...
  settings.update(dict([s.split('=', 1) for s in options.settings]))

  if options.password == '-':
    options.password = sys.stdin.read()
  elif options.password is None:
    options.password = getpass.getpass()

  meter   = Meter(settings=settings)
  result  = meter.test(options.password)

  print 'Password strength: {} ({})'.format(
    result[0],
    _(ratings[min(len(ratings) - 1, int(result[0] * len(ratings)))])
    )

  if result[1]:
    print 'Possible improvements:'
    for item in result[1].values():
      print '  -',item

  if result[0] >= options.minimum:
    return 0
  return 100 + int(round(result[0] * 100))

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
