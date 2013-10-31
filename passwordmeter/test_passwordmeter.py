# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/10/29
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import unittest
import passwordmeter as pwm

class TestFactor(pwm.Factor):
  category = 'test'
  def test(self, value, extra):
    return (0.5, 'test value is: ' + value)

#------------------------------------------------------------------------------
class TestPasswordMeter(unittest.TestCase):

  #----------------------------------------------------------------------------
  def test_default(self):
    res = pwm.test('password')
    self.assertEqual(len(res), 2)
    self.assertIsInstance(res[0], float)
    self.assertIsInstance(res[1], dict)

  #----------------------------------------------------------------------------
  def test_notword(self):
    self.assertEqual(
      pwm.Meter(settings=dict(factors='notword')).test('password')[0], 0)
    self.assertEqual(
      pwm.Meter(settings=dict(factors='notword')).test('not0klsd@#$')[0], 1)

  #----------------------------------------------------------------------------
  def test_factorsAsString(self):
    self.assertEqual(
      pwm.Meter(settings=dict(
        factors='length,passwordmeter.test_passwordmeter.TestFactor')).test('short')[1],
      {'test': 'test value is: short',
       'length': 'Increase the length of the password'})

  #----------------------------------------------------------------------------
  def test_factorsAsList(self):
    self.assertEqual(
      pwm.Meter(settings=dict(
        factors=['length', TestFactor])).test('short')[1],
      {'test': 'test value is: short',
       'length': 'Increase the length of the password'})

  #----------------------------------------------------------------------------
  def test_strength(self):
    meter = pwm.Meter()
    passwords = (
      '',
      'password',
      'password1',
      'pssa',
      'pss4wr',
      'pssawrd',
      'pss4wr0d',
      'p$$4wr0d!',
      'p$$4WR0d!',
      'p$4$WR0d!',
      'my voice is my p$$4WR0d!',
      'mY voiCE is my p$$4WR0d!',
      'mY voiC3 !s m-y p$$4WR0d!',
      )
    for idx, pw0 in enumerate(passwords[:-1]):
      pw1 = passwords[idx + 1]
      sc0 = meter.test(pw0)[0]
      sc1 = meter.test(pw1)[0]
      self.assertLessEqual(
        sc0, sc1,
        'expected password "%s" (%f) to be as strong or stronger than "%s" (%f)'
        % (pw1, sc1, pw0, sc0))

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
