# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/10/26
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import re, asset, pkg_resources

from .i18n import _

#------------------------------------------------------------------------------
DEFAULT_INFLECT = 0.75
DEFAULT_WEIGHT  = 1.0
DEFAULT_CLIPMIN = 0
DEFAULT_CLIPMAX = 1.3
DEFAULT_SKEW    = 0
DEFAULT_SPREAD  = 1.0
DEFAULT_FACTORS = 'length,charmix,variety,casemix,notword,phrase'

#------------------------------------------------------------------------------
common10k = frozenset(asset.load('passwordmeter:res/common.txt').read().split('\n'))

#------------------------------------------------------------------------------
def asym(value, target, switch=DEFAULT_INFLECT):
  if value >= target:
    return 1 - ( ( 1 - switch ) * target / value )
  return switch * value / target

#------------------------------------------------------------------------------
def curve(value, offset=0.05):
  if value < 0:
    value = 0
  return 1.0 / ( offset + value )

#------------------------------------------------------------------------------
def curveavg(values):
  score  = 0
  weight = 0
  for v in values:
    w = curve(v)
    score  += v * w
    weight += w
  return score / weight

#------------------------------------------------------------------------------
class Factor(object):
  def __init__(self, weight=DEFAULT_WEIGHT,
               clipmin=DEFAULT_CLIPMIN, clipmax=DEFAULT_CLIPMAX,
               skew=DEFAULT_SKEW, spread=DEFAULT_SPREAD,
               category=None,
               ):
    self.weight     = float(weight)
    self.clipmin    = float(clipmin)
    self.clipmax    = float(clipmax)
    self.skew       = float(skew)
    self.spread     = float(spread)
    if category is not None:
      self.category = category
  def test(self, value, extra):
    raise NotImplementedError()
  def adjust(self, value):
    value = self.skew + self.spread * value
    if value < self.clipmin:
      value = self.clipmin
    if value > self.clipmax:
      value = self.clipmax
    return value, self.weight

#------------------------------------------------------------------------------
class LengthFactor(Factor):
  category = 'length'
  def __init__(self, target=8, *args, **kw):
    super(LengthFactor, self).__init__(*args, **kw)
    self.target = int(target)
  def test(self, value, extra):
    value = len(value)
    return (asym(value, self.target), _('Increase the length of the password'))

#------------------------------------------------------------------------------
class CharmixFactor(Factor):
  category = 'charmix'
  matchers = (
    re.compile('[a-zA-Z]'),     # alpha / TODO: what about non-ascii letters?
    re.compile('[0-9]'),        # numeric
    re.compile('[^a-zA-Z0-9]'), # symbols
    )
  message = 'Use a good mix of numbers, letters, and symbols'
  def test(self, value, extra):
    if not self.matchers:
      return 1.0
    scores    = [len(matcher.findall(value)) for matcher in self.matchers]
    target    = max(1, 0.25 * sum(scores) / len(scores))
    scores    = [asym(score, target) * 1 / DEFAULT_INFLECT for score in scores]
    return (curveavg(scores), _(self.message))

#------------------------------------------------------------------------------
class CasemixFactor(CharmixFactor):
  category = 'casemix'
  matchers = (
    re.compile('[a-z]'),
    re.compile('[A-Z]'),
    )
  message = 'Use a good mix of UPPER case and lower case letters'

#------------------------------------------------------------------------------
class VarietyFactor(Factor):
  category = 'variety'
  def test(self, value, extra):
    diff = 1.0
    same = 0.0
    for idx in range(1, len(value)):
      if value[idx] == value[idx - 1]:
        same += 1
      else:
        diff += 1
    score = curveavg([
      len(set(value)) / max(1, float(len(value))),
      diff / (diff + same ** 1.5)])
    return (score, _('Minimize character duplicates and repetitions'))

#------------------------------------------------------------------------------
class NotWordFactor(Factor):
  category = 'notword'
  def test(self, value, extra):
    if value in common10k:
      return (0, _('Avoid using one of the ten thousand most common passwords'))
    # TODO: check against dictionary words too... maybe use ispell?
    #         http://code.activestate.com/recipes/117221-spell-checking/
    # todo: check for 'l33t-speak'...
    return (1.0, None)

#------------------------------------------------------------------------------
class PhraseFactor(Factor):
  category = 'phrase'
  base = 0.65
  message = 'Passphrases (e.g. an obfuscated sentence) are better than passwords'
  def test(self, value, extra):
    # todo: this might be improved... for example, i should:
    #   - value words of different lengths (large distribution) -- check stddev
    #   - check the likelihood that the elements are in fact words
    if not value:
      return (0, _(self.message))
    wlens  = [len(s) for s in value.split()]
    score  = asym(len(wlens), 4, switch=self.base)
    spread = max(wlens) - min(wlens)
    if spread <= 0:
      score = self.base
    else:
      score *= asym(spread, 4, switch=self.base)
      score = self.base * ( 1 + score )
    return (score, _(self.message))

#------------------------------------------------------------------------------
class Meter(object):

  #----------------------------------------------------------------------------
  def __init__(self, settings=None):
    if settings is None:
      settings = dict()
    self.threshold = float(settings.get('threshold', DEFAULT_INFLECT))
    factors = settings.get('factors') or DEFAULT_FACTORS
    if asset.isstr(factors):
      factors = [s.strip() for s in factors.split(',')]
    for key in settings.keys():
      key = key.split('.')
      if len(key) >= 3 \
          and key[0] == 'factor' and key[2] == 'class' \
          and key[1] not in factors:
        factors.append(key[1])
    self.factors   = [self._load(factor, settings) for factor in factors]
    self.logger    = asset.symbol(settings.get('logger'))
    self.pessimism = 1.0 / float(settings.get('pessimism', 10))

  #----------------------------------------------------------------------------
  def _load(self, factor, settings):
    predef = {
      'length'   : LengthFactor,
      'charmix'  : CharmixFactor,
      'casemix'  : CasemixFactor,
      'variety'  : VarietyFactor,
      'notword'  : NotWordFactor,
      'phrase'   : PhraseFactor,
      }
    params = dict()
    if asset.isstr(factor):
      for key, value in settings.items():
        if key.startswith('factor.' + factor + '.'):
          params[key[len(factor) + 8:]] = value
    factor = params.pop('class', factor)
    if factor in predef:
      return predef[factor](**params)
    return asset.symbol(factor)(**params)

  #----------------------------------------------------------------------------
  def test(self, value, extra=None):
    '''
    Tests the supplied `value` for general characteristics of a good
    password. Returns a tuple of (float, dict), where float is a
    quotient in the range [0, 1] representing very weak to very strong
    passwords. dict, which may be None, is a list of known ways that
    the password can be improved, where the key is a fixed value (from
    the list below or from the settings in the constructor) and the
    value is a human-readable (potentially internationalized) string.

    The optional parameter `extra` can be any kind of object that is
    passed through unaltered to all factors contributing to this
    meter. This is primarily for custom :class:`Factor`
    implementations that need extra information -- it is not used by
    any of the standard factors.
    '''
    score  = 0
    weight = 0
    morelist = []
    for factor in self.factors:
      result   = factor.test(value, extra)
      scr, wgt = factor.adjust(result[0])
      crv      = curve(scr, offset=self.pessimism)
      if self.logger:
        self.logger.debug(
          'factor %s: score=%f, base-weight=%f, curve-weight=%f',
          factor.category, scr, wgt, crv)
      wgt    *= crv
      score  += scr * wgt
      weight += wgt
      if result[1]:
        morelist.append((scr, factor, result[1]))
    score = max(0, min(1, score / weight))
    more  = dict()
    if score < 1.0:
      # todo: this should be a slightly more intelligent selection process
      for scur, factor, reason in morelist:
        if scur < self.threshold:
          more[factor.category] = reason
    return (score, more)

#------------------------------------------------------------------------------
def test(value, extra=None):
  return Meter().test(value, extra=extra)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
